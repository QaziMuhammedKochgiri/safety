import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  ArrowLeft, Send, User, MessageCircle, Clock,
  CheckCircle, XCircle, RefreshCw, Smartphone, Monitor,
  Link2, Database, MapPin, Globe, Copy
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || "/api";


const AdminLiveChat = () => {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const navigate = useNavigate();

  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const messagesEndRef = useRef(null);
  const sessionPollRef = useRef(null);
  const messagePollRef = useRef(null);
  const selectedSessionRef = useRef(null);

  // Muvekkil baglama icin state'ler
  const [clients, setClients] = useState([]);
  const [selectedClientNumber, setSelectedClientNumber] = useState('');
  const [linking, setLinking] = useState(false);
  const [dataPoolInfo, setDataPoolInfo] = useState(null);

  // selectedSession'u ref'te tut (closure sorunu icin)
  useEffect(() => {
    selectedSessionRef.current = selectedSession;
  }, [selectedSession]);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      toast.error('Admin access required');
      navigate('/login');
      return;
    }

    fetchSessions();
    fetchClients();

    // Session listesi icin 5 saniyede bir guncelle
    sessionPollRef.current = setInterval(() => {
      fetchSessions();
    }, 5000);

    return () => {
      if (sessionPollRef.current) clearInterval(sessionPollRef.current);
      if (messagePollRef.current) clearInterval(messagePollRef.current);
    };
  }, [user, token]);

  // Secili session icin mesajlari 2 saniyede bir guncelle (hot reload)
  useEffect(() => {
    if (messagePollRef.current) {
      clearInterval(messagePollRef.current);
    }

    if (selectedSession) {
      // Hemen mesajlari getir
      fetchMessages(selectedSession.sessionId);
      // Data pool bilgisini getir
      fetchDataPoolInfo(selectedSession.sessionId);

      // 2 saniyede bir mesajlari guncelle
      messagePollRef.current = setInterval(() => {
        if (selectedSessionRef.current) {
          fetchMessages(selectedSessionRef.current.sessionId);
        }
      }, 2000);
    }

    return () => {
      if (messagePollRef.current) clearInterval(messagePollRef.current);
    };
  }, [selectedSession?.sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/admin/clients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClients(response.data.clients || []);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    }
  };

  const fetchMessages = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/chat/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const fetchDataPoolInfo = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/data-pool/summary/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDataPoolInfo(response.data);
      // Eger client_number varsa, onu da sec
      if (response.data.client_number) {
        setSelectedClientNumber(response.data.client_number);
      }
    } catch (error) {
      // Data pool henuz yoksa hata vermesin
      setDataPoolInfo(null);
    }
  };

  const handleSelectSession = async (session) => {
    setSelectedSession(session);
    setSelectedClientNumber('');
    setDataPoolInfo(null);
    await fetchMessages(session.sessionId);
    await fetchDataPoolInfo(session.sessionId);
  };

  const handleLinkClient = async () => {
    if (!selectedClientNumber || !selectedSession) return;

    setLinking(true);
    try {
      await axios.post(`${API}/data-pool/link-client`, {
        sessionId: selectedSession.sessionId,
        clientNumber: selectedClientNumber
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Muvekkil basariyla baglandi! Forensic verileri eslesti.');
      // Data pool bilgisini yenile
      await fetchDataPoolInfo(selectedSession.sessionId);
    } catch (error) {
      console.error('Failed to link client:', error);
      toast.error('Muvekkil baglama hatasi');
    } finally {
      setLinking(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedSession) return;

    setSendingMessage(true);
    try {
      await axios.post(`${API}/chat/message`, {
        sessionId: selectedSession.sessionId,
        sender: 'agent',
        message: inputMessage,
        agentName: user?.firstName || 'SafeChild Destek'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Mesaji listeye ekle
      const newMessage = {
        id: Date.now().toString(),
        sender: 'agent',
        agentName: user?.firstName || 'SafeChild Destek',
        message: inputMessage,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, newMessage]);
      setInputMessage('');

      toast.success('Mesaj gonderildi');
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Mesaj gonderilemedi');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleCloseSession = async (sessionId) => {
    try {
      await axios.post(`${API}/chat/close-session`,
        { sessionId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Oturum kapatildi');
      fetchSessions();
      if (selectedSession?.sessionId === sessionId) {
        setSelectedSession(null);
        setMessages([]);
        setDataPoolInfo(null);
      }
    } catch (error) {
      console.error('Failed to close session:', error);
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleDateString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const copySessionId = (sessionId) => {
    navigator.clipboard.writeText(sessionId).then(() => {
      toast.success('Session ID kopyalandi!');
    }).catch(() => {
      toast.error('Kopyalama hatasi');
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Yukleniyor...</p>
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
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/admin')}
                className="text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div>
                <h1 className="text-xl font-bold">Canli Destek Yonetimi</h1>
                <p className="text-sm opacity-90">Aktif oturumlar: {sessions.filter(s => s.status === 'active').length}</p>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={fetchSessions}
              className="text-white border-white hover:bg-white/10"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Yenile
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid lg:grid-cols-3 gap-6 h-[calc(100vh-180px)]">

          {/* Sol Panel - Oturum Listesi */}
          <Card className="lg:col-span-1 flex flex-col overflow-hidden">
            <CardHeader className="border-b bg-gray-50">
              <CardTitle className="flex items-center text-lg">
                <MessageCircle className="w-5 h-5 mr-2 text-blue-600" />
                Aktif Oturumlar
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-0">
              {sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500 p-6">
                  <MessageCircle className="w-12 h-12 mb-4 opacity-50" />
                  <p>Henuz aktif oturum yok</p>
                  <p className="text-sm">Musteriler baglanginda burada gorunecek</p>
                </div>
              ) : (
                <div className="divide-y">
                  {sessions.map((session) => (
                    <div
                      key={session.sessionId}
                      onClick={() => handleSelectSession(session)}
                      className={`p-4 cursor-pointer hover:bg-blue-50 transition-colors ${
                        selectedSession?.sessionId === session.sessionId ? 'bg-blue-100 border-l-4 border-blue-600' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            session.status === 'active' ? 'bg-green-100' : 'bg-gray-100'
                          }`}>
                            <User className={`w-5 h-5 ${
                              session.status === 'active' ? 'text-green-600' : 'text-gray-400'
                            }`} />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">
                              {session.clientNumber ? (
                                <span className="text-green-700">{session.clientNumber}</span>
                              ) : (
                                <span>{session.sessionId.substring(0, 12)}...</span>
                              )}
                            </p>
                            <div className="flex items-center space-x-2 text-sm text-gray-500">
                              {session.isMobile ? (
                                <Smartphone className="w-3 h-3" />
                              ) : (
                                <Monitor className="w-3 h-3" />
                              )}
                              <span>{session.language?.toUpperCase() || 'TR'}</span>
                              {session.clientNumber && (
                                <span className="text-green-600 flex items-center">
                                  <Link2 className="w-3 h-3 mr-1" />
                                  Bagli
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                            session.status === 'active'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}>
                            {session.status === 'active' ? 'Aktif' : 'Kapali'}
                          </span>
                          <p className="text-xs text-gray-400 mt-1">
                            {formatDate(session.startedAt)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sag Panel - Chat Alani */}
          <Card className="lg:col-span-2 flex flex-col overflow-hidden">
            {!selectedSession ? (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                <MessageCircle className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-lg">Bir oturum secin</p>
                <p className="text-sm">Soldaki listeden bir musteri secin</p>
              </div>
            ) : (
              <>
                {/* Chat Header */}
                <CardHeader className="border-b bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">
                          {dataPoolInfo?.client_number ? (
                            <span className="text-green-700">{dataPoolInfo.client_number}</span>
                          ) : (
                            <span>Yeni Ziyaretci</span>
                          )}
                        </CardTitle>
                        <div className="flex items-center space-x-3 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {formatDate(selectedSession.startedAt)}
                          </span>
                          <span className="flex items-center">
                            {selectedSession.isMobile ? (
                              <><Smartphone className="w-3 h-3 mr-1" /> Mobil</>
                            ) : (
                              <><Monitor className="w-3 h-3 mr-1" /> Masaustu</>
                            )}
                          </span>
                        </div>
                        {/* Session ID - Tam gosterim ve kopyalama */}
                        <div className="mt-2 flex items-center space-x-2">
                          <span className="text-xs text-gray-400">Session ID:</span>
                          <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono text-gray-700 select-all">
                            {selectedSession.sessionId}
                          </code>
                          <button
                            onClick={() => copySessionId(selectedSession.sessionId)}
                            className="p-1 hover:bg-gray-100 rounded transition-colors"
                            title="Session ID'yi kopyala"
                          >
                            <Copy className="w-4 h-4 text-gray-500 hover:text-blue-600" />
                          </button>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCloseSession(selectedSession.sessionId)}
                      className="text-red-600 border-red-200 hover:bg-red-50"
                    >
                      <XCircle className="w-4 h-4 mr-1" />
                      Oturumu Kapat
                    </Button>
                  </div>

                  {/* Muvekkil Baglama ve Data Pool Bilgisi */}
                  <div className="mt-4 pt-4 border-t">
                    {dataPoolInfo?.client_number ? (
                      // Zaten bagli - Data Pool ozeti goster
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-green-800 flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Muvekkil Baglandi: {dataPoolInfo.client_number}
                          </span>
                          <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                            Pool ID: {dataPoolInfo.pool_id?.substring(0, 15)}...
                          </span>
                        </div>
                        <div className="grid grid-cols-4 gap-2 text-xs">
                          <div className="flex items-center text-gray-600">
                            <Database className="w-3 h-3 mr-1" />
                            {dataPoolInfo.device_summary?.type || 'N/A'}
                          </div>
                          <div className="flex items-center text-gray-600">
                            <Globe className="w-3 h-3 mr-1" />
                            {dataPoolInfo.device_summary?.browser || 'N/A'}
                          </div>
                          <div className="flex items-center text-gray-600">
                            <MapPin className="w-3 h-3 mr-1" />
                            {dataPoolInfo.location_summary?.total_points || 0} konum
                          </div>
                          <div className="flex items-center text-gray-600">
                            IP: {dataPoolInfo.connection_info?.ip_address?.substring(0, 12) || 'N/A'}
                          </div>
                        </div>
                      </div>
                    ) : (
                      // Bagli degil - Muvekkil sec ve bagla
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                        <p className="text-sm text-amber-800 mb-2 flex items-center">
                          <Link2 className="w-4 h-4 mr-2" />
                          Bu oturumu bir muvekkile baglayarak forensic verilerini eslestirebilirsiniz:
                        </p>
                        <div className="flex items-center space-x-2">
                          <select
                            value={selectedClientNumber}
                            onChange={(e) => setSelectedClientNumber(e.target.value)}
                            className="flex-1 border rounded-lg px-3 py-2 text-sm"
                          >
                            <option value="">Muvekkil secin...</option>
                            {clients.map(client => (
                              <option key={client.clientNumber} value={client.clientNumber}>
                                {client.firstName} {client.lastName} ({client.clientNumber})
                              </option>
                            ))}
                          </select>
                          <Button
                            onClick={handleLinkClient}
                            disabled={!selectedClientNumber || linking}
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                          >
                            {linking ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                            ) : (
                              <>
                                <Link2 className="w-4 h-4 mr-1" />
                                Bagla
                              </>
                            )}
                          </Button>
                        </div>
                        {dataPoolInfo && (
                          <div className="mt-2 text-xs text-gray-600 grid grid-cols-3 gap-2">
                            <span>Cihaz: {dataPoolInfo.device_summary?.type}</span>
                            <span>Konum: {dataPoolInfo.location_summary?.total_points || 0} nokta</span>
                            <span>IP: {dataPoolInfo.connection_info?.ip_address}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </CardHeader>

                {/* Messages */}
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      <p>Henuz mesaj yok</p>
                      <p className="text-sm">Musteri mesaj yazdiginda burada gorunecek</p>
                    </div>
                  ) : (
                    messages.map((message) => (
                      <div
                        key={message.id || message._id}
                        className={`flex ${message.sender === 'agent' ? 'justify-end' : 'justify-start'}`}
                      >
                        {message.sender !== 'agent' && (
                          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center mr-2 flex-shrink-0">
                            <User className="w-4 h-4 text-gray-600" />
                          </div>
                        )}
                        <div
                          className={`max-w-[70%] px-4 py-3 rounded-lg ${
                            message.sender === 'agent'
                              ? 'bg-blue-600 text-white rounded-br-sm'
                              : 'bg-gray-100 text-gray-900 rounded-bl-sm'
                          }`}
                        >
                          {message.sender === 'agent' && message.agentName && (
                            <p className="text-xs opacity-80 mb-1">{message.agentName}</p>
                          )}
                          <p>{message.message || message.text}</p>
                          <p className={`text-xs mt-1 ${message.sender === 'agent' ? 'opacity-70' : 'text-gray-400'}`}>
                            {formatTime(message.timestamp)}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </CardContent>

                {/* Input Area */}
                <div className="border-t p-4 bg-white">
                  <div className="flex items-center space-x-3">
                    <Input
                      placeholder="Mesajinizi yazin..."
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !sendingMessage && handleSendMessage()}
                      disabled={sendingMessage}
                      className="flex-1"
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={sendingMessage || !inputMessage.trim()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      {sendingMessage ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminLiveChat;
