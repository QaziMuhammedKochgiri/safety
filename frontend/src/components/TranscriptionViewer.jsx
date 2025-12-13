import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Mic,
  Search,
  Play,
  Pause,
  Upload,
  Download,
  Clock,
  AlertTriangle,
  RefreshCw,
  FileAudio,
  Globe,
  Hash,
  ChevronDown,
  ChevronUp,
  Filter,
  X,
  Volume2
} from 'lucide-react';
import axios from 'axios';

// Source display names
const SOURCE_NAMES = {
  whatsapp_voice: 'WhatsApp Sesli',
  telegram_voice: 'Telegram Sesli',
  phone_recording: 'Telefon Kaydı',
  video_audio: 'Video Sesi',
  unknown: 'Bilinmiyor'
};

// Risk level colors
const RISK_COLORS = {
  high: 'bg-red-100 text-red-700 border-red-300',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  low: 'bg-blue-100 text-blue-700 border-blue-300',
  none: 'bg-gray-100 text-gray-600 border-gray-300'
};

const TranscriptionViewer = ({ caseId, onTranscriptSelect }) => {
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [transcripts, setTranscripts] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [transcriptDetail, setTranscriptDetail] = useState(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  // Playback state
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(-1);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [filterSource, setFilterSource] = useState('all');
  const [filterRisk, setFilterRisk] = useState('all');

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!caseId) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [transcriptsRes, statsRes] = await Promise.all([
        axios.get(`/api/transcriptions/${caseId}`, { headers }),
        axios.get(`/api/transcriptions/${caseId}/stats`, { headers })
      ]);

      setTranscripts(transcriptsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Error fetching transcriptions:', err);
      setError(err.response?.data?.detail || 'Transkriptler yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Fetch transcript detail
  const fetchTranscriptDetail = async (transcriptId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `/api/transcriptions/${caseId}/transcript/${transcriptId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTranscriptDetail(response.data);
    } catch (err) {
      console.error('Error fetching transcript detail:', err);
    }
  };

  // Handle transcript selection
  const handleSelectTranscript = (transcript) => {
    setSelectedTranscript(transcript);
    fetchTranscriptDetail(transcript.id);
    if (onTranscriptSelect) {
      onTranscriptSelect(transcript);
    }
  };

  // Upload audio files
  const handleUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();

      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const response = await axios.post(
        `/api/transcriptions/${caseId}/batch-transcribe`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(progress);
          }
        }
      );

      // Refresh data
      await fetchData();

      // Show result
      alert(`${response.data.successful} dosya başarıyla işlendi, ${response.data.failed} hata.`);
    } catch (err) {
      console.error('Upload error:', err);
      alert('Yükleme hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Search transcripts
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    setSearching(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `/api/transcriptions/${caseId}/search`,
        {
          params: { query: searchQuery },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSearchResults(response.data);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  // Filter transcripts
  const filteredTranscripts = transcripts.filter(t => {
    if (filterSource !== 'all' && t.source !== filterSource) return false;

    if (filterRisk !== 'all') {
      const riskCount = (t.riskIndicators || []).length;
      if (filterRisk === 'high' && riskCount < 5) return false;
      if (filterRisk === 'medium' && (riskCount < 2 || riskCount >= 5)) return false;
      if (filterRisk === 'low' && (riskCount < 1 || riskCount >= 2)) return false;
      if (filterRisk === 'none' && riskCount > 0) return false;
    }

    return true;
  });

  // Get risk level
  const getRiskLevel = (riskIndicators) => {
    const count = (riskIndicators || []).length;
    if (count >= 5) return 'high';
    if (count >= 2) return 'medium';
    if (count >= 1) return 'low';
    return 'none';
  };

  // Highlight search term in text
  const highlightText = (text, query) => {
    if (!query) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase()
        ? <mark key={i} className="bg-yellow-200 px-0.5">{part}</mark>
        : part
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center justify-center">
          <RefreshCw className="w-10 h-10 animate-spin text-purple-500 mb-4" />
          <p className="text-gray-600">Transkriptler yükleniyor...</p>
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
            onClick={fetchData}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Mic className="w-6 h-6 text-purple-500" />
            <h2 className="text-lg font-semibold text-gray-800">Ses Transkriptleri</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-lg transition-colors ${
                showFilters ? 'bg-purple-100 text-purple-600' : 'hover:bg-gray-100'
              }`}
            >
              <Filter className="w-5 h-5" />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleUpload}
              accept="audio/*,video/*,.opus,.ogg,.m4a"
              multiple
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  %{uploadProgress}
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Ses Yükle
                </>
              )}
            </button>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-800">
                {stats.totalTranscriptions}
              </div>
              <div className="text-sm text-gray-500">Toplam Transkript</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-800">
                {stats.totalDurationFormatted}
              </div>
              <div className="text-sm text-gray-500">Toplam Süre</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-800">
                {stats.totalWords?.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Toplam Kelime</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold text-red-600">{stats.riskStats?.high || 0}</span>
                <span className="text-xl font-bold text-yellow-600">{stats.riskStats?.medium || 0}</span>
                <span className="text-xl font-bold text-blue-600">{stats.riskStats?.low || 0}</span>
              </div>
              <div className="text-sm text-gray-500">Risk Seviyeleri</div>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white rounded-lg shadow-lg p-4">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">
                Kaynak
              </label>
              <select
                value={filterSource}
                onChange={(e) => setFilterSource(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value="all">Tümü</option>
                <option value="whatsapp_voice">WhatsApp</option>
                <option value="telegram_voice">Telegram</option>
                <option value="phone_recording">Telefon Kaydı</option>
                <option value="video_audio">Video</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">
                Risk Seviyesi
              </label>
              <select
                value={filterRisk}
                onChange={(e) => setFilterRisk(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value="all">Tümü</option>
                <option value="high">Yüksek</option>
                <option value="medium">Orta</option>
                <option value="low">Düşük</option>
                <option value="none">Risk Yok</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Transkriptlerde ara..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
          >
            {searching ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Ara'}
          </button>
          {searchResults && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSearchResults(null);
              }}
              className="px-3 py-2 text-gray-500 hover:text-gray-700"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Search Results */}
        {searchResults && (
          <div className="mt-4 border-t pt-4">
            <div className="text-sm text-gray-500 mb-3">
              {searchResults.length} sonuç bulundu
            </div>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {searchResults.map((result) => (
                <div
                  key={result.transcriptId}
                  className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                  onClick={() => {
                    const transcript = transcripts.find(t => t.id === result.transcriptId);
                    if (transcript) handleSelectTranscript(transcript);
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{result.fileName}</span>
                    <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                      {result.matchCount} eşleşme
                    </span>
                  </div>
                  {result.matchingSegments.slice(0, 2).map((seg, idx) => (
                    <div key={idx} className="text-sm text-gray-600 mb-1">
                      <span className="text-xs text-gray-400 mr-2">
                        {seg.startFormatted}
                      </span>
                      {highlightText(seg.text, searchQuery)}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Transcript List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* List */}
        <div className="bg-white rounded-lg shadow-lg p-4">
          <h3 className="font-semibold text-gray-800 mb-4">
            Transkript Listesi ({filteredTranscripts.length})
          </h3>

          {filteredTranscripts.length === 0 ? (
            <div className="text-center py-8">
              <FileAudio className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Henüz transkript yok</p>
              <p className="text-sm text-gray-400 mt-1">
                Ses dosyası yükleyerek başlayın
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {filteredTranscripts.map((transcript) => {
                const riskLevel = getRiskLevel(transcript.riskIndicators);
                const isSelected = selectedTranscript?.id === transcript.id;

                return (
                  <div
                    key={transcript.id}
                    onClick={() => handleSelectTranscript(transcript)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-800 truncate">
                          {transcript.fileName}
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {transcript.durationFormatted}
                          </span>
                          <span className="flex items-center gap-1">
                            <Globe className="w-3 h-3" />
                            {transcript.language?.toUpperCase()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Hash className="w-3 h-3" />
                            {transcript.wordCount} kelime
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                          {SOURCE_NAMES[transcript.source] || transcript.source}
                        </span>
                        {riskLevel !== 'none' && (
                          <span className={`text-xs px-2 py-1 rounded border ${RISK_COLORS[riskLevel]}`}>
                            {riskLevel === 'high' ? 'Yüksek Risk' :
                             riskLevel === 'medium' ? 'Orta Risk' : 'Düşük Risk'}
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {transcript.fullText}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Detail View */}
        <div className="bg-white rounded-lg shadow-lg p-4">
          {selectedTranscript && transcriptDetail ? (
            <>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-800">Transkript Detayı</h3>
                <button
                  onClick={() => {
                    setSelectedTranscript(null);
                    setTranscriptDetail(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Meta info */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-2 bg-gray-50 rounded text-sm">
                  <span className="text-gray-500">Süre:</span>{' '}
                  <span className="font-medium">{transcriptDetail.durationFormatted}</span>
                </div>
                <div className="p-2 bg-gray-50 rounded text-sm">
                  <span className="text-gray-500">Dil:</span>{' '}
                  <span className="font-medium">{transcriptDetail.language?.toUpperCase()}</span>
                </div>
                <div className="p-2 bg-gray-50 rounded text-sm">
                  <span className="text-gray-500">Kelime:</span>{' '}
                  <span className="font-medium">{transcriptDetail.wordCount}</span>
                </div>
                <div className="p-2 bg-gray-50 rounded text-sm">
                  <span className="text-gray-500">İşlem:</span>{' '}
                  <span className="font-medium">{transcriptDetail.processingTime?.toFixed(1)}s</span>
                </div>
              </div>

              {/* Risk indicators */}
              {transcriptDetail.riskIndicators?.length > 0 && (
                <div className="mb-4 p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-center gap-2 text-red-700 font-medium mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    Risk Göstergeleri ({transcriptDetail.riskIndicators.length})
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {transcriptDetail.riskIndicators.map((risk, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded"
                      >
                        {risk}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Keywords */}
              {transcriptDetail.keywords?.length > 0 && (
                <div className="mb-4">
                  <div className="text-sm text-gray-500 mb-2">Anahtar Kelimeler</div>
                  <div className="flex flex-wrap gap-2">
                    {transcriptDetail.keywords.map((keyword, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Segments */}
              <div className="border-t pt-4">
                <div className="text-sm text-gray-500 mb-3">
                  Zaman Damgalı Metin ({transcriptDetail.segments?.length || 0} segment)
                </div>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {transcriptDetail.segments?.map((seg, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg transition-colors ${
                        currentSegmentIndex === idx
                          ? 'bg-purple-100 border border-purple-300'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                        <Clock className="w-3 h-3" />
                        {seg.startFormatted} - {seg.endFormatted}
                      </div>
                      <p className="text-sm text-gray-700">{seg.text}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Full text */}
              <div className="border-t pt-4 mt-4">
                <div className="text-sm text-gray-500 mb-2">Tam Metin</div>
                <div className="p-3 bg-gray-50 rounded-lg max-h-[200px] overflow-y-auto">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {transcriptDetail.fullText}
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-[400px] text-center">
              <Volume2 className="w-16 h-16 text-gray-300 mb-4" />
              <p className="text-gray-500">Detay görüntülemek için bir transkript seçin</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TranscriptionViewer;
