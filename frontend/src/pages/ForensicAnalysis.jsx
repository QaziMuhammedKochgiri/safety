import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  Upload, FileCheck, Download, Clock, CheckCircle, XCircle, 
  Smartphone, MessageSquare, Phone, Shield, Trash2, RefreshCw 
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_API_URL || "/api";

const ForensicAnalysis = () => {
  const { user, token } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();
  
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState({});

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    loadMyCases();
    
    // Poll for processing cases every 10 seconds
    const interval = setInterval(() => {
      loadMyCases();
    }, 10000);
    
    return () => clearInterval(interval);
  }, [user, navigate]);

  const loadMyCases = async () => {
    try {
      const response = await axios.get(
        `${API}/forensics/my-cases`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCases(response.data.cases || []);
    } catch (error) {
      console.error('Error loading cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Check file size (max 500MB)
      const maxSize = 500 * 1024 * 1024; // 500MB
      if (selectedFile.size > maxSize) {
        toast.error(
          language === 'de' 
            ? 'Datei zu groß (max 500MB)' 
            : 'File too large (max 500MB)'
        );
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error(
        language === 'de' ? 'Bitte wählen Sie eine Datei' : 'Please select a file'
      );
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append('backup_file', file);

    try {
      const response = await axios.post(
        `${API}/forensics/analyze`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000 // 60 seconds
        }
      );

      toast.success(
        language === 'de' 
          ? 'Analyse gestartet! Überprüfen Sie den Status unten.' 
          : 'Analysis started! Check status below.',
        { description: response.data.message }
      );

      setFile(null);
      // Clear file input
      document.getElementById('file-input').value = '';
      
      // Reload cases immediately
      await loadMyCases();
      
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(
        language === 'de' 
          ? 'Fehler beim Hochladen' 
          : 'Upload error',
        { description: error.response?.data?.detail || error.message }
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (caseId, format = 'txt') => {
    try {
      toast.info(language === 'de' ? 'Download wird vorbereitet...' : 'Preparing download...');
      
      const response = await axios.get(
        `${API}/forensics/report/${caseId}?format=${format}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `SafeChild_Report_${caseId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(language === 'de' ? 'Download erfolgreich!' : 'Download successful!');
    } catch (error) {
      toast.error(
        language === 'de' ? 'Download fehlgeschlagen' : 'Download failed',
        { description: error.response?.data?.detail || error.message }
      );
    }
  };

  const handleDelete = async (caseId) => {
    if (!window.confirm(
      language === 'de' 
        ? 'Sind Sie sicher, dass Sie diesen Fall löschen möchten?' 
        : 'Are you sure you want to delete this case?'
    )) {
      return;
    }

    try {
      await axios.delete(
        `${API}/forensics/case/${caseId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(language === 'de' ? 'Fall gelöscht' : 'Case deleted');
      loadMyCases();
    } catch (error) {
      toast.error(
        language === 'de' ? 'Löschen fehlgeschlagen' : 'Delete failed',
        { description: error.response?.data?.detail || error.message }
      );
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusText = (status) => {
    const texts = {
      'processing': language === 'de' ? 'Verarbeitung...' : 'Processing...',
      'completed': language === 'de' ? 'Abgeschlossen' : 'Completed',
      'failed': language === 'de' ? 'Fehlgeschlagen' : 'Failed'
    };
    return texts[status] || status;
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString(language === 'de' ? 'de-DE' : 'en-US');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-12">
      <div className="container mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {language === 'de' ? 'Forensische Analyse' : 'Forensic Analysis'}
          </h1>
          <p className="text-xl text-gray-600">
            {language === 'de' 
              ? 'Professionelle Analyse von mobilen Geräten für Sorgerechtsfälle' 
              : 'Professional mobile device analysis for custody cases'}
          </p>
        </div>

        {/* Upload Section */}
        <Card className="mb-8 max-w-3xl mx-auto border-2 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="w-6 h-6 mr-2 text-blue-600" />
              {language === 'de' ? 'Neue Analyse starten' : 'Start New Analysis'}
            </CardTitle>
            <CardDescription>
              {language === 'de' 
                ? 'Laden Sie Backup-Dateien von mobilen Geräten hoch' 
                : 'Upload backup files from mobile devices'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert className="mb-6 border-blue-200 bg-blue-50">
              <Smartphone className="w-5 h-5 text-blue-600" />
              <AlertDescription className="text-blue-900 ml-2">
                <strong>{language === 'de' ? 'Unterstützte Formate:' : 'Supported formats:'}</strong>
                <br />
                • WhatsApp Database (.db)
                <br />
                • Telegram Database (.db)
                <br />
                • Android Backup (.ab, .tar, .tar.gz)
                <br />
                • Maximum Dateigröße: 500MB
              </AlertDescription>
            </Alert>

            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <input
                  id="file-input"
                  type="file"
                  onChange={handleFileChange}
                  accept=".ab,.tar,.gz,.tgz,.db,.zip"
                  className="hidden"
                />
                <label
                  htmlFor="file-input"
                  className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium"
                >
                  {language === 'de' ? 'Datei auswählen' : 'Choose file'}
                </label>
                {file && (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                    <p className="text-sm text-green-800 font-medium">
                      ✓ {file.name}
                    </p>
                    <p className="text-xs text-green-600">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                )}
              </div>

              <Button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full bg-blue-600 hover:bg-blue-700"
                size="lg"
              >
                {uploading ? (
                  <>
                    <Clock className="w-5 h-5 mr-2 animate-spin" />
                    {language === 'de' ? 'Hochladen & Analysieren...' : 'Uploading & Analyzing...'}
                  </>
                ) : (
                  <>
                    <FileCheck className="w-5 h-5 mr-2" />
                    {language === 'de' ? 'Analyse starten (Kostenlos)' : 'Start Analysis (Free)'}
                  </>
                )}
              </Button>

              <p className="text-xs text-center text-gray-500">
                {language === 'de' 
                  ? '100% Open Source • Datenschutzkonform • Mahkemede kabul edilebilir' 
                  : '100% Open Source • Privacy Compliant • Court Admissible'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Cases List */}
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">
              {language === 'de' ? 'Meine Fälle' : 'My Cases'}
            </h2>
            <Button
              onClick={loadMyCases}
              variant="outline"
              size="sm"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              {language === 'de' ? 'Aktualisieren' : 'Refresh'}
            </Button>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <Clock className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-600" />
              <p className="text-gray-600">{language === 'de' ? 'Lädt...' : 'Loading...'}</p>
            </div>
          ) : cases.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center text-gray-500">
                <Shield className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg">
                  {language === 'de' 
                    ? 'Keine Fälle gefunden. Starten Sie Ihre erste Analyse oben.' 
                    : 'No cases found. Start your first analysis above.'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {cases.map((caseItem) => (
                <Card key={caseItem.case_id} className="border-2 hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-3">
                          {getStatusIcon(caseItem.status)}
                          <div>
                            <h3 className="font-bold text-lg">{caseItem.case_id}</h3>
                            <p className="text-sm text-gray-600">
                              {getStatusText(caseItem.status)}
                            </p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                          <div>
                            <span className="text-gray-600">
                              {language === 'de' ? 'Datei:' : 'File:'}
                            </span>
                            <p className="font-medium">{caseItem.file_name}</p>
                          </div>
                          <div>
                            <span className="text-gray-600">
                              {language === 'de' ? 'Größe:' : 'Size:'}
                            </span>
                            <p className="font-medium">{formatFileSize(caseItem.file_size)}</p>
                          </div>
                          <div>
                            <span className="text-gray-600">
                              {language === 'de' ? 'Erstellt:' : 'Created:'}
                            </span>
                            <p className="font-medium">{formatDate(caseItem.created_at)}</p>
                          </div>
                          {caseItem.completed_at && (
                            <div>
                              <span className="text-gray-600">
                                {language === 'de' ? 'Abgeschlossen:' : 'Completed:'}
                              </span>
                              <p className="font-medium">{formatDate(caseItem.completed_at)}</p>
                            </div>
                          )}
                        </div>
                        
                        {caseItem.statistics && (
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4">
                            {caseItem.statistics.whatsapp_messages > 0 && (
                              <div className="bg-green-50 p-3 rounded border border-green-200">
                                <MessageSquare className="w-4 h-4 text-green-600 mb-1" />
                                <p className="text-xs text-gray-600">WhatsApp</p>
                                <p className="font-bold text-green-700">
                                  {caseItem.statistics.whatsapp_messages}
                                </p>
                              </div>
                            )}
                            {caseItem.statistics.telegram_messages > 0 && (
                              <div className="bg-blue-50 p-3 rounded border border-blue-200">
                                <MessageSquare className="w-4 h-4 text-blue-600 mb-1" />
                                <p className="text-xs text-gray-600">Telegram</p>
                                <p className="font-bold text-blue-700">
                                  {caseItem.statistics.telegram_messages}
                                </p>
                              </div>
                            )}
                            {caseItem.statistics.sms_messages > 0 && (
                              <div className="bg-purple-50 p-3 rounded border border-purple-200">
                                <MessageSquare className="w-4 h-4 text-purple-600 mb-1" />
                                <p className="text-xs text-gray-600">SMS</p>
                                <p className="font-bold text-purple-700">
                                  {caseItem.statistics.sms_messages}
                                </p>
                              </div>
                            )}
                            {caseItem.statistics.call_logs > 0 && (
                              <div className="bg-orange-50 p-3 rounded border border-orange-200">
                                <Phone className="w-4 h-4 text-orange-600 mb-1" />
                                <p className="text-xs text-gray-600">
                                  {language === 'de' ? 'Anrufe' : 'Calls'}
                                </p>
                                <p className="font-bold text-orange-700">
                                  {caseItem.statistics.call_logs}
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {caseItem.status === 'failed' && caseItem.error && (
                          <Alert className="mt-3 border-red-200 bg-red-50">
                            <XCircle className="w-4 h-4 text-red-600" />
                            <AlertDescription className="text-red-800 ml-2">
                              {caseItem.error}
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>

                      <div className="flex flex-col space-y-2 ml-4">
                        {caseItem.status === 'completed' && (
                          <>
                            <Button
                              onClick={() => handleDownload(caseItem.case_id, 'txt')}
                              size="sm"
                              className="bg-blue-600 hover:bg-blue-700"
                            >
                              <Download className="w-4 h-4 mr-1" />
                              TXT
                            </Button>
                            {caseItem.report_pdf && (
                              <Button
                                onClick={() => handleDownload(caseItem.case_id, 'pdf')}
                                size="sm"
                                className="bg-red-600 hover:bg-red-700"
                              >
                                <Download className="w-4 h-4 mr-1" />
                                PDF
                              </Button>
                            )}
                          </>
                        )}
                        {(caseItem.status === 'completed' || caseItem.status === 'failed') && (
                          <Button
                            onClick={() => handleDelete(caseItem.case_id)}
                            size="sm"
                            variant="outline"
                            className="border-red-300 text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForensicAnalysis;
