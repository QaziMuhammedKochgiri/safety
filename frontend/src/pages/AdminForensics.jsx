import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import {
  Fingerprint, ArrowLeft, Search, Filter, Trash2, Eye,
  Download, Clock, CheckCircle, XCircle, RefreshCw, Link as LinkIcon,
  MessageCircle, Phone, Users, Calendar, FileText, Image, AlertTriangle,
  ChevronDown, ChevronUp
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminForensics = () => {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCase, setSelectedCase] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedMessages, setExpandedMessages] = useState({});

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      toast.error(language === 'de' ? 'Admin-Zugriff erforderlich' : 'Admin access required');
      navigate('/login');
      return;
    }
    fetchCases();
  }, [user, token, statusFilter]);

  const fetchCases = async () => {
    try {
      setLoading(true);
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await axios.get(`${API}/admin/forensics`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      setCases(response.data.cases || []);
    } catch (error) {
      console.error('Failed to fetch cases:', error);
      toast.error(language === 'de' ? 'Fehler beim Laden der Fälle' : 'Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCase = async (caseId) => {
    if (!window.confirm(
      language === 'de' 
        ? 'Sind Sie sicher, dass Sie diesen Fall löschen möchten?' 
        : 'Are you sure you want to delete this case?'
    )) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/forensics/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'de' ? 'Fall gelöscht' : 'Case deleted');
      fetchCases();
    } catch (error) {
      toast.error(
        language === 'de' ? 'Fehler beim Löschen' : 'Failed to delete case',
        { description: error.response?.data?.detail || error.message }
      );
    }
  };

  const handleViewDetails = async (caseItem) => {
    try {
      const response = await axios.get(`${API}/admin/forensics/${caseItem.case_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedCase(response.data);
      setActiveTab('overview');
      setExpandedMessages({});
      setShowDetailsModal(true);
    } catch (error) {
      toast.error(language === 'de' ? 'Fehler beim Laden' : 'Failed to load details');
    }
  };

  const handleDownloadReport = async (format) => {
    if (!selectedCase || selectedCase.status !== 'completed') return;

    try {
      const response = await axios.get(`${API}/forensics/${selectedCase.case_id}/report`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { format },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${selectedCase.case_id}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(language === 'de' ? 'Bericht heruntergeladen' : 'Report downloaded');
    } catch (error) {
      toast.error(language === 'de' ? 'Fehler beim Download' : 'Failed to download report');
    }
  };

  const toggleMessageExpand = (platform, index) => {
    const key = `${platform}-${index}`;
    setExpandedMessages(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const renderMessageBubble = (msg, platform, index) => {
    const isExpanded = expandedMessages[`${platform}-${index}`];
    const platformColors = {
      whatsapp: 'bg-green-50 border-green-200',
      telegram: 'bg-blue-50 border-blue-200',
      sms: 'bg-purple-50 border-purple-200',
      signal: 'bg-indigo-50 border-indigo-200'
    };

    return (
      <div
        key={index}
        className={`p-3 rounded-lg border ${platformColors[platform]} mb-2`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-sm">{msg.sender || msg.from || 'Unknown'}</span>
              <span className="text-xs text-gray-500">
                {msg.timestamp ? new Date(msg.timestamp).toLocaleString() : '-'}
              </span>
            </div>
            <p className={`text-sm text-gray-700 ${!isExpanded && msg.content?.length > 200 ? 'line-clamp-2' : ''}`}>
              {msg.content || msg.body || msg.text || '-'}
            </p>
            {msg.content?.length > 200 && (
              <button
                onClick={() => toggleMessageExpand(platform, index)}
                className="text-xs text-indigo-600 hover:underline mt-1"
              >
                {isExpanded ? (language === 'de' ? 'Weniger' : 'Show less') : (language === 'de' ? 'Mehr' : 'Show more')}
              </button>
            )}
          </div>
          {msg.has_media && (
            <Image className="w-4 h-4 text-gray-400 ml-2" />
          )}
        </div>
      </div>
    );
  };

  const handleShareReport = async () => {
    if (!selectedCase || selectedCase.status !== 'completed') return;
    
    try {
      const response = await axios.post(`${API}/admin/forensics/${selectedCase.case_id}/share`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const shareUrl = response.data.url;
      // Copy to clipboard
      await navigator.clipboard.writeText(shareUrl);
      
      toast.success(
        language === 'de' ? 'Link kopiert!' : 'Link copied!',
        { description: shareUrl }
      );
    } catch (error) {
      console.error(error);
      toast.error(language === 'de' ? 'Fehler beim Erstellen des Links' : 'Failed to create link');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusText = (status) => {
    const texts = {
      'processing': language === 'de' ? 'Verarbeitung' : 'Processing',
      'completed': language === 'de' ? 'Abgeschlossen' : 'Completed',
      'failed': language === 'de' ? 'Fehlgeschlagen' : 'Failed'
    };
    return texts[status] || status;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-300';
      case 'processing': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'failed': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString(language === 'de' ? 'de-DE' : 'en-US');
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  };

  const filteredCases = cases.filter(c => {
    const matchesSearch = 
      c.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.client_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.file_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Button
                variant="ghost"
                onClick={() => navigate('/admin/dashboard')}
                className="text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Zurück' : 'Back'}
              </Button>
              <Fingerprint className="w-8 h-8" />
              <div>
                <h1 className="text-xl font-bold">
                  {language === 'de' ? 'Forensische Fälle' : 'Forensic Cases'}
                </h1>
                <p className="text-sm opacity-90">
                  {language === 'de' ? 'Verwaltung' : 'Management'}
                </p>
              </div>
            </div>
            <Button
              onClick={fetchCases}
              variant="outline"
              className="text-white border-white hover:bg-white/10"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              {language === 'de' ? 'Aktualisieren' : 'Refresh'}
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="grid md:grid-cols-2 gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder={language === 'de' ? 'Suche nach Case ID, Email, Datei...' : 'Search by Case ID, Email, File...'}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              {/* Status Filter */}
              <div className="flex items-center space-x-2">
                <Filter className="w-5 h-5 text-gray-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="all">{language === 'de' ? 'Alle Status' : 'All Status'}</option>
                  <option value="processing">{language === 'de' ? 'Verarbeitung' : 'Processing'}</option>
                  <option value="completed">{language === 'de' ? 'Abgeschlossen' : 'Completed'}</option>
                  <option value="failed">{language === 'de' ? 'Fehlgeschlagen' : 'Failed'}</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Statistics Cards */}
        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600">{language === 'de' ? 'Gesamt' : 'Total'}</div>
              <div className="text-3xl font-bold">{cases.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600">{language === 'de' ? 'Verarbeitung' : 'Processing'}</div>
              <div className="text-3xl font-bold text-blue-600">
                {cases.filter(c => c.status === 'processing').length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600">{language === 'de' ? 'Abgeschlossen' : 'Completed'}</div>
              <div className="text-3xl font-bold text-green-600">
                {cases.filter(c => c.status === 'completed').length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600">{language === 'de' ? 'Fehlgeschlagen' : 'Failed'}</div>
              <div className="text-3xl font-bold text-red-600">
                {cases.filter(c => c.status === 'failed').length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Cases Table */}
        <Card>
          <CardHeader>
            <CardTitle>
              {language === 'de' ? 'Forensische Fälle' : 'Forensic Cases'} ({filteredCases.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 mx-auto mb-4 animate-spin text-indigo-600" />
                <p className="text-gray-600">{language === 'de' ? 'Lädt...' : 'Loading...'}</p>
              </div>
            ) : filteredCases.length === 0 ? (
              <div className="text-center py-12">
                <Fingerprint className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-600">
                  {language === 'de' ? 'Keine Fälle gefunden' : 'No cases found'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b-2 border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Case ID</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Kunde' : 'Client'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Datei' : 'File'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Erstellt' : 'Created'}
                      </th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Aktionen' : 'Actions'}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredCases.map((caseItem) => (
                      <tr key={caseItem.case_id} className="hover:bg-gray-50">
                        <td className="px-4 py-4">
                          <div className="font-medium text-gray-900">{caseItem.case_id}</div>
                          <div className="text-sm text-gray-500">{caseItem.client_number}</div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="text-sm text-gray-900">{caseItem.client_email}</div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="text-sm text-gray-900">{caseItem.file_name}</div>
                          <div className="text-xs text-gray-500">{formatFileSize(caseItem.file_size)}</div>
                        </td>
                        <td className="px-4 py-4">
                          <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(caseItem.status)}`}>
                            {getStatusIcon(caseItem.status)}
                            <span>{getStatusText(caseItem.status)}</span>
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {formatDate(caseItem.created_at)}
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center justify-center space-x-2">
                            <Button
                              onClick={() => handleViewDetails(caseItem)}
                              size="sm"
                              variant="outline"
                              className="border-indigo-300 text-indigo-600 hover:bg-indigo-50"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleDeleteCase(caseItem.case_id)}
                              size="sm"
                              variant="outline"
                              className="border-red-300 text-red-600 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Details Modal with Tabs */}
      {showDetailsModal && selectedCase && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-5xl w-full max-h-[95vh] flex flex-col">
            {/* Header */}
            <div className="p-4 border-b flex items-center justify-between shrink-0">
              <div>
                <h2 className="text-xl font-bold">{language === 'de' ? 'Fall Details' : 'Case Details'}</h2>
                <p className="text-sm text-gray-500">{selectedCase.case_id}</p>
              </div>
              <Button onClick={() => setShowDetailsModal(false)} variant="ghost" size="sm">✕</Button>
            </div>

            {/* Tabs */}
            <div className="border-b px-4 shrink-0">
              <nav className="flex space-x-1 overflow-x-auto">
                {[
                  { id: 'overview', label: language === 'de' ? 'Übersicht' : 'Overview', icon: FileText },
                  { id: 'messages', label: language === 'de' ? 'Nachrichten' : 'Messages', icon: MessageCircle },
                  { id: 'timeline', label: 'Timeline', icon: Calendar },
                  { id: 'contacts', label: language === 'de' ? 'Kontakte' : 'Contacts', icon: Users },
                  { id: 'analysis', label: language === 'de' ? 'AI Analyse' : 'AI Analysis', icon: AlertTriangle }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                      activeTab === tab.id
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">{language === 'de' ? 'Fall-ID' : 'Case ID'}</p>
                      <p className="font-medium">{selectedCase.case_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(selectedCase.status)}`}>
                        {getStatusIcon(selectedCase.status)}
                        <span>{getStatusText(selectedCase.status)}</span>
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">{language === 'de' ? 'Kunde' : 'Client'}</p>
                      <p className="font-medium">{selectedCase.client_email}</p>
                      <p className="text-xs text-gray-500">{selectedCase.client_number}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">{language === 'de' ? 'Datei' : 'File'}</p>
                      <p className="font-medium">{selectedCase.file_name}</p>
                      <p className="text-xs text-gray-500">{formatFileSize(selectedCase.file_size)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">{language === 'de' ? 'Erstellt' : 'Created'}</p>
                      <p className="font-medium">{formatDate(selectedCase.created_at)}</p>
                    </div>
                    {selectedCase.completed_at && (
                      <div>
                        <p className="text-sm text-gray-600">{language === 'de' ? 'Abgeschlossen' : 'Completed'}</p>
                        <p className="font-medium">{formatDate(selectedCase.completed_at)}</p>
                      </div>
                    )}
                  </div>

                  {selectedCase.statistics && (
                    <div>
                      <h3 className="font-semibold mb-3">{language === 'de' ? 'Statistiken' : 'Statistics'}</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-green-50 p-3 rounded border border-green-200">
                          <p className="text-xs text-gray-600">WhatsApp</p>
                          <p className="text-2xl font-bold text-green-700">{selectedCase.statistics?.whatsapp_messages || 0}</p>
                        </div>
                        <div className="bg-blue-50 p-3 rounded border border-blue-200">
                          <p className="text-xs text-gray-600">Telegram</p>
                          <p className="text-2xl font-bold text-blue-700">{selectedCase.statistics?.telegram_messages || 0}</p>
                        </div>
                        <div className="bg-purple-50 p-3 rounded border border-purple-200">
                          <p className="text-xs text-gray-600">SMS</p>
                          <p className="text-2xl font-bold text-purple-700">{selectedCase.statistics?.sms_messages || 0}</p>
                        </div>
                        <div className="bg-orange-50 p-3 rounded border border-orange-200">
                          <p className="text-xs text-gray-600">{language === 'de' ? 'Anrufe' : 'Calls'}</p>
                          <p className="text-2xl font-bold text-orange-700">{selectedCase.statistics?.call_logs || 0}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {selectedCase.error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded">
                      <p className="text-sm font-semibold text-red-800">{language === 'de' ? 'Fehler' : 'Error'}</p>
                      <p className="text-sm text-red-600 mt-1">{selectedCase.error}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Messages Tab */}
              {activeTab === 'messages' && (
                <div className="space-y-6">
                  {/* WhatsApp Messages */}
                  {selectedCase.whatsapp?.messages?.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                          <MessageCircle className="w-4 h-4 text-white" />
                        </div>
                        WhatsApp ({selectedCase.whatsapp.messages.length})
                      </h3>
                      <div className="max-h-80 overflow-y-auto">
                        {selectedCase.whatsapp.messages.slice(0, 50).map((msg, idx) =>
                          renderMessageBubble(msg, 'whatsapp', idx)
                        )}
                        {selectedCase.whatsapp.messages.length > 50 && (
                          <p className="text-center text-sm text-gray-500 py-2">
                            ... {language === 'de' ? 'und' : 'and'} {selectedCase.whatsapp.messages.length - 50} {language === 'de' ? 'weitere' : 'more'}
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Telegram Messages */}
                  {selectedCase.telegram?.messages?.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                          <MessageCircle className="w-4 h-4 text-white" />
                        </div>
                        Telegram ({selectedCase.telegram.messages.length})
                      </h3>
                      <div className="max-h-80 overflow-y-auto">
                        {selectedCase.telegram.messages.slice(0, 50).map((msg, idx) =>
                          renderMessageBubble(msg, 'telegram', idx)
                        )}
                      </div>
                    </div>
                  )}

                  {/* SMS Messages */}
                  {selectedCase.sms?.messages?.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center">
                          <Phone className="w-4 h-4 text-white" />
                        </div>
                        SMS ({selectedCase.sms.messages.length})
                      </h3>
                      <div className="max-h-80 overflow-y-auto">
                        {selectedCase.sms.messages.slice(0, 50).map((msg, idx) =>
                          renderMessageBubble(msg, 'sms', idx)
                        )}
                      </div>
                    </div>
                  )}

                  {/* Signal Messages */}
                  {selectedCase.signal?.messages?.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <div className="w-6 h-6 bg-indigo-500 rounded-full flex items-center justify-center">
                          <MessageCircle className="w-4 h-4 text-white" />
                        </div>
                        Signal ({selectedCase.signal.messages.length})
                      </h3>
                      <div className="max-h-80 overflow-y-auto">
                        {selectedCase.signal.messages.slice(0, 50).map((msg, idx) =>
                          renderMessageBubble(msg, 'signal', idx)
                        )}
                      </div>
                    </div>
                  )}

                  {!selectedCase.whatsapp?.messages?.length && !selectedCase.telegram?.messages?.length &&
                   !selectedCase.sms?.messages?.length && !selectedCase.signal?.messages?.length && (
                    <div className="text-center py-12 text-gray-500">
                      <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>{language === 'de' ? 'Keine Nachrichten gefunden' : 'No messages found'}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Timeline Tab */}
              {activeTab === 'timeline' && (
                <div>
                  {selectedCase.timeline?.length > 0 ? (
                    <div className="relative">
                      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
                      <div className="space-y-4">
                        {selectedCase.timeline.slice(0, 100).map((event, idx) => (
                          <div key={idx} className="flex gap-4 relative">
                            <div className="w-8 h-8 rounded-full bg-indigo-100 border-2 border-indigo-500 flex items-center justify-center z-10">
                              <Calendar className="w-4 h-4 text-indigo-600" />
                            </div>
                            <div className="flex-1 bg-gray-50 p-3 rounded-lg">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-medium text-indigo-600">{event.platform || event.source}</span>
                                <span className="text-xs text-gray-500">
                                  {event.timestamp ? new Date(event.timestamp).toLocaleString() : '-'}
                                </span>
                              </div>
                              <p className="text-sm text-gray-700">{event.description || event.content || event.event_type}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      {selectedCase.timeline.length > 100 && (
                        <p className="text-center text-sm text-gray-500 mt-4">
                          ... {language === 'de' ? 'und' : 'and'} {selectedCase.timeline.length - 100} {language === 'de' ? 'weitere Ereignisse' : 'more events'}
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>{language === 'de' ? 'Keine Timeline-Daten' : 'No timeline data'}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Contacts Tab */}
              {activeTab === 'contacts' && (
                <div>
                  {selectedCase.contact_network?.contacts?.length > 0 ? (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {selectedCase.contact_network.contacts.map((contact, idx) => (
                        <div key={idx} className="bg-gray-50 p-4 rounded-lg border">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                              <Users className="w-5 h-5 text-indigo-600" />
                            </div>
                            <div>
                              <p className="font-medium">{contact.name || contact.phone || 'Unknown'}</p>
                              {contact.phone && <p className="text-xs text-gray-500">{contact.phone}</p>}
                              {contact.message_count && (
                                <p className="text-xs text-indigo-600">{contact.message_count} messages</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>{language === 'de' ? 'Keine Kontakte gefunden' : 'No contacts found'}</p>
                    </div>
                  )}
                </div>
              )}

              {/* AI Analysis Tab */}
              {activeTab === 'analysis' && (
                <div>
                  {selectedCase.ai_analysis ? (
                    <div className="space-y-6">
                      {selectedCase.ai_analysis.risk_score !== undefined && (
                        <div className="bg-gradient-to-r from-red-50 to-orange-50 p-4 rounded-lg border border-red-200">
                          <h3 className="font-semibold text-red-800 mb-2">
                            {language === 'de' ? 'Risikobewertung' : 'Risk Assessment'}
                          </h3>
                          <div className="flex items-center gap-4">
                            <div className="text-4xl font-bold text-red-600">
                              {selectedCase.ai_analysis.risk_score}/10
                            </div>
                            <div className="flex-1">
                              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-yellow-400 via-orange-500 to-red-600"
                                  style={{ width: `${selectedCase.ai_analysis.risk_score * 10}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {selectedCase.ai_analysis.summary && (
                        <div className="bg-gray-50 p-4 rounded-lg border">
                          <h3 className="font-semibold mb-2">{language === 'de' ? 'Zusammenfassung' : 'Summary'}</h3>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedCase.ai_analysis.summary}</p>
                        </div>
                      )}

                      {selectedCase.ai_analysis.flags?.length > 0 && (
                        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                          <h3 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5" />
                            {language === 'de' ? 'Warnhinweise' : 'Warning Flags'}
                          </h3>
                          <ul className="space-y-2">
                            {selectedCase.ai_analysis.flags.map((flag, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm text-yellow-800">
                                <span className="text-yellow-600">•</span>
                                {flag}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <AlertTriangle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>{language === 'de' ? 'Keine AI-Analyse verfügbar' : 'No AI analysis available'}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t bg-gray-50 flex justify-between items-center shrink-0">
              <div className="flex gap-2">
                {selectedCase.status === 'completed' && (
                  <>
                    <Button
                      onClick={() => handleDownloadReport('pdf')}
                      variant="outline"
                      size="sm"
                      className="border-green-300 text-green-600 hover:bg-green-50"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      PDF
                    </Button>
                    <Button
                      onClick={() => handleDownloadReport('txt')}
                      variant="outline"
                      size="sm"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      TXT
                    </Button>
                  </>
                )}
              </div>
              <div className="flex gap-2">
                {selectedCase.status === 'completed' && (
                  <Button
                    onClick={handleShareReport}
                    variant="outline"
                    className="border-blue-300 text-blue-600 hover:bg-blue-50"
                  >
                    <LinkIcon className="w-4 h-4 mr-2" />
                    {language === 'de' ? 'Link teilen' : 'Share Link'}
                  </Button>
                )}
                <Button onClick={() => setShowDetailsModal(false)} variant="outline">
                  {language === 'de' ? 'Schließen' : 'Close'}
                </Button>
                <Button
                  onClick={() => handleDeleteCase(selectedCase.case_id)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  {language === 'de' ? 'Löschen' : 'Delete'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminForensics;
