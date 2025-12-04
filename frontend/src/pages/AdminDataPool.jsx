import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Database, Search, User, Smartphone, MapPin, Globe, Clock,
  FileText, Image, MessageCircle, Phone, Mail, Folder,
  ChevronDown, ChevronRight, ExternalLink, Download, RefreshCw,
  Monitor, Cpu, Wifi, Battery, Eye, Shield, AlertTriangle,
  CheckCircle, XCircle, Calendar, Hash, Activity, Server
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';

const AdminDataPool = () => {
  const navigate = useNavigate();
  const [clientNumber, setClientNumber] = useState('');
  const [clientData, setClientData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState(null);

  // Data states
  const [browserData, setBrowserData] = useState(null);
  const [whatsappData, setWhatsappData] = useState(null);
  const [telegramData, setTelegramData] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [forensicReports, setForensicReports] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);

  const fetchAllData = async () => {
    if (!clientNumber.trim()) {
      toast.error('Lütfen müvekkil numarası girin');
      return;
    }

    setLoading(true);
    setActiveSection(null);

    try {
      // Fetch client info
      const clientRes = await api.get(`/clients/${clientNumber}`);
      setClientData(clientRes.data);

      // Fetch all data in parallel
      const [browserRes, docsRes, forensicsRes, chatRes] = await Promise.allSettled([
        api.get(`/data-pool/by-client/${clientNumber}`),
        api.get(`/documents/client/${clientNumber}`),
        api.get(`/forensics/client/${clientNumber}`),
        api.get(`/chat/history/${clientNumber}`)
      ]);

      // Browser/Device Data
      if (browserRes.status === 'fulfilled') {
        setBrowserData(browserRes.value.data);
      }

      // Documents
      if (docsRes.status === 'fulfilled') {
        setDocuments(docsRes.value.data.documents || docsRes.value.data || []);
      }

      // Forensic Reports (WhatsApp, Telegram, etc.)
      if (forensicsRes.status === 'fulfilled') {
        const reports = forensicsRes.value.data.analyses || forensicsRes.value.data || [];
        setForensicReports(reports);

        // Separate WhatsApp and Telegram
        setWhatsappData(reports.filter(r => r.source === 'whatsapp' || r.data_type === 'whatsapp'));
        setTelegramData(reports.filter(r => r.source === 'telegram' || r.data_type === 'telegram'));
      }

      // Chat History
      if (chatRes.status === 'fulfilled') {
        setChatHistory(chatRes.value.data.messages || chatRes.value.data || []);
      }

      toast.success('Veriler yüklendi');
    } catch (error) {
      console.error('Error fetching data:', error);
      if (error.response?.status === 404) {
        toast.error('Müvekkil bulunamadı');
      } else {
        toast.error('Veriler yüklenirken hata oluştu');
      }
      setClientData(null);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section) => {
    setActiveSection(activeSection === section ? null : section);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('tr-TR');
  };

  const DataCard = ({ title, icon: Icon, count, color, section, children }) => {
    const isActive = activeSection === section;
    const hasData = count > 0;

    return (
      <div className={`bg-white rounded-xl shadow-sm border overflow-hidden transition-all ${isActive ? 'ring-2 ring-blue-500' : ''}`}>
        <button
          onClick={() => hasData && toggleSection(section)}
          disabled={!hasData}
          className={`w-full p-4 flex items-center justify-between ${hasData ? 'hover:bg-gray-50 cursor-pointer' : 'opacity-50 cursor-not-allowed'}`}
        >
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-xl ${color}`}>
              <Icon className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500">{count} kayıt</p>
            </div>
          </div>
          {hasData && (
            isActive ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {isActive && hasData && (
          <div className="border-t p-4 bg-gray-50">
            {children}
          </div>
        )}
      </div>
    );
  };

  // Render Browser/Device Data
  const renderBrowserData = () => {
    if (!browserData?.pools?.length) return <p className="text-gray-500">Veri bulunamadı</p>;

    return (
      <div className="space-y-4">
        {browserData.pools.map((pool, idx) => (
          <div key={idx} className="bg-white rounded-lg p-4 border space-y-4">
            {/* Session Info */}
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <p className="text-xs text-gray-500">Session ID</p>
                <code className="text-sm font-mono">{pool.session_id}</code>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">Oluşturulma</p>
                <p className="text-sm">{formatDate(pool.created_at)}</p>
              </div>
            </div>

            {/* Device Info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center space-x-2">
                <Smartphone className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Cihaz</p>
                  <p className="text-sm font-medium">{pool.device?.deviceType || '-'}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Monitor className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">İşletim Sistemi</p>
                  <p className="text-sm font-medium">{pool.device?.os} {pool.device?.osVersion}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Tarayıcı</p>
                  <p className="text-sm font-medium">{pool.device?.browser} {pool.device?.browserVersion}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Wifi className="w-4 h-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Bağlantı</p>
                  <p className="text-sm font-medium">{pool.device?.connection?.effectiveType || '-'}</p>
                </div>
              </div>
            </div>

            {/* Hardware */}
            <div className="grid grid-cols-3 gap-4 bg-gray-50 rounded-lg p-3">
              <div className="text-center">
                <Cpu className="w-5 h-5 text-blue-500 mx-auto mb-1" />
                <p className="text-xs text-gray-500">CPU Çekirdek</p>
                <p className="font-semibold">{pool.device?.hardwareConcurrency || '-'}</p>
              </div>
              <div className="text-center">
                <Server className="w-5 h-5 text-green-500 mx-auto mb-1" />
                <p className="text-xs text-gray-500">RAM</p>
                <p className="font-semibold">{pool.device?.deviceMemory ? `${pool.device.deviceMemory} GB` : '-'}</p>
              </div>
              <div className="text-center">
                <Monitor className="w-5 h-5 text-purple-500 mx-auto mb-1" />
                <p className="text-xs text-gray-500">Ekran</p>
                <p className="font-semibold">{pool.fingerprint?.screenResolution || '-'}</p>
              </div>
            </div>

            {/* IP & Location */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-yellow-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Globe className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-800">IP Bilgisi</span>
                </div>
                <p className="font-mono text-lg">{pool.ip_address}</p>
                <p className="text-xs text-yellow-600 mt-1">Timezone: {pool.fingerprint?.timezone}</p>
              </div>

              <div className="bg-green-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <MapPin className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium text-green-800">Konum Verileri</span>
                </div>
                <p className="font-semibold text-lg">{pool.locations?.length || 0} nokta</p>
                {pool.locations?.[0] && (
                  <p className="text-xs text-green-600 mt-1">
                    Son: {pool.locations[pool.locations.length - 1]?.latitude?.toFixed(6)},
                    {pool.locations[pool.locations.length - 1]?.longitude?.toFixed(6)}
                  </p>
                )}
              </div>
            </div>

            {/* Permissions */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(pool.permissions || {}).map(([key, value]) => (
                <span
                  key={key}
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                    value ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {value ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                  {key}
                </span>
              ))}
            </div>

            {/* Locations Map Link */}
            {pool.locations?.length > 0 && (
              <a
                href={`https://www.google.com/maps?q=${pool.locations[0].latitude},${pool.locations[0].longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
              >
                <MapPin className="w-4 h-4 mr-1" />
                Haritada Görüntüle
                <ExternalLink className="w-3 h-3 ml-1" />
              </a>
            )}
          </div>
        ))}
      </div>
    );
  };

  // Render WhatsApp Data
  const renderWhatsappData = () => {
    if (!whatsappData?.length) return <p className="text-gray-500">WhatsApp verisi bulunamadı</p>;

    return (
      <div className="space-y-3">
        {whatsappData.map((report, idx) => (
          <div key={idx} className="bg-white rounded-lg p-4 border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <MessageCircle className="w-5 h-5 text-green-500" />
                <span className="font-medium">Case: {report.case_id}</span>
              </div>
              <span className={`px-2 py-1 rounded text-xs ${
                report.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {report.status}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Mesaj Sayısı</p>
                <p className="font-semibold">{report.statistics?.total_messages || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Medya</p>
                <p className="font-semibold">{report.statistics?.media_count || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Tarih</p>
                <p className="font-semibold">{formatDate(report.created_at)}</p>
              </div>
            </div>
            <button
              onClick={() => navigate(`/admin/forensics/${report.case_id}`)}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800 flex items-center"
            >
              Detayları Görüntüle <ExternalLink className="w-3 h-3 ml-1" />
            </button>
          </div>
        ))}
      </div>
    );
  };

  // Render Telegram Data
  const renderTelegramData = () => {
    if (!telegramData?.length) return <p className="text-gray-500">Telegram verisi bulunamadı</p>;

    return (
      <div className="space-y-3">
        {telegramData.map((report, idx) => (
          <div key={idx} className="bg-white rounded-lg p-4 border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <MessageCircle className="w-5 h-5 text-blue-500" />
                <span className="font-medium">Case: {report.case_id}</span>
              </div>
              <span className={`px-2 py-1 rounded text-xs ${
                report.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {report.status}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Mesaj Sayısı</p>
                <p className="font-semibold">{report.statistics?.total_messages || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Medya</p>
                <p className="font-semibold">{report.statistics?.media_count || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Tarih</p>
                <p className="font-semibold">{formatDate(report.created_at)}</p>
              </div>
            </div>
            <button
              onClick={() => navigate(`/admin/forensics/${report.case_id}`)}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800 flex items-center"
            >
              Detayları Görüntüle <ExternalLink className="w-3 h-3 ml-1" />
            </button>
          </div>
        ))}
      </div>
    );
  };

  // Render Documents
  const renderDocuments = () => {
    if (!documents?.length) return <p className="text-gray-500">Belge bulunamadı</p>;

    const images = documents.filter(d => d.fileType?.startsWith('image/') || d.category === 'photo');
    const pdfs = documents.filter(d => d.fileType === 'application/pdf' || d.category === 'document');
    const others = documents.filter(d => !images.includes(d) && !pdfs.includes(d));

    return (
      <div className="space-y-4">
        {/* Images */}
        {images.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
              <Image className="w-4 h-4 mr-2" /> Fotoğraflar ({images.length})
            </h4>
            <div className="grid grid-cols-4 gap-2">
              {images.slice(0, 8).map((img, idx) => (
                <div key={idx} className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    src={img.url || img.fileUrl}
                    alt={img.fileName}
                    className="w-full h-full object-cover"
                    onError={(e) => e.target.src = '/placeholder-image.png'}
                  />
                </div>
              ))}
            </div>
            {images.length > 8 && (
              <p className="text-sm text-gray-500 mt-2">+{images.length - 8} daha fazla</p>
            )}
          </div>
        )}

        {/* PDFs/Documents */}
        {pdfs.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
              <FileText className="w-4 h-4 mr-2" /> Belgeler ({pdfs.length})
            </h4>
            <div className="space-y-2">
              {pdfs.map((doc, idx) => (
                <div key={idx} className="flex items-center justify-between bg-white p-2 rounded border">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-red-500" />
                    <span className="text-sm truncate max-w-xs">{doc.fileName}</span>
                  </div>
                  <a
                    href={doc.url || doc.fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Other files */}
        {others.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
              <Folder className="w-4 h-4 mr-2" /> Diğer Dosyalar ({others.length})
            </h4>
            <div className="space-y-2">
              {others.map((doc, idx) => (
                <div key={idx} className="flex items-center justify-between bg-white p-2 rounded border">
                  <div className="flex items-center space-x-2">
                    <Folder className="w-4 h-4 text-gray-500" />
                    <span className="text-sm truncate max-w-xs">{doc.fileName}</span>
                  </div>
                  <a
                    href={doc.url || doc.fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render Chat History
  const renderChatHistory = () => {
    if (!chatHistory?.length) return <p className="text-gray-500">Sohbet geçmişi bulunamadı</p>;

    return (
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {chatHistory.map((msg, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-lg ${
              msg.sender === 'client'
                ? 'bg-blue-50 ml-8'
                : 'bg-gray-100 mr-8'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-600">
                {msg.sender === 'client' ? 'Müvekkil' : 'Avukat'}
              </span>
              <span className="text-xs text-gray-400">{formatDate(msg.timestamp)}</span>
            </div>
            <p className="text-sm">{msg.content || msg.message}</p>
          </div>
        ))}
      </div>
    );
  };

  // Render Forensic Reports
  const renderForensicReports = () => {
    const browserForensics = forensicReports.filter(r => r.source === 'browser_data_pool' || r.data_type === 'browser_forensics');

    if (!browserForensics?.length) return <p className="text-gray-500">Browser forensic verisi bulunamadı</p>;

    return (
      <div className="space-y-3">
        {browserForensics.map((report, idx) => (
          <div key={idx} className="bg-white rounded-lg p-4 border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Shield className="w-5 h-5 text-purple-500" />
                <span className="font-medium">Case: {report.case_id}</span>
              </div>
              <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-700">
                {report.data_type}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Konum Noktaları</p>
                <p className="font-semibold">{report.statistics?.location_points || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Sayfa Ziyareti</p>
                <p className="font-semibold">{report.statistics?.page_visits || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Etkileşim</p>
                <p className="font-semibold">{report.statistics?.interactions || 0}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-2">
          <Database className="w-8 h-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Data Pool</h1>
        </div>
        <p className="text-gray-600">Müvekkil verilerini merkezi olarak inceleyin</p>
      </div>

      {/* Search Box */}
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Müvekkil Numarası
            </label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={clientNumber}
                onChange={(e) => setClientNumber(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && fetchAllData()}
                placeholder="Örn: SC20251203110100362994"
                className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <button
            onClick={fetchAllData}
            disabled={loading}
            className="mt-7 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
          >
            {loading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            <span>Verileri İncele</span>
          </button>
        </div>
      </div>

      {/* Client Info */}
      {clientData && (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-lg p-6 mb-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <User className="w-8 h-8" />
              </div>
              <div>
                <h2 className="text-xl font-bold">{clientData.firstName} {clientData.lastName}</h2>
                <p className="text-blue-200">{clientData.clientNumber}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center space-x-2 text-blue-200">
                <Mail className="w-4 h-4" />
                <span>{clientData.email}</span>
              </div>
              <div className="flex items-center space-x-2 text-blue-200 mt-1">
                <Phone className="w-4 h-4" />
                <span>{clientData.phone}</span>
              </div>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-white/20 flex items-center space-x-6">
            <div>
              <p className="text-blue-200 text-xs">Kayıt Tarihi</p>
              <p className="font-medium">{formatDate(clientData.createdAt)}</p>
            </div>
            <div>
              <p className="text-blue-200 text-xs">Durum</p>
              <p className="font-medium capitalize">{clientData.status}</p>
            </div>
            <div>
              <p className="text-blue-200 text-xs">Ülke</p>
              <p className="font-medium">{clientData.country || '-'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Data Cards Grid */}
      {clientData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Browser/Device Data */}
          <DataCard
            title="Tarayıcı & Cihaz Verileri"
            icon={Smartphone}
            count={browserData?.pools?.length || 0}
            color="bg-gradient-to-br from-indigo-500 to-purple-600"
            section="browser"
          >
            {renderBrowserData()}
          </DataCard>

          {/* WhatsApp Data */}
          <DataCard
            title="WhatsApp Verileri"
            icon={MessageCircle}
            count={whatsappData?.length || 0}
            color="bg-gradient-to-br from-green-500 to-green-600"
            section="whatsapp"
          >
            {renderWhatsappData()}
          </DataCard>

          {/* Telegram Data */}
          <DataCard
            title="Telegram Verileri"
            icon={MessageCircle}
            count={telegramData?.length || 0}
            color="bg-gradient-to-br from-blue-400 to-blue-500"
            section="telegram"
          >
            {renderTelegramData()}
          </DataCard>

          {/* Documents */}
          <DataCard
            title="Belgeler & Dosyalar"
            icon={FileText}
            count={documents?.length || 0}
            color="bg-gradient-to-br from-orange-500 to-red-500"
            section="documents"
          >
            {renderDocuments()}
          </DataCard>

          {/* Chat History */}
          <DataCard
            title="Sohbet Geçmişi"
            icon={MessageCircle}
            count={chatHistory?.length || 0}
            color="bg-gradient-to-br from-pink-500 to-rose-500"
            section="chat"
          >
            {renderChatHistory()}
          </DataCard>

          {/* Forensic Reports */}
          <DataCard
            title="Forensic Raporları"
            icon={Shield}
            count={forensicReports?.length || 0}
            color="bg-gradient-to-br from-gray-600 to-gray-700"
            section="forensics"
          >
            {renderForensicReports()}
          </DataCard>
        </div>
      )}

      {/* Empty State */}
      {!clientData && !loading && (
        <div className="text-center py-16">
          <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">Veri Havuzu Boş</h3>
          <p className="text-gray-400">Müvekkil numarası girerek verileri görüntüleyin</p>
        </div>
      )}
    </div>
  );
};

export default AdminDataPool;
