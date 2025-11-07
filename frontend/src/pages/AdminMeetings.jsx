import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { 
  Video, ArrowLeft, Search, Filter, Trash2, Eye, 
  Clock, CheckCircle, XCircle, Calendar, RefreshCw,
  Edit
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminMeetings = () => {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('');

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      toast.error(language === 'de' ? 'Admin-Zugriff erforderlich' : 'Admin access required');
      navigate('/login');
      return;
    }
    fetchMeetings();
  }, [user, token, statusFilter]);

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await axios.get(`${API}/admin/meetings`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      setMeetings(response.data.meetings || []);
    } catch (error) {
      console.error('Failed to fetch meetings:', error);
      toast.error(language === 'de' ? 'Fehler beim Laden der Meetings' : 'Failed to load meetings');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMeeting = async (meetingId) => {
    if (!window.confirm(
      language === 'de' 
        ? 'Sind Sie sicher, dass Sie dieses Meeting löschen möchten?' 
        : 'Are you sure you want to delete this meeting?'
    )) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/meetings/${meetingId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'de' ? 'Meeting gelöscht' : 'Meeting deleted');
      fetchMeetings();
      if (showDetailsModal) setShowDetailsModal(false);
    } catch (error) {
      toast.error(
        language === 'de' ? 'Fehler beim Löschen' : 'Failed to delete meeting',
        { description: error.response?.data?.detail || error.message }
      );
    }
  };

  const handleViewDetails = async (meeting) => {
    try {
      const response = await axios.get(`${API}/admin/meetings/${meeting.meetingId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedMeeting(response.data);
      setShowDetailsModal(true);
    } catch (error) {
      toast.error(language === 'de' ? 'Fehler beim Laden' : 'Failed to load details');
    }
  };

  const handleUpdateStatus = async () => {
    if (!newStatus || !selectedMeeting) return;

    try {
      await axios.patch(
        `${API}/admin/meetings/${selectedMeeting.meetingId}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(language === 'de' ? 'Status aktualisiert' : 'Status updated');
      setShowStatusModal(false);
      fetchMeetings();
      // Update selected meeting
      const response = await axios.get(`${API}/admin/meetings/${selectedMeeting.meetingId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedMeeting(response.data);
    } catch (error) {
      toast.error(
        language === 'de' ? 'Fehler beim Aktualisieren' : 'Failed to update status',
        { description: error.response?.data?.detail || error.message }
      );
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'scheduled':
        return <Calendar className="w-5 h-5 text-blue-600" />;
      case 'in_progress':
        return <Clock className="w-5 h-5 text-yellow-600 animate-pulse" />;
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusText = (status) => {
    const texts = {
      'scheduled': language === 'de' ? 'Geplant' : 'Scheduled',
      'in_progress': language === 'de' ? 'Läuft' : 'In Progress',
      'completed': language === 'de' ? 'Abgeschlossen' : 'Completed',
      'cancelled': language === 'de' ? 'Abgesagt' : 'Cancelled'
    };
    return texts[status] || status;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'completed': return 'bg-green-100 text-green-800 border-green-300';
      case 'cancelled': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString(language === 'de' ? 'de-DE' : 'en-US');
  };

  const filteredMeetings = meetings.filter(m => {
    const matchesSearch = 
      m.meetingId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.clientEmail.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.title.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-cyan-600 to-blue-600 text-white">
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
              <Video className="w-8 h-8" />
              <div>
                <h1 className="text-xl font-bold">
                  {language === 'de' ? 'Video-Konsultationen' : 'Video Consultations'}
                </h1>
                <p className="text-sm opacity-90">
                  {language === 'de' ? 'Verwaltung' : 'Management'}
                </p>
              </div>
            </div>
            <Button
              onClick={fetchMeetings}
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
                  placeholder={language === 'de' ? 'Suche nach Meeting ID, Email, Titel...' : 'Search by Meeting ID, Email, Title...'}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                />
              </div>

              {/* Status Filter */}
              <div className="flex items-center space-x-2">
                <Filter className="w-5 h-5 text-gray-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                >
                  <option value="all">{language === 'de' ? 'Alle Status' : 'All Status'}</option>
                  <option value="scheduled">{language === 'de' ? 'Geplant' : 'Scheduled'}</option>
                  <option value="in_progress">{language === 'de' ? 'Läuft' : 'In Progress'}</option>
                  <option value="completed">{language === 'de' ? 'Abgeschlossen' : 'Completed'}</option>
                  <option value="cancelled">{language === 'de' ? 'Abgesagt' : 'Cancelled'}</option>
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
              <div className="text-3xl font-bold">{meetings.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600">{language === 'de' ? 'Geplant' : 'Scheduled'}</div>
              <div className="text-3xl font-bold text-blue-600">
                {meetings.filter(m => m.status === 'scheduled').length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600">{language === 'de' ? 'Läuft' : 'In Progress'}</div>
              <div className="text-3xl font-bold text-yellow-600">
                {meetings.filter(m => m.status === 'in_progress').length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600">{language === 'de' ? 'Abgeschlossen' : 'Completed'}</div>
              <div className="text-3xl font-bold text-green-600">
                {meetings.filter(m => m.status === 'completed').length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Meetings Table */}
        <Card>
          <CardHeader>
            <CardTitle>
              {language === 'de' ? 'Video-Konsultationen' : 'Video Consultations'} ({filteredMeetings.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 mx-auto mb-4 animate-spin text-cyan-600" />
                <p className="text-gray-600">{language === 'de' ? 'Lädt...' : 'Loading...'}</p>
              </div>
            ) : filteredMeetings.length === 0 ? (
              <div className="text-center py-12">
                <Video className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-600">
                  {language === 'de' ? 'Keine Meetings gefunden' : 'No meetings found'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b-2 border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Meeting ID</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Titel' : 'Title'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Kunde' : 'Client'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Geplant für' : 'Scheduled'}
                      </th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">
                        {language === 'de' ? 'Aktionen' : 'Actions'}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredMeetings.map((meeting) => (
                      <tr key={meeting.meetingId} className="hover:bg-gray-50">
                        <td className="px-4 py-4">
                          <div className="font-medium text-gray-900">{meeting.meetingId}</div>
                          <div className="text-sm text-gray-500">{meeting.clientNumber}</div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="text-sm text-gray-900 font-medium">{meeting.title}</div>
                          <div className="text-xs text-gray-500">{meeting.meetingType}</div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="text-sm text-gray-900">{meeting.clientEmail}</div>
                        </td>
                        <td className="px-4 py-4">
                          <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(meeting.status)}`}>
                            {getStatusIcon(meeting.status)}
                            <span>{getStatusText(meeting.status)}</span>
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {formatDate(meeting.scheduledTime)}
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center justify-center space-x-2">
                            <Button
                              onClick={() => handleViewDetails(meeting)}
                              size="sm"
                              variant="outline"
                              className="border-cyan-300 text-cyan-600 hover:bg-cyan-50"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleDeleteMeeting(meeting.meetingId)}
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

      {/* Details Modal */}
      {showDetailsModal && selectedMeeting && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">{language === 'de' ? 'Meeting Details' : 'Meeting Details'}</h2>
                <Button
                  onClick={() => setShowDetailsModal(false)}
                  variant="ghost"
                  size="sm"
                >
                  ✕
                </Button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">{language === 'de' ? 'Meeting-ID' : 'Meeting ID'}</p>
                  <p className="font-medium">{selectedMeeting.meetingId}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(selectedMeeting.status)}`}>
                      {getStatusIcon(selectedMeeting.status)}
                      <span>{getStatusText(selectedMeeting.status)}</span>
                    </span>
                    <Button
                      onClick={() => {
                        setNewStatus(selectedMeeting.status);
                        setShowStatusModal(true);
                      }}
                      size="sm"
                      variant="outline"
                    >
                      <Edit className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-600">{language === 'de' ? 'Titel' : 'Title'}</p>
                  <p className="font-medium">{selectedMeeting.title}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">{language === 'de' ? 'Typ' : 'Type'}</p>
                  <p className="font-medium">{selectedMeeting.meetingType}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">{language === 'de' ? 'Kunde' : 'Client'}</p>
                  <p className="font-medium">{selectedMeeting.clientEmail}</p>
                  <p className="text-xs text-gray-500">{selectedMeeting.clientNumber}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">{language === 'de' ? 'Dauer' : 'Duration'}</p>
                  <p className="font-medium">{selectedMeeting.duration} {language === 'de' ? 'Minuten' : 'minutes'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">{language === 'de' ? 'Geplant für' : 'Scheduled'}</p>
                  <p className="font-medium">{formatDate(selectedMeeting.scheduledTime)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">{language === 'de' ? 'Erstellt' : 'Created'}</p>
                  <p className="font-medium">{formatDate(selectedMeeting.createdAt)}</p>
                </div>
                {selectedMeeting.startedAt && (
                  <div>
                    <p className="text-sm text-gray-600">{language === 'de' ? 'Gestartet' : 'Started'}</p>
                    <p className="font-medium">{formatDate(selectedMeeting.startedAt)}</p>
                  </div>
                )}
                {selectedMeeting.endedAt && (
                  <div>
                    <p className="text-sm text-gray-600">{language === 'de' ? 'Beendet' : 'Ended'}</p>
                    <p className="font-medium">{formatDate(selectedMeeting.endedAt)}</p>
                  </div>
                )}
              </div>

              {selectedMeeting.description && (
                <div>
                  <p className="text-sm text-gray-600 mb-2">{language === 'de' ? 'Beschreibung' : 'Description'}</p>
                  <p className="text-sm bg-gray-50 p-3 rounded border">{selectedMeeting.description}</p>
                </div>
              )}

              <div>
                <p className="text-sm text-gray-600 mb-2">{language === 'de' ? 'Meeting-Link' : 'Meeting URL'}</p>
                <a
                  href={selectedMeeting.meetingUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-cyan-600 hover:text-cyan-800 break-all"
                >
                  {selectedMeeting.meetingUrl}
                </a>
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-2">{language === 'de' ? 'Raum-Name' : 'Room Name'}</p>
                <p className="text-sm font-mono bg-gray-50 p-2 rounded border">{selectedMeeting.roomName}</p>
              </div>
            </div>
            <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
              <Button
                onClick={() => setShowDetailsModal(false)}
                variant="outline"
              >
                {language === 'de' ? 'Schließen' : 'Close'}
              </Button>
              <Button
                onClick={() => handleDeleteMeeting(selectedMeeting.meetingId)}
                className="bg-red-600 hover:bg-red-700"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Löschen' : 'Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Status Update Modal */}
      {showStatusModal && selectedMeeting && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6 border-b">
              <h3 className="text-xl font-bold">{language === 'de' ? 'Status Aktualisieren' : 'Update Status'}</h3>
            </div>
            <div className="p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {language === 'de' ? 'Neuer Status' : 'New Status'}
              </label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              >
                <option value="scheduled">{language === 'de' ? 'Geplant' : 'Scheduled'}</option>
                <option value="in_progress">{language === 'de' ? 'Läuft' : 'In Progress'}</option>
                <option value="completed">{language === 'de' ? 'Abgeschlossen' : 'Completed'}</option>
                <option value="cancelled">{language === 'de' ? 'Abgesagt' : 'Cancelled'}</option>
              </select>
            </div>
            <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
              <Button
                onClick={() => setShowStatusModal(false)}
                variant="outline"
              >
                {language === 'de' ? 'Abbrechen' : 'Cancel'}
              </Button>
              <Button
                onClick={handleUpdateStatus}
                className="bg-cyan-600 hover:bg-cyan-700"
              >
                {language === 'de' ? 'Aktualisieren' : 'Update'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminMeetings;
