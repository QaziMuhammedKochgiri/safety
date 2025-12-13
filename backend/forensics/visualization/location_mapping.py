"""
GPS Location Mapping Engine for SafeChild

Extracts GPS coordinates from various sources and provides
visualization data for Leaflet.js maps:
- EXIF GPS from photos
- Google Location History
- iOS Significant Locations
- Social media check-ins

Uses OpenStreetMap/Nominatim for reverse geocoding.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import struct
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


class LocationSource(Enum):
    """Source of location data"""
    EXIF = "exif"
    GOOGLE_HISTORY = "google_history"
    IOS_SIGNIFICANT = "ios_significant"
    SOCIAL_CHECKIN = "social_checkin"
    WHATSAPP_LOCATION = "whatsapp_location"
    TELEGRAM_LOCATION = "telegram_location"
    MANUAL = "manual"


@dataclass
class GeoLocation:
    """
    Represents a GPS location point.
    Compatible with Leaflet.js marker format.
    """
    id: str
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None
    accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    source: LocationSource = LocationSource.EXIF
    address: Optional[str] = None
    place_name: Optional[str] = None
    file_name: Optional[str] = None
    media_type: Optional[str] = None  # photo, video, document
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_leaflet_marker(self) -> Dict[str, Any]:
        """Convert to Leaflet.js marker format"""
        return {
            "id": self.id,
            "position": [self.latitude, self.longitude],
            "popup": {
                "address": self.address,
                "placeName": self.place_name,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "source": self.source.value,
                "fileName": self.file_name,
                "mediaType": self.media_type,
                "accuracy": self.accuracy_meters
            },
            "icon": self._get_marker_icon()
        }

    def to_heatmap_point(self) -> List[float]:
        """Convert to heatmap format [lat, lng, intensity]"""
        return [self.latitude, self.longitude, 1.0]

    def _get_marker_icon(self) -> str:
        """Get marker icon based on source/type"""
        icons = {
            LocationSource.EXIF: "camera",
            LocationSource.GOOGLE_HISTORY: "map-pin",
            LocationSource.IOS_SIGNIFICANT: "smartphone",
            LocationSource.SOCIAL_CHECKIN: "map",
            LocationSource.WHATSAPP_LOCATION: "message-circle",
            LocationSource.TELEGRAM_LOCATION: "send",
            LocationSource.MANUAL: "flag"
        }
        return icons.get(self.source, "map-pin")


@dataclass
class LocationCluster:
    """Cluster of nearby locations (frequent places)"""
    id: str
    center_lat: float
    center_lng: float
    location_ids: List[str]
    visit_count: int
    first_visit: Optional[datetime] = None
    last_visit: Optional[datetime] = None
    total_duration_minutes: int = 0
    label: Optional[str] = None
    address: Optional[str] = None
    cluster_type: str = "frequent"  # frequent, travel, anomaly

    def to_leaflet_marker(self) -> Dict[str, Any]:
        """Convert to Leaflet.js cluster marker"""
        return {
            "id": self.id,
            "position": [self.center_lat, self.center_lng],
            "popup": {
                "label": self.label or f"Konum {self.id[:6]}",
                "address": self.address,
                "visitCount": self.visit_count,
                "firstVisit": self.first_visit.isoformat() if self.first_visit else None,
                "lastVisit": self.last_visit.isoformat() if self.last_visit else None,
                "totalDuration": self.total_duration_minutes,
                "type": self.cluster_type
            },
            "radius": min(30 + (self.visit_count * 2), 100),
            "color": self._get_cluster_color()
        }

    def _get_cluster_color(self) -> str:
        """Get cluster color based on type"""
        colors = {
            "frequent": "#4CAF50",  # Green
            "travel": "#2196F3",    # Blue
            "anomaly": "#F44336",   # Red
            "work": "#FF9800",      # Orange
            "home": "#9C27B0"       # Purple
        }
        return colors.get(self.cluster_type, "#9E9E9E")


class LocationMapper:
    """
    Main class for extracting and analyzing GPS locations.
    """

    # Haversine formula for distance calculation
    EARTH_RADIUS_KM = 6371

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.locations: Dict[str, GeoLocation] = {}
        self.clusters: List[LocationCluster] = []
        self._location_counter = 0

    def extract_exif_gps(self, image_data: bytes, file_name: str = None) -> Optional[GeoLocation]:
        """
        Extract GPS coordinates from image EXIF data.

        Supports JPEG and TIFF formats with GPS IFD.
        """
        try:
            # Check for JPEG magic bytes
            if image_data[:2] == b'\xff\xd8':
                return self._parse_jpeg_exif(image_data, file_name)
            # Check for TIFF
            elif image_data[:2] in [b'II', b'MM']:
                return self._parse_tiff_exif(image_data, file_name)
            else:
                logger.debug(f"Unknown image format for {file_name}")
                return None
        except Exception as e:
            logger.error(f"EXIF extraction error for {file_name}: {e}")
            return None

    def _parse_jpeg_exif(self, data: bytes, file_name: str = None) -> Optional[GeoLocation]:
        """Parse EXIF from JPEG"""
        # Find APP1 marker with EXIF
        offset = 2
        while offset < len(data) - 4:
            if data[offset] != 0xFF:
                break

            marker = data[offset + 1]

            # APP1 marker (EXIF)
            if marker == 0xE1:
                length = struct.unpack('>H', data[offset + 2:offset + 4])[0]
                exif_data = data[offset + 4:offset + 2 + length]

                # Check for "Exif\x00\x00"
                if exif_data[:6] == b'Exif\x00\x00':
                    tiff_data = exif_data[6:]
                    return self._parse_tiff_exif(tiff_data, file_name)
                break
            # Skip other markers
            elif marker in [0xE0, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF]:
                length = struct.unpack('>H', data[offset + 2:offset + 4])[0]
                offset += 2 + length
            else:
                offset += 1

        return None

    def _parse_tiff_exif(self, data: bytes, file_name: str = None) -> Optional[GeoLocation]:
        """Parse EXIF from TIFF structure"""
        if len(data) < 8:
            return None

        # Check byte order
        byte_order = data[:2]
        if byte_order == b'II':
            endian = '<'  # Little endian
        elif byte_order == b'MM':
            endian = '>'  # Big endian
        else:
            return None

        # Check TIFF magic number
        magic = struct.unpack(endian + 'H', data[2:4])[0]
        if magic != 42:
            return None

        # Get IFD0 offset
        ifd0_offset = struct.unpack(endian + 'I', data[4:8])[0]

        # Parse IFD0 for GPS IFD pointer
        gps_ifd_offset = None
        exif_ifd_offset = None
        timestamp = None

        if ifd0_offset < len(data) - 2:
            num_entries = struct.unpack(endian + 'H', data[ifd0_offset:ifd0_offset + 2])[0]
            entry_offset = ifd0_offset + 2

            for _ in range(num_entries):
                if entry_offset + 12 > len(data):
                    break

                tag = struct.unpack(endian + 'H', data[entry_offset:entry_offset + 2])[0]
                value_offset = struct.unpack(endian + 'I', data[entry_offset + 8:entry_offset + 12])[0]

                if tag == 0x8825:  # GPS IFD pointer
                    gps_ifd_offset = value_offset
                elif tag == 0x8769:  # EXIF IFD pointer
                    exif_ifd_offset = value_offset
                elif tag == 0x0132:  # DateTime
                    try:
                        dt_str = data[value_offset:value_offset + 19].decode('ascii').strip('\x00')
                        timestamp = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                    except:
                        pass

                entry_offset += 12

        if gps_ifd_offset is None:
            return None

        # Parse GPS IFD
        gps_data = self._parse_gps_ifd(data, gps_ifd_offset, endian)

        if gps_data and 'latitude' in gps_data and 'longitude' in gps_data:
            self._location_counter += 1
            loc_id = f"loc_{self.case_id}_{self._location_counter}"

            location = GeoLocation(
                id=loc_id,
                latitude=gps_data['latitude'],
                longitude=gps_data['longitude'],
                timestamp=timestamp,
                altitude_meters=gps_data.get('altitude'),
                source=LocationSource.EXIF,
                file_name=file_name,
                media_type="photo"
            )

            self.locations[loc_id] = location
            return location

        return None

    def _parse_gps_ifd(self, data: bytes, offset: int, endian: str) -> Optional[Dict[str, float]]:
        """Parse GPS IFD entries"""
        if offset >= len(data) - 2:
            return None

        result = {}

        try:
            num_entries = struct.unpack(endian + 'H', data[offset:offset + 2])[0]
            entry_offset = offset + 2

            lat_ref = None
            lon_ref = None
            lat_values = None
            lon_values = None
            alt = None
            alt_ref = 0

            for _ in range(min(num_entries, 50)):  # Limit entries
                if entry_offset + 12 > len(data):
                    break

                tag = struct.unpack(endian + 'H', data[entry_offset:entry_offset + 2])[0]
                tag_type = struct.unpack(endian + 'H', data[entry_offset + 2:entry_offset + 4])[0]
                count = struct.unpack(endian + 'I', data[entry_offset + 4:entry_offset + 8])[0]
                value_or_offset = struct.unpack(endian + 'I', data[entry_offset + 8:entry_offset + 12])[0]

                # GPS Latitude Ref (N/S)
                if tag == 1:
                    lat_ref = chr(data[entry_offset + 8])

                # GPS Latitude
                elif tag == 2:
                    lat_values = self._parse_rational_array(data, value_or_offset, 3, endian)

                # GPS Longitude Ref (E/W)
                elif tag == 3:
                    lon_ref = chr(data[entry_offset + 8])

                # GPS Longitude
                elif tag == 4:
                    lon_values = self._parse_rational_array(data, value_or_offset, 3, endian)

                # GPS Altitude Ref (0 = above sea level, 1 = below)
                elif tag == 5:
                    alt_ref = data[entry_offset + 8]

                # GPS Altitude
                elif tag == 6:
                    alt_val = self._parse_rational(data, value_or_offset, endian)
                    if alt_val is not None:
                        alt = alt_val if alt_ref == 0 else -alt_val

                entry_offset += 12

            # Convert to decimal degrees
            if lat_values and len(lat_values) == 3 and lon_values and len(lon_values) == 3:
                lat = lat_values[0] + lat_values[1] / 60 + lat_values[2] / 3600
                lon = lon_values[0] + lon_values[1] / 60 + lon_values[2] / 3600

                if lat_ref == 'S':
                    lat = -lat
                if lon_ref == 'W':
                    lon = -lon

                # Validate coordinates
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    result['latitude'] = lat
                    result['longitude'] = lon
                    if alt is not None:
                        result['altitude'] = alt

            return result if result else None

        except Exception as e:
            logger.debug(f"GPS IFD parsing error: {e}")
            return None

    def _parse_rational_array(self, data: bytes, offset: int, count: int, endian: str) -> List[float]:
        """Parse array of RATIONAL values (two unsigned longs)"""
        values = []
        for i in range(count):
            val = self._parse_rational(data, offset + i * 8, endian)
            if val is not None:
                values.append(val)
        return values

    def _parse_rational(self, data: bytes, offset: int, endian: str) -> Optional[float]:
        """Parse single RATIONAL value"""
        if offset + 8 > len(data):
            return None
        try:
            numerator = struct.unpack(endian + 'I', data[offset:offset + 4])[0]
            denominator = struct.unpack(endian + 'I', data[offset + 4:offset + 8])[0]
            if denominator == 0:
                return None
            return numerator / denominator
        except:
            return None

    def add_location(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
        source: LocationSource = LocationSource.MANUAL,
        address: Optional[str] = None,
        place_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> GeoLocation:
        """Add a location point manually"""
        self._location_counter += 1
        loc_id = f"loc_{self.case_id}_{self._location_counter}"

        location = GeoLocation(
            id=loc_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            source=source,
            address=address,
            place_name=place_name,
            metadata=metadata or {}
        )

        self.locations[loc_id] = location
        return location

    def import_google_location_history(self, records: List[Dict]) -> int:
        """
        Import Google Location History records.

        Expected format: [{"latitudeE7": int, "longitudeE7": int, "timestamp": str, ...}]
        """
        count = 0
        for record in records:
            try:
                lat = record.get('latitudeE7', 0) / 1e7
                lng = record.get('longitudeE7', 0) / 1e7

                if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                    continue

                ts = None
                ts_str = record.get('timestamp') or record.get('timestampMs')
                if ts_str:
                    if isinstance(ts_str, str):
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    elif isinstance(ts_str, (int, float)):
                        ts = datetime.fromtimestamp(ts_str / 1000)

                self.add_location(
                    latitude=lat,
                    longitude=lng,
                    timestamp=ts,
                    source=LocationSource.GOOGLE_HISTORY,
                    metadata={
                        'accuracy': record.get('accuracy'),
                        'activity': record.get('activity')
                    }
                )
                count += 1
            except Exception as e:
                logger.debug(f"Error importing Google location: {e}")

        return count

    def import_ios_significant_locations(self, records: List[Dict]) -> int:
        """
        Import iOS Significant Locations.

        Expected format: [{"latitude": float, "longitude": float, "timestamp": str, ...}]
        """
        count = 0
        for record in records:
            try:
                lat = float(record.get('latitude', 0))
                lng = float(record.get('longitude', 0))

                if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                    continue

                ts = None
                ts_str = record.get('timestamp')
                if ts_str:
                    ts = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))

                self.add_location(
                    latitude=lat,
                    longitude=lng,
                    timestamp=ts,
                    source=LocationSource.IOS_SIGNIFICANT,
                    place_name=record.get('place'),
                    metadata=record.get('metadata', {})
                )
                count += 1
            except Exception as e:
                logger.debug(f"Error importing iOS location: {e}")

        return count

    def detect_clusters(self, radius_km: float = 0.5, min_visits: int = 2) -> List[LocationCluster]:
        """
        Detect location clusters (frequent places) using simple DBSCAN-like approach.

        Args:
            radius_km: Maximum distance between points in same cluster
            min_visits: Minimum visits to form a cluster
        """
        self.clusters = []

        if len(self.locations) < min_visits:
            return self.clusters

        locations_list = list(self.locations.values())
        visited = set()
        cluster_id = 0

        for loc in locations_list:
            if loc.id in visited:
                continue

            # Find all neighbors within radius
            neighbors = []
            for other in locations_list:
                if other.id != loc.id and other.id not in visited:
                    dist = self._haversine_distance(
                        loc.latitude, loc.longitude,
                        other.latitude, other.longitude
                    )
                    if dist <= radius_km:
                        neighbors.append(other)

            if len(neighbors) + 1 >= min_visits:
                # Form cluster
                cluster_locs = [loc] + neighbors
                for cl in cluster_locs:
                    visited.add(cl.id)

                # Calculate centroid
                center_lat = sum(l.latitude for l in cluster_locs) / len(cluster_locs)
                center_lng = sum(l.longitude for l in cluster_locs) / len(cluster_locs)

                # Get timestamps
                timestamps = [l.timestamp for l in cluster_locs if l.timestamp]
                first_visit = min(timestamps) if timestamps else None
                last_visit = max(timestamps) if timestamps else None

                cluster = LocationCluster(
                    id=f"cluster_{cluster_id}",
                    center_lat=center_lat,
                    center_lng=center_lng,
                    location_ids=[l.id for l in cluster_locs],
                    visit_count=len(cluster_locs),
                    first_visit=first_visit,
                    last_visit=last_visit
                )

                self.clusters.append(cluster)
                cluster_id += 1

        return self.clusters

    def get_timeline(self) -> List[Dict[str, Any]]:
        """
        Get locations as timeline events for animation.
        """
        timeline = []
        sorted_locs = sorted(
            [l for l in self.locations.values() if l.timestamp],
            key=lambda x: x.timestamp
        )

        for loc in sorted_locs:
            timeline.append({
                "timestamp": loc.timestamp.isoformat(),
                "position": [loc.latitude, loc.longitude],
                "id": loc.id,
                "source": loc.source.value,
                "address": loc.address
            })

        return timeline

    def get_heatmap_data(self) -> List[List[float]]:
        """Get data for heatmap layer"""
        return [loc.to_heatmap_point() for loc in self.locations.values()]

    def get_bounds(self) -> Optional[Dict[str, List[float]]]:
        """Get map bounds containing all locations"""
        if not self.locations:
            return None

        lats = [l.latitude for l in self.locations.values()]
        lngs = [l.longitude for l in self.locations.values()]

        return {
            "southWest": [min(lats), min(lngs)],
            "northEast": [max(lats), max(lngs)]
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get location statistics"""
        if not self.locations:
            return {
                "totalLocations": 0,
                "sources": {},
                "dateRange": None,
                "clusters": 0
            }

        sources = defaultdict(int)
        for loc in self.locations.values():
            sources[loc.source.value] += 1

        timestamps = [l.timestamp for l in self.locations.values() if l.timestamp]
        date_range = None
        if timestamps:
            date_range = {
                "start": min(timestamps).isoformat(),
                "end": max(timestamps).isoformat()
            }

        return {
            "totalLocations": len(self.locations),
            "sources": dict(sources),
            "dateRange": date_range,
            "clusters": len(self.clusters),
            "bounds": self.get_bounds()
        }

    def to_leaflet_json(self) -> Dict[str, Any]:
        """Export all data in Leaflet.js compatible format"""
        return {
            "markers": [loc.to_leaflet_marker() for loc in self.locations.values()],
            "clusters": [c.to_leaflet_marker() for c in self.clusters],
            "heatmap": self.get_heatmap_data(),
            "timeline": self.get_timeline(),
            "bounds": self.get_bounds(),
            "statistics": self.get_statistics(),
            "metadata": {
                "caseId": self.case_id,
                "generatedAt": datetime.now().isoformat()
            }
        }

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km using Haversine formula"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return self.EARTH_RADIUS_KM * c


# Convenience functions

def extract_gps_from_images(
    case_id: str,
    images: List[Tuple[bytes, str]]  # [(image_data, filename), ...]
) -> LocationMapper:
    """
    Extract GPS from multiple images.

    Args:
        case_id: Case identifier
        images: List of (image_bytes, filename) tuples

    Returns:
        LocationMapper with extracted locations
    """
    mapper = LocationMapper(case_id)

    for image_data, filename in images:
        mapper.extract_exif_gps(image_data, filename)

    mapper.detect_clusters()
    return mapper
