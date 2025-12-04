import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Search,
  MessageSquare,
  User,
  Calendar,
  Send,
  Loader2,
  Inbox,
  Clock,
  CheckCheck,
  Monitor,
  Smartphone
} from 'lucide-react';
import axios from 'axios';

const API_URL = '/api';

const AdminMessages = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [filteredSessions, setFilteredSessions] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, active: 0, closed: 0 });

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = sessions.filter(s =>
        s.sessionId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.language?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredSessions(filtered);
    } else {
      setFilteredSessions(sessions);
    }
  }, [searchTerm, sessions]);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const sessionList = response.data.sessions || [];
      setSessions(sessionList);
      setFilteredSessions(sessionList);

      // Calculate stats
      const active = sessionList.filter(s => s.status === 'active').length;
      setStats({
        total: sessionList.length,
        active,
        closed: sessionList.length - active
      });
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to load chat sessions');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (sessionId) => {
    setMessagesLoading(true);
    try {
      const response = await axios.get(`${API_URL}/chat/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data.messages || []);
    } catch (error) {
      toast.error('Failed to load messages');
    } finally {
      setMessagesLoading(false);
    }
  };

  const handleSelectSession = (session) => {
    setSelectedSession(session);
    fetchMessages(session.sessionId);
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return language === 'de' ? 'Gestern' : 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('de-DE', { weekday: 'short' });
    }
    return date.toLocaleDateString('de-DE');
  };

  const getLanguageLabel = (lang) => {
    const labels = { de: 'Deutsch', en: 'English', tr: 'Turkce' };
    return labels[lang] || lang;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => navigate('/admin')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {language === 'de' ? 'Zuruck' : 'Back'}
            </Button>
            <div>
              <h1 className="text-2xl font-bold">
                {language === 'de' ? 'Chat Nachrichten' : 'Chat Messages'}
              </h1>
              <p className="text-gray-500">
                {language === 'de' ? 'Live Chat Verlauf' : 'Live Chat History'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4 text-center">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-xs text-gray-500">
                {language === 'de' ? 'Gesamt Sessions' : 'Total Sessions'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Clock className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-2xl font-bold">{stats.active}</p>
              <p className="text-xs text-gray-500">
                {language === 'de' ? 'Aktiv' : 'Active'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <CheckCheck className="w-8 h-8 mx-auto mb-2 text-gray-600" />
              <p className="text-2xl font-bold">{stats.closed}</p>
              <p className="text-xs text-gray-500">
                {language === 'de' ? 'Geschlossen' : 'Closed'}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Sessions List */}
          <div className="md:col-span-1">
            <Card className="h-[600px] flex flex-col">
              <CardHeader className="pb-3">
                <div className="relative">
                  <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder={language === 'de' ? 'Suchen...' : 'Search...'}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-0">
                {loading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                  </div>
                ) : filteredSessions.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">
                      {language === 'de' ? 'Keine Sessions' : 'No sessions'}
                    </p>
                  </div>
                ) : (
                  <div className="divide-y">
                    {filteredSessions.map((session) => (
                      <div
                        key={session.sessionId}
                        className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                          selectedSession?.sessionId === session.sessionId ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => handleSelectSession(session)}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center space-x-2">
                            {session.isMobile ? (
                              <Smartphone className="w-4 h-4 text-gray-400" />
                            ) : (
                              <Monitor className="w-4 h-4 text-gray-400" />
                            )}
                            <span className="font-medium text-sm truncate max-w-[120px]">
                              {session.sessionId?.substring(0, 8)}...
                            </span>
                          </div>
                          <span className="text-xs text-gray-400">
                            {formatTime(session.startedAt)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">
                            {getLanguageLabel(session.language)}
                          </span>
                          <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                            {session.status === 'active' ? 'Active' : 'Closed'}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Messages View */}
          <div className="md:col-span-2">
            <Card className="h-[600px] flex flex-col">
              {selectedSession ? (
                <>
                  <CardHeader className="border-b pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                          {selectedSession.isMobile ? (
                            <Smartphone className="w-5 h-5 text-blue-600" />
                          ) : (
                            <Monitor className="w-5 h-5 text-blue-600" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium">
                            Session: {selectedSession.sessionId?.substring(0, 12)}...
                          </p>
                          <p className="text-xs text-gray-500">
                            {getLanguageLabel(selectedSession.language)} - {formatTime(selectedSession.startedAt)}
                          </p>
                        </div>
                      </div>
                      <Badge variant={selectedSession.status === 'active' ? 'default' : 'secondary'}>
                        {selectedSession.status === 'active' ? 'Active' : 'Closed'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto p-4 space-y-3">
                    {messagesLoading ? (
                      <div className="flex justify-center py-12">
                        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                      </div>
                    ) : messages.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                        <p className="text-sm">
                          {language === 'de' ? 'Keine Nachrichten' : 'No messages'}
                        </p>
                      </div>
                    ) : (
                      messages.map((msg, index) => (
                        <div
                          key={msg.id || index}
                          className={`flex ${msg.sender === 'agent' || msg.sender === 'bot' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[70%] p-3 rounded-lg ${
                              msg.sender === 'agent' || msg.sender === 'bot'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            <p className="text-sm">{msg.message}</p>
                            <div className={`flex items-center justify-end mt-1 space-x-1 ${
                              msg.sender === 'agent' || msg.sender === 'bot' ? 'text-blue-200' : 'text-gray-400'
                            }`}>
                              <span className="text-xs">
                                {msg.timestamp && new Date(msg.timestamp).toLocaleTimeString('de-DE', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                              {(msg.sender === 'agent' || msg.sender === 'bot') && <CheckCheck className="w-3 h-3" />}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </CardContent>
                </>
              ) : (
                <CardContent className="flex-1 flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>
                      {language === 'de'
                        ? 'Wahlen Sie eine Session aus'
                        : 'Select a session'}
                    </p>
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminMessages;
