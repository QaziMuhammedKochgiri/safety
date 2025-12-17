import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  ArrowLeft, Search, FileText, Download, Eye, Trash2, File,
  FileImage, FileVideo, Loader2, Calendar, User, Brain, Sparkles,
  MessageSquare, AlertCircle, CheckCircle, X
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api';

const AdminDocuments = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [filteredDocs, setFilteredDocs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, byType: {} });

  // File viewer state
  const [viewerOpen, setViewerOpen] = useState(false);
  const [currentDoc, setCurrentDoc] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [fileLoading, setFileLoading] = useState(false);

  // AI Analysis state
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  const [aiPrompt, setAiPrompt] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = documents.filter(d =>
        d.fileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.clientNumber?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.documentNumber?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredDocs(filtered);
    } else {
      setFilteredDocs(documents);
    }
  }, [searchTerm, documents]);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_URL}/documents/all`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const docs = response.data.documents || [];
      setDocuments(docs);
      setFilteredDocs(docs);

      // Calculate stats
      const byType = {};
      docs.forEach(d => {
        const ext = d.fileName?.split('.').pop()?.toLowerCase() || 'unknown';
        byType[ext] = (byType[ext] || 0) + 1;
      });
      setStats({ total: docs.length, byType });
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (fileName) => {
    const ext = fileName?.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
      return <FileImage className="w-5 h-5 text-green-600" />;
    }
    if (['mp4', 'mov', 'avi', 'webm'].includes(ext)) {
      return <FileVideo className="w-5 h-5 text-purple-600" />;
    }
    if (ext === 'pdf') {
      return <FileText className="w-5 h-5 text-red-600" />;
    }
    return <File className="w-5 h-5 text-blue-600" />;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleViewFile = async (doc) => {
    setCurrentDoc(doc);
    setViewerOpen(true);
    setFileContent(null);
    setAiResult(null);
    setFileLoading(true);

    try {
      const ext = doc.fileName?.split('.').pop()?.toLowerCase();

      // For images, fetch as blob and create object URL
      if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
        const response = await axios.get(`${API_URL}/documents/${doc.documentNumber}/download`, {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        });
        const url = URL.createObjectURL(response.data);
        setFileContent({ type: 'image', url });
      }
      // For PDFs, fetch as blob
      else if (ext === 'pdf') {
        const response = await axios.get(`${API_URL}/documents/${doc.documentNumber}/download`, {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        });
        const url = URL.createObjectURL(response.data);
        setFileContent({ type: 'pdf', url });
      }
      // For text files, fetch as text
      else if (['txt', 'csv', 'json', 'xml'].includes(ext)) {
        const response = await axios.get(`${API_URL}/documents/${doc.documentNumber}/download`, {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'text'
        });
        setFileContent({ type: 'text', content: response.data });
      }
      else {
        setFileContent({ type: 'unsupported', message: 'Preview not available for this file type. You can download it instead.' });
      }
    } catch (error) {
      console.error('Error loading file:', error);
      toast.error('Failed to load file');
      setFileContent({ type: 'error', message: 'Failed to load file content' });
    } finally {
      setFileLoading(false);
    }
  };

  const handleAIAnalysis = async () => {
    if (!aiPrompt.trim()) {
      toast.error(language === 'de' ? 'Bitte geben Sie eine Frage ein' : 'Please enter a question');
      return;
    }

    setAiAnalyzing(true);
    setAiResult(null);

    try {
      // First, get the document content
      const docResponse = await axios.get(`${API_URL}/documents/${currentDoc.documentNumber}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'text'
      });

      // Then send to AI for analysis
      const aiResponse = await axios.post(
        `${API_URL}/ai/analyze-document`,
        {
          documentContent: docResponse.data,
          fileName: currentDoc.fileName,
          question: aiPrompt,
          documentNumber: currentDoc.documentNumber
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setAiResult(aiResponse.data);
      toast.success(language === 'de' ? 'Analyse abgeschlossen' : 'Analysis complete');
    } catch (error) {
      console.error('AI Analysis error:', error);
      toast.error(error.response?.data?.detail || 'AI analysis failed');
      setAiResult({
        analysis: 'AI analysis failed. Please try again.',
        error: true
      });
    } finally {
      setAiAnalyzing(false);
    }
  };

  const quickAIPrompts = [
    { de: 'Was ist der Hauptinhalt dieses Dokuments?', en: 'What is the main content of this document?' },
    { de: 'Gibt es rechtliche Probleme in diesem Dokument?', en: 'Are there any legal issues in this document?' },
    { de: 'Fasse dieses Dokument zusammen', en: 'Summarize this document' },
    { de: 'Welche Daten sind relevant für den Fall?', en: 'What data is relevant for the case?' }
  ];

  const handleDownload = async (doc) => {
    try {
      const response = await axios.get(`${API_URL}/documents/${doc.documentNumber}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Download started');
    } catch (error) {
      toast.error('Download failed');
    }
  };

  const handleDelete = async (documentNumber) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await axios.delete(`${API_URL}/documents/${documentNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Document deleted');
      fetchDocuments();
    } catch (error) {
      toast.error('Failed to delete document');
    }
  };

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
                {language === 'de' ? 'Dokumente mit AI' : 'Documents with AI'}
              </h1>
              <p className="text-gray-500">
                {stats.total} {language === 'de' ? 'Dokumente' : 'documents'} • {language === 'de' ? 'AI-Analyse verfügbar' : 'AI Analysis Available'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Search */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Search className="w-5 h-5 text-gray-400" />
              <Input
                placeholder={language === 'de' ? 'Suchen...' : 'Search...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-gray-600">{language === 'de' ? 'Gesamt' : 'Total'}</div>
            </CardContent>
          </Card>
          {Object.entries(stats.byType).slice(0, 3).map(([ext, count]) => (
            <Card key={ext}>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-purple-600">{count}</div>
                <div className="text-sm text-gray-600 uppercase">{ext}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Documents List */}
        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
          </div>
        ) : filteredDocs.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">{language === 'de' ? 'Keine Dokumente gefunden' : 'No documents found'}</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {filteredDocs.map((doc) => (
              <Card key={doc.documentNumber} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1">
                      {getFileIcon(doc.fileName)}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium truncate">{doc.fileName}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <User className="w-3 h-3 mr-1" />
                            {doc.clientNumber}
                          </span>
                          <span className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(doc.uploadedAt).toLocaleDateString()}
                          </span>
                          <span>{formatFileSize(doc.fileSize)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleViewFile(doc)}
                        className="border-purple-200 hover:bg-purple-50"
                      >
                        <Brain className="w-4 h-4 mr-1 text-purple-600" />
                        {language === 'de' ? 'AI Analyse' : 'AI Analyze'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleViewFile(doc)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownload(doc)}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDelete(doc.documentNumber)}
                        className="text-red-600 hover:bg-red-50"
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
      </div>

      {/* File Viewer + AI Analysis Modal */}
      <Dialog open={viewerOpen} onOpenChange={setViewerOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>{currentDoc?.fileName}</span>
              <Button variant="ghost" size="sm" onClick={() => setViewerOpen(false)}>
                <X className="w-4 h-4" />
              </Button>
            </DialogTitle>
          </DialogHeader>

          <div className="grid md:grid-cols-2 gap-4 flex-1 overflow-hidden">
            {/* Left: File Preview */}
            <div className="border rounded-lg p-4 overflow-auto bg-gray-50">
              <h3 className="font-semibold mb-3 flex items-center">
                <Eye className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Vorschau' : 'Preview'}
              </h3>
              {fileLoading ? (
                <div className="text-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
                </div>
              ) : fileContent?.type === 'image' ? (
                <img src={fileContent.url} alt={currentDoc?.fileName} className="max-w-full rounded" />
              ) : fileContent?.type === 'pdf' ? (
                <iframe src={fileContent.url} className="w-full h-96 rounded" title="PDF Preview" />
              ) : fileContent?.type === 'text' ? (
                <pre className="bg-white p-4 rounded text-sm overflow-auto max-h-96 whitespace-pre-wrap">{fileContent.content}</pre>
              ) : fileContent?.type === 'unsupported' ? (
                <div className="text-center py-8 text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-2" />
                  <p>{fileContent.message}</p>
                  <Button onClick={() => handleDownload(currentDoc)} className="mt-4">
                    <Download className="w-4 h-4 mr-2" />
                    Download File
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-2" />
                  <p>Unable to preview this file</p>
                </div>
              )}
            </div>

            {/* Right: AI Analysis */}
            <div className="border rounded-lg p-4 overflow-auto bg-gradient-to-br from-purple-50 to-blue-50">
              <h3 className="font-semibold mb-3 flex items-center text-purple-700">
                <Sparkles className="w-4 h-4 mr-2" />
                {language === 'de' ? 'AI Analyse' : 'AI Analysis'}
              </h3>

              {/* Quick Prompts */}
              <div className="mb-4">
                <p className="text-xs text-gray-600 mb-2">{language === 'de' ? 'Schnellauswahl:' : 'Quick prompts:'}</p>
                <div className="flex flex-wrap gap-2">
                  {quickAIPrompts.map((prompt, idx) => (
                    <Button
                      key={idx}
                      size="sm"
                      variant="outline"
                      onClick={() => setAiPrompt(language === 'de' ? prompt.de : prompt.en)}
                      className="text-xs"
                    >
                      {language === 'de' ? prompt.de : prompt.en}
                    </Button>
                  ))}
                </div>
              </div>

              {/* AI Prompt Input */}
              <div className="mb-4">
                <div className="flex space-x-2">
                  <Input
                    placeholder={language === 'de' ? 'Frage an AI...' : 'Ask AI...'}
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAIAnalysis()}
                  />
                  <Button onClick={handleAIAnalysis} disabled={aiAnalyzing} className="bg-purple-600 hover:bg-purple-700">
                    {aiAnalyzing ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Brain className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* AI Result */}
              {aiResult && (
                <div className={`p-4 rounded-lg ${aiResult.error ? 'bg-red-50 border border-red-200' : 'bg-white border border-purple-200'}`}>
                  <div className="flex items-start space-x-2 mb-2">
                    {aiResult.error ? (
                      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="font-semibold text-sm mb-2">
                        {aiResult.error ? 'Error' : (language === 'de' ? 'Analyse Ergebnis:' : 'Analysis Result:')}
                      </p>
                      <div className="text-sm text-gray-700 whitespace-pre-wrap">
                        {aiResult.analysis || aiResult.summary || aiResult.response || 'No result'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {!aiResult && !aiAnalyzing && (
                <div className="text-center py-8 text-gray-400">
                  <MessageSquare className="w-12 h-12 mx-auto mb-2" />
                  <p className="text-sm">{language === 'de' ? 'Stellen Sie eine Frage über das Dokument' : 'Ask a question about the document'}</p>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDocuments;
