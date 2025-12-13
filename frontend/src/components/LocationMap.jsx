import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MapPin,
  Calendar,
  Clock,
  Filter,
  Layers,
  Play,
  Pause,
  RotateCcw,
  Download,
  Info,
  AlertTriangle,
  Home,
  Building,
  Car,
  Image,
  MessageCircle,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize
} from 'lucide-react';
import axios from 'axios';

// Source icons mapping
const SOURCE_ICONS = {
  exif: Image,
  google_history: MapPin,
  ios_significant: Home,
  whatsapp_location: MessageCircle,
  manual: MapPin
};

// Source colors
const SOURCE_COLORS = {
  exif: '#10B981',           // Green for photos
  google_history: '#3B82F6', // Blue for Google
  ios_significant: '#8B5CF6', // Purple for iOS
  whatsapp_location: '#22C55E', // WhatsApp green
  manual: '#6B7280'          // Gray for manual
};

// Cluster type icons
const CLUSTER_TYPE_ICONS = {
  home: Home,
  work: Building,
  frequent: MapPin,
  commute: Car
};

const LocationMap = ({ caseId, onLocationSelect }) => {
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [stats, setStats] = useState(null);

  // Map controls
  const [viewMode, setViewMode] = useState('markers'); // markers, heatmap, clusters
  const [selectedSources, setSelectedSources] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedMarker, setSelectedMarker] = useState(null);

  // Timeline animation
  const [isPlaying, setIsPlaying] = useState(false);
  const [timelineIndex, setTimelineIndex] = useState(0);
  const [animationSpeed, setAnimationSpeed] = useState(1000);
  const animationRef = useRef(null);

  // Map refs
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const heatLayerRef = useRef(null);
  const clusterLayerRef = useRef(null);
  const leafletRef = useRef(null);

  // Fetch location data
  const fetchLocationData = useCallback(async () => {
    if (!caseId) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [mapResponse, statsResponse] = await Promise.all([
        axios.get(`/api/locations/${caseId}`, { headers }),
        axios.get(`/api/locations/${caseId}/stats`, { headers })
      ]);

      setMapData(mapResponse.data);
      setStats(statsResponse.data);

      // Initialize source filters
      if (mapResponse.data?.statistics?.sources) {
        setSelectedSources(Object.keys(mapResponse.data.statistics.sources));
      }
    } catch (err) {
      console.error('Error fetching location data:', err);
      setError(err.response?.data?.detail || 'Konum verileri yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    fetchLocationData();
  }, [fetchLocationData]);

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapData || !mapContainerRef.current) return;

    const initMap = async () => {
      // Dynamic import of Leaflet
      const L = await import('leaflet');
      await import('leaflet/dist/leaflet.css');

      // Fix default marker icon issue
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
      });

      leafletRef.current = L;

      // Destroy previous map if exists
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
      }

      // Create map
      const bounds = mapData.bounds;
      const center = bounds
        ? [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]
        : [39.9334, 32.8597]; // Default: Ankara

      const map = L.map(mapContainerRef.current, {
        center,
        zoom: 10,
        zoomControl: false
      });

      // Add OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      // Add custom zoom control
      L.control.zoom({ position: 'topright' }).addTo(map);

      mapInstanceRef.current = map;

      // Create layer groups
      markersLayerRef.current = L.layerGroup().addTo(map);
      clusterLayerRef.current = L.layerGroup().addTo(map);

      // Fit bounds if available
      if (bounds && bounds[0] && bounds[1]) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }

      // Initial render
      renderMarkers(L);
      renderClusters(L);
    };

    initMap();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [mapData]);

  // Update markers when filters change
  useEffect(() => {
    if (leafletRef.current && markersLayerRef.current) {
      renderMarkers(leafletRef.current);
    }
  }, [selectedSources, viewMode]);

  // Render markers on map
  const renderMarkers = (L) => {
    if (!markersLayerRef.current || !mapData?.markers) return;

    markersLayerRef.current.clearLayers();

    if (viewMode !== 'markers') return;

    const filteredMarkers = mapData.markers.filter(marker =>
      selectedSources.includes(marker.popup?.source?.toLowerCase() || 'manual')
    );

    filteredMarkers.forEach(marker => {
      const source = marker.popup?.source?.toLowerCase() || 'manual';
      const color = SOURCE_COLORS[source] || SOURCE_COLORS.manual;

      // Create custom icon
      const icon = L.divIcon({
        className: 'custom-marker',
        html: `
          <div style="
            background-color: ${color};
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 24]
      });

      const leafletMarker = L.marker(marker.position, { icon })
        .addTo(markersLayerRef.current);

      // Popup content
      const popupContent = `
        <div style="min-width: 200px;">
          <div style="font-weight: bold; margin-bottom: 8px; color: ${color};">
            ${marker.popup?.source || 'Bilinmiyor'}
          </div>
          ${marker.popup?.timestamp ? `
            <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 4px; font-size: 12px;">
              <span>Tarih: ${new Date(marker.popup.timestamp).toLocaleDateString('tr-TR')}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 4px; font-size: 12px;">
              <span>Saat: ${new Date(marker.popup.timestamp).toLocaleTimeString('tr-TR')}</span>
            </div>
          ` : ''}
          ${marker.popup?.address ? `
            <div style="font-size: 12px; color: #666; margin-top: 8px;">
              ${marker.popup.address}
            </div>
          ` : ''}
          ${marker.popup?.fileName ? `
            <div style="font-size: 11px; color: #888; margin-top: 4px;">
              Dosya: ${marker.popup.fileName}
            </div>
          ` : ''}
          <div style="font-size: 11px; color: #999; margin-top: 8px;">
            ${marker.position[0].toFixed(6)}, ${marker.position[1].toFixed(6)}
          </div>
        </div>
      `;

      leafletMarker.bindPopup(popupContent);

      leafletMarker.on('click', () => {
        setSelectedMarker(marker);
        if (onLocationSelect) {
          onLocationSelect(marker);
        }
      });
    });
  };

  // Render clusters
  const renderClusters = (L) => {
    if (!clusterLayerRef.current || !mapData?.clusters) return;

    clusterLayerRef.current.clearLayers();

    mapData.clusters.forEach(cluster => {
      const clusterType = cluster.popup?.type || 'frequent';
      const visitCount = cluster.popup?.visitCount || 0;

      // Size based on visit count
      const size = Math.min(60, Math.max(30, 20 + visitCount * 2));

      const icon = L.divIcon({
        className: 'cluster-marker',
        html: `
          <div style="
            background-color: rgba(239, 68, 68, 0.8);
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: ${size > 40 ? '14px' : '12px'};
          ">
            ${visitCount}
          </div>
        `,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2]
      });

      const marker = L.marker(cluster.position, { icon })
        .addTo(clusterLayerRef.current);

      const popupContent = `
        <div style="min-width: 180px;">
          <div style="font-weight: bold; margin-bottom: 8px; color: #EF4444;">
            Sık Ziyaret Edilen Konum
          </div>
          <div style="font-size: 12px; margin-bottom: 4px;">
            <strong>Ziyaret Sayısı:</strong> ${visitCount}
          </div>
          ${cluster.popup?.firstVisit ? `
            <div style="font-size: 12px; margin-bottom: 4px;">
              <strong>İlk Ziyaret:</strong> ${new Date(cluster.popup.firstVisit).toLocaleDateString('tr-TR')}
            </div>
          ` : ''}
          ${cluster.popup?.lastVisit ? `
            <div style="font-size: 12px; margin-bottom: 4px;">
              <strong>Son Ziyaret:</strong> ${new Date(cluster.popup.lastVisit).toLocaleDateString('tr-TR')}
            </div>
          ` : ''}
          <div style="font-size: 11px; color: #999; margin-top: 8px;">
            ${cluster.position[0].toFixed(6)}, ${cluster.position[1].toFixed(6)}
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
    });
  };

  // Initialize heatmap
  const initHeatmap = async () => {
    if (!mapInstanceRef.current || !mapData?.heatmap) return;

    try {
      // Dynamic import of leaflet.heat
      await import('leaflet.heat');
      const L = leafletRef.current;

      if (heatLayerRef.current) {
        mapInstanceRef.current.removeLayer(heatLayerRef.current);
      }

      if (viewMode === 'heatmap' && mapData.heatmap.length > 0) {
        heatLayerRef.current = L.heatLayer(mapData.heatmap, {
          radius: 25,
          blur: 15,
          maxZoom: 17,
          gradient: {
            0.4: 'blue',
            0.6: 'cyan',
            0.7: 'lime',
            0.8: 'yellow',
            1.0: 'red'
          }
        }).addTo(mapInstanceRef.current);
      }
    } catch (err) {
      console.error('Error initializing heatmap:', err);
    }
  };

  useEffect(() => {
    if (viewMode === 'heatmap') {
      initHeatmap();
    } else if (heatLayerRef.current && mapInstanceRef.current) {
      mapInstanceRef.current.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }
  }, [viewMode, mapData]);

  // Timeline animation
  useEffect(() => {
    if (isPlaying && mapData?.timeline?.length > 0) {
      animationRef.current = setInterval(() => {
        setTimelineIndex(prev => {
          if (prev >= mapData.timeline.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, animationSpeed);
    }

    return () => {
      if (animationRef.current) {
        clearInterval(animationRef.current);
      }
    };
  }, [isPlaying, animationSpeed, mapData?.timeline?.length]);

  // Focus on timeline location
  useEffect(() => {
    if (mapInstanceRef.current && mapData?.timeline?.[timelineIndex]) {
      const point = mapData.timeline[timelineIndex];
      mapInstanceRef.current.setView([point.lat, point.lng], 14, {
        animate: true,
        duration: 0.5
      });
    }
  }, [timelineIndex, mapData?.timeline]);

  // Toggle source filter
  const toggleSource = (source) => {
    setSelectedSources(prev =>
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };

  // Export map as image
  const exportMap = () => {
    if (!mapInstanceRef.current) return;

    // Use leaflet-image or html2canvas for actual implementation
    alert('Harita dışa aktarma özelliği yakında eklenecek');
  };

  // Fit all markers
  const fitAllMarkers = () => {
    if (mapInstanceRef.current && mapData?.bounds) {
      mapInstanceRef.current.fitBounds(mapData.bounds, { padding: [50, 50] });
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center justify-center">
          <RefreshCw className="w-10 h-10 animate-spin text-blue-500 mb-4" />
          <p className="text-gray-600">Konum verileri yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center justify-center text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Hata Oluştu</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchLocationData}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  if (!mapData || mapData.markers?.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center justify-center text-center">
          <MapPin className="w-16 h-16 text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">
            Konum Verisi Bulunamadı
          </h3>
          <p className="text-gray-500">
            Bu dava için henüz GPS konum verisi bulunmuyor.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MapPin className="w-6 h-6 text-blue-500" />
            <h2 className="text-lg font-semibold text-gray-800">GPS Konum Haritası</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-lg transition-colors ${
                showFilters ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
              }`}
              title="Filtreler"
            >
              <Filter className="w-5 h-5" />
            </button>
            <button
              onClick={fetchLocationData}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Yenile"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <button
              onClick={exportMap}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Dışa Aktar"
            >
              <Download className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        {stats && (
          <div className="flex items-center gap-6 mt-3 text-sm">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">
                <strong>{stats.totalLocations}</strong> konum
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">
                <strong>{stats.clusters}</strong> sık ziyaret
              </span>
            </div>
            {stats.dateRange?.start && (
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">
                  {new Date(stats.dateRange.start).toLocaleDateString('tr-TR')} -{' '}
                  {new Date(stats.dateRange.end).toLocaleDateString('tr-TR')}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="p-4 bg-gray-50 border-b">
          <div className="flex flex-wrap gap-4">
            {/* View Mode */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">
                Görünüm Modu
              </label>
              <div className="flex gap-1">
                {[
                  { value: 'markers', label: 'Noktalar', icon: MapPin },
                  { value: 'heatmap', label: 'Isı Haritası', icon: Layers },
                  { value: 'clusters', label: 'Kümeler', icon: Home }
                ].map(mode => (
                  <button
                    key={mode.value}
                    onClick={() => setViewMode(mode.value)}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                      viewMode === mode.value
                        ? 'bg-blue-500 text-white'
                        : 'bg-white border hover:bg-gray-50'
                    }`}
                  >
                    <mode.icon className="w-4 h-4" />
                    {mode.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Source Filters */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">
                Kaynak Filtresi
              </label>
              <div className="flex gap-1 flex-wrap">
                {Object.entries(stats?.sources || {}).map(([source, count]) => {
                  const SourceIcon = SOURCE_ICONS[source] || MapPin;
                  const color = SOURCE_COLORS[source] || SOURCE_COLORS.manual;
                  const isSelected = selectedSources.includes(source);

                  return (
                    <button
                      key={source}
                      onClick={() => toggleSource(source)}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                        isSelected
                          ? 'bg-white border-2'
                          : 'bg-gray-100 opacity-50'
                      }`}
                      style={{
                        borderColor: isSelected ? color : 'transparent'
                      }}
                    >
                      <SourceIcon className="w-4 h-4" style={{ color }} />
                      <span className="capitalize">{source.replace('_', ' ')}</span>
                      <span className="ml-1 px-1.5 py-0.5 bg-gray-100 rounded text-xs">
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Map Container */}
      <div className="relative">
        <div
          ref={mapContainerRef}
          className="w-full h-[500px]"
          style={{ minHeight: '500px' }}
        />

        {/* Map Controls */}
        <div className="absolute top-4 left-4 flex flex-col gap-2 z-[1000]">
          <button
            onClick={fitAllMarkers}
            className="p-2 bg-white rounded-lg shadow hover:bg-gray-50 transition-colors"
            title="Tümünü Göster"
          >
            <Maximize className="w-5 h-5" />
          </button>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
          <div className="text-xs font-medium text-gray-500 mb-2">Kaynaklar</div>
          <div className="space-y-1">
            {Object.entries(SOURCE_COLORS).map(([source, color]) => (
              <div key={source} className="flex items-center gap-2 text-xs">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="capitalize">{source.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline Controls */}
      {mapData?.timeline?.length > 0 && (
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setTimelineIndex(0);
                  setIsPlaying(false);
                }}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                title="Başa Dön"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`p-2 rounded-lg transition-colors ${
                  isPlaying ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'
                }`}
                title={isPlaying ? 'Durdur' : 'Oynat'}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
            </div>

            {/* Timeline Slider */}
            <div className="flex-1">
              <input
                type="range"
                min={0}
                max={mapData.timeline.length - 1}
                value={timelineIndex}
                onChange={(e) => setTimelineIndex(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Timeline Info */}
            <div className="text-sm text-gray-600 min-w-[150px] text-right">
              {mapData.timeline[timelineIndex]?.timestamp && (
                <span>
                  {new Date(mapData.timeline[timelineIndex].timestamp).toLocaleString('tr-TR')}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Selected Marker Details */}
      {selectedMarker && (
        <div className="p-4 border-t">
          <div className="flex items-start gap-4">
            <div
              className="p-3 rounded-lg"
              style={{
                backgroundColor: SOURCE_COLORS[selectedMarker.popup?.source?.toLowerCase()] + '20'
              }}
            >
              {(() => {
                const SourceIcon = SOURCE_ICONS[selectedMarker.popup?.source?.toLowerCase()] || MapPin;
                return (
                  <SourceIcon
                    className="w-6 h-6"
                    style={{
                      color: SOURCE_COLORS[selectedMarker.popup?.source?.toLowerCase()]
                    }}
                  />
                );
              })()}
            </div>
            <div className="flex-1">
              <div className="font-medium text-gray-800">
                {selectedMarker.popup?.source || 'Bilinmeyen Kaynak'}
              </div>
              {selectedMarker.popup?.timestamp && (
                <div className="text-sm text-gray-500 flex items-center gap-2 mt-1">
                  <Clock className="w-4 h-4" />
                  {new Date(selectedMarker.popup.timestamp).toLocaleString('tr-TR')}
                </div>
              )}
              {selectedMarker.popup?.address && (
                <div className="text-sm text-gray-600 mt-2">
                  {selectedMarker.popup.address}
                </div>
              )}
              <div className="text-xs text-gray-400 mt-2">
                Koordinatlar: {selectedMarker.position[0].toFixed(6)}, {selectedMarker.position[1].toFixed(6)}
              </div>
            </div>
            <button
              onClick={() => setSelectedMarker(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              &times;
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LocationMap;
