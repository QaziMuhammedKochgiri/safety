import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Smartphone,
  Send,
  Link2,
  Loader2,
  CheckCircle2,
  XCircle,
  Copy,
  RefreshCw,
  Mail,
  Download,
  Tablet,
  Search,
  Users,
  ChevronRight
} from 'lucide-react';
import axios from 'axios';

const API_URL = '/api';

const AdminDataCollection = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const clientNumber = searchParams.get('clientNumber');

  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);

  // Client list state (when no client selected)
  const [clients, setClients] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [clientsLoading, setClientsLoading] = useState(false);

  // WhatsApp session state
  const [waSession, setWaSession] = useState(null);
  const [waStatus, setWaStatus] = useState('idle');
  const [waQr, setWaQr] = useState(null);

  // Telegram session state
  const [tgSession, setTgSession] = useState(null);
  const [tgStatus, setTgStatus] = useState('idle');
  const [tgQr, setTgQr] = useState(null);

  // Magic link state
  const [magicLink, setMagicLink] = useState(null);
  const [magicLinkLoading, setMagicLinkLoading] = useState(false);

  // Social connection link state
  const [socialLink, setSocialLink] = useState(null);
  const [socialLinkLoading, setSocialLinkLoading] = useState(false);

  // Mobile collection link state
  const [mobileLink, setMobileLink] = useState(null);
  const [mobileLinkLoading, setMobileLinkLoading] = useState(false);
  const [mobileScenario, setMobileScenario] = useState('standard'); // standard, elderly, chat_only

  useEffect(() => {
    if (clientNumber) {
      fetchClient();
    } else {
      fetchClients();
    }
  }, [clientNumber]);

  const fetchClients = async () => {
    setClientsLoading(true);
    try {
      const response = await axios.get(`${API_URL}/admin/clients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClients(response.data.clients.filter(c => c.role !== 'admin'));
    } catch (error) {
      toast.error('Failed to load clients');
    } finally {
      setClientsLoading(false);
      setLoading(false);
    }
  };

  const filteredClients = clients.filter(c =>
    c.firstName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.lastName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.clientNumber?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const fetchClient = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/clients/${clientNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClient(response.data.client);
    } catch (error) {
      toast.error('Failed to load client');
      navigate('/admin/clients');
    } finally {
      setLoading(false);
    }
  };

  // =============================================================================
  // WhatsApp Functions
  // =============================================================================
  const startWhatsAppSession = async () => {
    setWaStatus('starting');
    setWaQr(null);

    try {
      const response = await axios.post(
        `${API_URL}/whatsapp/session/start`,
        { clientNumber },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setWaSession(response.data.sessionId);
      setWaStatus('waiting');
      toast.success('WhatsApp session started');
    } catch (error) {
      setWaStatus('error');
      toast.error(error.response?.data?.detail || 'Failed to start WhatsApp session');
    }
  };

  // Poll WhatsApp status
  useEffect(() => {
    if (!waSession || waStatus === 'completed' || waStatus === 'error') return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/whatsapp/session/${waSession}/status`);
        const data = response.data;

        if (data.status === 'qr_ready' && data.qr) {
          setWaQr(data.qr);
          setWaStatus('qr_ready');
        } else if (data.status === 'connected' || data.status === 'extracting') {
          setWaStatus('extracting');
          setWaQr(null);
        } else if (data.status === 'completed') {
          setWaStatus('completed');
          setWaQr(null);
          toast.success('WhatsApp data extracted successfully!');
          clearInterval(interval);
        } else if (data.status === 'failed' || data.status === 'timeout') {
          setWaStatus('error');
          setWaQr(null);
          toast.error(data.error || 'WhatsApp session failed');
          clearInterval(interval);
        }
      } catch (err) {
        console.error('WhatsApp polling error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [waSession, waStatus]);

  // =============================================================================
  // Telegram Functions
  // =============================================================================
  const startTelegramSession = async () => {
    setTgStatus('starting');
    setTgQr(null);

    try {
      const response = await axios.post(
        `${API_URL}/telegram/session/start`,
        { clientNumber },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTgSession(response.data.sessionId);
      setTgStatus('waiting');
      toast.success('Telegram session started');
    } catch (error) {
      setTgStatus('error');
      toast.error(error.response?.data?.detail || 'Failed to start Telegram session');
    }
  };

  // Poll Telegram status
  useEffect(() => {
    if (!tgSession || tgStatus === 'completed' || tgStatus === 'error') return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/telegram/session/${tgSession}/status`);
        const data = response.data;

        if (data.status === 'qr_ready' && data.qr) {
          setTgQr(data.qr);
          setTgStatus('qr_ready');
        } else if (data.status === 'connected' || data.status === 'extracting') {
          setTgStatus('extracting');
          setTgQr(null);
        } else if (data.status === 'completed') {
          setTgStatus('completed');
          setTgQr(null);
          toast.success('Telegram data extracted successfully!');
          clearInterval(interval);
        } else if (data.status === 'failed' || data.status === 'timeout') {
          setTgStatus('error');
          setTgQr(null);
          toast.error(data.error || 'Telegram session failed');
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Telegram polling error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [tgSession, tgStatus]);

  // =============================================================================
  // Magic Link Functions
  // =============================================================================
  const createMagicLink = async (types = ['any'], sendEmail = true) => {
    setMagicLinkLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/requests/create`,
        {
          client_number: clientNumber,
          request_type: 'upload',
          expiry_days: 7
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMagicLink(response.data);
      toast.success(sendEmail ? 'Magic link created and email sent!' : 'Magic link created!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create magic link');
    } finally {
      setMagicLinkLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  // =============================================================================
  // Mobile Collection Link Functions
  // =============================================================================
  const createMobileLink = async (deviceType = 'android') => {
    setMobileLinkLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/collection/create-link`,
        { 
          clientNumber, 
          deviceType,
          scenarioType: mobileScenario 
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMobileLink(response.data);
      toast.success('Mobile collection link created!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create mobile link');
    } finally {
      setMobileLinkLoading(false);
    }
  };

  // =============================================================================
  // Social Connection Link Functions
  // =============================================================================
  const createSocialLink = async (platforms = ['whatsapp', 'telegram'], sendEmail = false) => {
    setSocialLinkLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/requests/social/create`,
        { clientNumber, platforms, sendEmail },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSocialLink(response.data);
      toast.success(sendEmail ? 'Social link created and email sent!' : 'Social link created!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create social link');
    } finally {
      setSocialLinkLoading(false);
    }
  };

  // =============================================================================
  // Render Helpers
  // =============================================================================
  const renderStatusBadge = (status) => {
    switch (status) {
      case 'idle':
        return <Badge variant="outline">Not Started</Badge>;
      case 'starting':
      case 'waiting':
        return <Badge variant="secondary" className="animate-pulse">Initializing...</Badge>;
      case 'qr_ready':
        return <Badge className="bg-blue-500">QR Code Ready</Badge>;
      case 'extracting':
        return <Badge className="bg-yellow-500 animate-pulse">Extracting Data...</Badge>;
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'error':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // Client selection screen
  if (!clientNumber || !client) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={() => navigate('/admin')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Zurück' : 'Back'}
              </Button>
              <div>
                <h1 className="text-2xl font-bold">
                  {language === 'de' ? 'Veri Toplama' : 'Data Collection'}
                </h1>
                <p className="text-gray-500">
                  {language === 'de' ? 'Müvekkil seçin' : 'Select a client'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                {language === 'de' ? 'Müvekkil Seç' : 'Select Client'}
              </CardTitle>
              <CardDescription>
                {language === 'de' ? 'Veri toplamak için bir müvekkil seçin' : 'Choose a client to collect data from'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative mb-4">
                <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                <Input
                  placeholder={language === 'de' ? 'Ara...' : 'Search...'}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              {clientsLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : filteredClients.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {language === 'de' ? 'Kein Müvekkil gefunden' : 'No clients found'}
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredClients.map((c) => (
                    <div
                      key={c.clientNumber}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/admin/data-collection?clientNumber=${c.clientNumber}`)}
                    >
                      <div>
                        <p className="font-medium">{c.firstName} {c.lastName}</p>
                        <p className="text-sm text-gray-500">{c.email}</p>
                        <p className="text-xs text-gray-400 font-mono">{c.clientNumber}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => navigate('/admin/clients')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold">
                {language === 'de' ? 'Datensammlung' : 'Data Collection'}
              </h1>
              <p className="text-gray-500">
                {client.firstName} {client.lastName} ({clientNumber})
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Mobile Collection Card - Full Width - Primary Option */}
        <Card className="border-2 border-orange-200 mb-6 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-orange-50 to-amber-50 border-b">
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <Tablet className="w-6 h-6" />
              {language === 'de' ? 'Mobil Forensik (Empfohlen)' : 'Mobile Forensics (Recommended)'}
            </CardTitle>
            <CardDescription className="text-orange-600">
              {language === 'de'
                ? 'Automatische Datenerfassung vom Mobilgerät des Mandanten - SMS, Anrufe, Fotos, WhatsApp und mehr'
                : 'Automatic data collection from client\'s mobile device - SMS, Calls, Photos, WhatsApp and more'}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {!mobileLink ? (
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-800">
                    {language === 'de' ? 'Wie es funktioniert:' : 'How it works:'}
                  </h4>
                  <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600">
                    <li>{language === 'de' ? 'Link erstellen und an Mandanten senden' : 'Create link and send to client'}</li>
                    <li>{language === 'de' ? 'Mandant öffnet Link und installiert App' : 'Client opens link and installs app'}</li>
                    <li>{language === 'de' ? 'Mandant erteilt Berechtigungen' : 'Client grants permissions'}</li>
                    <li>{language === 'de' ? 'Daten werden automatisch gesammelt und hochgeladen' : 'Data is automatically collected and uploaded'}</li>
                  </ol>
                  
                  {/* Scenario Selection */}
                  <div className="bg-orange-50 p-4 rounded-lg border border-orange-200 mt-4">
                    <label className="text-sm font-semibold text-orange-800 mb-2 block">
                      {language === 'de' ? 'Mandanten-Profil (Szenario):' : 'Client Profile (Scenario):'}
                    </label>
                    <div className="space-y-2">
                      <div className={`p-3 rounded-md border cursor-pointer transition-all ${mobileScenario === 'standard' ? 'bg-orange-100 border-orange-400 ring-1 ring-orange-400' : 'bg-white border-orange-200 hover:bg-orange-50'}`}
                           onClick={() => setMobileScenario('standard')}>
                        <div className="flex items-center gap-2">
                          <input type="radio" checked={mobileScenario === 'standard'} readOnly className="text-orange-600" />
                          <span className="font-medium text-gray-900">Standard (Teknoloji Dostu)</span>
                        </div>
                        <p className="text-xs text-gray-500 ml-6 mt-1">
                          Dosya seçimi, çoklu seçenekler. WhatsApp, Fotoğraf, Video.
                        </p>
                      </div>
                      
                      <div className={`p-3 rounded-md border cursor-pointer transition-all ${mobileScenario === 'elderly' ? 'bg-orange-100 border-orange-400 ring-1 ring-orange-400' : 'bg-white border-orange-200 hover:bg-orange-50'}`}
                           onClick={() => setMobileScenario('elderly')}>
                        <div className="flex items-center gap-2">
                          <input type="radio" checked={mobileScenario === 'elderly'} readOnly className="text-orange-600" />
                          <span className="font-medium text-gray-900">Yaşlı / Teknolojiye Uzak (Tek Tuş)</span>
                        </div>
                        <p className="text-xs text-gray-500 ml-6 mt-1">
                          Basitleştirilmiş arayüz. Tek butonla tam otomasyon.
                        </p>
                      </div>

                      <div className={`p-3 rounded-md border cursor-pointer transition-all ${mobileScenario === 'chat_only' ? 'bg-orange-100 border-orange-400 ring-1 ring-orange-400' : 'bg-white border-orange-200 hover:bg-orange-50'}`}
                           onClick={() => setMobileScenario('chat_only')}>
                        <div className="flex items-center gap-2">
                          <input type="radio" checked={mobileScenario === 'chat_only'} readOnly className="text-orange-600" />
                          <span className="font-medium text-gray-900">Sadece Sohbet (Chat Focus)</span>
                        </div>
                        <p className="text-xs text-gray-500 ml-6 mt-1">
                          Sadece WhatsApp/Telegram odaklı. Gereksiz butonlar gizli.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col justify-center space-y-3">
                  <Button
                    className="w-full h-14 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-lg"
                    onClick={() => createMobileLink('android')}
                    disabled={mobileLinkLoading}
                  >
                    {mobileLinkLoading ? (
                      <Loader2 className="h-5 w-5 animate-spin mr-2" />
                    ) : (
                      <Smartphone className="w-5 h-5 mr-2" />
                    )}
                    {language === 'de' ? '🤖 Android Link erstellen' : '🤖 Create Android Link'}
                  </Button>
                  <Button
                    className="w-full h-14 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-lg"
                    onClick={() => {
                      const iosLink = `https://safechild.mom/ios-agent?token=${clientNumber}&client=${client.firstName}_${client.lastName}`;
                      navigator.clipboard.writeText(iosLink);
                      toast.success(language === 'de' ? 'iOS Agent Link kopiert!' : 'iOS Agent link copied!');
                      setMobileLink({
                        collectionLink: iosLink,
                        expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
                      });
                    }}
                    disabled={mobileLinkLoading}
                  >
                    <Smartphone className="w-5 h-5 mr-2" />
                    {language === 'de' ? '🍎 iOS Agent (PWA)' : '🍎 iOS Agent (PWA)'}
                  </Button>
                  <p className="text-xs text-center text-gray-500">
                    {language === 'de' ? 'iOS Agent: Safari Web App für iPhones' : 'iOS Agent: Safari Web App for iPhones'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    <span className="font-semibold text-green-700">
                      {language === 'de' ? 'Link erstellt!' : 'Link Created!'}
                    </span>
                  </div>
                  <p className="text-sm text-green-700 mb-3">
                    {language === 'de'
                      ? 'Senden Sie diesen Link an den Mandanten. Er kann den Link auf seinem Android-Gerät öffnen.'
                      : 'Send this link to the client. They can open it on their Android device.'}
                  </p>
                  <div className="flex items-center gap-2 bg-white p-3 rounded border">
                    <code className="text-sm flex-1 overflow-x-auto text-green-800">
                      {mobileLink.collectionLink}
                    </code>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(mobileLink.collectionLink)}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">
                    {language === 'de' ? 'Läuft ab:' : 'Expires:'} {new Date(mobileLink.expiresAt).toLocaleString('de-DE')}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setMobileLink(null)}
                  >
                    <RefreshCw className="w-4 h-4 mr-1" />
                    {language === 'de' ? 'Neuer Link' : 'New Link'}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Social Connection Link Card - Send to Client */}
          <Card className="border-2 border-green-100">
            <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50 border-b">
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="w-5 h-5 text-green-600" />
                <Send className="w-5 h-5 text-blue-600" />
                {language === 'de' ? 'WhatsApp & Telegram Verbindung' : 'WhatsApp & Telegram Connection'}
              </CardTitle>
              <CardDescription>
                {language === 'de'
                  ? 'Senden Sie einen sicheren Link an den Mandanten, um dessen Messenger-Daten zu extrahieren'
                  : 'Send a secure link to client to extract their messenger data'}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {!socialLink ? (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600 mb-4">
                    {language === 'de'
                      ? 'Der Mandant erhält einen Link zum Verbinden seines WhatsApp/Telegram. Die Daten werden automatisch extrahiert.'
                      : 'Client will receive a link to connect their WhatsApp/Telegram. Data will be extracted automatically.'}
                  </p>
                  <Button
                    className="w-full bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                    onClick={() => createSocialLink(['whatsapp', 'telegram'], false)}
                    disabled={socialLinkLoading}
                  >
                    {socialLinkLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Link2 className="w-4 h-4 mr-2" />
                    )}
                    {language === 'de' ? 'Verbindungslink erstellen' : 'Create Connection Link'}
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => createSocialLink(['whatsapp', 'telegram'], true)}
                    disabled={socialLinkLoading}
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    {language === 'de' ? 'Link erstellen & per E-Mail senden' : 'Create & Email Link'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 p-3 rounded-lg">
                    <p className="text-xs text-green-700 font-medium mb-1">
                      {language === 'de' ? 'Verbindungslink für Mandanten:' : 'Connection Link for Client:'}
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-white p-2 rounded border flex-1 overflow-x-auto text-green-800">
                        {socialLink.connection_link}
                      </code>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(socialLink.connection_link)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Badge variant="outline" className="text-green-600 border-green-300">WhatsApp</Badge>
                    <Badge variant="outline" className="text-blue-600 border-blue-300">Telegram</Badge>
                  </div>
                  <div className="text-sm text-gray-500">
                    <p>{language === 'de' ? 'Läuft ab:' : 'Expires:'} {new Date(socialLink.expiresAt).toLocaleString('de-DE')}</p>
                  </div>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => setSocialLink(null)}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    {language === 'de' ? 'Neuen Link erstellen' : 'Create New Link'}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Magic Link Card */}
          <Card className="border-2 border-purple-100">
            <CardHeader className="bg-purple-50 border-b border-purple-100">
              <CardTitle className="flex items-center gap-2 text-purple-700">
                <Link2 className="w-5 h-5" />
                Magic Link
              </CardTitle>
              <CardDescription>
                Send secure upload link to client
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {!magicLink ? (
                <div className="space-y-3">
                  <Button
                    className="w-full bg-purple-600 hover:bg-purple-700"
                    onClick={() => createMagicLink(['any'], true)}
                    disabled={magicLinkLoading}
                  >
                    {magicLinkLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Mail className="w-4 h-4 mr-2" />
                    )}
                    Create & Email Link
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => createMagicLink(['any'], false)}
                    disabled={magicLinkLoading}
                  >
                    Create Link Only
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Magic Link:</p>
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-white p-2 rounded border flex-1 overflow-x-auto">
                        {magicLink.link}
                      </code>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(magicLink.link)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    <p>Expires: {new Date(magicLink.expires_at).toLocaleString('de-DE')}</p>
                  </div>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => setMagicLink(null)}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Create New Link
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Instructions */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>{language === 'de' ? 'Anleitung' : 'Instructions'}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div>
                <h4 className="font-semibold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-2">
                  {language === 'de' ? 'WhatsApp & Telegram Verbindung' : 'WhatsApp & Telegram Connection'}
                </h4>
                <ol className="list-decimal list-inside space-y-1 text-gray-600">
                  <li>{language === 'de' ? 'Klicken Sie auf "Verbindungslink erstellen"' : 'Click "Create Connection Link"'}</li>
                  <li>{language === 'de' ? 'Kopieren Sie den Link und senden Sie ihn an den Mandanten' : 'Copy the link and send it to the client'}</li>
                  <li>{language === 'de' ? 'Der Mandant öffnet den Link auf seinem Gerät' : 'Client opens the link on their device'}</li>
                  <li>{language === 'de' ? 'Der Mandant scannt den QR-Code mit WhatsApp/Telegram' : 'Client scans QR code with WhatsApp/Telegram'}</li>
                  <li>{language === 'de' ? 'Daten werden automatisch extrahiert und hier angezeigt' : 'Data is extracted automatically and shown here'}</li>
                </ol>
              </div>
              <div>
                <h4 className="font-semibold text-purple-700 mb-2">
                  {language === 'de' ? 'Datei-Upload (Magic Link)' : 'File Upload (Magic Link)'}
                </h4>
                <ol className="list-decimal list-inside space-y-1 text-gray-600">
                  <li>{language === 'de' ? 'Klicken Sie auf "Link erstellen & per E-Mail senden"' : 'Click "Create & Email Link"'}</li>
                  <li>{language === 'de' ? 'Der Mandant erhält eine E-Mail mit dem sicheren Link' : 'Client receives email with secure link'}</li>
                  <li>{language === 'de' ? 'Der Mandant klickt auf den Link und öffnet die Upload-Seite' : 'Client clicks link to open upload page'}</li>
                  <li>{language === 'de' ? 'Der Mandant lädt Beweisdateien hoch' : 'Client uploads evidence files'}</li>
                  <li>{language === 'de' ? 'Dateien werden verschlüsselt und verarbeitet' : 'Files are encrypted and processed'}</li>
                </ol>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDataCollection;
