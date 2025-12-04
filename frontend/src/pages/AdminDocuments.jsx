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
  FileText,
  Download,
  Eye,
  Trash2,
  File,
  FileImage,
  FileVideo,
  Loader2,
  Calendar,
  User
} from 'lucide-react';
import axios from 'axios';

const API_URL = '/api';

const AdminDocuments = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [filteredDocs, setFilteredDocs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, byType: {} });

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
              {language === 'de' ? 'Zuruck' : 'Back'}
            </Button>
            <div>
              <h1 className="text-2xl font-bold">
                {language === 'de' ? 'Dokumente' : 'Documents'}
              </h1>
              <p className="text-gray-500">
                {stats.total} {language === 'de' ? 'Dokumente insgesamt' : 'total documents'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4 text-center">
              <FileText className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-xs text-gray-500">Total</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <FileImage className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-2xl font-bold">{(stats.byType?.jpg || 0) + (stats.byType?.png || 0) + (stats.byType?.jpeg || 0)}</p>
              <p className="text-xs text-gray-500">Images</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <FileVideo className="w-8 h-8 mx-auto mb-2 text-purple-600" />
              <p className="text-2xl font-bold">{(stats.byType?.mp4 || 0) + (stats.byType?.mov || 0)}</p>
              <p className="text-xs text-gray-500">Videos</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <File className="w-8 h-8 mx-auto mb-2 text-red-600" />
              <p className="text-2xl font-bold">{stats.byType?.pdf || 0}</p>
              <p className="text-xs text-gray-500">PDFs</p>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <Input
                placeholder={language === 'de' ? 'Suchen...' : 'Search documents...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Documents List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : filteredDocs.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">
                {language === 'de' ? 'Keine Dokumente gefunden' : 'No documents found'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filteredDocs.map((doc) => (
              <Card key={doc.documentNumber} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {getFileIcon(doc.fileName)}
                      <div>
                        <p className="font-medium">{doc.fileName}</p>
                        <div className="flex items-center space-x-3 text-sm text-gray-500">
                          <span className="flex items-center">
                            <User className="w-3 h-3 mr-1" />
                            {doc.clientNumber}
                          </span>
                          <span className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(doc.uploadedAt).toLocaleDateString('de-DE')}
                          </span>
                          <span>{formatFileSize(doc.fileSize)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">{doc.documentNumber}</Badge>
                      <Button size="sm" variant="outline" onClick={() => handleDownload(doc)}>
                        <Download className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleDelete(doc.documentNumber)}>
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDocuments;
