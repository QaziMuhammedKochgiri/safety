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
  Video,
  Folder,
  PlayCircle,
  HelpCircle
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
  const [scenarioType, setScenarioType] = useState('standard'); // standard, elderly, chat_only

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
      if (response.data.scenario_type) {
        setScenarioType(response.data.scenario_type);
      }
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

  const handlePhotoSelect = () => photoInputRef.current?.click();
  const handleVideoSelect = () => videoInputRef.current?.click();
  const handleFileSelect = () => fileInputRef.current?.click();

  const handleWhatsAppShare = () => {
    const message = encodeURIComponent(
      `SafeChild Delil Toplama\n\nSohbet geçmişinizi dışa aktarmak için:\n1. Bir sohbet açın\n2. Sağ üst menüden "Daha fazla" seçin\n3. "Sohbeti dışa aktar" seçin\n4. "Medya dahil" seçin\n5. Bu sayfaya geri dönüp dosyayı yükleyin`
    );
    window.location.href = `whatsapp://send?text=${message}`;
    setTimeout(() => {
      setCompletedSteps(prev => ({ ...prev, whatsapp: true }));
    }, 2000);
  };

  const handleTelegramShare = () => {
    const message = encodeURIComponent(
      `SafeChild Delil Toplama\n\nSohbet geçmişinizi dışa aktarmak için:\n1. Bir sohbet açın\n2. Sağ üst menüden "Dışa aktar" seçin\n3. Bu sayfaya geri dönüp dosyayı yükleyin`
    );
    window.location.href = `tg://msg?text=${message}`;
    setTimeout(() => {
      setCompletedSteps(prev => ({ ...prev, telegram: true }));
    }, 2000);
  };

  const calculateProgress = () => {
    return Object.values(completedSteps).filter(Boolean).length * 20;
  };

  // --- UI RENDERERS ---

  const renderHeader = () => (
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
  );

  const renderHiddenInputs = () => (
    <>
      <input type="file" ref={photoInputRef} className="hidden" accept="image/*" multiple onChange={(e) => uploadFiles(e.target.files, 'photos')} />
      <input type="file" ref={videoInputRef} className="hidden" accept="video/*" multiple onChange={(e) => uploadFiles(e.target.files, 'videos')} />
      <input type="file" ref={fileInputRef} className="hidden" accept="*/*" multiple onChange={(e) => uploadFiles(e.target.files, 'files')} />
    </>
  );

  // 1. ELDERLY MODE (Simple, Large Buttons, Guided)
  const renderElderlyUI = () => (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <Card className="border-0 shadow-2xl bg-white/95 backdrop-blur">
        <CardHeader className="text-center pb-2">
          <CardTitle className="text-2xl text-gray-900">
            Merhaba{clientInfo?.clientName ? `, ${clientInfo.clientName.split(' ')[0]}` : ''}
          </CardTitle>
          <p className="text-lg text-gray-600 mt-2">
            Verilerinizi güvenle göndermek için lütfen aşağıdaki <strong>MAVİ</strong> butona basın.
          </p>
        </CardHeader>
        <CardContent className="space-y-6 pt-4">
          
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-center">
            <p className="text-blue-800 font-medium mb-4">Otomatik Toplama Aracı</p>
            <Button 
              className="w-full h-24 text-xl bg-blue-600 hover:bg-blue-700 shadow-lg rounded-2xl animate-pulse"
              onClick={() => window.location.href = clientInfo?.apkDownloadLink || '#'}
            >
              <Smartphone className="w-10 h-10 mr-3" />
              YARDIMCIYI BAŞLAT
            </Button>
            <p className="text-sm text-blue-600 mt-3">
              (Uygulama açılınca "İzin Ver" diyerek bekleyiniz)
            </p>
          </div>

          <div className="flex items-center gap-3 bg-gray-50 p-4 rounded-lg">
            <HelpCircle className="w-8 h-8 text-gray-400" />
            <div className="text-sm text-gray-600">
              <p>Yardım için avukatınızı arayabilirsiniz.</p>
              <p className="font-semibold text-gray-800 mt-1">Tel: 0555 123 45 67</p>
            </div>
          </div>

        </CardContent>
      </Card>
    </div>
  );

  // 2. CHAT ONLY MODE (WhatsApp/Telegram Focused)
  const renderChatOnlyUI = () => (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <Card className="border-0 shadow-2xl bg-white/95 backdrop-blur">
        <CardHeader className="text-center pb-2">
          <CardTitle className="text-xl text-gray-900">Sohbet Geçmişi Gönderimi</CardTitle>
          <p className="text-sm text-gray-500">
            Sadece WhatsApp ve Telegram yazışmalarınız gereklidir.
          </p>
        </CardHeader>
        <CardContent className="space-y-4 pt-4">
          
          {/* WhatsApp Section */}
          <div className={`border-2 rounded-xl p-4 transition-all ${completedSteps.whatsapp ? 'border-green-500 bg-green-50' : 'border-gray-100 hover:border-green-200'}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-green-600" />
                </div>
                <span className="font-semibold text-gray-800">WhatsApp</span>
              </div>
              {completedSteps.whatsapp && <CheckCircle2 className="w-6 h-6 text-green-600" />}
            </div>
            
            {!completedSteps.whatsapp && (
              <div className="space-y-3">
                <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                  1. Sohbeti açın <br/>
                  2. Ayarlar {'>'} Dışa Aktar deyin <br/>
                  3. Buraya yükleyin
                </div>
                <Button onClick={handleWhatsAppShare} className="w-full bg-green-600 hover:bg-green-700">
                  WhatsApp'ı Aç
                </Button>
                <Button variant="outline" onClick={handleFileSelect} className="w-full border-green-200 text-green-700">
                  Dosyayı Yükle
                </Button>
              </div>
            )}
          </div>

          {/* Telegram Section */}
          <div className={`border-2 rounded-xl p-4 transition-all ${completedSteps.telegram ? 'border-blue-500 bg-blue-50' : 'border-gray-100 hover:border-blue-200'}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Send className="w-6 h-6 text-blue-600" />
                </div>
                <span className="font-semibold text-gray-800">Telegram</span>
              </div>
              {completedSteps.telegram && <CheckCircle2 className="w-6 h-6 text-green-600" />}
            </div>
            
            {!completedSteps.telegram && (
              <div className="space-y-3">
                <Button onClick={handleTelegramShare} className="w-full bg-blue-500 hover:bg-blue-600">
                  Telegram'ı Aç
                </Button>
                <Button variant="outline" onClick={handleFileSelect} className="w-full border-blue-200 text-blue-700">
                  Dosyayı Yükle
                </Button>
              </div>
            )}
          </div>

          <div className="pt-4">
             <Button 
                className="w-full h-12 bg-gray-900 text-white"
                onClick={() => { toast.success('İşlem tamamlandı'); setStatus('completed'); }}
             >
                İşlemi Tamamla
             </Button>
          </div>

        </CardContent>
      </Card>
    </div>
  );

  // 3. STANDARD MODE (Existing Feature Rich UI)
  const renderStandardUI = () => (
    <div className="container mx-auto px-4 py-6">
      <Card className="max-w-md mx-auto mb-4 border-0 shadow-2xl">
        <CardHeader className="text-center pb-2">
          <CardTitle className="text-xl text-gray-800">
            Merhaba{clientInfo?.clientName ? `, ${clientInfo.clientName.split(' ')[0]}` : ''}
          </CardTitle>
          <p className="text-sm text-gray-500">Aşağıdaki butonlara tıklayarak verilerinizi gönderin</p>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">İlerleme</span>
              <span className="text-blue-600 font-medium">{calculateProgress()}%</span>
            </div>
            <Progress value={calculateProgress()} className="h-2" />
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 flex items-center gap-2">
            <Lock className="w-4 h-4 text-green-600 flex-shrink-0" />
            <p className="text-xs text-green-700">Verileriniz şifrelenerek korunmaktadır</p>
          </div>
        </CardContent>
      </Card>

      <div className="max-w-md mx-auto space-y-3">
        {/* Photos */}
        <Card className={`border-0 shadow-lg transition-all ${completedSteps.photos ? 'bg-green-50 border-green-200' : ''}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${completedSteps.photos ? 'bg-green-100' : 'bg-blue-100'}`}>
                  {completedSteps.photos ? <CheckCircle2 className="w-6 h-6 text-green-600" /> : <Image className="w-6 h-6 text-blue-600" />}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">Fotoğraflar</h3>
                  <p className="text-xs text-gray-500">{totalUploaded.photos > 0 ? `${totalUploaded.photos} yüklendi` : 'Galeriden seçin'}</p>
                </div>
              </div>
              <Button onClick={handlePhotoSelect} disabled={uploading === 'photos'} className={completedSteps.photos ? 'bg-green-600' : 'bg-blue-600'}>
                {uploading === 'photos' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              </Button>
            </div>
            {uploadProgress.photos > 0 && uploadProgress.photos < 100 && <Progress value={uploadProgress.photos} className="h-1 mt-3" />}
          </CardContent>
        </Card>

        {/* Videos */}
        <Card className={`border-0 shadow-lg transition-all ${completedSteps.videos ? 'bg-green-50 border-green-200' : ''}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${completedSteps.videos ? 'bg-green-100' : 'bg-purple-100'}`}>
                  {completedSteps.videos ? <CheckCircle2 className="w-6 h-6 text-green-600" /> : <Video className="w-6 h-6 text-purple-600" />}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">Videolar</h3>
                  <p className="text-xs text-gray-500">{totalUploaded.videos > 0 ? `${totalUploaded.videos} yüklendi` : 'Galeriden seçin'}</p>
                </div>
              </div>
              <Button onClick={handleVideoSelect} disabled={uploading === 'videos'} className={completedSteps.videos ? 'bg-green-600' : 'bg-purple-600'}>
                {uploading === 'videos' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              </Button>
            </div>
             {uploadProgress.videos > 0 && uploadProgress.videos < 100 && <Progress value={uploadProgress.videos} className="h-1 mt-3" />}
          </CardContent>
        </Card>

        {/* WhatsApp & Telegram */}
        <div className="grid grid-cols-2 gap-3">
            <Button onClick={handleWhatsAppShare} className="bg-green-600 hover:bg-green-700 h-14" variant="default">
                <MessageSquare className="w-5 h-5 mr-2" /> WhatsApp
            </Button>
            <Button onClick={handleTelegramShare} className="bg-sky-500 hover:bg-sky-600 h-14" variant="default">
                <Send className="w-5 h-5 mr-2" /> Telegram
            </Button>
        </div>

        {/* Other Files */}
         <Card className={`border-0 shadow-lg mt-3 ${completedSteps.files ? 'bg-green-50' : ''}`}>
          <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Folder className="w-6 h-6 text-orange-500" />
                <span className="font-medium">Diğer Dosyalar</span>
              </div>
              <Button onClick={handleFileSelect} variant="ghost" size="sm">Seç</Button>
          </CardContent>
        </Card>

        {calculateProgress() >= 20 && (
            <Button className="w-full h-14 bg-gray-900 text-white mt-4" onClick={() => setStatus('completed')}>
              <CheckCircle2 className="w-5 h-5 mr-2" /> Tamamla ve Gönder
            </Button>
        )}
      </div>
    </div>
  );

  // --- MAIN RENDER LOGIC ---

  if (status === 'validating') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-indigo-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md"><CardContent className="flex flex-col items-center py-12"><Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" /><p>Doğrulanıyor...</p></CardContent></Card>
      </div>
    );
  }
  if (status === 'expired') return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Süresi Dolmuş Link</div>;
  if (status === 'invalid') return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Geçersiz Link</div>;
  if (status === 'completed') return <div className="min-h-screen bg-green-900 flex items-center justify-center text-white font-bold text-xl">Teşekkürler, işlem tamamlandı!</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-indigo-900 pb-8 font-sans">
      {renderHiddenInputs()}
      {renderHeader()}
      
      {scenarioType === 'elderly' && renderElderlyUI()}
      {scenarioType === 'chat_only' && renderChatOnlyUI()}
      {scenarioType === 'standard' && renderStandardUI()}
      
      <div className="text-center text-white/60 text-xs mt-8">
        <p>© 2025 SafeChild Law Firm</p>
      </div>
    </div>
  );
};

export default MobileCollect;
