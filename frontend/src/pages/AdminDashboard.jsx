import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { 
  Users, FileText, Shield, MessageSquare, 
  LogOut, TrendingUp, Activity, Eye, Video, Fingerprint
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = () => {
  const { language } = useLanguage();
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      toast.error(language === 'de' ? 'Admin-Zugriff erforderlich' : 'Admin access required');
      navigate('/login');
      return;
    }
    fetchStats();
  }, [user, token]);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      toast.error(language === 'de' ? 'Fehler beim Laden der Statistiken' : 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    toast.success(language === 'de' ? 'Erfolgreich abgemeldet' : 'Successfully logged out');
    navigate('/');
  };

  if (loading || !stats) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">{language === 'de' ? 'Laden...' : 'Loading...'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8" />
              <div>
                <h1 className="text-xl font-bold">
                  {language === 'de' ? 'Admin Dashboard' : 'Admin Dashboard'}
                </h1>
                <p className="text-sm opacity-90">SafeChild Rechtsanwaltskanzlei</p>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="text-white border-white hover:bg-white/10"
            >
              <LogOut className="w-4 h-4 mr-2" />
              {language === 'de' ? 'Abmelden' : 'Logout'}
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Card */}
        <Card className="mb-8 border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-white">
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {language === 'de' ? 'Willkommen, Admin' : 'Welcome, Admin'}
                </h2>
                <p className="text-gray-600">
                  {language === 'de' 
                    ? 'Verwalten Sie Mandanten, Dokumente und System-Einstellungen' 
                    : 'Manage clients, documents, and system settings'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Statistics Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Card className="border-2 hover:border-blue-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'Gesamt Mandanten' : 'Total Clients'}
              </CardTitle>
              <Users className="w-8 h-8 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalClients}</div>
              <p className="text-xs text-gray-600 mt-1">
                {stats.activeClients} {language === 'de' ? 'aktiv' : 'active'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:border-green-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'Dokumente' : 'Documents'}
              </CardTitle>
              <FileText className="w-8 h-8 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalDocuments}</div>
              <p className="text-xs text-gray-600 mt-1">
                {language === 'de' ? 'Hochgeladene Dateien' : 'Uploaded files'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:border-purple-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'Nachrichten' : 'Messages'}
              </CardTitle>
              <MessageSquare className="w-8 h-8 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalMessages}</div>
              <p className="text-xs text-gray-600 mt-1">
                {language === 'de' ? 'Chat-Nachrichten' : 'Chat messages'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:border-orange-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'Neue Mandanten' : 'New Clients'}
              </CardTitle>
              <TrendingUp className="w-8 h-8 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.recentClients}</div>
              <p className="text-xs text-gray-600 mt-1">
                {language === 'de' ? 'Letzte 7 Tage' : 'Last 7 days'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:border-red-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'Einwilligungen' : 'Consents'}
              </CardTitle>
              <Activity className="w-8 h-8 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalConsents}</div>
              <p className="text-xs text-gray-600 mt-1">
                {language === 'de' ? 'Consent Logs' : 'Consent logs'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:border-indigo-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'Forensische Fälle' : 'Forensic Cases'}
              </CardTitle>
              <Fingerprint className="w-8 h-8 text-indigo-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalForensicCases || 0}</div>
              <p className="text-xs text-gray-600 mt-1">
                {stats.processingCases || 0} {language === 'de' ? 'in Bearbeitung' : 'processing'} • {stats.completedCases || 0} {language === 'de' ? 'abgeschlossen' : 'completed'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:border-cyan-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'Video-Konsultationen' : 'Video Consultations'}
              </CardTitle>
              <Video className="w-8 h-8 text-cyan-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalMeetings || 0}</div>
              <p className="text-xs text-gray-600 mt-1">
                {stats.scheduledMeetings || 0} {language === 'de' ? 'geplant' : 'scheduled'} • {stats.completedMeetings || 0} {language === 'de' ? 'abgeschlossen' : 'completed'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:border-green-500 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {language === 'de' ? 'System Status' : 'System Status'}
              </CardTitle>
              <Activity className="w-8 h-8 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {language === 'de' ? 'Online' : 'Online'}
              </div>
              <p className="text-xs text-gray-600 mt-1">
                {language === 'de' ? 'Alle Systeme funktionieren' : 'All systems operational'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle>{language === 'de' ? 'Schnellzugriff' : 'Quick Actions'}</CardTitle>
            <CardDescription>
              {language === 'de' ? 'Häufig verwendete Funktionen' : 'Frequently used functions'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Button
                onClick={() => navigate('/admin/clients')}
                className="h-24 flex flex-col items-center justify-center space-y-2 bg-blue-600 hover:bg-blue-700"
              >
                <Users className="w-8 h-8" />
                <span>{language === 'de' ? 'Mandanten verwalten' : 'Manage Clients'}</span>
              </Button>
              
              <Button
                onClick={() => navigate('/admin/forensics')}
                className="h-24 flex flex-col items-center justify-center space-y-2 bg-indigo-600 hover:bg-indigo-700"
              >
                <Fingerprint className="w-8 h-8" />
                <span>{language === 'de' ? 'Forensische Fälle' : 'Forensic Cases'}</span>
              </Button>

              <Button
                onClick={() => navigate('/admin/meetings')}
                className="h-24 flex flex-col items-center justify-center space-y-2 bg-cyan-600 hover:bg-cyan-700"
              >
                <Video className="w-8 h-8" />
                <span>{language === 'de' ? 'Video-Konsultationen' : 'Video Consultations'}</span>
              </Button>
              
              <Button
                onClick={() => navigate('/admin/documents')}
                className="h-24 flex flex-col items-center justify-center space-y-2 bg-green-600 hover:bg-green-700"
              >
                <FileText className="w-8 h-8" />
                <span>{language === 'de' ? 'Dokumente' : 'Documents'}</span>
              </Button>
              
              <Button
                onClick={() => navigate('/admin/consents')}
                className="h-24 flex flex-col items-center justify-center space-y-2 bg-purple-600 hover:bg-purple-700"
              >
                <Shield className="w-8 h-8" />
                <span>{language === 'de' ? 'Einwilligungen' : 'Consents'}</span>
              </Button>
              
              <Button
                onClick={() => navigate('/admin/messages')}
                className="h-24 flex flex-col items-center justify-center space-y-2 bg-orange-600 hover:bg-orange-700"
              >
                <MessageSquare className="w-8 h-8" />
                <span>{language === 'de' ? 'Nachrichten' : 'Messages'}</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
