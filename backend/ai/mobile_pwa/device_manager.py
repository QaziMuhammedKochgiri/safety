"""
Device Manager
Manages device information, capabilities, and security for mobile PWA.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib


class DeviceType(str, Enum):
    """Types of devices."""
    ANDROID_PHONE = "android_phone"
    ANDROID_TABLET = "android_tablet"
    IPHONE = "iphone"
    IPAD = "ipad"
    DESKTOP_WINDOWS = "desktop_windows"
    DESKTOP_MAC = "desktop_mac"
    DESKTOP_LINUX = "desktop_linux"
    CHROMEBOOK = "chromebook"
    UNKNOWN = "unknown"


class BiometricType(str, Enum):
    """Types of biometric authentication."""
    FINGERPRINT = "fingerprint"
    FACE_ID = "face_id"
    IRIS = "iris"
    VOICE = "voice"
    NONE = "none"


class SecurityLevel(str, Enum):
    """Device security levels."""
    HIGH = "high"  # Biometrics + PIN + encryption
    MEDIUM = "medium"  # PIN/password + encryption
    LOW = "low"  # Basic lock screen
    NONE = "none"  # No security


@dataclass
class DeviceCapabilities:
    """Device capabilities for feature detection."""
    # Storage
    has_indexeddb: bool
    has_cache_api: bool
    has_local_storage: bool
    storage_estimate_bytes: Optional[int]

    # Media
    has_camera: bool
    has_microphone: bool
    has_geolocation: bool
    has_accelerometer: bool
    has_gyroscope: bool

    # PWA features
    has_service_worker: bool
    has_push_notifications: bool
    has_background_sync: bool
    has_periodic_sync: bool
    has_share_api: bool
    has_file_system_api: bool

    # Security
    has_biometrics: bool
    biometric_types: List[BiometricType]
    has_secure_storage: bool
    has_web_crypto: bool

    # Network
    has_network_info: bool
    connection_type: Optional[str]  # wifi, cellular, etc.
    effective_type: Optional[str]  # 4g, 3g, 2g, slow-2g

    # Display
    screen_width: int
    screen_height: int
    pixel_ratio: float
    is_touch_screen: bool
    supports_hdr: bool

    # Performance
    hardware_concurrency: int  # CPU cores
    device_memory_gb: Optional[float]


@dataclass
class DeviceInfo:
    """Information about a registered device."""
    device_id: str
    user_id: str
    device_type: DeviceType
    device_name: str

    # Hardware
    manufacturer: Optional[str]
    model: Optional[str]
    os_name: str
    os_version: str

    # Browser/PWA
    browser_name: str
    browser_version: str
    is_pwa_installed: bool
    pwa_display_mode: str  # standalone, browser, fullscreen

    # Capabilities
    capabilities: DeviceCapabilities

    # Security
    security_level: SecurityLevel
    has_screen_lock: bool
    biometric_enabled: bool

    # Registration
    registered_at: str
    last_seen: str
    last_ip: Optional[str]
    last_location: Optional[Dict[str, float]]

    # Status
    is_active: bool
    is_trusted: bool
    trust_score: float  # 0-100


@dataclass
class SecurityStatus:
    """Security status for a device."""
    device_id: str
    overall_status: str  # secure, warning, at_risk

    # Checks
    screen_lock_enabled: bool
    encryption_enabled: bool
    biometric_enabled: bool
    os_up_to_date: bool
    app_up_to_date: bool

    # Threats
    rooted_or_jailbroken: bool
    debug_mode_enabled: bool
    unknown_sources_enabled: bool
    developer_options_enabled: bool

    # Recent activity
    suspicious_activity_detected: bool
    suspicious_activity_details: Optional[str]

    # Recommendations
    recommendations: List[str]
    checked_at: str


@dataclass
class DeviceSession:
    """An active session on a device."""
    session_id: str
    device_id: str
    user_id: str
    started_at: str
    last_activity: str
    expires_at: str
    is_active: bool
    ip_address: Optional[str]
    location: Optional[Dict[str, float]]


class DeviceManager:
    """Manages devices for the PWA."""

    # Minimum requirements for trusted devices
    MIN_REQUIREMENTS = {
        "storage_bytes": 100 * 1024 * 1024,  # 100 MB
        "screen_width": 320,
        "screen_height": 480
    }

    def __init__(self):
        self.devices: Dict[str, DeviceInfo] = {}
        self.user_devices: Dict[str, List[str]] = {}  # user_id -> device_ids
        self.sessions: Dict[str, DeviceSession] = {}
        self.security_checks: Dict[str, SecurityStatus] = {}

    def register_device(
        self,
        user_id: str,
        device_name: str,
        device_type: DeviceType,
        os_name: str,
        os_version: str,
        browser_name: str,
        browser_version: str,
        capabilities: DeviceCapabilities,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        is_pwa_installed: bool = False,
        pwa_display_mode: str = "browser"
    ) -> DeviceInfo:
        """Register a new device."""
        device_id = hashlib.md5(
            f"{user_id}-{manufacturer}-{model}-{browser_name}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        now = datetime.datetime.now().isoformat()

        # Determine security level
        security_level = self._assess_security_level(capabilities)

        # Calculate trust score
        trust_score = self._calculate_trust_score(capabilities, security_level)

        device = DeviceInfo(
            device_id=device_id,
            user_id=user_id,
            device_type=device_type,
            device_name=device_name,
            manufacturer=manufacturer,
            model=model,
            os_name=os_name,
            os_version=os_version,
            browser_name=browser_name,
            browser_version=browser_version,
            is_pwa_installed=is_pwa_installed,
            pwa_display_mode=pwa_display_mode,
            capabilities=capabilities,
            security_level=security_level,
            has_screen_lock=True,  # Assume true, verify later
            biometric_enabled=capabilities.has_biometrics,
            registered_at=now,
            last_seen=now,
            last_ip=None,
            last_location=None,
            is_active=True,
            is_trusted=trust_score >= 70,
            trust_score=trust_score
        )

        self.devices[device_id] = device

        # Track user devices
        if user_id not in self.user_devices:
            self.user_devices[user_id] = []
        self.user_devices[user_id].append(device_id)

        return device

    def update_device(
        self,
        device_id: str,
        ip_address: Optional[str] = None,
        location: Optional[Dict[str, float]] = None,
        is_pwa_installed: Optional[bool] = None,
        capabilities: Optional[DeviceCapabilities] = None
    ) -> bool:
        """Update device information."""
        if device_id not in self.devices:
            return False

        device = self.devices[device_id]
        device.last_seen = datetime.datetime.now().isoformat()

        if ip_address:
            device.last_ip = ip_address
        if location:
            device.last_location = location
        if is_pwa_installed is not None:
            device.is_pwa_installed = is_pwa_installed
        if capabilities:
            device.capabilities = capabilities
            device.security_level = self._assess_security_level(capabilities)
            device.trust_score = self._calculate_trust_score(
                capabilities, device.security_level
            )
            device.is_trusted = device.trust_score >= 70

        return True

    def unregister_device(self, device_id: str) -> bool:
        """Unregister a device."""
        if device_id not in self.devices:
            return False

        device = self.devices[device_id]
        user_id = device.user_id

        # Remove from user devices
        if user_id in self.user_devices:
            if device_id in self.user_devices[user_id]:
                self.user_devices[user_id].remove(device_id)

        # End all sessions
        for session in list(self.sessions.values()):
            if session.device_id == device_id:
                del self.sessions[session.session_id]

        del self.devices[device_id]
        return True

    def create_session(
        self,
        device_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        location: Optional[Dict[str, float]] = None,
        session_duration_hours: int = 24
    ) -> Optional[DeviceSession]:
        """Create a new session for a device."""
        if device_id not in self.devices:
            return None

        session_id = hashlib.md5(
            f"{device_id}-{user_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        now = datetime.datetime.now()
        expires = now + datetime.timedelta(hours=session_duration_hours)

        session = DeviceSession(
            session_id=session_id,
            device_id=device_id,
            user_id=user_id,
            started_at=now.isoformat(),
            last_activity=now.isoformat(),
            expires_at=expires.isoformat(),
            is_active=True,
            ip_address=ip_address,
            location=location
        )

        self.sessions[session_id] = session

        # Update device
        self.update_device(device_id, ip_address=ip_address, location=location)

        return session

    def validate_session(self, session_id: str) -> Optional[DeviceSession]:
        """Validate a session."""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # Check if expired
        expires = datetime.datetime.fromisoformat(session.expires_at)
        if datetime.datetime.now() > expires:
            session.is_active = False
            return None

        if not session.is_active:
            return None

        # Update last activity
        session.last_activity = datetime.datetime.now().isoformat()
        return session

    def end_session(self, session_id: str) -> bool:
        """End a session."""
        if session_id not in self.sessions:
            return False

        self.sessions[session_id].is_active = False
        return True

    def end_all_sessions(self, user_id: str, except_session: Optional[str] = None) -> int:
        """End all sessions for a user."""
        count = 0
        for session in self.sessions.values():
            if session.user_id == user_id and session.session_id != except_session:
                session.is_active = False
                count += 1
        return count

    def check_security(self, device_id: str) -> Optional[SecurityStatus]:
        """Perform security check on a device."""
        if device_id not in self.devices:
            return None

        device = self.devices[device_id]
        caps = device.capabilities
        recommendations = []

        # Security checks
        screen_lock_enabled = device.has_screen_lock
        encryption_enabled = caps.has_secure_storage and caps.has_web_crypto
        biometric_enabled = device.biometric_enabled
        os_up_to_date = True  # Would need version checking logic
        app_up_to_date = True  # Would need version checking logic

        # Threat detection (simulated - would need actual detection logic)
        rooted_or_jailbroken = False
        debug_mode_enabled = False
        unknown_sources_enabled = False
        developer_options_enabled = False

        # Generate recommendations
        if not biometric_enabled and caps.has_biometrics:
            recommendations.append("Enable biometric authentication for faster, more secure access")
        if not screen_lock_enabled:
            recommendations.append("Enable screen lock to protect your device")
        if not encryption_enabled:
            recommendations.append("Enable device encryption to protect your data")
        if not device.is_pwa_installed:
            recommendations.append("Install the app for better offline access and security")

        # Determine overall status
        critical_issues = [
            rooted_or_jailbroken,
            not screen_lock_enabled,
            not encryption_enabled
        ]
        warning_issues = [
            not biometric_enabled,
            developer_options_enabled,
            unknown_sources_enabled
        ]

        if any(critical_issues):
            overall_status = "at_risk"
        elif any(warning_issues):
            overall_status = "warning"
        else:
            overall_status = "secure"

        status = SecurityStatus(
            device_id=device_id,
            overall_status=overall_status,
            screen_lock_enabled=screen_lock_enabled,
            encryption_enabled=encryption_enabled,
            biometric_enabled=biometric_enabled,
            os_up_to_date=os_up_to_date,
            app_up_to_date=app_up_to_date,
            rooted_or_jailbroken=rooted_or_jailbroken,
            debug_mode_enabled=debug_mode_enabled,
            unknown_sources_enabled=unknown_sources_enabled,
            developer_options_enabled=developer_options_enabled,
            suspicious_activity_detected=False,
            suspicious_activity_details=None,
            recommendations=recommendations,
            checked_at=datetime.datetime.now().isoformat()
        )

        self.security_checks[device_id] = status
        return status

    def get_user_devices(self, user_id: str) -> List[DeviceInfo]:
        """Get all devices for a user."""
        device_ids = self.user_devices.get(user_id, [])
        return [self.devices[did] for did in device_ids if did in self.devices]

    def get_active_sessions(self, user_id: str) -> List[DeviceSession]:
        """Get active sessions for a user."""
        return [
            s for s in self.sessions.values()
            if s.user_id == user_id and s.is_active
        ]

    def detect_device_type(
        self,
        user_agent: str,
        screen_width: int,
        screen_height: int,
        is_touch: bool
    ) -> DeviceType:
        """Detect device type from characteristics."""
        ua_lower = user_agent.lower()

        # Check for mobile devices
        if "iphone" in ua_lower:
            return DeviceType.IPHONE
        if "ipad" in ua_lower:
            return DeviceType.IPAD
        if "android" in ua_lower:
            if screen_width < 768 or is_touch:
                return DeviceType.ANDROID_PHONE
            else:
                return DeviceType.ANDROID_TABLET

        # Check for desktop
        if "windows" in ua_lower:
            return DeviceType.DESKTOP_WINDOWS
        if "macintosh" in ua_lower or "mac os" in ua_lower:
            return DeviceType.DESKTOP_MAC
        if "linux" in ua_lower:
            if "cros" in ua_lower:
                return DeviceType.CHROMEBOOK
            return DeviceType.DESKTOP_LINUX

        return DeviceType.UNKNOWN

    def check_minimum_requirements(
        self,
        capabilities: DeviceCapabilities
    ) -> Dict[str, Any]:
        """Check if device meets minimum requirements."""
        results = {
            "meets_requirements": True,
            "issues": []
        }

        # Storage check
        if capabilities.storage_estimate_bytes:
            if capabilities.storage_estimate_bytes < self.MIN_REQUIREMENTS["storage_bytes"]:
                results["meets_requirements"] = False
                results["issues"].append(
                    f"Insufficient storage. Required: {self.MIN_REQUIREMENTS['storage_bytes'] // (1024*1024)}MB"
                )

        # Screen size check
        if capabilities.screen_width < self.MIN_REQUIREMENTS["screen_width"]:
            results["meets_requirements"] = False
            results["issues"].append(
                f"Screen width too small. Required: {self.MIN_REQUIREMENTS['screen_width']}px"
            )

        if capabilities.screen_height < self.MIN_REQUIREMENTS["screen_height"]:
            results["meets_requirements"] = False
            results["issues"].append(
                f"Screen height too small. Required: {self.MIN_REQUIREMENTS['screen_height']}px"
            )

        # Required features
        if not capabilities.has_indexeddb:
            results["meets_requirements"] = False
            results["issues"].append("IndexedDB required for offline storage")

        if not capabilities.has_service_worker:
            results["meets_requirements"] = False
            results["issues"].append("Service Worker required for offline functionality")

        return results

    def get_feature_availability(
        self,
        device_id: str
    ) -> Dict[str, bool]:
        """Get feature availability for a device."""
        if device_id not in self.devices:
            return {}

        caps = self.devices[device_id].capabilities

        return {
            "offline_mode": caps.has_service_worker and caps.has_indexeddb,
            "push_notifications": caps.has_push_notifications,
            "camera_capture": caps.has_camera,
            "voice_recording": caps.has_microphone,
            "location_tracking": caps.has_geolocation,
            "biometric_auth": caps.has_biometrics,
            "file_upload": caps.has_file_system_api,
            "background_sync": caps.has_background_sync,
            "share_content": caps.has_share_api,
            "secure_storage": caps.has_secure_storage
        }

    def _assess_security_level(self, capabilities: DeviceCapabilities) -> SecurityLevel:
        """Assess the security level based on capabilities."""
        has_biometrics = capabilities.has_biometrics and len(capabilities.biometric_types) > 0
        has_secure_storage = capabilities.has_secure_storage
        has_crypto = capabilities.has_web_crypto

        if has_biometrics and has_secure_storage and has_crypto:
            return SecurityLevel.HIGH
        elif has_secure_storage and has_crypto:
            return SecurityLevel.MEDIUM
        elif has_secure_storage or has_crypto:
            return SecurityLevel.LOW
        else:
            return SecurityLevel.NONE

    def _calculate_trust_score(
        self,
        capabilities: DeviceCapabilities,
        security_level: SecurityLevel
    ) -> float:
        """Calculate trust score for a device (0-100)."""
        score = 0.0

        # Security level (40 points max)
        security_scores = {
            SecurityLevel.HIGH: 40,
            SecurityLevel.MEDIUM: 30,
            SecurityLevel.LOW: 15,
            SecurityLevel.NONE: 0
        }
        score += security_scores[security_level]

        # Biometrics (15 points)
        if capabilities.has_biometrics:
            score += 15

        # Secure storage (15 points)
        if capabilities.has_secure_storage:
            score += 15

        # Web Crypto (10 points)
        if capabilities.has_web_crypto:
            score += 10

        # Service Worker (10 points)
        if capabilities.has_service_worker:
            score += 10

        # IndexedDB (5 points)
        if capabilities.has_indexeddb:
            score += 5

        # Cache API (5 points)
        if capabilities.has_cache_api:
            score += 5

        return min(100.0, score)

    def get_device_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered devices."""
        total = len(self.devices)
        by_type = {}
        by_security = {}
        active_count = 0
        trusted_count = 0
        pwa_installed = 0

        for device in self.devices.values():
            # By type
            dtype = device.device_type.value
            by_type[dtype] = by_type.get(dtype, 0) + 1

            # By security level
            slevel = device.security_level.value
            by_security[slevel] = by_security.get(slevel, 0) + 1

            # Counts
            if device.is_active:
                active_count += 1
            if device.is_trusted:
                trusted_count += 1
            if device.is_pwa_installed:
                pwa_installed += 1

        return {
            "total_devices": total,
            "active_devices": active_count,
            "trusted_devices": trusted_count,
            "pwa_installed": pwa_installed,
            "by_type": by_type,
            "by_security_level": by_security,
            "active_sessions": sum(1 for s in self.sessions.values() if s.is_active)
        }
