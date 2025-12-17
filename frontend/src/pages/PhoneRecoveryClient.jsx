import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Input } from '../components/ui/input';
import {
  Smartphone, Upload, CheckCircle, AlertCircle, Loader2,
  Download, Shield, Clock, FileArchive, Apple, Bot,
  HelpCircle, RefreshCw, Monitor, Usb, Wifi, Lock,
  Play, ExternalLink, Copy, Check
} from 'lucide-react';
import WebUSBRecoveryAgent from '../components/WebUSBRecoveryAgent';

const API_BASE = '/api';

const PhoneRecoveryClient = () => {
  const { code } = useParams();
  const navigate = useNavigate();

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [caseData, setCaseData] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [screenLockCode, setScreenLockCode] = useState('');
  const [copied, setCopied] = useState(false);

  // Detect if user is on mobile
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  const isAndroid = /Android/i.test(navigator.userAgent);
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);

  // Validate recovery code on mount
  useEffect(() => {
    validateCode();
  }, [code]);

  // Poll for status when processing
  useEffect(() => {
    let interval;
    if (caseData?.status === 'processing' || caseData?.status === 'backup_ready') {
      interval = setInterval(fetchStatus, 5000);
    }
    return () => clearInterval(interval);
  }, [caseData?.status]);

  const validateCode = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE}/recovery/validate/${code}`);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 410) {
          setError('Bu kurtarma linki suresi dolmus. Lutfen avukatinizdan yeni bir link isteyin.');
        } else if (response.status === 404) {
          setError('Gecersiz kurtarma kodu. Lutfen linki kontrol edin ve tekrar deneyin.');
        } else {
          setError(data.detail || 'Kurtarma kodu dogrulanamadi.');
        }
        return;
      }

      setCaseData(data);
      determineStep(data);
    } catch (err) {
      setError('Baglanti hatasi. Lutfen internet baglantinizi kontrol edin.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/recovery/status/${code}`);
      if (response.ok) {
        const data = await response.json();
        setProcessingStatus(data);

        if (data.status === 'completed') {
          setCaseData(prev => ({ ...prev, status: 'completed' }));
          setCurrentStep(5);
        } else if (data.status === 'failed') {
          setError('Islem basarisiz oldu. Lutfen destekle iletisime gecin.');
        }
      }
    } catch (err) {
      console.error('Status fetch error:', err);
    }
  };

  const determineStep = (data) => {
    switch (data.status) {
      case 'pending':
        setCurrentStep(1); // Welcome & device detection
        break;
      case 'awaiting_passcode':
        setCurrentStep(2);
        break;
      case 'backup_ready':
      case 'processing':
        setCurrentStep(4);
        break;
      case 'completed':
        setCurrentStep(5);
        break;
      default:
        setCurrentStep(1);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(percent);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          setCaseData(prev => ({ ...prev, status: 'processing' }));
          setCurrentStep(4);
        } else {
          setError('Yukleme basarisiz. Lutfen tekrar deneyin.');
        }
        setUploading(false);
      });

      xhr.addEventListener('error', () => {
        setError('Yukleme basarisiz. Internet baglantinizi kontrol edin.');
        setUploading(false);
      });

      xhr.open('POST', `${API_BASE}/recovery/upload-backup/${code}`);
      xhr.send(formData);

    } catch (err) {
      setError('Yukleme hatasi: ' + err.message);
      setUploading(false);
    }
  };

  const handleStartRecovery = async () => {
    if (screenLockCode.length < 4) {
      setError('Ekran kilidi kodu en az 4 karakter olmalidir.');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/recovery/start-agent/${code}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          screen_lock: screenLockCode,
          is_mobile: isMobile,
          platform: isAndroid ? 'android' : isIOS ? 'ios' : 'desktop'
        })
      });

      if (response.ok) {
        setCurrentStep(4);
      } else {
        const data = await response.json();
        setError(data.detail || 'Islem baslatilamadi.');
      }
    } catch (err) {
      setError('Baglanti hatasi: ' + err.message);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Device type: use detected type if "auto", otherwise use case data
  const deviceType = caseData?.device_type === 'auto'
    ? (isAndroid ? 'android' : isIOS ? 'ios' : 'android')
    : (caseData?.device_type || 'android');
  const isTargetAndroid = deviceType === 'android';

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Kurtarma linki dogrulaniyor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-800 mb-2">Hata</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button onClick={() => { setError(null); validateCode(); }} variant="outline">
              Tekrar Dene
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg">
                <Smartphone className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Telefon Veri Kurtarma</h1>
                <p className="text-sm text-gray-500">SafeChild Guvenli Portal</p>
              </div>
            </div>
            <Badge variant="outline" className="text-blue-600 border-blue-200">
              <Shield className="w-3 h-3 mr-1" />
              Sifreli
            </Badge>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-3xl">
        {/* Step Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center gap-2">
            {[1, 2, 3, 4, 5].map((step) => (
              <React.Fragment key={step}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  currentStep >= step
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-400'
                }`}>
                  {currentStep > step ? <CheckCircle className="w-4 h-4" /> : step}
                </div>
                {step < 5 && (
                  <div className={`w-8 h-1 ${currentStep > step ? 'bg-blue-600' : 'bg-gray-200'}`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Step 1: Welcome & Scenario Selection */}
        {currentStep === 1 && (
          <Card>
            <CardHeader className="text-center">
              <div className={`w-20 h-20 mx-auto mb-4 rounded-2xl flex items-center justify-center ${
                isTargetAndroid ? 'bg-green-100' : 'bg-gray-100'
              }`}>
                {isTargetAndroid ? <Bot className="w-10 h-10 text-green-600" /> : <Apple className="w-10 h-10 text-gray-600" />}
              </div>
              <CardTitle className="text-2xl">
                {isTargetAndroid ? 'Android' : 'iOS'} Veri Kurtarma
              </CardTitle>
              <CardDescription>
                Avukatiniz bu linki size gonderdi. Telefonunuzdaki verileri guvenli sekilde kurtaracagiz.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Scenario Selection */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-800 text-center">Nasil devam etmek istersiniz?</h3>

                {/* Scenario 1: Has Computer */}
                <div
                  className="p-4 border-2 rounded-xl cursor-pointer hover:border-blue-500 transition-all"
                  onClick={() => setCurrentStep(2)}
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Monitor className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-800">Bilgisayarim Var</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Telefonunuzu USB kablosu ile bilgisayariniza baglayarak veri aktarimi yapilacak.
                      </p>
                      <div className="flex items-center gap-2 mt-2 text-xs text-blue-600">
                        <Usb className="w-4 h-4" />
                        <span>USB + Bilgisayar gerekli</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scenario 2: Mobile Only */}
                <div
                  className="p-4 border-2 rounded-xl cursor-pointer hover:border-purple-500 transition-all"
                  onClick={() => setCurrentStep(3)}
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <Wifi className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-800">Sadece Telefonum Var (Kablosuz)</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Bilgisayara gerek yok. Dogrudan telefonunuzdan islem yapilacak.
                      </p>
                      <div className="flex items-center gap-2 mt-2 text-xs text-purple-600">
                        <Smartphone className="w-4 h-4" />
                        <span>Sadece telefon yeterli</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <Alert>
                <Shield className="w-4 h-4" />
                <AlertDescription>
                  Tum verileriniz sifrelenerek aktarilir ve 15 gun sonra otomatik olarak silinir.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        )}

        {/* Step 2: With Computer (USB) Instructions */}
        {currentStep === 2 && (
          <Card>
            <CardHeader className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-2xl flex items-center justify-center">
                <Usb className="w-8 h-8 text-blue-600" />
              </div>
              <CardTitle className="text-2xl">USB ile Baglanti</CardTitle>
              <CardDescription>
                {isTargetAndroid
                  ? 'Telefonunuzu bilgisayariniza baglayin ve asagidaki butona tiklayin'
                  : 'Asagidaki adimlari takip edin'
                }
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {isTargetAndroid ? (
                <>
                  {/* WebUSB supported browser check */}
                  {!navigator.usb ? (
                    <Alert variant="destructive">
                      <AlertCircle className="w-4 h-4" />
                      <AlertDescription>
                        Bu tarayici WebUSB desteklemiyor. Lutfen <strong>Google Chrome</strong> veya <strong>Microsoft Edge</strong> kullanin.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <>
                      {/* Prerequisites */}
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-semibold text-gray-800 mb-3">Oncelikle:</h3>
                        <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
                          <li>
                            <strong>USB Hata Ayiklamayi Acin:</strong>
                            <p className="ml-5 text-gray-600">Ayarlar &gt; Gelistirici Secenekleri &gt; USB Hata Ayiklama</p>
                          </li>
                          <li>
                            <strong>Telefonu USB ile Bilgisayara Baglayin</strong>
                          </li>
                          <li>
                            <strong>Telefonda "USB Hata Ayiklamaya Izin Ver" diyalogunu onaylayin</strong>
                          </li>
                        </ol>
                      </div>

                      {/* WebUSB Recovery Agent */}
                      <WebUSBRecoveryAgent
                        recoveryCode={code}
                        onComplete={(stats) => {
                          setProcessingStatus({ statistics: stats, status: 'completed' });
                          setCurrentStep(5);
                        }}
                        onError={(error) => setError(error)}
                      />
                    </>
                  )}

                  <div className="flex gap-3">
                    <Button variant="outline" onClick={() => setCurrentStep(1)} className="flex-1">
                      Geri
                    </Button>
                  </div>
                </>
              ) : (
                <div className="space-y-4">
                  <Alert className="bg-yellow-50 border-yellow-200">
                    <AlertCircle className="w-4 h-4 text-yellow-600" />
                    <AlertDescription className="text-yellow-800">
                      iOS cihazlar icin iTunes/Finder backup olusturmaniz gerekmektedir.
                    </AlertDescription>
                  </Alert>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-800 mb-3">iTunes Backup Olusturma:</h3>
                    <ol className="list-decimal list-inside space-y-3 text-sm text-gray-700">
                      <li>iPhone'u bilgisayariniza baglayin</li>
                      <li>iTunes (Windows) veya Finder (Mac) acin</li>
                      <li>Cihazinizi secin</li>
                      <li><strong>"Yerel yedeklemeyi sifrele" secenegini KAPATIN</strong></li>
                      <li>"Simdi Yedekle" tiklayin</li>
                      <li>Yedekleme tamamlaninca backup klasorunu ZIP'leyin</li>
                    </ol>
                  </div>

                  <Button onClick={() => setCurrentStep('upload')} className="w-full h-12">
                    Backup Dosyasini Yukle
                  </Button>

                  <div className="flex gap-3">
                    <Button variant="outline" onClick={() => setCurrentStep(1)} className="flex-1">
                      Geri
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Step 3: Mobile Only (Plugless) */}
        {currentStep === 3 && (
          <Card>
            <CardHeader className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-2xl flex items-center justify-center">
                <Wifi className="w-8 h-8 text-purple-600" />
              </div>
              <CardTitle className="text-2xl">Kablosuz Kurtarma</CardTitle>
              <CardDescription>
                Ekran kilidini girin ve islemi baslatin
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {isTargetAndroid ? (
                <>
                  {/* Android APK Flow */}
                  <Alert className="bg-green-50 border-green-200">
                    <Bot className="w-4 h-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      Android cihaziniz icin SafeChild Recovery uygulamasini indirmeniz gerekmektedir.
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-800 mb-3">Ekran Kilidi Kodunuz</h3>
                      <p className="text-sm text-gray-600 mb-3">
                        Telefonunuzun ekran kilidini acmak icin kullandiginiz PIN veya sifre:
                      </p>
                      <Input
                        type="password"
                        placeholder="PIN veya Sifre"
                        value={screenLockCode}
                        onChange={(e) => setScreenLockCode(e.target.value)}
                        className="text-center text-xl tracking-widest"
                      />
                    </div>

                    <Button
                      className="w-full h-14 text-lg bg-gradient-to-r from-green-500 to-emerald-600"
                      onClick={() => {
                        // Trigger APK download
                        window.location.href = '/download/safechild-recovery.apk';
                      }}
                    >
                      <Download className="w-5 h-5 mr-2" />
                      SafeChild Recovery APK Indir
                    </Button>

                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <h4 className="font-semibold text-blue-800 mb-2">Kurulum Sonrasi:</h4>
                      <ol className="list-decimal list-inside space-y-1 text-sm text-blue-700">
                        <li>APK'yi yukleyin (Bilinmeyen kaynaklara izin verin)</li>
                        <li>Uygulamayi acin</li>
                        <li>Istenen tum izinleri verin</li>
                        <li>Kurtarma kodunu girin: <strong>{code}</strong></li>
                        <li>"Baslat" butonuna basin</li>
                      </ol>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* iOS MDM Flow */}
                  <Alert className="bg-gray-100 border-gray-300">
                    <Apple className="w-4 h-4 text-gray-600" />
                    <AlertDescription className="text-gray-700">
                      iOS icin MDM profili kurulumu gerekmektedir.
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-800 mb-3">Ekran Kilidi Kodunuz</h3>
                      <Input
                        type="password"
                        placeholder="iPhone PIN veya Sifre"
                        value={screenLockCode}
                        onChange={(e) => setScreenLockCode(e.target.value)}
                        className="text-center text-xl tracking-widest"
                      />
                    </div>

                    <Button
                      className="w-full h-14 text-lg"
                      onClick={() => {
                        // Trigger MDM profile download
                        window.location.href = `${API_BASE}/recovery/ios-profile/${code}`;
                      }}
                    >
                      <Download className="w-5 h-5 mr-2" />
                      MDM Profili Kur
                    </Button>

                    <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                      <h4 className="font-semibold text-yellow-800 mb-2">Onemli:</h4>
                      <p className="text-sm text-yellow-700">
                        Profil kurulduktan sonra Ayarlar &gt; Genel &gt; Profiller bolumunden
                        SafeChild profilini onaylamaniz gerekmektedir.
                      </p>
                    </div>
                  </div>
                </>
              )}

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setCurrentStep(1)} className="flex-1">
                  Geri
                </Button>
                <Button onClick={handleStartRecovery} className="flex-1">
                  <Play className="w-4 h-4 mr-2" />
                  Islemi Baslat
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Upload Step (for iOS backup) */}
        {currentStep === 'upload' && (
          <Card>
            <CardHeader className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-2xl flex items-center justify-center">
                <Upload className="w-8 h-8 text-blue-600" />
              </div>
              <CardTitle className="text-2xl">Backup Yukle</CardTitle>
              <CardDescription>
                iTunes backup ZIP dosyasini secin
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                  uploadFile ? 'border-green-500 bg-green-50' : 'border-gray-300 hover:border-blue-500'
                }`}
              >
                {uploadFile ? (
                  <div>
                    <FileArchive className="w-12 h-12 text-green-600 mx-auto mb-3" />
                    <p className="font-semibold text-gray-800">{uploadFile.name}</p>
                    <p className="text-sm text-gray-500">
                      {(uploadFile.size / (1024 * 1024 * 1024)).toFixed(2)} GB
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      onClick={() => setUploadFile(null)}
                    >
                      Farkli Dosya Sec
                    </Button>
                  </div>
                ) : (
                  <div>
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 mb-2">Dosyayi buraya surukleyin veya</p>
                    <label className="cursor-pointer">
                      <span className="text-blue-600 hover:underline">dosya secin</span>
                      <input
                        type="file"
                        className="hidden"
                        accept=".zip"
                        onChange={handleFileSelect}
                      />
                    </label>
                  </div>
                )}
              </div>

              {uploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Yukleniyor...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              )}

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setCurrentStep(2)} className="flex-1">
                  Geri
                </Button>
                <Button
                  onClick={handleUpload}
                  disabled={!uploadFile || uploading}
                  className="flex-1"
                >
                  {uploading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                  {uploading ? 'Yukleniyor...' : 'Yukle'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Processing */}
        {currentStep === 4 && (
          <Card>
            <CardHeader className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-2xl flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              </div>
              <CardTitle className="text-2xl">Veriler Isleniyor</CardTitle>
              <CardDescription>
                Verileriniz toplanip isleniyor
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600 mb-2">
                  {processingStatus?.progress_percent || 0}%
                </div>
                <Progress value={processingStatus?.progress_percent || 0} className="h-3 mb-2" />
                <p className="text-sm text-gray-600">
                  {processingStatus?.current_step || 'Baslatiliyor...'}
                </p>
              </div>

              <Alert>
                <Clock className="w-4 h-4" />
                <AlertDescription>
                  Bu islem 30 dakika ile birkac saat arasinda surebilir.
                  Sayfayi kapatabilirsiniz - islem tamamlandiginda avukatiniz bilgilendirilecek.
                </AlertDescription>
              </Alert>

              <Button variant="outline" onClick={fetchStatus} className="w-full">
                <RefreshCw className="w-4 h-4 mr-2" />
                Durumu Yenile
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 5: Complete */}
        {currentStep === 5 && (
          <Card className="border-green-200 bg-green-50">
            <CardHeader className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-2xl flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl text-green-800">Kurtarma Tamamlandi!</CardTitle>
              <CardDescription className="text-green-700">
                Verileriniz basariyla kurtarildi
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {processingStatus?.statistics && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-blue-600">{processingStatus.statistics.photos}</p>
                    <p className="text-sm text-gray-600">Foto</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-purple-600">{processingStatus.statistics.videos}</p>
                    <p className="text-sm text-gray-600">Video</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-green-600">{processingStatus.statistics.messages}</p>
                    <p className="text-sm text-gray-600">Mesaj</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-red-600">{processingStatus.statistics.deleted_files}</p>
                    <p className="text-sm text-gray-600">Silinen Dosya</p>
                  </div>
                </div>
              )}

              <Alert>
                <Shield className="w-4 h-4" />
                <AlertDescription>
                  Avukatiniz bilgilendirildi ve sizinle en kisa surede iletisime gececek.
                  Tum veriler 15 gun sonra otomatik olarak silinecektir.
                </AlertDescription>
              </Alert>

              <Button onClick={() => navigate('/')} variant="outline" className="w-full">
                Ana Sayfaya Don
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Yardim icin: support@safechild.mom</p>
          <p className="mt-1">
            <Shield className="w-3 h-3 inline mr-1" />
            Tum veriler sifrelenmektedir
          </p>
        </div>
      </div>
    </div>
  );
};

export default PhoneRecoveryClient;
