"""
USB Device Manager for Phone Recovery
Handles USB device detection, authorization, and info gathering for Android and iOS devices.
"""

import asyncio
import subprocess
import re
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class USBDevice:
    """Represents a connected USB device"""
    device_id: str
    device_type: str  # "android" | "ios" | "unknown"
    device_model: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    is_authorized: bool = False
    usb_bus: Optional[str] = None
    usb_device: Optional[str] = None
    storage_total: Optional[int] = None
    os_version: Optional[str] = None


class USBDeviceManager:
    """
    Manages USB device detection and authorization for phone recovery.
    Supports both Android (via ADB) and iOS (via libimobiledevice) devices.
    """

    def __init__(self):
        self._adb_path = self._find_adb()
        self._idevice_path = self._find_idevice_tools()

    def _find_adb(self) -> str:
        """Find ADB binary path"""
        try:
            result = subprocess.run(["which", "adb"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "adb"

    def _find_idevice_tools(self) -> Dict[str, str]:
        """Find libimobiledevice tool paths"""
        tools = {}
        for tool in ["idevice_id", "ideviceinfo", "idevicebackup2"]:
            try:
                result = subprocess.run(["which", tool], capture_output=True, text=True)
                if result.returncode == 0:
                    tools[tool] = result.stdout.strip()
            except Exception:
                tools[tool] = tool
        return tools

    async def scan_devices(self) -> List[USBDevice]:
        """
        Scan for all connected USB devices (Android and iOS).
        Returns a list of USBDevice objects.
        """
        devices = []

        # Scan for Android devices
        android_devices = await self._scan_android_devices()
        devices.extend(android_devices)

        # Scan for iOS devices
        ios_devices = await self._scan_ios_devices()
        devices.extend(ios_devices)

        logger.info(f"Found {len(devices)} USB devices: {len(android_devices)} Android, {len(ios_devices)} iOS")
        return devices

    async def _scan_android_devices(self) -> List[USBDevice]:
        """Scan for connected Android devices via ADB"""
        devices = []

        try:
            # Start ADB server if not running
            await self._run_command([self._adb_path, "start-server"])

            # List devices
            result = await self._run_command([self._adb_path, "devices", "-l"])

            if result.returncode != 0:
                logger.error(f"ADB devices command failed: {result.stderr}")
                return devices

            lines = result.stdout.strip().split("\n")[1:]  # Skip header

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                device_id = parts[0]
                status = parts[1]

                device = USBDevice(
                    device_id=device_id,
                    device_type="android",
                    is_authorized=(status == "device"),
                    serial_number=device_id
                )

                # Parse additional info from -l output
                for part in parts[2:]:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        if key == "model":
                            device.device_model = value.replace("_", " ")
                        elif key == "device":
                            device.manufacturer = value

                # Get more details if authorized
                if device.is_authorized:
                    device = await self._get_android_device_details(device)

                devices.append(device)

        except Exception as e:
            logger.error(f"Error scanning Android devices: {e}")

        return devices

    async def _scan_ios_devices(self) -> List[USBDevice]:
        """Scan for connected iOS devices via libimobiledevice"""
        devices = []

        try:
            # List iOS devices
            idevice_id = self._idevice_path.get("idevice_id", "idevice_id")
            result = await self._run_command([idevice_id, "-l"])

            if result.returncode != 0:
                # No iOS devices or tool not available
                return devices

            udids = result.stdout.strip().split("\n")

            for udid in udids:
                if not udid.strip():
                    continue

                device = USBDevice(
                    device_id=udid.strip(),
                    device_type="ios",
                    serial_number=udid.strip(),
                    is_authorized=True  # If listed, it's paired
                )

                # Get device details
                device = await self._get_ios_device_details(device)
                devices.append(device)

        except Exception as e:
            logger.error(f"Error scanning iOS devices: {e}")

        return devices

    async def _get_android_device_details(self, device: USBDevice) -> USBDevice:
        """Get detailed info for an Android device"""
        try:
            # Get device model
            result = await self._run_command([
                self._adb_path, "-s", device.device_id,
                "shell", "getprop", "ro.product.model"
            ])
            if result.returncode == 0:
                device.device_model = result.stdout.strip()

            # Get manufacturer
            result = await self._run_command([
                self._adb_path, "-s", device.device_id,
                "shell", "getprop", "ro.product.manufacturer"
            ])
            if result.returncode == 0:
                device.manufacturer = result.stdout.strip()

            # Get Android version
            result = await self._run_command([
                self._adb_path, "-s", device.device_id,
                "shell", "getprop", "ro.build.version.release"
            ])
            if result.returncode == 0:
                device.os_version = f"Android {result.stdout.strip()}"

            # Get storage info
            result = await self._run_command([
                self._adb_path, "-s", device.device_id,
                "shell", "df", "/data"
            ])
            if result.returncode == 0:
                device.storage_total = self._parse_storage_info(result.stdout)

        except Exception as e:
            logger.error(f"Error getting Android device details: {e}")

        return device

    async def _get_ios_device_details(self, device: USBDevice) -> USBDevice:
        """Get detailed info for an iOS device"""
        try:
            ideviceinfo = self._idevice_path.get("ideviceinfo", "ideviceinfo")
            result = await self._run_command([ideviceinfo, "-u", device.device_id])

            if result.returncode == 0:
                info = self._parse_plist_output(result.stdout)
                device.device_model = info.get("ProductType", info.get("DeviceName"))
                device.os_version = f"iOS {info.get('ProductVersion', 'Unknown')}"
                device.manufacturer = "Apple"

                # Try to get storage
                if "TotalDataCapacity" in info:
                    device.storage_total = int(info["TotalDataCapacity"])

        except Exception as e:
            logger.error(f"Error getting iOS device details: {e}")

        return device

    async def authorize_device(self, device_id: str) -> bool:
        """
        Authorize a device for data extraction.
        For Android: Accept ADB authorization prompt
        For iOS: Trust certificate (requires physical confirmation on device)
        """
        try:
            # Check if it's an Android device
            result = await self._run_command([self._adb_path, "devices"])
            if device_id in result.stdout:
                # Android device - try to reconnect to trigger auth
                await self._run_command([self._adb_path, "-s", device_id, "reconnect"])
                await asyncio.sleep(2)

                # Check if now authorized
                result = await self._run_command([self._adb_path, "devices"])
                return f"{device_id}\tdevice" in result.stdout

            # Check if it's an iOS device
            idevice_id = self._idevice_path.get("idevice_id", "idevice_id")
            result = await self._run_command([idevice_id, "-l"])
            if device_id in result.stdout:
                # iOS device - it's already paired if listed
                return True

            logger.warning(f"Device {device_id} not found")
            return False

        except Exception as e:
            logger.error(f"Error authorizing device {device_id}: {e}")
            return False

    async def get_device_info(self, device_id: str) -> Optional[USBDevice]:
        """Get detailed information for a specific device"""
        devices = await self.scan_devices()
        for device in devices:
            if device.device_id == device_id:
                return device
        return None

    async def is_device_connected(self, device_id: str) -> bool:
        """Check if a device is currently connected"""
        devices = await self.scan_devices()
        return any(d.device_id == device_id for d in devices)

    async def wait_for_device(self, device_id: str, timeout: int = 60) -> bool:
        """Wait for a specific device to connect"""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await self.is_device_connected(device_id):
                return True
            await asyncio.sleep(2)
        return False

    async def _run_command(self, cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Run a shell command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            return subprocess.CompletedProcess(
                cmd,
                process.returncode,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace")
            )
        except asyncio.TimeoutError:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, -1, "", "Timeout")
        except Exception as e:
            logger.error(f"Error running command {' '.join(cmd)}: {e}")
            return subprocess.CompletedProcess(cmd, -1, "", str(e))

    def _parse_storage_info(self, df_output: str) -> Optional[int]:
        """Parse df command output to get total storage in bytes"""
        try:
            lines = df_output.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 2:
                    # Size is in 1K blocks
                    return int(parts[1]) * 1024
        except Exception:
            pass
        return None

    def _parse_plist_output(self, output: str) -> Dict[str, str]:
        """Parse ideviceinfo plist-style output"""
        info = {}
        for line in output.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()
        return info


# Singleton instance
_device_manager: Optional[USBDeviceManager] = None


def get_device_manager() -> USBDeviceManager:
    """Get the singleton USBDeviceManager instance"""
    global _device_manager
    if _device_manager is None:
        _device_manager = USBDeviceManager()
    return _device_manager
