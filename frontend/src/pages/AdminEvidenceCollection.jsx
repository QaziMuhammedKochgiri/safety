import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Loader2,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Shield,
  Smartphone,
  Send,
  Camera,
  Users,
  Video,
  Mail,
  MessageSquare,
  CheckCircle2,
  Clock,
  AlertCircle,
  Archive,
  FileText,
  Download,
  Eye,
  Link2,
  Play,
  Hash,
  Calendar,
  User,
  Folder,
  ChevronRight,
  BarChart3,
  ExternalLink
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

const API_URL = '/api';

// Platform icons and colors
const platformConfig = {
  whatsapp: { icon: Smartphone, color: 'bg-green-500', textColor: 'text-green-600', name: 'WhatsApp' },
  telegram: { icon: Send, color: 'bg-blue-500', textColor: 'text-blue-600', name: 'Telegram' },
  instagram: { icon: Camera, color: 'bg-pink-500', textColor: 'text-pink-600', name: 'Instagram' },
  facebook: { icon: Users, color: 'bg-blue-600', textColor: 'text-blue-700', name: 'Facebook' },
  tiktok: { icon: Video, color: 'bg-black', textColor: 'text-gray-900', name: 'TikTok' },
  email: { icon: Mail, color: 'bg-gray-500', textColor: 'text-gray-600', name: 'Email' },
  sms: { icon: MessageSquare, color: 'bg-green-600', textColor: 'text-green-700', name: 'SMS' }
};

// Status badges
const statusConfig = {
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'Pending' },
  collecting: { color: 'bg-blue-100 text-blue-800', icon: Loader2, label: 'Collecting' },
  collected: { color: 'bg-green-100 text-green-800', icon: CheckCircle2, label: 'Collected' },
  verified: { color: 'bg-emerald-100 text-emerald-800', icon: Shield, label: 'Verified' },
  failed: { color: 'bg-red-100 text-red-800', icon: AlertCircle, label: 'Failed' },
  archived: { color: 'bg-gray-100 text-gray-800', icon: Archive, label: 'Archived' }
};

