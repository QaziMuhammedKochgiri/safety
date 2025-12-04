import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Plus,
  FileSearch,
  AlertTriangle,
  CheckCircle,
  XCircle,
  HelpCircle,
  Clock,
  Trash2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  User,
  Calendar,
  Shield,
  FileText,
  Download
} from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || '';

// Kategori seçenekleri
const STATEMENT_CATEGORIES = [
  { value: 'communication', label: 'İletişim', labelDe: 'Kommunikation', icon: '💬' },
  { value: 'custody', label: 'Velayet/Görüşme', labelDe: 'Sorgerecht', icon: '👨‍👩‍👧' },
  { value: 'violence', label: 'Şiddet/Tehdit', labelDe: 'Gewalt/Drohung', icon: '⚠️' },
  { value: 'financial', label: 'Finansal', labelDe: 'Finanziell', icon: '💰' },
  { value: 'other', label: 'Diğer', labelDe: 'Sonstiges', icon: '📋' }
];

// Durum badge'leri
const STATUS_BADGES = {
  verified: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Doğrulandı' },
  contradicted: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Çelişiyor' },
  partially_verified: { color: 'bg-yellow-100 text-yellow-800', icon: HelpCircle, label: 'Kısmen Doğrulandı' },
  insufficient_data: { color: 'bg-gray-100 text-gray-800', icon: HelpCircle, label: 'Yetersiz Veri' },
  pending: { color: 'bg-blue-100 text-blue-800', icon: Clock, label: 'Bekliyor' },
  analyzing: { color: 'bg-purple-100 text-purple-800', icon: RefreshCw, label: 'Analiz Ediliyor' },
  completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Tamamlandı' },
  failed: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Başarısız' }
};

