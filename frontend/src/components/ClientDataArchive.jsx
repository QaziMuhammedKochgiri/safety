import React, { useState, useEffect } from 'react';
import {
  Folder, Image, Video, FileText, File, Download,
  Eye, Search, Filter, Calendar, SortAsc, SortDesc,
  Grid, List, Clock, Package
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import FileViewer from './FileViewer';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_API_URL || "/api";

/**
 * ClientDataArchive Component
 * Comprehensive file browser for all client data
 * Features: Search, filter, sort, preview, download
 */
const ClientDataArchive = ({ clientNumber, token }) => {
  const [files, setFiles] = useState([]);
  const [filteredFiles, setFilteredFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid'); // grid or list
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, image, video, document, other
  const [sortBy, setSortBy] = useState('date'); // date, name, size, type
  const [sortOrder, setSortOrder] = useState('desc'); // asc, desc
  const [selectedFile, setSelectedFile] = useState(null);
  const [showFileViewer, setShowFileViewer] = useState(false);

  useEffect(() => {
    if (clientNumber) {
      fetchFiles();
    }
  }, [clientNumber]);

  useEffect(() => {
    applyFiltersAndSort();
  }, [files, searchTerm, filterType, sortBy, sortOrder]);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/clients/${clientNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const documents = response.data.documents || [];
      setFiles(documents);
    } catch (error) {
      console.error('Failed to fetch files:', error);
      toast.error('Failed to load client files');
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const applyFiltersAndSort = () => {
    let result = [...files];

    // Apply search filter
    if (searchTerm) {
      result = result.filter(file =>
        file.fileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        file.documentNumber?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply type filter
    if (filterType !== 'all') {
      result = result.filter(file => {
        const type = (file.fileType || '').toLowerCase();
        switch (filterType) {
          case 'image':
            return type.includes('image');
          case 'video':
            return type.includes('video');
          case 'document':
            return type.includes('pdf') || type.includes('doc') || type.includes('text');
          case 'other':
            return !type.includes('image') && !type.includes('video') &&
                   !type.includes('pdf') && !type.includes('doc');
          default:
            return true;
        }
      });
    }

    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'date':
          comparison = new Date(b.uploadedAt || b.createdAt) - new Date(a.uploadedAt || a.createdAt);
          break;
        case 'name':
          comparison = (a.fileName || '').localeCompare(b.fileName || '');
          break;
        case 'size':
          comparison = (a.fileSize || 0) - (b.fileSize || 0);
          break;
        case 'type':
          comparison = (a.fileType || '').localeCompare(b.fileType || '');
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredFiles(result);
  };

  const handleViewFile = (file) => {
    setSelectedFile(file);
    setShowFileViewer(true);
  };

  const handleDownloadAll = () => {
    toast.info('Downloading all files...');
    // TODO: Implement bulk download
  };

  const getFileIcon = (fileType) => {
    const type = (fileType || '').toLowerCase();
    if (type.includes('image')) return <Image className="w-5 h-5 text-blue-500" />;
    if (type.includes('video')) return <Video className="w-5 h-5 text-purple-500" />;
    if (type.includes('pdf') || type.includes('doc')) return <FileText className="w-5 h-5 text-red-500" />;
    return <File className="w-5 h-5 text-gray-500" />;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFileTypeBadge = (fileType) => {
    const type = (fileType || '').toLowerCase();
    if (type.includes('image')) return <Badge className="bg-blue-100 text-blue-700 border-blue-200">Image</Badge>;
    if (type.includes('video')) return <Badge className="bg-purple-100 text-purple-700 border-purple-200">Video</Badge>;
    if (type.includes('pdf')) return <Badge className="bg-red-100 text-red-700 border-red-200">PDF</Badge>;
    if (type.includes('doc')) return <Badge className="bg-orange-100 text-orange-700 border-orange-200">Document</Badge>;
    return <Badge variant="outline">File</Badge>;
  };

  const getFileStats = () => {
    const stats = {
      total: files.length,
      images: files.filter(f => (f.fileType || '').toLowerCase().includes('image')).length,
      videos: files.filter(f => (f.fileType || '').toLowerCase().includes('video')).length,
      documents: files.filter(f => {
        const type = (f.fileType || '').toLowerCase();
        return type.includes('pdf') || type.includes('doc');
      }).length,
      totalSize: files.reduce((sum, f) => sum + (f.fileSize || 0), 0)
    };
    return stats;
  };

  const stats = getFileStats();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading files...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* File Viewer Modal */}
      {showFileViewer && selectedFile && (
        <FileViewer
          file={selectedFile}
          onClose={() => {
            setShowFileViewer(false);
            setSelectedFile(null);
          }}
        />
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Package className="w-8 h-8 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-gray-500">Total Files</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Image className="w-8 h-8 text-green-600" />
              <div>
                <p className="text-2xl font-bold">{stats.images}</p>
                <p className="text-xs text-gray-500">Images</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Video className="w-8 h-8 text-purple-600" />
              <div>
                <p className="text-2xl font-bold">{stats.videos}</p>
                <p className="text-xs text-gray-500">Videos</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-red-600" />
              <div>
                <p className="text-2xl font-bold">{stats.documents}</p>
                <p className="text-xs text-gray-500">Documents</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Folder className="w-8 h-8 text-orange-600" />
              <div>
                <p className="text-xl font-bold">{formatFileSize(stats.totalSize)}</p>
                <p className="text-xs text-gray-500">Total Size</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="image">Images</option>
                <option value="video">Videos</option>
                <option value="document">Documents</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="date">Date</option>
                <option value="name">Name</option>
                <option value="size">Size</option>
                <option value="type">Type</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
              </Button>
            </div>

            {/* View Mode */}
            <div className="flex gap-1">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('grid')}
              >
                <Grid className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('list')}
              >
                <List className="w-4 h-4" />
              </Button>
            </div>

            {/* Download All */}
            <Button variant="outline" size="sm" onClick={handleDownloadAll}>
              <Download className="w-4 h-4 mr-2" />
              Download All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Files Display */}
      {filteredFiles.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Folder className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">No files found</p>
            <p className="text-gray-400 text-sm mt-1">
              {searchTerm || filterType !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Client has not uploaded any files yet'}
            </p>
          </CardContent>
        </Card>
      ) : viewMode === 'grid' ? (
        // Grid View
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredFiles.map((file) => (
            <Card
              key={file.documentNumber || file._id}
              className="hover:shadow-lg transition-shadow cursor-pointer group"
              onClick={() => handleViewFile(file)}
            >
              <CardContent className="p-4">
                <div className="aspect-square bg-gray-100 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                  {file.fileType?.includes('image') ? (
                    <img
                      src={`${BACKEND_URL}${file.filePath}`}
                      alt={file.fileName}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform"
                    />
                  ) : (
                    <div className="text-gray-400">
                      {getFileIcon(file.fileType)}
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-sm truncate">{file.fileName}</p>
                  <div className="flex items-center justify-between">
                    {getFileTypeBadge(file.fileType)}
                    <span className="text-xs text-gray-500">{formatFileSize(file.fileSize)}</span>
                  </div>
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(file.uploadedAt)}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        // List View
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {filteredFiles.map((file) => (
                <div
                  key={file.documentNumber || file._id}
                  className="p-4 hover:bg-gray-50 transition-colors cursor-pointer flex items-center gap-4"
                  onClick={() => handleViewFile(file)}
                >
                  <div className="flex-shrink-0">
                    {getFileIcon(file.fileType)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{file.fileName}</p>
                    <p className="text-sm text-gray-500 truncate">
                      {file.documentNumber} • {formatDate(file.uploadedAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {getFileTypeBadge(file.fileType)}
                    <span className="text-sm text-gray-500 min-w-[60px] text-right">
                      {formatFileSize(file.fileSize)}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewFile(file);
                      }}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ClientDataArchive;
