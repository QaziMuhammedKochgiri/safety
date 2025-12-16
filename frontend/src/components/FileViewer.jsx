import React, { useState } from 'react';
import {
  X, Download, Eye, FileText, Film, Image as ImageIcon,
  FileAudio, File, ZoomIn, ZoomOut, RotateCw
} from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';

/**
 * FileViewer Component
 * Displays file previews for images, videos, PDFs, and documents
 * Supports zoom, rotation, and download functionality
 */
const FileViewer = ({ file, onClose }) => {
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);

  if (!file) return null;

  const getFileIcon = () => {
    const type = file.fileType || file.type || '';
    if (type.includes('image')) return <ImageIcon className="w-6 h-6 text-blue-500" />;
    if (type.includes('video')) return <Film className="w-6 h-6 text-purple-500" />;
    if (type.includes('pdf')) return <FileText className="w-6 h-6 text-red-500" />;
    if (type.includes('audio')) return <FileAudio className="w-6 h-6 text-green-500" />;
    return <File className="w-6 h-6 text-gray-500" />;
  };

  const getFileUrl = () => {
    // Construct file URL from backend
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
    if (file.filePath) {
      return `${BACKEND_URL}${file.filePath}`;
    }
    if (file.url) {
      return file.url;
    }
    return null;
  };

  const handleDownload = () => {
    const url = getFileUrl();
    if (!url) return;

    const link = document.createElement('a');
    link.href = url;
    link.download = file.fileName || file.name || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));
  const handleRotate = () => setRotation(prev => (prev + 90) % 360);

  const renderPreview = () => {
    const url = getFileUrl();
    const type = file.fileType || file.type || '';

    // Image Preview
    if (type.includes('image')) {
      return (
        <div className="flex items-center justify-center bg-gray-100 rounded-lg p-4 min-h-[400px]">
          <img
            src={url}
            alt={file.fileName || file.name}
            className="max-w-full max-h-[600px] object-contain transition-all"
            style={{
              transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
            }}
          />
        </div>
      );
    }

    // Video Preview
    if (type.includes('video')) {
      return (
        <div className="flex items-center justify-center bg-black rounded-lg overflow-hidden">
          <video
            controls
            className="max-w-full max-h-[600px]"
            style={{ transform: `scale(${zoom / 100})` }}
          >
            <source src={url} type={type} />
            Your browser does not support the video tag.
          </video>
        </div>
      );
    }

    // PDF Preview
    if (type.includes('pdf')) {
      return (
        <div className="bg-gray-100 rounded-lg overflow-hidden">
          <iframe
            src={url}
            className="w-full"
            style={{ height: '600px' }}
            title={file.fileName || file.name}
          />
        </div>
      );
    }

    // Audio Preview
    if (type.includes('audio')) {
      return (
        <div className="flex flex-col items-center justify-center bg-gray-100 rounded-lg p-12 min-h-[400px]">
          <FileAudio className="w-24 h-24 text-green-500 mb-6" />
          <audio controls className="w-full max-w-md">
            <source src={url} type={type} />
            Your browser does not support the audio tag.
          </audio>
          <p className="text-gray-600 mt-4">{file.fileName || file.name}</p>
        </div>
      );
    }

    // Default: No Preview Available
    return (
      <div className="flex flex-col items-center justify-center bg-gray-100 rounded-lg p-12 min-h-[400px]">
        <File className="w-24 h-24 text-gray-400 mb-4" />
        <p className="text-lg font-semibold text-gray-700 mb-2">Preview not available</p>
        <p className="text-sm text-gray-500 mb-6">
          {file.fileName || file.name}
        </p>
        <Button onClick={handleDownload}>
          <Download className="w-4 h-4 mr-2" />
          Download File
        </Button>
      </div>
    );
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-6xl max-h-[90vh] overflow-y-auto bg-white">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            {getFileIcon()}
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {file.fileName || file.name}
              </h2>
              <p className="text-sm text-gray-500">
                {formatFileSize(file.fileSize || file.size)} • {formatDate(file.uploadedAt || file.createdAt)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Controls (for images and videos) */}
        {(file.fileType?.includes('image') || file.type?.includes('image') ||
          file.fileType?.includes('video') || file.type?.includes('video')) && (
          <div className="bg-gray-50 px-6 py-3 border-b flex items-center justify-center gap-4">
            <Button variant="outline" size="sm" onClick={handleZoomOut} disabled={zoom <= 50}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium text-gray-600 min-w-[60px] text-center">
              {zoom}%
            </span>
            <Button variant="outline" size="sm" onClick={handleZoomIn} disabled={zoom >= 200}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            {(file.fileType?.includes('image') || file.type?.includes('image')) && (
              <>
                <div className="w-px h-6 bg-gray-300 mx-2" />
                <Button variant="outline" size="sm" onClick={handleRotate}>
                  <RotateCw className="w-4 h-4 mr-2" />
                  Rotate
                </Button>
              </>
            )}
          </div>
        )}

        {/* Preview Area */}
        <div className="p-6">
          {renderPreview()}
        </div>

        {/* Metadata */}
        <div className="bg-gray-50 px-6 py-4 border-t">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">File Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">File Name</p>
              <p className="font-medium text-gray-900 truncate">{file.fileName || file.name}</p>
            </div>
            <div>
              <p className="text-gray-500">File Size</p>
              <p className="font-medium text-gray-900">{formatFileSize(file.fileSize || file.size)}</p>
            </div>
            <div>
              <p className="text-gray-500">File Type</p>
              <p className="font-medium text-gray-900">{file.fileType || file.type || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-gray-500">Upload Date</p>
              <p className="font-medium text-gray-900">{formatDate(file.uploadedAt || file.createdAt)}</p>
            </div>
            {file.documentNumber && (
              <div>
                <p className="text-gray-500">Document Number</p>
                <p className="font-mono text-xs text-gray-900">{file.documentNumber}</p>
              </div>
            )}
            {file.category && (
              <div>
                <p className="text-gray-500">Category</p>
                <p className="font-medium text-gray-900">{file.category}</p>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default FileViewer;