const AdminVerification = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { language } = useLanguage();
  const { token } = useAuth();

  const [verifications, setVerifications] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewForm, setShowNewForm] = useState(false);
  const [selectedVerification, setSelectedVerification] = useState(null);
  const [expandedStatements, setExpandedStatements] = useState({});

  // Yeni doğrulama formu
  const [newVerification, setNewVerification] = useState({
    client_number: searchParams.get('clientNumber') || '',
    session_id: searchParams.get('sessionId') || '',
    case_id: '',
    statements: [{ category: 'communication', statement: '', involves_person: '' }],
    notes: ''
  });

  // Session'a ait data pool bilgisi
  const [sessionPoolInfo, setSessionPoolInfo] = useState(null);
  const [loadingPool, setLoadingPool] = useState(false);

  useEffect(() => {
    fetchVerifications();
    fetchClients();
  }, []);

  const fetchVerifications = async () => {
    try {
      const response = await fetch(`${API_URL}/api/verification/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setVerifications(data.verifications || []);
      }
    } catch (error) {
      console.error('Error fetching verifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/clients`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setClients(data.clients || []);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  // Session ID girildiğinde data pool bilgisini getir
  const fetchSessionPoolInfo = async (sessionId) => {
    if (!sessionId || sessionId.length < 5) {
      setSessionPoolInfo(null);
      return;
    }

    setLoadingPool(true);
    try {
      const response = await fetch(`${API_URL}/api/data-pool/summary/${sessionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSessionPoolInfo(data);

        // Eğer pool'da client_number varsa otomatik seç
        if (data.client_number && !newVerification.client_number) {
          setNewVerification(prev => ({ ...prev, client_number: data.client_number }));
        }
      } else {
        setSessionPoolInfo(null);
      }
    } catch (error) {
      console.error('Error fetching session pool:', error);
      setSessionPoolInfo(null);
    } finally {
      setLoadingPool(false);
    }
  };

  const handleCreateVerification = async () => {
    if (!newVerification.client_number) {
      toast.error('Lütfen bir müvekkil seçin');
      return;
    }

    if (newVerification.statements.every(s => !s.statement.trim())) {
      toast.error('En az bir beyan girin');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/verification/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newVerification,
          statements: newVerification.statements.filter(s => s.statement.trim())
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Doğrulama talebi oluşturuldu, analiz başlatıldı');
        setShowNewForm(false);
        setNewVerification({
          client_number: '',
          session_id: '',
          case_id: '',
          statements: [{ category: 'communication', statement: '', involves_person: '' }],
          notes: ''
        });
        setSessionPoolInfo(null);
        fetchVerifications();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Hata oluştu');
      }
    } catch (error) {
      toast.error('Bağlantı hatası');
    }
  };

  const handleDeleteVerification = async (verificationId) => {
    if (!window.confirm('Bu doğrulama talebini silmek istediğinize emin misiniz?')) return;

    try {
      const response = await fetch(`${API_URL}/api/verification/${verificationId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Doğrulama talebi silindi');
        setSelectedVerification(null);
        fetchVerifications();
      }
    } catch (error) {
      toast.error('Silme hatası');
    }
  };

  const handleReanalyze = async (verificationId) => {
    try {
      const response = await fetch(`${API_URL}/api/verification/${verificationId}/reanalyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Tekrar analiz başlatıldı');
        fetchVerifications();
      }
    } catch (error) {
      toast.error('Hata oluştu');
    }
  };

  const addStatement = () => {
    setNewVerification(prev => ({
      ...prev,
      statements: [...prev.statements, { category: 'communication', statement: '', involves_person: '' }]
    }));
  };

  const removeStatement = (index) => {
    setNewVerification(prev => ({
      ...prev,
      statements: prev.statements.filter((_, i) => i !== index)
    }));
  };

  const updateStatement = (index, field, value) => {
    setNewVerification(prev => ({
      ...prev,
      statements: prev.statements.map((s, i) => i === index ? { ...s, [field]: value } : s)
    }));
  };

  const toggleStatementExpand = (id) => {
    setExpandedStatements(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-green-500';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate('/admin')}>
                <ArrowLeft className="w-5 h-5 mr-2" />
                {language === 'de' ? 'Zurück' : 'Geri'}
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <Shield className="w-6 h-6 text-blue-600" />
                  {language === 'de' ? 'Aussagenüberprüfung' : 'Beyan Doğrulama'}
                </h1>
                <p className="text-sm text-gray-500">
                  {language === 'de'
                    ? 'Mandantenaussagen mit digitalen Beweisen vergleichen'
                    : 'Müvekkil beyanlarını dijital kanıtlarla karşılaştırın'}
                </p>
              </div>
            </div>
            <Button onClick={() => setShowNewForm(true)} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              {language === 'de' ? 'Neue Überprüfung' : 'Yeni Doğrulama'}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Yeni Doğrulama Formu */}
        {showNewForm && (
          <Card className="mb-6 border-2 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSearch className="w-5 h-5" />
                {language === 'de' ? 'Neue Aussagenüberprüfung' : 'Yeni Beyan Doğrulama'}
              </CardTitle>
              <CardDescription>
                {language === 'de'
                  ? 'Geben Sie die Aussagen des Mandanten ein, um sie mit digitalen Beweisen zu vergleichen'
                  : 'Müvekkilin beyanlarını girin, dijital kanıtlarla karşılaştırılacak'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Session ID / Token */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'de' ? 'Sitzungs-ID / Token (optional)' : 'Oturum ID / Token (opsiyonel)'}
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newVerification.session_id}
                    onChange={(e) => {
                      const val = e.target.value;
                      setNewVerification(prev => ({ ...prev, session_id: val }));
                      // Debounce ile pool bilgisini getir
                      clearTimeout(window.sessionPoolTimeout);
                      window.sessionPoolTimeout = setTimeout(() => fetchSessionPoolInfo(val), 500);
                    }}
                    placeholder={language === 'de' ? 'z.B. live_17647737108_abc123' : 'Örn: live_17647737108_abc123'}
                    className="flex-1 border rounded-lg px-3 py-2"
                  />
                  {loadingPool && (
                    <div className="flex items-center px-3">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'de'
                    ? 'Geben Sie die Sitzungs-ID ein, um Browser-Forensik-Daten zu verknüpfen'
                    : 'Tarayıcı forensik verilerini bağlamak için oturum ID\'sini girin (AdminLiveChat\'ten kopyalayın)'}
                </p>

                {/* Session Pool Bilgisi */}
                {sessionPoolInfo && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="text-sm font-medium text-blue-800 mb-2">
                      {language === 'de' ? 'Verknüpfte Daten gefunden' : 'Bağlı Veri Havuzu Bulundu'}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500">{language === 'de' ? 'Pool-ID:' : 'Havuz ID:'}</span>{' '}
                        <span className="font-mono">{sessionPoolInfo.pool_id}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">{language === 'de' ? 'Gerät:' : 'Cihaz:'}</span>{' '}
                        {sessionPoolInfo.device_summary?.type} ({sessionPoolInfo.device_summary?.browser})
                      </div>
                      <div>
                        <span className="text-gray-500">{language === 'de' ? 'Standorte:' : 'Konum:'}</span>{' '}
                        {sessionPoolInfo.location_summary?.total_points || 0} nokta
                      </div>
                      <div>
                        <span className="text-gray-500">IP:</span>{' '}
                        {sessionPoolInfo.connection_info?.ip_address}
                      </div>
                    </div>
                    {sessionPoolInfo.client_number && (
                      <div className="mt-2 text-xs text-green-700">
                        Bu oturum <strong>{sessionPoolInfo.client_number}</strong> müvekkiline bağlı
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Müvekkil Seçimi */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'de' ? 'Mandant' : 'Müvekkil'} *
                </label>
                <select
                  value={newVerification.client_number}
                  onChange={(e) => setNewVerification(prev => ({ ...prev, client_number: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">{language === 'de' ? 'Mandant auswählen...' : 'Müvekkil seçin...'}</option>
                  {clients.map(client => (
                    <option key={client.clientNumber} value={client.clientNumber}>
                      {client.firstName} {client.lastName} ({client.clientNumber})
                    </option>
                  ))}
                </select>
              </div>

              {/* Beyanlar */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'de' ? 'Aussagen' : 'Beyanlar'} *
                </label>

                {newVerification.statements.map((stmt, index) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg mb-3 border">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium text-sm">#{index + 1}</span>
                      <select
                        value={stmt.category}
                        onChange={(e) => updateStatement(index, 'category', e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      >
                        {STATEMENT_CATEGORIES.map(cat => (
                          <option key={cat.value} value={cat.value}>
                            {cat.icon} {language === 'de' ? cat.labelDe : cat.label}
                          </option>
                        ))}
                      </select>
                      {newVerification.statements.length > 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeStatement(index)}
                          className="ml-auto text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>

                    <textarea
                      value={stmt.statement}
                      onChange={(e) => updateStatement(index, 'statement', e.target.value)}
                      placeholder={language === 'de'
                        ? 'Aussage des Mandanten eingeben...'
                        : 'Müvekkilin beyanını girin... (Örn: "Eşim son 3 ayda benimle hiç iletişim kurmadı")'}
                      className="w-full border rounded-lg px-3 py-2 min-h-[80px] text-sm"
                    />

                    <input
                      type="text"
                      value={stmt.involves_person}
                      onChange={(e) => updateStatement(index, 'involves_person', e.target.value)}
                      placeholder={language === 'de' ? 'Betroffene Person (optional)' : 'İlgili kişi (opsiyonel, örn: eş, çocuk)'}
                      className="w-full border rounded-lg px-3 py-2 mt-2 text-sm"
                    />
                  </div>
                ))}

                <Button variant="outline" onClick={addStatement} className="w-full">
                  <Plus className="w-4 h-4 mr-2" />
                  {language === 'de' ? 'Weitere Aussage hinzufügen' : 'Başka Beyan Ekle'}
                </Button>
              </div>

              {/* Notlar */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'de' ? 'Notizen' : 'Notlar'}
                </label>
                <textarea
                  value={newVerification.notes}
                  onChange={(e) => setNewVerification(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder={language === 'de' ? 'Zusätzliche Notizen...' : 'Ek notlar...'}
                  className="w-full border rounded-lg px-3 py-2 min-h-[60px]"
                />
              </div>

              {/* Butonlar */}
              <div className="flex gap-2">
                <Button onClick={handleCreateVerification} className="bg-blue-600 hover:bg-blue-700">
                  <FileSearch className="w-4 h-4 mr-2" />
                  {language === 'de' ? 'Analyse starten' : 'Analizi Başlat'}
                </Button>
                <Button variant="outline" onClick={() => setShowNewForm(false)}>
                  {language === 'de' ? 'Abbrechen' : 'İptal'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Doğrulama Listesi */}
        <div className="grid gap-4">
          {verifications.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Shield className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {language === 'de' ? 'Keine Überprüfungen' : 'Henüz Doğrulama Yok'}
                </h3>
                <p className="text-gray-500 mb-4">
                  {language === 'de'
                    ? 'Erstellen Sie Ihre erste Aussagenüberprüfung'
                    : 'İlk beyan doğrulama talebinizi oluşturun'}
                </p>
                <Button onClick={() => setShowNewForm(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  {language === 'de' ? 'Neue Überprüfung' : 'Yeni Doğrulama'}
                </Button>
              </CardContent>
            </Card>
          ) : (
            verifications.map(verification => (
              <Card
                key={verification.verification_id}
                className={`cursor-pointer hover:border-blue-300 transition-colors ${
                  selectedVerification?.verification_id === verification.verification_id ? 'border-blue-500' : ''
                }`}
                onClick={() => setSelectedVerification(
                  selectedVerification?.verification_id === verification.verification_id ? null : verification
                )}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-3 rounded-full ${getRiskColor(verification.summary?.risk_level)}`} />
                      <div>
                        <div className="font-medium flex items-center gap-2">
                          <User className="w-4 h-4" />
                          {verification.client_name || verification.client_number}
                        </div>
                        <div className="text-sm text-gray-500 flex items-center gap-2">
                          <Calendar className="w-3 h-3" />
                          {new Date(verification.created_at).toLocaleDateString('tr-TR')}
                          <span className="mx-1">•</span>
                          {verification.statements?.length || 0} beyan
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {STATUS_BADGES[verification.status] && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_BADGES[verification.status].color}`}>
                          {STATUS_BADGES[verification.status].label}
                        </span>
                      )}
                      {selectedVerification?.verification_id === verification.verification_id
                        ? <ChevronUp className="w-5 h-5 text-gray-400" />
                        : <ChevronDown className="w-5 h-5 text-gray-400" />
                      }
                    </div>
                  </div>

                  {/* Detay Görünümü */}
                  {selectedVerification?.verification_id === verification.verification_id && (
                    <div className="mt-4 pt-4 border-t" onClick={(e) => e.stopPropagation()}>
                      {/* Özet */}
                      {verification.summary && (
                        <div className={`p-4 rounded-lg mb-4 ${
                          verification.summary.risk_level === 'high' ? 'bg-red-50 border border-red-200' :
                          verification.summary.risk_level === 'medium' ? 'bg-yellow-50 border border-yellow-200' :
                          verification.summary.risk_level === 'low' ? 'bg-blue-50 border border-blue-200' :
                          'bg-green-50 border border-green-200'
                        }`}>
                          <div className="font-medium text-lg mb-2">{verification.summary.risk_message}</div>
                          <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                            <div className="text-center">
                              <div className="font-bold text-green-600">{verification.summary.verified}</div>
                              <div className="text-gray-500">Doğrulandı</div>
                            </div>
                            <div className="text-center">
                              <div className="font-bold text-red-600">{verification.summary.contradicted}</div>
                              <div className="text-gray-500">Çelişiyor</div>
                            </div>
                            <div className="text-center">
                              <div className="font-bold text-yellow-600">{verification.summary.partially_verified}</div>
                              <div className="text-gray-500">Kısmi</div>
                            </div>
                            <div className="text-center">
                              <div className="font-bold text-gray-600">{verification.summary.insufficient_data}</div>
                              <div className="text-gray-500">Yetersiz</div>
                            </div>
                          </div>
                          <div className="text-sm whitespace-pre-line bg-white p-3 rounded border">
                            {verification.summary.recommendation}
                          </div>
                        </div>
                      )}

                      {/* Beyan Sonuçları */}
                      <div className="space-y-3">
                        <h4 className="font-medium">Beyan Sonuçları:</h4>
                        {verification.results?.map((result, idx) => (
                          <div
                            key={result.statement_id || idx}
                            className="bg-gray-50 p-3 rounded-lg border"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <div className="text-sm font-medium text-gray-600 mb-1">
                                  {STATEMENT_CATEGORIES.find(c => c.value === result.category)?.icon} {' '}
                                  {STATEMENT_CATEGORIES.find(c => c.value === result.category)?.label}
                                </div>
                                <div className="text-sm">"{result.statement_text}"</div>
                              </div>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_BADGES[result.status]?.color || 'bg-gray-100'}`}>
                                {STATUS_BADGES[result.status]?.label || result.status}
                              </span>
                            </div>

                            <div className="text-sm text-gray-600 mb-2">
                              <strong>Güven: </strong>{result.confidence}%
                            </div>

                            <div className="text-sm bg-white p-2 rounded border">
                              {result.evidence_summary}
                            </div>

                            {result.evidence_details?.length > 0 && (
                              <div className="mt-2">
                                <button
                                  onClick={() => toggleStatementExpand(result.statement_id)}
                                  className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                                >
                                  {expandedStatements[result.statement_id] ? 'Kanıtları Gizle' : `${result.evidence_count} Kanıt Göster`}
                                  {expandedStatements[result.statement_id] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                </button>

                                {expandedStatements[result.statement_id] && (
                                  <div className="mt-2 space-y-1">
                                    {result.evidence_details.map((ev, evIdx) => (
                                      <div key={evIdx} className="text-xs bg-gray-100 p-2 rounded flex items-center gap-2">
                                        {ev.supports_statement === true && <CheckCircle className="w-3 h-3 text-green-600" />}
                                        {ev.supports_statement === false && <XCircle className="w-3 h-3 text-red-600" />}
                                        {ev.supports_statement === null && <HelpCircle className="w-3 h-3 text-gray-400" />}
                                        <span className="font-medium">{ev.type}:</span>
                                        <span>{ev.summary}</span>
                                        {ev.date && <span className="text-gray-400">({ev.date})</span>}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}

                            <div className={`mt-2 text-sm font-medium ${
                              result.status === 'verified' ? 'text-green-600' :
                              result.status === 'contradicted' ? 'text-red-600' :
                              'text-gray-600'
                            }`}>
                              {result.recommendation}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Aksiyon Butonları */}
                      <div className="flex gap-2 mt-4 pt-4 border-t">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleReanalyze(verification.verification_id)}
                        >
                          <RefreshCw className="w-4 h-4 mr-1" />
                          Tekrar Analiz
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:bg-red-50"
                          onClick={() => handleDeleteVerification(verification.verification_id)}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Sil
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminVerification;
