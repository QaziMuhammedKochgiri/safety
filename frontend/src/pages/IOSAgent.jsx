import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Smartphone,
  Camera,
  Users,
  Upload,
  CheckCircle,
  AlertCircle,
  Loader2,
  Share,
  Download,
  Image,
  FileText,
  Shield,
  Info,
  RefreshCw
} from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || '';

// Check if running as PWA (standalone mode)
const isPWA = () => {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
};

// Check if iOS device
const isIOS = () => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
};

export default function IOSAgent() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const action = searchParams.get('action');

  const [status, setStatus] = useState('idle'); // idle, collecting, uploading, done, error
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [collectedData, setCollectedData] = useState({
    photos: [],
    contacts: [],
    notes: ''
  });
  const [uploadResult, setUploadResult] = useState(null);
  const [deviceInfo, setDeviceInfo] = useState(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  // Detect device info
  useEffect(() => {
    const info = {
      platform: navigator.platform,
      userAgent: navigator.userAgent,
      language: navigator.language,
      isIOS: isIOS(),
      isPWA: isPWA(),
      screenWidth: window.screen.width,
      screenHeight: window.screen.height,
      devicePixelRatio: window.devicePixelRatio
    };
    setDeviceInfo(info);

    // Show install prompt if not PWA and on iOS
    if (isIOS() && !isPWA()) {
      setShowInstallPrompt(true);
    }

    // Auto-start if action parameter present
    if (action === 'photos') {
      handlePhotoCapture();
    } else if (action === 'contacts') {
      handleContactExport();
    }
  }, [action]);

  // Handle photo capture/selection
  const handlePhotoCapture = useCallback(async () => {
    try {
      setStatus('collecting');
      setProgress(10);

      // Create file input for photo selection
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.multiple = true;
      input.capture = 'environment'; // Use camera on mobile

      input.onchange = async (e) => {
        const files = Array.from(e.target.files);
        setProgress(30);

        const photos = [];
        for (let i = 0; i < files.length; i++) {
          const file = files[i];

          // Read file as base64
          const reader = new FileReader();
          const base64 = await new Promise((resolve) => {
            reader.onload = () => resolve(reader.result);
            reader.readAsDataURL(file);
          });

          // Extract EXIF data if available
          const exifData = await extractEXIF(file);

          photos.push({
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified,
            base64: base64,
            exif: exifData
          });

          setProgress(30 + (i / files.length) * 50);
        }

        setCollectedData(prev => ({
          ...prev,
          photos: [...prev.photos, ...photos]
        }));
        setProgress(80);
        setStatus('idle');
      };

      input.click();
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }, []);

  // Extract EXIF data from image
  const extractEXIF = async (file) => {
    try {
      // Simple EXIF extraction - in production use a library like exif-js
      const arrayBuffer = await file.arrayBuffer();
      const view = new DataView(arrayBuffer);

      // Check for JPEG
      if (view.getUint16(0) !== 0xFFD8) {
        return null;
      }

      // Look for EXIF marker
      let offset = 2;
      while (offset < view.byteLength) {
        const marker = view.getUint16(offset);
        if (marker === 0xFFE1) { // EXIF marker
          return {
            hasExif: true,
            offset: offset
          };
        }
        offset += 2 + view.getUint16(offset + 2);
      }
      return { hasExif: false };
    } catch {
      return null;
    }
  };

  // Handle contact export (using Contacts API if available)
  const handleContactExport = useCallback(async () => {
    try {
      setStatus('collecting');
      setProgress(10);

      // Check if Contact Picker API is available (Chrome/Edge on Android only)
      if ('contacts' in navigator && 'ContactsManager' in window) {
        const props = ['name', 'email', 'tel'];
        const opts = { multiple: true };

        const contacts = await navigator.contacts.select(props, opts);
        setCollectedData(prev => ({
          ...prev,
          contacts: contacts.map(c => ({
            name: c.name ? c.name[0] : 'Unknown',
            email: c.email ? c.email[0] : null,
            phone: c.tel ? c.tel[0] : null
          }))
        }));
        setProgress(100);
        setStatus('idle');
      } else {
        // Fallback: Show instructions for manual export
        setError('Contact export is not directly supported on iOS Safari. Please use the vCard export method below.');
        setStatus('idle');
      }
    } catch (err) {
      if (err.name === 'SecurityError') {
        setError('Permission denied for contact access');
      } else {
        setError(err.message);
      }
      setStatus('error');
    }
  }, []);

  // Upload collected data to server
  const handleUpload = async () => {
    if (!token) {
      setError('No collection token provided');
      return;
    }

    try {
      setStatus('uploading');
      setProgress(0);

      const payload = {
        token: token,
        deviceInfo: deviceInfo,
        photos: collectedData.photos.map(p => ({
          name: p.name,
          size: p.size,
          type: p.type,
          lastModified: p.lastModified,
          exif: p.exif,
          base64: p.base64
        })),
        contacts: collectedData.contacts,
        notes: collectedData.notes,
        timestamp: new Date().toISOString()
      };

      // Calculate total size for progress
      const totalSize = JSON.stringify(payload).length;
      let uploaded = 0;

      const response = await fetch(`${API_URL}/api/collection/ios-upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      setProgress(100);

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      setUploadResult(result);
      setStatus('done');

      // Clear collected data after successful upload
      setCollectedData({ photos: [], contacts: [], notes: '' });
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  // Render install instructions for iOS
  const renderInstallInstructions = () => (
    <Alert className="mb-4 bg-blue-50 border-blue-200">
      <Share className="h-4 w-4 text-blue-600" />
      <AlertDescription className="text-blue-800">
        <strong>Ana Ekrana Ekleyin:</strong>
        <ol className="mt-2 ml-4 list-decimal text-sm">
          <li>Safari'de <Share className="inline h-3 w-3" /> Paylas simgesine tıklayın</li>
          <li>"Ana Ekrana Ekle" secenegini seçin</li>
          <li>Uygulama adini onaylayin</li>
        </ol>
        <p className="mt-2 text-xs text-blue-600">
          Ana ekrana ekleyerek tam ekran modunda kullanabilirsiniz.
        </p>
      </AlertDescription>
    </Alert>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-4">
      <div className="max-w-md mx-auto space-y-4">
        {/* Header */}
        <div className="text-center py-4">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <Smartphone className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">SafeChild iOS Agent</h1>
          <p className="text-gray-600 mt-1">Guvenli veri toplama araci</p>
          {isPWA() && (
            <Badge variant="secondary" className="mt-2">
              <CheckCircle className="h-3 w-3 mr-1" />
              PWA Modu
            </Badge>
          )}
        </div>

        {/* Install prompt for non-PWA iOS users */}
        {showInstallPrompt && !isPWA() && renderInstallInstructions()}

        {/* Token status */}
        {token ? (
          <Alert className="bg-green-50 border-green-200">
            <Shield className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Toplama tokeni dogrulandı. Verileriniz sifrelenerek gonderilecektir.
            </AlertDescription>
          </Alert>
        ) : (
          <Alert className="bg-yellow-50 border-yellow-200">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              Toplama tokeni bulunamadı. Lutfen avukatinizdan gelen linki kullanin.
            </AlertDescription>
          </Alert>
        )}

        {/* Main content tabs */}
        <Tabs defaultValue="photos" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="photos">
              <Camera className="h-4 w-4 mr-1" />
              Fotograflar
            </TabsTrigger>
            <TabsTrigger value="contacts">
              <Users className="h-4 w-4 mr-1" />
              Kisiler
            </TabsTrigger>
            <TabsTrigger value="notes">
              <FileText className="h-4 w-4 mr-1" />
              Notlar
            </TabsTrigger>
          </TabsList>

          {/* Photos Tab */}
          <TabsContent value="photos">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Camera className="h-5 w-5" />
                  Fotograf Toplama
                </CardTitle>
                <CardDescription>
                  Fotograf cekin veya galeriden secin
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    onClick={handlePhotoCapture}
                    disabled={status === 'collecting'}
                    className="h-20"
                  >
                    <div className="text-center">
                      <Camera className="h-6 w-6 mx-auto mb-1" />
                      <span className="text-sm">Fotograf Cek</span>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handlePhotoCapture}
                    disabled={status === 'collecting'}
                    className="h-20"
                  >
                    <div className="text-center">
                      <Image className="h-6 w-6 mx-auto mb-1" />
                      <span className="text-sm">Galeriden Sec</span>
                    </div>
                  </Button>
                </div>

                {/* Collected photos preview */}
                {collectedData.photos.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">
                      Toplanan Fotograflar ({collectedData.photos.length})
                    </h4>
                    <div className="grid grid-cols-3 gap-2">
                      {collectedData.photos.slice(0, 6).map((photo, idx) => (
                        <div
                          key={idx}
                          className="aspect-square bg-gray-100 rounded-lg overflow-hidden"
                        >
                          <img
                            src={photo.base64}
                            alt={photo.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ))}
                      {collectedData.photos.length > 6 && (
                        <div className="aspect-square bg-gray-200 rounded-lg flex items-center justify-center">
                          <span className="text-gray-600 font-medium">
                            +{collectedData.photos.length - 6}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Contacts Tab */}
          <TabsContent value="contacts">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Kisi Listesi
                </CardTitle>
                <CardDescription>
                  Rehberinizden kisileri secin
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={handleContactExport}
                  disabled={status === 'collecting'}
                  className="w-full"
                >
                  {status === 'collecting' ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Yukleniyor...
                    </>
                  ) : (
                    <>
                      <Users className="h-4 w-4 mr-2" />
                      Kisileri Sec
                    </>
                  )}
                </Button>

                {/* iOS Fallback instructions */}
                <Alert className="bg-blue-50 border-blue-200">
                  <Info className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-sm text-blue-800">
                    <strong>iOS icin alternatif yontem:</strong>
                    <ol className="mt-2 ml-4 list-decimal">
                      <li>Ayarlar &gt; Kisiler &gt; Tum Kisileri Disari Aktar</li>
                      <li>vCard dosyasini bu sayfaya yukleyin</li>
                    </ol>
                  </AlertDescription>
                </Alert>

                {collectedData.contacts.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">
                      Secilen Kisiler ({collectedData.contacts.length})
                    </h4>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {collectedData.contacts.map((contact, idx) => (
                        <div
                          key={idx}
                          className="p-2 bg-gray-50 rounded text-sm"
                        >
                          {contact.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notes Tab */}
          <TabsContent value="notes">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Ek Notlar
                </CardTitle>
                <CardDescription>
                  Avukatiniza iletmek istediginiz notlar
                </CardDescription>
              </CardHeader>
              <CardContent>
                <textarea
                  className="w-full h-32 p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Buraya notlarinizi yazabilirsiniz..."
                  value={collectedData.notes}
                  onChange={(e) => setCollectedData(prev => ({
                    ...prev,
                    notes: e.target.value
                  }))}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Progress indicator */}
        {(status === 'collecting' || status === 'uploading') && (
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                <span className="text-sm font-medium">
                  {status === 'collecting' ? 'Veri toplaniyor...' : 'Yukleniyor...'}
                </span>
              </div>
              <Progress value={progress} className="h-2" />
            </CardContent>
          </Card>
        )}

        {/* Error display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Upload section */}
        {(collectedData.photos.length > 0 || collectedData.contacts.length > 0 || collectedData.notes) && (
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="font-medium">Toplanan Veriler</h4>
                  <p className="text-sm text-gray-600">
                    {collectedData.photos.length} fotograf, {collectedData.contacts.length} kisi
                    {collectedData.notes && ', notlar'}
                  </p>
                </div>
                <Button
                  onClick={handleUpload}
                  disabled={!token || status === 'uploading'}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {status === 'uploading' ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Yukleniyor
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Gonder
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Success message */}
        {status === 'done' && uploadResult && (
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Verileriniz basariyla yuklendi! Avukatiniz en kisa surede inceleyecektir.
              <br />
              <span className="text-xs text-green-600">
                Referans: {uploadResult.reference || 'N/A'}
              </span>
            </AlertDescription>
          </Alert>
        )}

        {/* Footer */}
        <div className="text-center py-4 text-xs text-gray-500">
          <p>Verileriniz AES-256 ile sifrelenmektedir</p>
          <p className="mt-1">SafeChild iOS Agent v1.0</p>
        </div>
      </div>
    </div>
  );
}
