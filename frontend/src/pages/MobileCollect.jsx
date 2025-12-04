import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import {
  Smartphone,
  Shield,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Clock,
  Lock,
  Image,
  MessageSquare,
  Send,
  Upload,
  FileText,
  Camera,
  Video,
  Folder
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';

const MobileCollect = () => {
  const { token } = useParams();
  const [status, setStatus] = useState('validating');
  const [clientInfo, setClientInfo] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});
  const [completedSteps, setCompletedSteps] = useState({
    photos: false,
    videos: false,
    whatsapp: false,
    telegram: false,
    files: false
  });
  const [uploading, setUploading] = useState(null);
  const [totalUploaded, setTotalUploaded] = useState({ photos: 0, videos: 0, files: 0 });

  const photoInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    validateToken();
  }, [token]);

  const validateToken = async () => {
    try {
      const response = await api.get(`/collection/validate/${token}`);
      setClientInfo(response.data);
      setStatus('valid');
    } catch (error) {
      if (error.response?.status === 410) {
        setStatus('expired');
      } else if (error.response?.status === 400) {
        setStatus('completed');
      } else {
        setStatus('invalid');
      }
    }
  };

  // Upload files to server
  const uploadFiles = async (files, type) => {
    if (!files || files.length === 0) return;

    setUploading(type);
    const formData = new FormData();
    formData.append('token', token);
    formData.append('type', type);

    // Add all files
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const response = await api.post('/collection/upload-files', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000, // 5 minute timeout for large uploads
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(prev => ({ ...prev, [type]: percent }));
        }
      });

      setTotalUploaded(prev => ({
        ...prev,
        [type]: prev[type] + files.length
      }));

      setCompletedSteps(prev => ({ ...prev, [type]: true }));
      toast.success(`${files.length} ${type === 'photos' ? 'fotoğraf' : type === 'videos' ? 'video' : 'dosya'} yüklendi!`);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Yükleme hatası. Lütfen tekrar deneyin.');
    } finally {
      setUploading(null);
      setUploadProgress(prev => ({ ...prev, [type]: 0 }));
    }
  };

  // Handle photo selection - opens gallery in multi-select mode
  const handlePhotoSelect = () => {
    photoInputRef.current?.click();
  };

  // Handle video selection
  const handleVideoSelect = () => {
    videoInputRef.current?.click();
  };

  // Handle file selection
  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  // WhatsApp share - opens WhatsApp with share intent
  const handleWhatsAppShare = () => {
    // Deep link to open WhatsApp
    // On mobile, this will prompt to share/export chats
    const message = encodeURIComponent(
      `SafeChild Delil Toplama\n\nSohbet geçmişinizi dışa aktarmak için:\n1. Bir sohbet açın\n2. Sağ üst menüden "Daha fazla" seçin\n3. "Sohbeti dışa aktar" seçin\n4. "Medya dahil" seçin\n5. Bu sayfaya geri dönüp dosyayı yükleyin`
    );

    // Try to open WhatsApp
    window.location.href = `whatsapp://send?text=${message}`;

    // Mark as instruction shown
    setTimeout(() => {
      setCompletedSteps(prev => ({ ...prev, whatsapp: true }));
    }, 2000);
  };

  // Telegram share
  const handleTelegramShare = () => {
    const message = encodeURIComponent(
      `SafeChild Delil Toplama\n\nSohbet geçmişinizi dışa aktarmak için:\n1. Bir sohbet açın\n2. Sağ üst menüden "Dışa aktar" seçin\n3. Bu sayfaya geri dönüp dosyayı yükleyin`
    );

    window.location.href = `tg://msg?text=${message}`;

    setTimeout(() => {
      setCompletedSteps(prev => ({ ...prev, telegram: true }));
    }, 2000);
  };

  // Calculate overall progress
  const overallProgress = Object.values(completedSteps).filter(Boolean).length * 20;

  // Render based on status
  if (status === 'validating') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-indigo-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
            <p className="text-gray-600">Doğrulanıyor...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'expired') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-orange-200">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Clock className="h-16 w-16 text-orange-500 mb-4" />
            <h2 className="text-xl font-bold text-gray-800 mb-2">Link Süresi Dolmuş</h2>
            <p className="text-gray-600">
              Bu bağlantının süresi dolmuştur. Lütfen avukatınızla iletişime geçin.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'invalid') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-red-200">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-16 w-16 text-red-500 mb-4" />
            <h2 className="text-xl font-bold text-gray-800 mb-2">Geçersiz Link</h2>
            <p className="text-gray-600">
              Bu bağlantı geçerli değil. Lütfen avukatınızla iletişime geçin.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'completed') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-800 to-emerald-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-green-200">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <CheckCircle2 className="h-16 w-16 text-green-500 mb-4" />
            <h2 className="text-xl font-bold text-gray-800 mb-2">Tamamlandı!</h2>
            <p className="text-gray-600">
              Verileriniz başarıyla alındı. Avukatınız inceleyecektir.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Valid token - show collection interface
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-indigo-900 pb-8">
      {/* Hidden file inputs */}
      <input
        type="file"
        ref={photoInputRef}
        className="hidden"
        accept="image/*"
        multiple
        onChange={(e) => uploadFiles(e.target.files, 'photos')}
      />
      <input
        type="file"
        ref={videoInputRef}
        className="hidden"
        accept="video/*"
        multiple
        onChange={(e) => uploadFiles(e.target.files, 'videos')}
      />
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="*/*"
        multiple
        onChange={(e) => uploadFiles(e.target.files, 'files')}
      />

      {/* Header */}
      <div className="bg-white/10 backdrop-blur-lg border-b border-white/20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-center gap-3">
            <Shield className="w-8 h-8 text-blue-300" />
            <div className="text-center">
              <h1 className="text-xl font-bold text-white">SafeChild</h1>
              <p className="text-xs text-blue-200">Güvenli Delil Toplama</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Welcome */}
        <Card className="max-w-md mx-auto mb-4 border-0 shadow-2xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-xl text-gray-800">
              Merhaba{clientInfo?.clientName ? `, ${clientInfo.clientName.split(' ')[0]}` : ''}
            </CardTitle>
            <p className="text-sm text-gray-500">
              Aşağıdaki butonlara tıklayarak verilerinizi gönderin
            </p>
          </CardHeader>
          <CardContent className="pt-2">
            {/* Progress */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">İlerleme</span>
                <span className="text-blue-600 font-medium">{overallProgress}%</span>
              </div>
              <Progress value={overallProgress} className="h-2" />
            </div>

            {/* Security Notice */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 flex items-center gap-2">
              <Lock className="w-4 h-4 text-green-600 flex-shrink-0" />
              <p className="text-xs text-green-700">
                Verileriniz şifrelenerek sadece avukatınız tarafından görülebilir
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="max-w-md mx-auto space-y-3">

          {/* Photos */}
          <Card className={`border-0 shadow-lg transition-all ${completedSteps.photos ? 'bg-green-50 border-green-200' : ''}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${completedSteps.photos ? 'bg-green-100' : 'bg-blue-100'}`}>
                    {completedSteps.photos ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    ) : (
                      <Image className="w-6 h-6 text-blue-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">Fotoğraflar</h3>
                    <p className="text-xs text-gray-500">
                      {totalUploaded.photos > 0 ? `${totalUploaded.photos} fotoğraf yüklendi` : 'Tüm fotoğraflarınızı seçin'}
                    </p>
                  </div>
                </div>
                <Button
                  onClick={handlePhotoSelect}
                  disabled={uploading === 'photos'}
                  className={`${completedSteps.photos ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                >
                  {uploading === 'photos' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-1" />
                      {completedSteps.photos ? 'Daha Ekle' : 'Seç'}
                    </>
                  )}
                </Button>
              </div>
              {uploadProgress.photos > 0 && uploadProgress.photos < 100 && (
                <Progress value={uploadProgress.photos} className="h-1 mt-3" />
              )}
            </CardContent>
          </Card>

          {/* Videos */}
          <Card className={`border-0 shadow-lg transition-all ${completedSteps.videos ? 'bg-green-50 border-green-200' : ''}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${completedSteps.videos ? 'bg-green-100' : 'bg-purple-100'}`}>
                    {completedSteps.videos ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    ) : (
                      <Video className="w-6 h-6 text-purple-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">Videolar</h3>
                    <p className="text-xs text-gray-500">
                      {totalUploaded.videos > 0 ? `${totalUploaded.videos} video yüklendi` : 'Tüm videolarınızı seçin'}
                    </p>
                  </div>
                </div>
                <Button
                  onClick={handleVideoSelect}
                  disabled={uploading === 'videos'}
                  className={`${completedSteps.videos ? 'bg-green-600 hover:bg-green-700' : 'bg-purple-600 hover:bg-purple-700'}`}
                >
                  {uploading === 'videos' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-1" />
                      {completedSteps.videos ? 'Daha Ekle' : 'Seç'}
                    </>
                  )}
                </Button>
              </div>
              {uploadProgress.videos > 0 && uploadProgress.videos < 100 && (
                <Progress value={uploadProgress.videos} className="h-1 mt-3" />
              )}
            </CardContent>
          </Card>

          {/* WhatsApp */}
          <Card className={`border-0 shadow-lg transition-all ${completedSteps.whatsapp ? 'bg-green-50 border-green-200' : ''}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${completedSteps.whatsapp ? 'bg-green-100' : 'bg-green-100'}`}>
                    {completedSteps.whatsapp ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    ) : (
                      <MessageSquare className="w-6 h-6 text-green-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">WhatsApp</h3>
                    <p className="text-xs text-gray-500">Sohbet geçmişinizi gönderin</p>
                  </div>
                </div>
                <Button
                  onClick={handleWhatsAppShare}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Send className="w-4 h-4 mr-1" />
                  Gönder
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Telegram */}
          <Card className={`border-0 shadow-lg transition-all ${completedSteps.telegram ? 'bg-green-50 border-green-200' : ''}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${completedSteps.telegram ? 'bg-green-100' : 'bg-sky-100'}`}>
                    {completedSteps.telegram ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    ) : (
                      <Send className="w-6 h-6 text-sky-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">Telegram</h3>
                    <p className="text-xs text-gray-500">Sohbet geçmişinizi gönderin</p>
                  </div>
                </div>
                <Button
                  onClick={handleTelegramShare}
                  className="bg-sky-600 hover:bg-sky-700"
                >
                  <Send className="w-4 h-4 mr-1" />
                  Gönder
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Other Files */}
          <Card className={`border-0 shadow-lg transition-all ${completedSteps.files ? 'bg-green-50 border-green-200' : ''}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${completedSteps.files ? 'bg-green-100' : 'bg-orange-100'}`}>
                    {completedSteps.files ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    ) : (
                      <Folder className="w-6 h-6 text-orange-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">Diğer Dosyalar</h3>
                    <p className="text-xs text-gray-500">
                      {totalUploaded.files > 0 ? `${totalUploaded.files} dosya yüklendi` : 'PDF, belgeler, ses kayıtları...'}
                    </p>
                  </div>
                </div>
                <Button
                  onClick={handleFileSelect}
                  disabled={uploading === 'files'}
                  className={`${completedSteps.files ? 'bg-green-600 hover:bg-green-700' : 'bg-orange-600 hover:bg-orange-700'}`}
                >
                  {uploading === 'files' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-1" />
                      {completedSteps.files ? 'Daha Ekle' : 'Seç'}
                    </>
                  )}
                </Button>
              </div>
              {uploadProgress.files > 0 && uploadProgress.files < 100 && (
                <Progress value={uploadProgress.files} className="h-1 mt-3" />
              )}
            </CardContent>
          </Card>

          {/* Complete Button */}
          {overallProgress >= 20 && (
            <Button
              className="w-full h-14 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-lg mt-4"
              onClick={() => {
                toast.success('Verileriniz başarıyla gönderildi!');
                setStatus('completed');
              }}
            >
              <CheckCircle2 className="w-5 h-5 mr-2" />
              Tamamla ve Gönder
            </Button>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-white/60 text-xs mt-8">
          <p>© 2025 SafeChild Law Firm</p>
          <p className="mt-1">Verileriniz güvenle korunmaktadır</p>
        </div>
      </div>
    </div>
  );
};

export default MobileCollect;
