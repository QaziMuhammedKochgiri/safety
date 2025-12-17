import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import {
  Smartphone, ArrowLeft, Plus, Download, CheckCircle, AlertCircle,
  Loader2, Image, MessageSquare, Users, Phone, Trash2, Clock,
  Copy, RefreshCw, Link2, ExternalLink, Search, Filter,
  Apple, Bot, FileText, Calendar, Shield, XCircle
} from 'lucide-react';
import axios from 'axios';

const API_URL = '/api';

const AdminPhoneRecovery = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();

  // State
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Create form state - device_type removed, client page auto-detects
  const [newCase, setNewCase] = useState({
    client_number: '',
    expires_in_days: 7
  });

  // Fetch cases
  const fetchCases = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/recovery/list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data || []);
    } catch (error) {
      console.error('Error fetching cases:', error);
      toast.error(language === 'de' ? 'Fehler beim Laden' : 'Failed to load cases');
    } finally {
      setLoading(false);
    }
  }, [token, language]);

  useEffect(() => {
    fetchCases();
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchCases, 10000);
    return () => clearInterval(interval);
  }, [fetchCases]);

  // Create new recovery link
  const handleCreateLink = async (e) => {
    e.preventDefault();
    if (!newCase.client_number.trim()) {
      toast.error(language === 'de' ? 'Mandantennummer erforderlich' : 'Client number required');
      return;
    }

    setCreating(true);
    try {
      const response = await axios.post(`${API_URL}/recovery/create-link`, {
        client_number: newCase.client_number,
        expires_in_days: newCase.expires_in_days
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(language === 'de' ? 'Link erstellt!' : 'Link created!');

      // Copy link to clipboard
      await navigator.clipboard.writeText(response.data.recovery_link);
      toast.success(language === 'de' ? 'Link in Zwischenablage kopiert' : 'Link copied to clipboard');

      // Reset form and refresh
      setNewCase({ client_number: '', expires_in_days: 7 });
      setShowCreateForm(false);
      fetchCases();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create link');
    } finally {
      setCreating(false);
    }
  };

  // Copy link to clipboard
  const copyLink = async (link) => {
    try {
      await navigator.clipboard.writeText(link);
      toast.success(language === 'de' ? 'Kopiert!' : 'Copied!');
    } catch (error) {
      toast.error('Failed to copy');
    }
  };

  // Download results
  const downloadResults = async (caseId) => {
    try {
      const response = await axios.get(`${API_URL}/recovery/cases/${caseId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${caseId}_recovery.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(language === 'de' ? 'Download gestartet' : 'Download started');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Download failed');
    }
  };

  // Delete case
  const deleteCase = async (caseId) => {
    if (!window.confirm(language === 'de'
      ? 'Möchten Sie diesen Fall wirklich löschen? Alle Daten werden gelöscht.'
      : 'Are you sure you want to delete this case? All data will be removed.')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/recovery/cases/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'de' ? 'Gelöscht' : 'Deleted');
      fetchCases();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Delete failed');
    }
  };

  // Status badge component
  const StatusBadge = ({ status }) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: Clock, label: language === 'de' ? 'Wartend' : 'Pending' },
      device_connected: { color: 'bg-blue-100 text-blue-800 border-blue-300', icon: Smartphone, label: language === 'de' ? 'Verbunden' : 'Connected' },
      extracting: { color: 'bg-purple-100 text-purple-800 border-purple-300', icon: Loader2, label: language === 'de' ? 'Extrahieren' : 'Extracting' },
      processing: { color: 'bg-orange-100 text-orange-800 border-orange-300', icon: Loader2, label: language === 'de' ? 'Verarbeiten' : 'Processing' },
      completed: { color: 'bg-green-100 text-green-800 border-green-300', icon: CheckCircle, label: language === 'de' ? 'Abgeschlossen' : 'Completed' },
      failed: { color: 'bg-red-100 text-red-800 border-red-300', icon: XCircle, label: language === 'de' ? 'Fehlgeschlagen' : 'Failed' },
      expired: { color: 'bg-gray-100 text-gray-800 border-gray-300', icon: AlertCircle, label: language === 'de' ? 'Abgelaufen' : 'Expired' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge variant="outline" className={`${config.color} flex items-center gap-1`}>
        <Icon className={`w-3 h-3 ${status === 'extracting' || status === 'processing' ? 'animate-spin' : ''}`} />
        {config.label}
      </Badge>
    );
  };

  // Filter cases
  const filteredCases = cases.filter(c => {
    const matchesSearch =
      c.client_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.case_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.recovery_code?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  // Stats
  const stats = {
    total: cases.length,
    pending: cases.filter(c => c.status === 'pending').length,
    processing: cases.filter(c => ['extracting', 'processing', 'device_connected'].includes(c.status)).length,
    completed: cases.filter(c => c.status === 'completed').length,
    failed: cases.filter(c => c.status === 'failed').length
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate('/admin')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Zurück' : 'Back'}
              </Button>
              <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
                  <Smartphone className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-800">
                    {language === 'de' ? 'Telefon Datenwiederherstellung' : 'Phone Data Recovery'}
                  </h1>
                  <p className="text-sm text-gray-500">
                    {language === 'de' ? 'Recovery-Links verwalten' : 'Manage recovery links'}
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={fetchCases}>
                <RefreshCw className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Aktualisieren' : 'Refresh'}
              </Button>
              <Button onClick={() => setShowCreateForm(true)} className="bg-gradient-to-r from-blue-600 to-purple-600">
                <Plus className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Neuer Link' : 'New Link'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <Card className="border-2">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
              <p className="text-sm text-gray-600">{language === 'de' ? 'Gesamt' : 'Total'}</p>
            </CardContent>
          </Card>
          <Card className="border-2 border-yellow-200 bg-yellow-50">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-yellow-700">{stats.pending}</p>
              <p className="text-sm text-yellow-600">{language === 'de' ? 'Wartend' : 'Pending'}</p>
            </CardContent>
          </Card>
          <Card className="border-2 border-purple-200 bg-purple-50">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-700">{stats.processing}</p>
              <p className="text-sm text-purple-600">{language === 'de' ? 'In Bearbeitung' : 'Processing'}</p>
            </CardContent>
          </Card>
          <Card className="border-2 border-green-200 bg-green-50">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-700">{stats.completed}</p>
              <p className="text-sm text-green-600">{language === 'de' ? 'Abgeschlossen' : 'Completed'}</p>
            </CardContent>
          </Card>
          <Card className="border-2 border-red-200 bg-red-50">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-red-700">{stats.failed}</p>
              <p className="text-sm text-red-600">{language === 'de' ? 'Fehlgeschlagen' : 'Failed'}</p>
            </CardContent>
          </Card>
        </div>

        {/* Create Form Modal */}
        {showCreateForm && (
          <Card className="mb-8 border-2 border-blue-300 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50">
              <CardTitle className="flex items-center gap-2">
                <Link2 className="w-5 h-5 text-blue-600" />
                {language === 'de' ? 'Neuen Recovery-Link erstellen' : 'Create New Recovery Link'}
              </CardTitle>
              <CardDescription>
                {language === 'de'
                  ? 'Link wird an den Mandanten gesendet, um Daten vom Telefon zu extrahieren'
                  : 'Link will be sent to client to extract data from their phone'}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleCreateLink} className="space-y-4">
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="client_number">
                      {language === 'de' ? 'Mandantennummer' : 'Client Number'} *
                    </Label>
                    <Input
                      id="client_number"
                      placeholder="SC2025..."
                      value={newCase.client_number}
                      onChange={(e) => setNewCase(prev => ({ ...prev, client_number: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="expires">{language === 'de' ? 'Gültig für (Tage)' : 'Valid for (days)'}</Label>
                    <Input
                      id="expires"
                      type="number"
                      min="1"
                      max="30"
                      value={newCase.expires_in_days}
                      onChange={(e) => setNewCase(prev => ({ ...prev, expires_in_days: parseInt(e.target.value) || 7 }))}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                    {language === 'de' ? 'Abbrechen' : 'Cancel'}
                  </Button>
                  <Button type="submit" disabled={creating}>
                    {creating ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Plus className="w-4 h-4 mr-2" />
                    )}
                    {language === 'de' ? 'Link erstellen' : 'Create Link'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Search and Filter */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <Input
              placeholder={language === 'de' ? 'Suchen...' : 'Search...'}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant={statusFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('all')}
            >
              {language === 'de' ? 'Alle' : 'All'}
            </Button>
            <Button
              variant={statusFilter === 'pending' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('pending')}
            >
              {language === 'de' ? 'Wartend' : 'Pending'}
            </Button>
            <Button
              variant={statusFilter === 'completed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('completed')}
            >
              {language === 'de' ? 'Abgeschlossen' : 'Completed'}
            </Button>
          </div>
        </div>

        {/* Cases List */}
        {filteredCases.length === 0 ? (
          <Card className="border-2 border-dashed">
            <CardContent className="p-12 text-center">
              <Smartphone className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">
                {language === 'de' ? 'Keine Recovery-Fälle' : 'No Recovery Cases'}
              </h3>
              <p className="text-gray-500 mb-4">
                {language === 'de'
                  ? 'Erstellen Sie einen neuen Recovery-Link, um zu beginnen'
                  : 'Create a new recovery link to get started'}
              </p>
              <Button onClick={() => setShowCreateForm(true)}>
                <Plus className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Ersten Link erstellen' : 'Create First Link'}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredCases.map((recoveryCase) => (
              <Card key={recoveryCase.case_id} className="border-2 hover:border-blue-300 transition-all">
                <CardContent className="p-6">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    {/* Case Info */}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-3 flex-wrap">
                        <div className={`p-2 rounded-lg ${recoveryCase.device_type === 'ios' ? 'bg-gray-100' : 'bg-green-100'}`}>
                          {recoveryCase.device_type === 'ios' ? (
                            <Apple className="w-5 h-5 text-gray-700" />
                          ) : (
                            <Bot className="w-5 h-5 text-green-700" />
                          )}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{recoveryCase.client_number}</p>
                          <p className="text-xs text-gray-500 font-mono">{recoveryCase.case_id}</p>
                        </div>
                        <StatusBadge status={recoveryCase.status} />
                      </div>

                      {/* Recovery Link */}
                      <div className="flex items-center gap-2 bg-gray-50 p-2 rounded-lg">
                        <code className="text-sm text-blue-600 flex-1 truncate">
                          https://safechild.mom/recover/{recoveryCase.recovery_code}
                        </code>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyLink(`https://safechild.mom/recover/${recoveryCase.recovery_code}`)}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => window.open(`https://safechild.mom/recover/${recoveryCase.recovery_code}`, '_blank')}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      </div>

                      {/* Progress */}
                      {(recoveryCase.status === 'extracting' || recoveryCase.status === 'processing') && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">{recoveryCase.current_step || 'Processing...'}</span>
                            <span className="font-medium">{recoveryCase.progress_percent || 0}%</span>
                          </div>
                          <Progress value={recoveryCase.progress_percent || 0} className="h-2" />
                        </div>
                      )}

                      {/* Dates */}
                      <div className="flex gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {language === 'de' ? 'Erstellt' : 'Created'}: {new Date(recoveryCase.created_at).toLocaleString()}
                        </span>
                        {recoveryCase.expires_at && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {language === 'de' ? 'Läuft ab' : 'Expires'}: {new Date(recoveryCase.expires_at).toLocaleDateString()}
                          </span>
                        )}
                        {recoveryCase.completed_at && (
                          <span className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="w-3 h-3" />
                            {language === 'de' ? 'Abgeschlossen' : 'Completed'}: {new Date(recoveryCase.completed_at).toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      {recoveryCase.status === 'completed' && (
                        <Button
                          onClick={() => downloadResults(recoveryCase.case_id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          {language === 'de' ? 'Download' : 'Download'}
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => deleteCase(recoveryCase.case_id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-12 grid md:grid-cols-2 gap-6">
          <Card className="border-2 border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-900">
                <Shield className="w-5 h-5" />
                {language === 'de' ? 'Wie es funktioniert' : 'How It Works'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-blue-800">
              <p>1. {language === 'de' ? 'Recovery-Link erstellen und an Mandanten senden' : 'Create recovery link and send to client'}</p>
              <p>2. {language === 'de' ? 'Mandant öffnet Link auf Computer oder Telefon' : 'Client opens link on computer or phone'}</p>
              <p>3. {language === 'de' ? 'Daten werden automatisch extrahiert und hochgeladen' : 'Data is automatically extracted and uploaded'}</p>
              <p>4. {language === 'de' ? 'Nach Abschluss hier herunterladen' : 'Download results here when complete'}</p>
            </CardContent>
          </Card>

          <Card className="border-2 border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-purple-900">
                <FileText className="w-5 h-5" />
                {language === 'de' ? 'Zwei Szenarien' : 'Two Scenarios'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-purple-800">
              <div>
                <p className="font-semibold">{language === 'de' ? 'Mit Computer (WebUSB):' : 'With Computer (WebUSB):'}</p>
                <p className="text-purple-600">{language === 'de' ? 'Mandant verbindet Telefon per USB mit Computer' : 'Client connects phone to computer via USB'}</p>
              </div>
              <div>
                <p className="font-semibold">{language === 'de' ? 'Ohne Computer (Mobil):' : 'Without Computer (Mobile):'}</p>
                <p className="text-purple-600">{language === 'de' ? 'Mandant installiert App direkt auf Telefon' : 'Client installs app directly on phone'}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminPhoneRecovery;
