import React, { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Upload, Download, FileText } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || "/api";

const Documents = () => {
  const { language } = useLanguage();
  const [activeMode, setActiveMode] = useState(null);
  const [clientNumber, setClientNumber] = useState('');
  const [fileNumber, setFileNumber] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleFileSelect = (e) => {
    setSelectedFiles(Array.from(e.target.files));
  };

  const handleUpload = async () => {
    if (!clientNumber) {
      toast.error(
        language === 'de' ? 'Fehler' : 'Error',
        { description: language === 'de' ? 'Bitte geben Sie Ihre Mandantennummer ein' : 'Please enter your client number' }
      );
      return;
    }

    if (selectedFiles.length === 0) {
      toast.error(
        language === 'de' ? 'Fehler' : 'Error',
        { description: language === 'de' ? 'Bitte wählen Sie mindestens eine Datei aus' : 'Please select at least one file' }
      );
      return;
    }

    try {
      // Validate client number first
      const validateResponse = await axios.get(`${API}/clients/${clientNumber}/validate`);
      
      if (!validateResponse.data.valid) {
        toast.error(t(language, 'invalidNumber'), {
          description: language === 'de' 
            ? 'Die eingegebene Mandantennummer ist nicht gültig oder nicht registriert.' 
            : 'The entered client number is not valid or not registered.'
        });
        return;
      }

      // Upload each file
      let uploadedCount = 0;
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('clientNumber', clientNumber);
        formData.append('file', file);

        await axios.post(`${API}/documents/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        uploadedCount++;
      }

      toast.success(t(language, 'uploadSuccess'), {
        description: language === 'de' 
          ? `${uploadedCount} Datei(en) erfolgreich hochgeladen` 
          : `${uploadedCount} file(s) uploaded successfully`
      });
      
      setClientNumber('');
      setSelectedFiles([]);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(
        language === 'de' ? 'Upload fehlgeschlagen' : 'Upload failed',
        { description: error.response?.data?.detail || error.message }
      );
    }
  };

  const handleDownload = async () => {
    if (!fileNumber) {
      toast.error(
        language === 'de' ? 'Fehler' : 'Error',
        { description: language === 'de' ? 'Bitte geben Sie die Dokumentennummer ein' : 'Please enter the document number' }
      );
      return;
    }

    try {
      const response = await axios.get(`${API}/documents/${fileNumber}/download`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from headers or use document number
      const contentDisposition = response.headers['content-disposition'];
      const filename = contentDisposition 
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `document_${fileNumber}.pdf`;
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(t(language, 'downloadSuccess'), {
        description: language === 'de' ? 'Ihre Datei wird heruntergeladen' : 'Your file is being downloaded'
      });
      
      setFileNumber('');
    } catch (error) {
      console.error('Download error:', error);
      
      let errorMessage = language === 'de' ? 'Download fehlgeschlagen' : 'Download failed';
      let errorDescription = error.message;
      
      if (error.response?.status === 404) {
        errorMessage = t(language, 'invalidNumber');
        errorDescription = language === 'de' 
          ? 'Die eingegebene Dokumentennummer wurde nicht gefunden.' 
          : 'The entered document number was not found.';
      } else if (error.response?.data?.detail) {
        errorDescription = error.response.data.detail;
      }
      
      toast.error(errorMessage, {
        description: errorDescription
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-5xl">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            {t(language, 'documentsTitle')}
          </h1>
          <p className="text-xl text-gray-600">
            {t(language, 'documentsSubtitle')}
          </p>
        </div>

        {/* Mode Selection */}
        {!activeMode && (
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <Card 
              className="border-2 hover:border-blue-500 hover:shadow-xl transition-all duration-300 cursor-pointer"
              onClick={() => setActiveMode('upload')}
            >
              <CardHeader className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Upload className="w-10 h-10 text-blue-600" />
                </div>
                <CardTitle className="text-2xl">{t(language, 'uploadTitle')}</CardTitle>
                <CardDescription className="text-base">
                  {language === 'de' 
                    ? 'Laden Sie Dokumente mit Ihrer Mandantennummer hoch' 
                    : 'Upload documents with your client number'}
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  {t(language, 'uploadButton')}
                </Button>
              </CardContent>
            </Card>

            <Card 
              className="border-2 hover:border-green-500 hover:shadow-xl transition-all duration-300 cursor-pointer"
              onClick={() => setActiveMode('download')}
            >
              <CardHeader className="text-center">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Download className="w-10 h-10 text-green-600" />
                </div>
                <CardTitle className="text-2xl">{t(language, 'downloadTitle')}</CardTitle>
                <CardDescription className="text-base">
                  {language === 'de' 
                    ? 'Laden Sie Dokumente mit der Dokumentennummer herunter' 
                    : 'Download documents with the document number'}
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  {t(language, 'downloadButton')}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Upload Mode */}
        {activeMode === 'upload' && (
          <Card className="max-w-2xl mx-auto border-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Upload className="w-6 h-6 text-blue-600" />
                  </div>
                  <CardTitle className="text-2xl">{t(language, 'uploadTitle')}</CardTitle>
                </div>
                <Button variant="ghost" onClick={() => setActiveMode(null)}>
                  {t(language, 'cancel')}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="clientNumber">{t(language, 'clientNumberLabel')}</Label>
                <Input
                  id="clientNumber"
                  placeholder={t(language, 'clientNumberPlaceholder')}
                  value={clientNumber}
                  onChange={(e) => setClientNumber(e.target.value)}
                />
                <p className="text-sm text-gray-500">
                  {language === 'de' 
                    ? 'Geben Sie Ihre registrierte Mandantennummer ein' 
                    : 'Enter your registered client number'}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="fileUpload">{t(language, 'selectFiles')}</Label>
                <Input
                  id="fileUpload"
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="cursor-pointer"
                />
                {selectedFiles.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {selectedFiles.map((file, index) => (
                      <div key={index} className="flex items-center space-x-2 text-sm text-gray-600">
                        <FileText className="w-4 h-4" />
                        <span>{file.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <Button className="w-full bg-blue-600 hover:bg-blue-700" onClick={handleUpload}>
                {t(language, 'submit')}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Download Mode */}
        {activeMode === 'download' && (
          <Card className="max-w-2xl mx-auto border-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <Download className="w-6 h-6 text-green-600" />
                  </div>
                  <CardTitle className="text-2xl">{t(language, 'downloadTitle')}</CardTitle>
                </div>
                <Button variant="ghost" onClick={() => setActiveMode(null)}>
                  {t(language, 'cancel')}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="fileNumber">{t(language, 'fileNumberLabel')}</Label>
                <Input
                  id="fileNumber"
                  placeholder={t(language, 'fileNumberPlaceholder')}
                  value={fileNumber}
                  onChange={(e) => setFileNumber(e.target.value)}
                />
                <p className="text-sm text-gray-500">
                  {language === 'de' 
                    ? 'Geben Sie die Dokumentennummer ein, die Sie erhalten haben' 
                    : 'Enter the document number you received'}
                </p>
              </div>

              <Button className="w-full bg-green-600 hover:bg-green-700" onClick={handleDownload}>
                {t(language, 'submit')}
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Documents;
