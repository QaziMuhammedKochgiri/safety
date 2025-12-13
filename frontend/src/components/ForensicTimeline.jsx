import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { Slider } from './ui/slider';
import { toast } from 'sonner';
import {
  MessageSquare,
  Phone,
  Image as ImageIcon,
  Video,
  FileText,
  MapPin,
  Clock,
  User,
  Users,
  AlertTriangle,
  Search,
  Filter,
  Download,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Calendar,
  Eye,
  Shield,
  Trash2,
  RefreshCw,
  Loader2,
  Flag,
  Star
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Message type configurations
const MESSAGE_TYPES = {
  text: { icon: MessageSquare, color: '#3b82f6', label: 'Textnachricht' },
  image: { icon: ImageIcon, color: '#8b5cf6', label: 'Bild' },
  video: { icon: Video, color: '#ec4899', label: 'Video' },
  audio: { icon: Phone, color: '#f59e0b', label: 'Sprachnachricht' },
  document: { icon: FileText, color: '#6366f1', label: 'Dokument' },
  location: { icon: MapPin, color: '#22c55e', label: 'Standort' },
  contact: { icon: User, color: '#14b8a6', label: 'Kontakt' },
  deleted: { icon: Trash2, color: '#ef4444', label: 'Geloscht' },
  call: { icon: Phone, color: '#06b6d4', label: 'Anruf' },
  system: { icon: AlertTriangle, color: '#94a3b8', label: 'System' }
};

// Risk level configurations
const RISK_LEVELS = {
  none: { color: '#22c55e', label: 'Kein Risiko', bgColor: 'bg-green-50' },
  low: { color: '#84cc16', label: 'Niedriges Risiko', bgColor: 'bg-lime-50' },
  medium: { color: '#f59e0b', label: 'Mittleres Risiko', bgColor: 'bg-amber-50' },
  high: { color: '#f97316', label: 'Hohes Risiko', bgColor: 'bg-orange-50' },
  critical: { color: '#ef4444', label: 'Kritisches Risiko', bgColor: 'bg-red-50' }
};

// Platform configurations
const PLATFORMS = {
  whatsapp: { color: '#25d366', label: 'WhatsApp' },
  telegram: { color: '#0088cc', label: 'Telegram' },
  instagram: { color: '#e4405f', label: 'Instagram' },
  facebook: { color: '#1877f2', label: 'Facebook' },
  sms: { color: '#64748b', label: 'SMS' },
  signal: { color: '#3a76f0', label: 'Signal' },
  snapchat: { color: '#fffc00', label: 'Snapchat' },
  tiktok: { color: '#000000', label: 'TikTok' }
};

const ForensicTimeline = ({
  caseId,
  token,
  messages = [],
  contacts = [],
  onMessageSelect,
  onExport
}) => {
  const timelineContainerRef = useRef(null);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [viewMode, setViewMode] = useState('timeline'); // timeline, conversation, grid
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [filterRisk, setFilterRisk] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [zoom, setZoom] = useState(100);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showDeletedOnly, setShowDeletedOnly] = useState(false);
  const [flaggedMessages, setFlaggedMessages] = useState(new Set());

  // Auto-scroll during playback
  useEffect(() => {
    let interval;
    if (isPlaying && filteredMessages.length > 0) {
      interval = setInterval(() => {
        setCurrentIndex(prev => {
          if (prev >= filteredMessages.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Filter messages
  const filteredMessages = useMemo(() => {
    return messages.filter(msg => {
      // Platform filter
      if (filterPlatform !== 'all' && msg.platform !== filterPlatform) return false;

      // Risk filter
      if (filterRisk !== 'all' && msg.risk_level !== filterRisk) return false;

      // Type filter
      if (filterType !== 'all' && msg.message_type !== filterType) return false;

      // Deleted only filter
      if (showDeletedOnly && !msg.is_deleted) return false;

      // Search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchText = msg.content?.toLowerCase().includes(query);
        const matchSender = msg.sender_name?.toLowerCase().includes(query);
        const matchPhone = msg.sender_phone?.includes(query);
        if (!matchText && !matchSender && !matchPhone) return false;
      }

      // Date range filter
      if (dateRange.start && new Date(msg.timestamp) < new Date(dateRange.start)) return false;
      if (dateRange.end && new Date(msg.timestamp) > new Date(dateRange.end)) return false;

      return true;
    }).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  }, [messages, filterPlatform, filterRisk, filterType, searchQuery, dateRange, showDeletedOnly]);

  // Group messages by date
  const messagesByDate = useMemo(() => {
    const groups = {};
    filteredMessages.forEach(msg => {
      const date = new Date(msg.timestamp).toLocaleDateString('de-DE');
      if (!groups[date]) groups[date] = [];
      groups[date].push(msg);
    });
    return groups;
  }, [filteredMessages]);

  // Group messages by conversation
  const messagesByConversation = useMemo(() => {
    const groups = {};
    filteredMessages.forEach(msg => {
      const key = msg.conversation_id || msg.sender_phone || 'unknown';
      if (!groups[key]) {
        groups[key] = {
          contact: contacts.find(c => c.phone === msg.sender_phone) || { name: msg.sender_name || 'Unbekannt' },
          messages: []
        };
      }
      groups[key].messages.push(msg);
    });
    return groups;
  }, [filteredMessages, contacts]);

  // Statistics
  const stats = useMemo(() => {
    const riskCounts = { none: 0, low: 0, medium: 0, high: 0, critical: 0 };
    const typeCounts = {};
    const platformCounts = {};
    let deletedCount = 0;

    messages.forEach(msg => {
      // Risk counts
      if (msg.risk_level) {
        riskCounts[msg.risk_level] = (riskCounts[msg.risk_level] || 0) + 1;
      }

      // Type counts
      const type = msg.message_type || 'text';
      typeCounts[type] = (typeCounts[type] || 0) + 1;

      // Platform counts
      const platform = msg.platform || 'unknown';
      platformCounts[platform] = (platformCounts[platform] || 0) + 1;

      // Deleted count
      if (msg.is_deleted) deletedCount++;
    });

    return {
      total: messages.length,
      filtered: filteredMessages.length,
      deleted: deletedCount,
      riskCounts,
      typeCounts,
      platformCounts,
      highRisk: riskCounts.high + riskCounts.critical
    };
  }, [messages, filteredMessages]);

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleDateString('de-DE', {
      weekday: 'short',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Handle message click
  const handleMessageClick = (msg) => {
    setSelectedMessage(msg);
    if (onMessageSelect) onMessageSelect(msg);
  };

  // Toggle flag
  const toggleFlag = (msgId) => {
    setFlaggedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(msgId)) {
        newSet.delete(msgId);
      } else {
        newSet.add(msgId);
      }
      return newSet;
    });
  };

  // Export flagged messages
  const handleExportFlagged = () => {
    const flagged = filteredMessages.filter(m => flaggedMessages.has(m.id));
    if (flagged.length === 0) {
      toast.error('Keine Nachrichten markiert');
      return;
    }
    if (onExport) onExport(flagged);
    toast.success(`${flagged.length} Nachrichten exportiert`);
  };

  // Get message icon
  const getMessageIcon = (type) => {
    const config = MESSAGE_TYPES[type] || MESSAGE_TYPES.text;
    const IconComponent = config.icon;
    return <IconComponent className="w-4 h-4" style={{ color: config.color }} />;
  };

  // Get risk badge
  const getRiskBadge = (level) => {
    const config = RISK_LEVELS[level] || RISK_LEVELS.none;
    return (
      <Badge
        variant="outline"
        className="text-xs"
        style={{ borderColor: config.color, color: config.color }}
      >
        {config.label}
      </Badge>
    );
  };

  // Render message bubble
  const renderMessageBubble = (msg, index) => {
    const isOutgoing = msg.is_outgoing;
    const isDeleted = msg.is_deleted;
    const riskConfig = RISK_LEVELS[msg.risk_level] || RISK_LEVELS.none;
    const typeConfig = MESSAGE_TYPES[msg.message_type] || MESSAGE_TYPES.text;
    const isFlagged = flaggedMessages.has(msg.id);
    const isCurrentPlayback = index === currentIndex && isPlaying;

    return (
      <div
        key={msg.id || index}
        className={`flex ${isOutgoing ? 'justify-end' : 'justify-start'} mb-2 ${
          isCurrentPlayback ? 'ring-2 ring-blue-500 ring-offset-2 rounded-lg' : ''
        }`}
        onClick={() => handleMessageClick(msg)}
      >
        <div
          className={`max-w-[70%] rounded-lg p-3 cursor-pointer transition-all hover:shadow-md ${
            isDeleted ? 'bg-red-50 border border-red-200' :
            isOutgoing ? 'bg-blue-100' : riskConfig.bgColor || 'bg-gray-100'
          }`}
          style={{
            borderLeft: msg.risk_level && msg.risk_level !== 'none'
              ? `3px solid ${riskConfig.color}`
              : undefined
          }}
        >
          {/* Header */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-gray-600">
              {msg.sender_name || msg.sender_phone || 'Unbekannt'}
            </span>
            {PLATFORMS[msg.platform] && (
              <Badge variant="secondary" className="text-xs py-0">
                {PLATFORMS[msg.platform].label}
              </Badge>
            )}
            {isDeleted && (
              <Badge variant="destructive" className="text-xs py-0">
                <Trash2 className="w-3 h-3 mr-1" />
                Geloscht
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="h-5 w-5 p-0 ml-auto"
              onClick={(e) => { e.stopPropagation(); toggleFlag(msg.id); }}
            >
              <Flag className={`w-3 h-3 ${isFlagged ? 'fill-yellow-500 text-yellow-500' : 'text-gray-400'}`} />
            </Button>
          </div>

          {/* Content */}
          <div className="flex items-start gap-2">
            {getMessageIcon(msg.message_type)}
            <div className="flex-1">
              {msg.message_type === 'image' && msg.media_url && (
                <img
                  src={msg.media_url}
                  alt="Bild"
                  className="max-w-full rounded mb-2 max-h-48 object-cover"
                />
              )}
              <p className={`text-sm ${isDeleted ? 'italic text-gray-400' : ''}`}>
                {isDeleted && !msg.content ? '[Nachricht geloscht]' : msg.content}
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-400">
              {formatTime(msg.timestamp)}
            </span>
            {msg.risk_level && msg.risk_level !== 'none' && getRiskBadge(msg.risk_level)}
          </div>

          {/* Risk indicators */}
          {msg.risk_keywords && msg.risk_keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {msg.risk_keywords.map((keyword, i) => (
                <Badge key={i} variant="outline" className="text-xs bg-red-50 text-red-600">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Forensische Zeitachse
          </h2>
          <Badge variant="secondary">{stats.total} Nachrichten</Badge>
          {stats.highRisk > 0 && (
            <Badge variant="destructive">{stats.highRisk} Risiko</Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex border rounded-lg overflow-hidden">
            <Button
              variant={viewMode === 'timeline' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('timeline')}
            >
              <Clock className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'conversation' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('conversation')}
            >
              <Users className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
            >
              <ImageIcon className="w-4 h-4" />
            </Button>
          </div>

          <Button variant="outline" size="sm" onClick={handleExportFlagged}>
            <Download className="w-4 h-4 mr-1" />
            Export ({flaggedMessages.size})
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {/* Search */}
            <div className="col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Suchen..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Platform filter */}
            <Select value={filterPlatform} onValueChange={setFilterPlatform}>
              <SelectTrigger>
                <SelectValue placeholder="Plattform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Alle Plattformen</SelectItem>
                {Object.entries(PLATFORMS).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Risk filter */}
            <Select value={filterRisk} onValueChange={setFilterRisk}>
              <SelectTrigger>
                <SelectValue placeholder="Risiko" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Alle Risikostufen</SelectItem>
                {Object.entries(RISK_LEVELS).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Type filter */}
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="Typ" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Alle Typen</SelectItem>
                {Object.entries(MESSAGE_TYPES).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Deleted only toggle */}
            <Button
              variant={showDeletedOnly ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowDeletedOnly(!showDeletedOnly)}
              className="flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Nur geloscht ({stats.deleted})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Statistics Bar */}
      <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
        {Object.entries(RISK_LEVELS).map(([key, config]) => (
          <Card key={key} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setFilterRisk(key)}>
            <CardContent className="p-2 text-center">
              <div className="text-lg font-bold" style={{ color: config.color }}>
                {stats.riskCounts[key] || 0}
              </div>
              <div className="text-xs text-gray-500">{config.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Playback Controls */}
      <Card>
        <CardContent className="p-3">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentIndex(0)}
                disabled={filteredMessages.length === 0}
              >
                <SkipBack className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
                disabled={currentIndex === 0}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant={isPlaying ? 'default' : 'outline'}
                size="sm"
                onClick={() => setIsPlaying(!isPlaying)}
                disabled={filteredMessages.length === 0}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentIndex(Math.min(filteredMessages.length - 1, currentIndex + 1))}
                disabled={currentIndex >= filteredMessages.length - 1}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentIndex(filteredMessages.length - 1)}
                disabled={filteredMessages.length === 0}
              >
                <SkipForward className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex-1">
              <Slider
                value={[currentIndex]}
                max={Math.max(0, filteredMessages.length - 1)}
                step={1}
                onValueChange={(value) => setCurrentIndex(value[0])}
                className="cursor-pointer"
              />
            </div>

            <div className="text-sm text-gray-500 min-w-[80px] text-right">
              {currentIndex + 1} / {filteredMessages.length}
            </div>

            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setZoom(Math.max(50, zoom - 10))}>
                <ZoomOut className="w-4 h-4" />
              </Button>
              <span className="text-sm w-12 text-center">{zoom}%</span>
              <Button variant="outline" size="sm" onClick={() => setZoom(Math.min(200, zoom + 10))}>
                <ZoomIn className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Card>
        <CardContent className="p-4">
          <ScrollArea className="h-[500px]" ref={timelineContainerRef}>
            {filteredMessages.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-30" />
                <p className="text-lg">Keine Nachrichten gefunden</p>
                <p className="text-sm">Passen Sie die Filter an oder laden Sie neue Daten</p>
              </div>
            ) : viewMode === 'timeline' ? (
              // Timeline View
              <div className="space-y-6">
                {Object.entries(messagesByDate).map(([date, msgs]) => (
                  <div key={date}>
                    <div className="sticky top-0 bg-white z-10 py-2 mb-2 border-b">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-600">{date}</span>
                        <Badge variant="secondary" className="text-xs">
                          {msgs.length} Nachrichten
                        </Badge>
                      </div>
                    </div>
                    <div style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}>
                      {msgs.map((msg, idx) => renderMessageBubble(msg, filteredMessages.indexOf(msg)))}
                    </div>
                  </div>
                ))}
              </div>
            ) : viewMode === 'conversation' ? (
              // Conversation View
              <div className="space-y-6">
                {Object.entries(messagesByConversation).map(([convId, data]) => (
                  <div key={convId} className="border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-4 pb-2 border-b">
                      <User className="w-5 h-5 text-gray-400" />
                      <span className="font-medium">{data.contact.name}</span>
                      <Badge variant="secondary">{data.messages.length}</Badge>
                    </div>
                    <div style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}>
                      {data.messages.map((msg, idx) => renderMessageBubble(msg, filteredMessages.indexOf(msg)))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // Grid View (Media only)
              <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
                {filteredMessages
                  .filter(m => ['image', 'video'].includes(m.message_type))
                  .map((msg, idx) => (
                    <div
                      key={msg.id || idx}
                      className="aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:opacity-80 transition-opacity relative"
                      onClick={() => handleMessageClick(msg)}
                    >
                      {msg.media_url ? (
                        msg.message_type === 'video' ? (
                          <div className="w-full h-full flex items-center justify-center bg-gray-200">
                            <Video className="w-8 h-8 text-gray-400" />
                          </div>
                        ) : (
                          <img
                            src={msg.media_url}
                            alt="Media"
                            className="w-full h-full object-cover"
                          />
                        )
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <ImageIcon className="w-8 h-8 text-gray-400" />
                        </div>
                      )}
                      {msg.is_deleted && (
                        <div className="absolute top-1 right-1">
                          <Badge variant="destructive" className="text-xs">
                            <Trash2 className="w-3 h-3" />
                          </Badge>
                        </div>
                      )}
                      {msg.risk_level && msg.risk_level !== 'none' && (
                        <div className="absolute bottom-1 left-1">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: RISK_LEVELS[msg.risk_level].color }}
                          />
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Message Detail Dialog */}
      <Dialog open={!!selectedMessage} onOpenChange={() => setSelectedMessage(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nachrichtendetails</DialogTitle>
          </DialogHeader>
          {selectedMessage && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label className="text-gray-500">Absender</Label>
                  <p className="font-medium">{selectedMessage.sender_name || selectedMessage.sender_phone}</p>
                </div>
                <div>
                  <Label className="text-gray-500">Zeitpunkt</Label>
                  <p className="font-medium">{formatDate(selectedMessage.timestamp)} {formatTime(selectedMessage.timestamp)}</p>
                </div>
                <div>
                  <Label className="text-gray-500">Plattform</Label>
                  <p className="font-medium">{PLATFORMS[selectedMessage.platform]?.label || selectedMessage.platform}</p>
                </div>
                <div>
                  <Label className="text-gray-500">Typ</Label>
                  <p className="font-medium">{MESSAGE_TYPES[selectedMessage.message_type]?.label || selectedMessage.message_type}</p>
                </div>
              </div>

              <div>
                <Label className="text-gray-500">Inhalt</Label>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg">
                  {selectedMessage.media_url && selectedMessage.message_type === 'image' && (
                    <img src={selectedMessage.media_url} alt="Media" className="max-w-full rounded mb-2" />
                  )}
                  <p className="whitespace-pre-wrap">{selectedMessage.content || '[Kein Text]'}</p>
                </div>
              </div>

              {selectedMessage.risk_level && selectedMessage.risk_level !== 'none' && (
                <div className={`p-3 rounded-lg ${RISK_LEVELS[selectedMessage.risk_level].bgColor}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4" style={{ color: RISK_LEVELS[selectedMessage.risk_level].color }} />
                    <span className="font-medium">Risikobewertung</span>
                  </div>
                  {getRiskBadge(selectedMessage.risk_level)}
                  {selectedMessage.risk_keywords && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {selectedMessage.risk_keywords.map((kw, i) => (
                        <Badge key={i} variant="outline" className="text-xs">
                          {kw}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {selectedMessage.risk_explanation && (
                    <p className="text-sm text-gray-600 mt-2">{selectedMessage.risk_explanation}</p>
                  )}
                </div>
              )}

              {selectedMessage.is_deleted && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-center gap-2">
                    <Trash2 className="w-4 h-4 text-red-500" />
                    <span className="font-medium text-red-700">Geloschte Nachricht</span>
                  </div>
                  <p className="text-sm text-red-600 mt-1">
                    Diese Nachricht wurde vom Benutzer geloscht und durch forensische Analyse wiederhergestellt.
                  </p>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => toggleFlag(selectedMessage.id)}>
                  <Flag className={`w-4 h-4 mr-2 ${flaggedMessages.has(selectedMessage.id) ? 'fill-yellow-500 text-yellow-500' : ''}`} />
                  {flaggedMessages.has(selectedMessage.id) ? 'Markierung entfernen' : 'Markieren'}
                </Button>
                <Button onClick={() => setSelectedMessage(null)}>
                  Schliesen
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ForensicTimeline;
