import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Users,
  Network,
  Filter,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  AlertTriangle,
  MessageSquare,
  Phone,
  RefreshCw,
  Info,
  X
} from 'lucide-react';
import axios from 'axios';

// Cytoscape.js will be loaded dynamically
let cytoscape = null;

const ContactNetworkGraph = ({ caseId, onNodeSelect }) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [networkData, setNetworkData] = useState(null);
  const [stats, setStats] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [filters, setFilters] = useState({
    minMessages: 1,
    platforms: [],
    showClusters: true
  });
  const [clusters, setClusters] = useState([]);
  const [suspiciousPatterns, setSuspiciousPatterns] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [showPatterns, setShowPatterns] = useState(false);

  // Load Cytoscape dynamically
  useEffect(() => {
    const loadCytoscape = async () => {
      if (!cytoscape) {
        const module = await import('cytoscape');
        cytoscape = module.default;
      }
    };
    loadCytoscape();
  }, []);

  // Fetch network data
  const fetchNetworkData = useCallback(async () => {
    if (!caseId) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [graphRes, statsRes, patternsRes] = await Promise.all([
        axios.get(`/api/network/${caseId}?min_messages=${filters.minMessages}`, { headers }),
        axios.get(`/api/network/${caseId}/stats`, { headers }),
        axios.get(`/api/network/${caseId}/suspicious`, { headers })
      ]);

      setNetworkData(graphRes.data);
      setStats(statsRes.data);
      setSuspiciousPatterns(patternsRes.data);
      setClusters(graphRes.data.metadata?.clusters || []);

    } catch (err) {
      console.error('Network graph error:', err);
      setError(err.response?.data?.detail || 'Graf yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  }, [caseId, filters.minMessages]);

  useEffect(() => {
    fetchNetworkData();
  }, [fetchNetworkData]);

  // Initialize Cytoscape
  useEffect(() => {
    if (!cytoscape || !networkData || !containerRef.current) return;

    // Destroy previous instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const { nodes, edges } = networkData.elements;

    // Create Cytoscape instance
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: nodes.map(n => ({
          data: {
            ...n.data,
            // Add cluster color as background
            background: filters.showClusters && n.data.clusterId !== null
              ? clusters.find(c => c.id === n.data.clusterId)?.color || n.data.color
              : n.data.color
          }
        })),
        edges: edges.map(e => ({
          data: e.data
        }))
      },
      style: [
        // Node styles
        {
          selector: 'node',
          style: {
            'background-color': 'data(background)',
            'label': 'data(label)',
            'width': 'data(size)',
            'height': 'data(size)',
            'font-size': '10px',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'color': '#333',
            'text-outline-color': '#fff',
            'text-outline-width': 2,
            'border-width': 2,
            'border-color': '#fff'
          }
        },
        // Primary node (case subject)
        {
          selector: 'node[type = "primary"]',
          style: {
            'border-width': 4,
            'border-color': '#4CAF50',
            'background-color': '#4CAF50'
          }
        },
        // Flagged node
        {
          selector: 'node[type = "flagged"]',
          style: {
            'border-width': 3,
            'border-color': '#F44336',
            'background-color': '#F44336'
          }
        },
        // Family node
        {
          selector: 'node[type = "family"]',
          style: {
            'border-width': 3,
            'border-color': '#2196F3'
          }
        },
        // Edge styles
        {
          selector: 'edge',
          style: {
            'width': 'data(width)',
            'line-color': 'data(color)',
            'curve-style': 'bezier',
            'opacity': 0.7
          }
        },
        // Selected node
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#FFD700',
            'overlay-color': '#FFD700',
            'overlay-opacity': 0.2
          }
        },
        // Hover effect
        {
          selector: 'node:active',
          style: {
            'overlay-opacity': 0.1
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 500,
        nodeRepulsion: 8000,
        idealEdgeLength: 100,
        edgeElasticity: 100,
        nestingFactor: 1.2,
        gravity: 80,
        numIter: 1000,
        coolingFactor: 0.99,
        minTemp: 1.0
      },
      minZoom: 0.2,
      maxZoom: 3,
      wheelSensitivity: 0.2
    });

    // Event handlers
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      if (onNodeSelect) {
        onNodeSelect(nodeData);
      }
    });

    cyRef.current.on('tap', (evt) => {
      if (evt.target === cyRef.current) {
        setSelectedNode(null);
        if (onNodeSelect) {
          onNodeSelect(null);
        }
      }
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [networkData, filters.showClusters, clusters, onNodeSelect]);

  // Graph controls
  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8);
    }
  };

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit();
    }
  };

  const handleExportPNG = () => {
    if (cyRef.current) {
      const png = cyRef.current.png({ full: true, scale: 2 });
      const link = document.createElement('a');
      link.download = `network-graph-${caseId}.png`;
      link.href = png;
      link.click();
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}s ${minutes}dk`;
    return `${minutes}dk`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-2" />
          <p className="text-gray-600">İletişim ağı yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-red-50 rounded-lg">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchNetworkData}
            className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-500" />
            <h3 className="font-semibold text-gray-800">İletişim Ağı Grafiği</h3>
          </div>

          {/* Stats */}
          {stats && (
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                <span>{stats.totalNodes} kişi</span>
              </div>
              <div className="flex items-center gap-1">
                <MessageSquare className="w-4 h-4" />
                <span>{stats.totalMessages?.toLocaleString()} mesaj</span>
              </div>
              <div className="flex items-center gap-1">
                <Phone className="w-4 h-4" />
                <span>{stats.totalCalls} arama</span>
              </div>
            </div>
          )}

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-lg transition-colors ${
                showFilters ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
              }`}
              title="Filtreler"
            >
              <Filter className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowPatterns(!showPatterns)}
              className={`p-2 rounded-lg transition-colors ${
                showPatterns ? 'bg-yellow-100 text-yellow-600' : 'hover:bg-gray-100'
              }`}
              title="Şüpheli Kalıplar"
            >
              <AlertTriangle className="w-4 h-4" />
              {suspiciousPatterns.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {suspiciousPatterns.length}
                </span>
              )}
            </button>
            <div className="w-px h-6 bg-gray-300" />
            <button
              onClick={handleZoomIn}
              className="p-2 hover:bg-gray-100 rounded-lg"
              title="Yakınlaştır"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 hover:bg-gray-100 rounded-lg"
              title="Uzaklaştır"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={handleFit}
              className="p-2 hover:bg-gray-100 rounded-lg"
              title="Sığdır"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleExportPNG}
              className="p-2 hover:bg-gray-100 rounded-lg"
              title="PNG Olarak İndir"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={fetchNetworkData}
              className="p-2 hover:bg-gray-100 rounded-lg"
              title="Yenile"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mt-4 p-4 bg-white border rounded-lg">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min. Mesaj Sayısı
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={filters.minMessages}
                  onChange={(e) => setFilters(f => ({ ...f, minMessages: parseInt(e.target.value) || 1 }))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kümeleri Göster
                </label>
                <label className="flex items-center gap-2 mt-2">
                  <input
                    type="checkbox"
                    checked={filters.showClusters}
                    onChange={(e) => setFilters(f => ({ ...f, showClusters: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm">Küme renklerini uygula</span>
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kümeler
                </label>
                <div className="flex flex-wrap gap-2">
                  {clusters.map(cluster => (
                    <span
                      key={cluster.id}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs text-white"
                      style={{ backgroundColor: cluster.color }}
                    >
                      {cluster.label}: {cluster.nodeCount}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Suspicious Patterns Panel */}
        {showPatterns && suspiciousPatterns.length > 0 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Tespit Edilen Şüpheli Kalıplar
            </h4>
            <div className="space-y-2">
              {suspiciousPatterns.map((pattern, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-white rounded border"
                >
                  <div>
                    <span className="font-medium">{pattern.label}</span>
                    <span className="text-gray-500 ml-2">-</span>
                    <span className="text-gray-600 ml-2">{pattern.description}</span>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    pattern.type.includes('one_way') ? 'bg-orange-100 text-orange-700' :
                    pattern.type === 'high_risk' ? 'bg-red-100 text-red-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {pattern.type.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Graph Container */}
      <div className="relative">
        <div
          ref={containerRef}
          className="w-full h-[500px] bg-gray-100"
        />

        {/* Node Detail Panel */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-80 bg-white rounded-lg shadow-lg border p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-800">{selectedNode.label}</h4>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              {/* Type Badge */}
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs text-white ${
                  selectedNode.type === 'primary' ? 'bg-green-500' :
                  selectedNode.type === 'family' ? 'bg-blue-500' :
                  selectedNode.type === 'flagged' ? 'bg-red-500' :
                  'bg-gray-500'
                }`}>
                  {selectedNode.type === 'primary' ? 'Ana Kişi' :
                   selectedNode.type === 'family' ? 'Aile' :
                   selectedNode.type === 'flagged' ? 'İşaretli' :
                   'Kişi'}
                </span>
                {selectedNode.clusterId !== null && (
                  <span
                    className="px-2 py-1 rounded text-xs text-white"
                    style={{ backgroundColor: clusters.find(c => c.id === selectedNode.clusterId)?.color }}
                  >
                    Küme {selectedNode.clusterId + 1}
                  </span>
                )}
              </div>

              {/* Platforms */}
              <div>
                <span className="text-gray-500">Platformlar:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedNode.platforms?.map(p => (
                    <span key={p} className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                      {p}
                    </span>
                  ))}
                </div>
              </div>

              {/* Message Stats */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-blue-50 rounded">
                  <div className="text-blue-600 font-medium">
                    {selectedNode.totalMessages?.toLocaleString()}
                  </div>
                  <div className="text-blue-400 text-xs">Toplam Mesaj</div>
                </div>
                <div className="p-2 bg-green-50 rounded">
                  <div className="text-green-600 font-medium">
                    {selectedNode.totalCalls}
                  </div>
                  <div className="text-green-400 text-xs">Arama</div>
                </div>
              </div>

              {/* Sent/Received */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Gönderilen: {selectedNode.sentMessages}</span>
                <span className="text-gray-500">Alınan: {selectedNode.receivedMessages}</span>
              </div>

              {/* Call Duration */}
              {selectedNode.callDuration > 0 && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Phone className="w-4 h-4" />
                  <span>Toplam Süre: {formatDuration(selectedNode.callDuration)}</span>
                </div>
              )}

              {/* Centrality */}
              <div>
                <span className="text-gray-500">Merkezilik Skoru:</span>
                <div className="mt-1 bg-gray-100 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-full rounded-full"
                    style={{ width: `${(selectedNode.centrality || 0) * 100}%` }}
                  />
                </div>
                <div className="text-right text-xs text-gray-400 mt-1">
                  {((selectedNode.centrality || 0) * 100).toFixed(1)}%
                </div>
              </div>

              {/* Risk Score */}
              {selectedNode.riskScore > 0 && (
                <div>
                  <span className="text-gray-500">Risk Skoru:</span>
                  <div className="mt-1 bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-full rounded-full ${
                        selectedNode.riskScore > 0.7 ? 'bg-red-500' :
                        selectedNode.riskScore > 0.4 ? 'bg-orange-500' :
                        'bg-yellow-500'
                      }`}
                      style={{ width: `${(selectedNode.riskScore || 0) * 100}%` }}
                    />
                  </div>
                  <div className="text-right text-xs text-gray-400 mt-1">
                    {((selectedNode.riskScore || 0) * 100).toFixed(1)}%
                  </div>
                </div>
              )}

              {/* Dates */}
              {selectedNode.firstContact && (
                <div className="text-xs text-gray-500">
                  <div>İlk İletişim: {new Date(selectedNode.firstContact).toLocaleDateString('tr-TR')}</div>
                  <div>Son İletişim: {new Date(selectedNode.lastContact).toLocaleDateString('tr-TR')}</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex items-center justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500" />
            <span className="text-gray-600">Ana Kişi (Client)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500" />
            <span className="text-gray-600">Aile</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500" />
            <span className="text-gray-600">İşaretli / Yüksek Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gray-400" />
            <span className="text-gray-600">Diğer Kişiler</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactNetworkGraph;