const AdminEvidenceCollection = () => {
  const { user, token } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();

  // State
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [platforms, setPlatforms] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionEvidence, setSessionEvidence] = useState([]);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // New Session Dialog
  const [showNewSession, setShowNewSession] = useState(false);
  const [newSessionData, setNewSessionData] = useState({
    case_id: '',
    client_number: '',
    platforms: [],
    notes: ''
  });
  const [creatingSession, setCreatingSession] = useState(false);

  // Translations
  const t = {
    title: language === 'de' ? 'Beweissammlung' : 'Evidence Collection',
    subtitle: language === 'de' ? 'Multi-Plattform Beweissicherung' : 'Multi-Platform Evidence Collection',
    newSession: language === 'de' ? 'Neue Sammlung' : 'New Collection',
    sessions: language === 'de' ? 'Sammlungen' : 'Sessions',
    dashboard: language === 'de' ? 'Dashboard' : 'Dashboard',
    platforms: language === 'de' ? 'Plattformen' : 'Platforms',
    tasks: language === 'de' ? 'Aufgaben' : 'Tasks',
    selectClient: language === 'de' ? 'Mandant auswahlen' : 'Select Client',
    selectPlatforms: language === 'de' ? 'Plattformen auswahlen' : 'Select Platforms',
    caseId: language === 'de' ? 'Fall-ID' : 'Case ID',
    notes: language === 'de' ? 'Notizen' : 'Notes',
    create: language === 'de' ? 'Erstellen' : 'Create',
    cancel: language === 'de' ? 'Abbrechen' : 'Cancel',
    noSessions: language === 'de' ? 'Keine Sammlungen gefunden' : 'No sessions found',
    totalSessions: language === 'de' ? 'Gesamt Sammlungen' : 'Total Sessions',
    totalEvidence: language === 'de' ? 'Gesammelte Beweise' : 'Collected Evidence',
    verifiedEvidence: language === 'de' ? 'Verifizierte Beweise' : 'Verified Evidence',
    activePlatforms: language === 'de' ? 'Aktive Plattformen' : 'Active Platforms',
    viewDetails: language === 'de' ? 'Details anzeigen' : 'View Details',
    generatePackage: language === 'de' ? 'Paket erstellen' : 'Generate Package',
    startCollection: language === 'de' ? 'Sammlung starten' : 'Start Collection',
    evidenceItems: language === 'de' ? 'Beweismittel' : 'Evidence Items',
    chainOfCustody: language === 'de' ? 'Beweismittelkette' : 'Chain of Custody',
    refresh: language === 'de' ? 'Aktualisieren' : 'Refresh'
  };

  // Axios config
  const axiosConfig = useCallback(() => ({
    headers: { Authorization: `Bearer ${token}` }
  }), [token]);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [sessionsRes, dashboardRes, platformsRes, clientsRes] = await Promise.all([
        axios.get(`${API_URL}/evidence/sessions`, axiosConfig()),
        axios.get(`${API_URL}/evidence/dashboard`, axiosConfig()),
        axios.get(`${API_URL}/evidence/platforms`, axiosConfig()),
        axios.get(`${API_URL}/clients`, axiosConfig())
      ]);

      setSessions(sessionsRes.data.sessions || []);
      setDashboardStats(dashboardRes.data);
      setPlatforms(platformsRes.data.platforms || []);
      setClients(clientsRes.data.clients || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  }, [axiosConfig]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load session evidence
  const loadSessionEvidence = async (sessionId) => {
    try {
      const response = await axios.get(
        `${API_URL}/evidence/sessions/${sessionId}/evidence`,
        axiosConfig()
      );
      setSessionEvidence(response.data.evidence || []);
    } catch (error) {
      console.error('Failed to load evidence:', error);
    }
  };

  // Create new session
  const handleCreateSession = async () => {
    if (!newSessionData.client_number || !newSessionData.case_id || newSessionData.platforms.length === 0) {
      return;
    }

    setCreatingSession(true);
    try {
      const response = await axios.post(
        `${API_URL}/evidence/sessions`,
        newSessionData,
        axiosConfig()
      );

      setSessions([response.data, ...sessions]);
      setShowNewSession(false);
      setNewSessionData({ case_id: '', client_number: '', platforms: [], notes: '' });
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setCreatingSession(false);
    }
  };

  // Toggle platform selection
  const togglePlatform = (platformId) => {
    setNewSessionData(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platformId)
        ? prev.platforms.filter(p => p !== platformId)
        : [...prev.platforms, platformId]
    }));
  };

  // Start platform collection
  const handleStartCollection = async (sessionId, platform) => {
    try {
      await axios.post(
        `${API_URL}/evidence/sessions/${sessionId}/start`,
        { platform },
        axiosConfig()
      );
      loadData();
    } catch (error) {
      console.error('Failed to start collection:', error);
    }
  };

  // Generate evidence package
  const handleGeneratePackage = async (sessionId) => {
    try {
      const response = await axios.post(
        `${API_URL}/evidence/sessions/${sessionId}/package`,
        { include_ai_analysis: true },
        axiosConfig()
      );

      // Show success or download
      alert(`Package generated: ${response.data.package_id}`);
    } catch (error) {
      console.error('Failed to generate package:', error);
    }
  };

  // Filter sessions
  const filteredSessions = sessions.filter(session => {
    const matchesSearch =
      session.session_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.case_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.client_number?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || session.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  // Platform icon component
  const PlatformIcon = ({ platform, size = 'md' }) => {
    const config = platformConfig[platform] || platformConfig.email;
    const IconComponent = config.icon;
    const sizeClass = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5';

    return (
      <div className={`${config.color} p-1.5 rounded-lg text-white`}>
        <IconComponent className={sizeClass} />
      </div>
    );
  };

  // Status badge component
  const StatusBadge = ({ status }) => {
    const config = statusConfig[status] || statusConfig.pending;
    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} gap-1`}>
        <IconComponent className={`w-3 h-3 ${status === 'collecting' ? 'animate-spin' : ''}`} />
        {config.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Shield className="w-7 h-7 text-blue-600" />
              {t.title}
            </h1>
            <p className="text-gray-500 mt-1">{t.subtitle}</p>
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={loadData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              {t.refresh}
            </Button>

            <Dialog open={showNewSession} onOpenChange={setShowNewSession}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  {t.newSession}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>{t.newSession}</DialogTitle>
                  <DialogDescription>
                    {language === 'de'
                      ? 'Erstellen Sie eine neue Beweissammlung fur einen Mandanten'
                      : 'Create a new evidence collection session for a client'}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                  {/* Client Selection */}
                  <div className="space-y-2">
                    <Label>{t.selectClient}</Label>
                    <Select
                      value={newSessionData.client_number}
                      onValueChange={(value) => setNewSessionData(prev => ({ ...prev, client_number: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={t.selectClient} />
                      </SelectTrigger>
                      <SelectContent>
                        {clients.map((client) => (
                          <SelectItem key={client.clientNumber} value={client.clientNumber}>
                            {client.fullName} ({client.clientNumber})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Case ID */}
                  <div className="space-y-2">
                    <Label>{t.caseId}</Label>
                    <Input
                      value={newSessionData.case_id}
                      onChange={(e) => setNewSessionData(prev => ({ ...prev, case_id: e.target.value }))}
                      placeholder="CASE-2024-001"
                    />
                  </div>

                  {/* Platform Selection */}
                  <div className="space-y-2">
                    <Label>{t.selectPlatforms}</Label>
                    <div className="grid grid-cols-3 gap-3">
                      {platforms.map((platform) => {
                        const config = platformConfig[platform.id] || platformConfig.email;
                        const IconComponent = config.icon;
                        const isSelected = newSessionData.platforms.includes(platform.id);

                        return (
                          <button
                            key={platform.id}
                            type="button"
                            onClick={() => togglePlatform(platform.id)}
                            className={`p-3 rounded-lg border-2 transition-all ${
                              isSelected
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <div className={`${config.color} p-1.5 rounded text-white`}>
                                <IconComponent className="w-4 h-4" />
                              </div>
                              <span className="font-medium text-sm">{platform.name}</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1 text-left">
                              {platform.collection_type === 'automated'
                                ? (language === 'de' ? 'Automatisch' : 'Automated')
                                : (language === 'de' ? 'Manuell' : 'Manual')}
                            </p>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Notes */}
                  <div className="space-y-2">
                    <Label>{t.notes}</Label>
                    <Input
                      value={newSessionData.notes}
                      onChange={(e) => setNewSessionData(prev => ({ ...prev, notes: e.target.value }))}
                      placeholder={language === 'de' ? 'Optionale Notizen...' : 'Optional notes...'}
                    />
                  </div>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowNewSession(false)}>
                    {t.cancel}
                  </Button>
                  <Button
                    onClick={handleCreateSession}
                    disabled={creatingSession || !newSessionData.client_number || !newSessionData.case_id || newSessionData.platforms.length === 0}
                  >
                    {creatingSession && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    {t.create}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <Tabs defaultValue="dashboard" className="space-y-4">
          <TabsList>
            <TabsTrigger value="dashboard" className="gap-2">
              <BarChart3 className="w-4 h-4" />
              {t.dashboard}
            </TabsTrigger>
            <TabsTrigger value="sessions" className="gap-2">
              <Folder className="w-4 h-4" />
              {t.sessions}
            </TabsTrigger>
            <TabsTrigger value="platforms" className="gap-2">
              <Smartphone className="w-4 h-4" />
              {t.platforms}
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-4">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">{t.totalSessions}</p>
                      <p className="text-3xl font-bold">{dashboardStats?.total_sessions || 0}</p>
                    </div>
                    <div className="p-3 bg-blue-100 rounded-full">
                      <Folder className="w-6 h-6 text-blue-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">{t.totalEvidence}</p>
                      <p className="text-3xl font-bold">{dashboardStats?.total_evidence_items || 0}</p>
                    </div>
                    <div className="p-3 bg-green-100 rounded-full">
                      <FileText className="w-6 h-6 text-green-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">{t.verifiedEvidence}</p>
                      <p className="text-3xl font-bold">{dashboardStats?.verified_evidence || 0}</p>
                    </div>
                    <div className="p-3 bg-emerald-100 rounded-full">
                      <Shield className="w-6 h-6 text-emerald-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">{t.activePlatforms}</p>
                      <p className="text-3xl font-bold">
                        {Object.keys(dashboardStats?.platform_usage || {}).length}
                      </p>
                    </div>
                    <div className="p-3 bg-purple-100 rounded-full">
                      <Link2 className="w-6 h-6 text-purple-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Platform Usage */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  {language === 'de' ? 'Plattform-Nutzung' : 'Platform Usage'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(dashboardStats?.platform_usage || {}).map(([platform, count]) => {
                    const config = platformConfig[platform] || platformConfig.email;
                    return (
                      <div
                        key={platform}
                        className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                      >
                        <PlatformIcon platform={platform} />
                        <div>
                          <p className="font-medium">{config.name}</p>
                          <p className="text-sm text-gray-500">{count} sessions</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Recent Sessions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  {language === 'de' ? 'Neueste Sammlungen' : 'Recent Sessions'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(dashboardStats?.recent_sessions || []).map((session) => (
                    <div
                      key={session.session_id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                      onClick={() => {
                        setSelectedSession(session);
                        loadSessionEvidence(session.session_id);
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex -space-x-1">
                          {(session.platforms || []).slice(0, 3).map((p, idx) => (
                            <div key={idx} className="border-2 border-white rounded-lg">
                              <PlatformIcon platform={p} size="sm" />
                            </div>
                          ))}
                        </div>
                        <div>
                          <p className="font-medium">{session.session_id}</p>
                          <p className="text-sm text-gray-500">{session.case_id}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge status={session.status} />
                        <Badge variant="outline">{session.evidence_count} items</Badge>
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sessions Tab */}
          <TabsContent value="sessions" className="space-y-4">
            {/* Search and Filters */}
            <div className="flex gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder={language === 'de' ? 'Suche nach ID, Fall, Mandant...' : 'Search by ID, case, client...'}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="collecting">Collecting</SelectItem>
                  <SelectItem value="collected">Collected</SelectItem>
                  <SelectItem value="verified">Verified</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sessions List */}
            <div className="space-y-3">
              {filteredSessions.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Folder className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">{t.noSessions}</p>
                  </CardContent>
                </Card>
              ) : (
                filteredSessions.map((session) => (
                  <Card key={session.session_id} className="hover:shadow-md transition-shadow">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          {/* Platform Icons */}
                          <div className="flex -space-x-1">
                            {(session.platforms || []).map((p, idx) => (
                              <div key={idx} className="border-2 border-white rounded-lg">
                                <PlatformIcon platform={p} />
                              </div>
                            ))}
                          </div>

                          {/* Session Info */}
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">{session.session_id}</span>
                              <StatusBadge status={session.status} />
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                              <span className="flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                {session.case_id}
                              </span>
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {session.client_number}
                              </span>
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(session.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Stats & Actions */}
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-sm font-medium">{session.evidence_count || 0} {t.evidenceItems}</p>
                            <p className="text-xs text-gray-500">
                              {session.total_messages || 0} messages, {session.total_media || 0} media
                            </p>
                          </div>

                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedSession(session);
                                loadSessionEvidence(session.session_id);
                              }}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              {t.viewDetails}
                            </Button>

                            {session.status === 'collected' && (
                              <Button
                                size="sm"
                                onClick={() => handleGeneratePackage(session.session_id)}
                              >
                                <Download className="w-4 h-4 mr-1" />
                                {t.generatePackage}
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Platforms Tab */}
          <TabsContent value="platforms" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {platforms.map((platform) => {
                const config = platformConfig[platform.id] || platformConfig.email;
                const IconComponent = config.icon;

                return (
                  <Card key={platform.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-4">
                        <div className={`${config.color} p-3 rounded-xl text-white`}>
                          <IconComponent className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">{platform.name}</h3>
                          <Badge variant="outline" className="mt-1">
                            {platform.collection_type === 'automated'
                              ? (language === 'de' ? 'Automatisiert' : 'Automated')
                              : platform.collection_type === 'manual'
                              ? (language === 'de' ? 'Manuell' : 'Manual')
                              : 'URL Archive'}
                          </Badge>
                          <p className="text-sm text-gray-500 mt-2">
                            {platform.description?.[language] || platform.description?.en}
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t flex justify-between items-center">
                        <span className="text-sm text-gray-500">
                          {dashboardStats?.platform_usage?.[platform.id] || 0} {language === 'de' ? 'Sammlungen' : 'collections'}
                        </span>
                        <Button variant="ghost" size="sm" className={config.textColor}>
                          <ExternalLink className="w-4 h-4 mr-1" />
                          {language === 'de' ? 'Dokumentation' : 'Documentation'}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>
        </Tabs>

        {/* Session Detail Modal */}
        {selectedSession && (
          <Dialog open={!!selectedSession} onOpenChange={() => setSelectedSession(null)}>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-600" />
                  {selectedSession.session_id}
                </DialogTitle>
                <DialogDescription>
                  {selectedSession.case_id} | {selectedSession.client_number}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6 py-4">
                {/* Session Status */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <StatusBadge status={selectedSession.status} />
                    <span className="text-sm text-gray-500">
                      Created: {new Date(selectedSession.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {selectedSession.platforms?.map((p) => (
                      <PlatformIcon key={p} platform={p} />
                    ))}
                  </div>
                </div>

                {/* Platform Collection Controls */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{t.startCollection}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {selectedSession.platforms?.map((platform) => {
                        const config = platformConfig[platform] || platformConfig.email;
                        const platformSession = selectedSession.platform_sessions?.[platform];

                        return (
                          <div
                            key={platform}
                            className="p-3 border rounded-lg flex items-center justify-between"
                          >
                            <div className="flex items-center gap-2">
                              <PlatformIcon platform={platform} size="sm" />
                              <span className="font-medium">{config.name}</span>
                            </div>
                            {platformSession ? (
                              <Badge variant="outline" className="text-green-600">
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                Active
                              </Badge>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleStartCollection(selectedSession.session_id, platform)}
                              >
                                <Play className="w-3 h-3 mr-1" />
                                Start
                              </Button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Evidence Items */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center justify-between">
                      <span>{t.evidenceItems} ({sessionEvidence.length})</span>
                      <Button variant="ghost" size="sm" onClick={() => loadSessionEvidence(selectedSession.session_id)}>
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {sessionEvidence.length === 0 ? (
                      <p className="text-center text-gray-500 py-8">
                        {language === 'de' ? 'Noch keine Beweise gesammelt' : 'No evidence collected yet'}
                      </p>
                    ) : (
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {sessionEvidence.slice(0, 20).map((evidence) => (
                          <div
                            key={evidence.evidence_id}
                            className="flex items-center justify-between p-2 bg-gray-50 rounded"
                          >
                            <div className="flex items-center gap-2">
                              <PlatformIcon platform={evidence.platform} size="sm" />
                              <div>
                                <span className="text-sm font-medium">{evidence.evidence_id}</span>
                                <Badge variant="outline" className="ml-2 text-xs">
                                  {evidence.evidence_type}
                                </Badge>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {evidence.verified ? (
                                <Badge className="bg-green-100 text-green-800">
                                  <Shield className="w-3 h-3 mr-1" />
                                  Verified
                                </Badge>
                              ) : (
                                <Badge variant="outline">Pending</Badge>
                              )}
                              {evidence.file_hash_sha256 && (
                                <Hash className="w-4 h-4 text-gray-400" title={evidence.file_hash_sha256} />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Chain of Custody */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{t.chainOfCustody}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(selectedSession.chain_of_custody || []).map((entry, idx) => (
                        <div key={idx} className="flex items-start gap-3">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2" />
                          <div className="flex-1">
                            <p className="text-sm font-medium">{entry.action}</p>
                            <p className="text-xs text-gray-500">
                              {new Date(entry.timestamp).toLocaleString()} | {entry.actor}
                            </p>
                            {entry.notes && (
                              <p className="text-xs text-gray-400 mt-1">{entry.notes}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setSelectedSession(null)}>
                  {t.cancel}
                </Button>
                <Button onClick={() => handleGeneratePackage(selectedSession.session_id)}>
                  <Download className="w-4 h-4 mr-2" />
                  {t.generatePackage}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  );
};

export default AdminEvidenceCollection;
