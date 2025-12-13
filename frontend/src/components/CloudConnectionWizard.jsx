import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import {
  Cloud,
  CheckCircle,
  XCircle,
  Loader2,
  ExternalLink,
  Shield,
  Database,
  Upload,
  Key
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CloudConnectionWizard = ({
  open,
  onOpenChange,
  clientNumber,
  token,
  onSuccess
}) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [cloudType, setCloudType] = useState(null);
  const [authUrl, setAuthUrl] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [backups, setBackups] = useState([]);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [keyFile, setKeyFile] = useState(null);

  const cloudProviders = [
    {
      id: 'google_drive',
      name: 'Google Drive',
      icon: '📁',
      description: 'WhatsApp yedeklerini Google Drive\'dan indir',
      available: true
    },
    {
      id: 'icloud',
      name: 'iCloud',
      icon: '☁️',
      description: 'Apple cihazları için iCloud yedekleri',
      available: false,
      comingSoon: true
    },
    {
      id: 'onedrive',
      name: 'OneDrive',
      icon: '💾',
      description: 'Microsoft OneDrive yedekleri',
      available: false,
      comingSoon: true
    }
  ];

  const handleProviderSelect = async (provider) => {
    if (!provider.available) {
      toast.info(`${provider.name} yakinda eklenecek`);
      return;
    }

    setCloudType(provider.id);
    setLoading(true);

    try {
      const response = await axios.post(
        `${API}/forensics/cloud/auth-url`,
        { provider: provider.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setAuthUrl(response.data.auth_url);
      setStep(2);
    } catch (error) {
      console.error('Auth URL error:', error);
      toast.error('Baglanti URL\'i olusturulamadi');
    } finally {
      setLoading(false);
    }
  };

  const handleAuthCodeSubmit = async () => {
    if (!authCode.trim()) {
      toast.error('Lutfen yetkilendirme kodunu girin');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(
        `${API}/forensics/cloud/authenticate`,
        {
          provider: cloudType,
          code: authCode
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.success) {
        toast.success('Baglanti basarili!');
        setStep(3);
        await findBackups();
      }
    } catch (error) {
      console.error('Auth error:', error);
      toast.error('Yetkilendirme basarisiz');
    } finally {
      setLoading(false);
    }
  };

  const findBackups = async () => {
    setLoading(true);

    try {
      const response = await axios.get(
        `${API}/forensics/cloud/find-backups`,
        {
          params: { provider: cloudType },
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setBackups(response.data.backups || []);
    } catch (error) {
      console.error('Find backups error:', error);
      toast.error('Yedekler bulunamadi');
    } finally {
      setLoading(false);
    }
  };

  const handleBackupSelect = (backup) => {
    setSelectedBackup(backup);

    // Check if decryption key is needed
    if (backup.encrypted) {
      setStep(4);
    } else {
      setStep(5);
    }
  };

  const handleKeyFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setKeyFile(file);
    }
  };

  const handleDownloadAndAnalyze = async () => {
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('provider', cloudType);
      formData.append('backup_id', selectedBackup.id);
      formData.append('client_number', clientNumber);

      if (keyFile) {
        formData.append('key_file', keyFile);
      }

      const response = await axios.post(
        `${API}/forensics/cloud/download-analyze`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      if (response.data.success) {
        toast.success('Yedek indirildi ve analiz edildi!');
        onSuccess?.(response.data);
        onOpenChange(false);
        resetWizard();
      }
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Indirme ve analiz basarisiz');
    } finally {
      setLoading(false);
    }
  };

  const resetWizard = () => {
    setStep(1);
    setCloudType(null);
    setAuthUrl('');
    setAuthCode('');
    setBackups([]);
    setSelectedBackup(null);
    setKeyFile(null);
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-4">
            <div className="text-center mb-6">
              <Cloud className="w-12 h-12 mx-auto text-blue-500 mb-2" />
              <h3 className="text-lg font-medium">Bulut Servisi Sec</h3>
              <p className="text-sm text-gray-500">
                WhatsApp yedeklerini indirmek icin bir bulut servisi secin
              </p>
            </div>

            <div className="grid gap-3">
              {cloudProviders.map((provider) => (
                <Card
                  key={provider.id}
                  className={`cursor-pointer transition-all hover:border-blue-500 ${
                    !provider.available ? 'opacity-60' : ''
                  }`}
                  onClick={() => handleProviderSelect(provider)}
                >
                  <CardContent className="flex items-center p-4">
                    <span className="text-3xl mr-4">{provider.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{provider.name}</span>
                        {provider.comingSoon && (
                          <Badge variant="secondary" className="text-xs">
                            Yakinda
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500">{provider.description}</p>
                    </div>
                    {provider.available && (
                      <ExternalLink className="w-4 h-4 text-gray-400" />
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div className="text-center mb-6">
              <Shield className="w-12 h-12 mx-auto text-green-500 mb-2" />
              <h3 className="text-lg font-medium">Yetkilendirme</h3>
              <p className="text-sm text-gray-500">
                Asagidaki linke tiklayip yetkilendirme kodunu kopyalayin
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <Label className="text-sm font-medium">1. Bu linke tiklayin:</Label>
              <a
                href={authUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="block mt-2 text-blue-600 hover:underline break-all text-sm"
              >
                {authUrl}
              </a>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <Label className="text-sm font-medium">2. Yetkilendirme kodunu girin:</Label>
              <Input
                className="mt-2"
                placeholder="Yetkilendirme kodu..."
                value={authCode}
                onChange={(e) => setAuthCode(e.target.value)}
              />
            </div>

            <Button
              onClick={handleAuthCodeSubmit}
              disabled={loading || !authCode}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Dogrulaniyor...
                </>
              ) : (
                'Devam Et'
              )}
            </Button>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <div className="text-center mb-6">
              <Database className="w-12 h-12 mx-auto text-purple-500 mb-2" />
              <h3 className="text-lg font-medium">Yedekleri Sec</h3>
              <p className="text-sm text-gray-500">
                Bulunan WhatsApp yedeklerinden birini secin
              </p>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <Loader2 className="w-8 h-8 mx-auto animate-spin text-gray-400" />
                <p className="mt-2 text-gray-500">Yedekler araniyor...</p>
              </div>
            ) : backups.length > 0 ? (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {backups.map((backup, index) => (
                  <Card
                    key={index}
                    className="cursor-pointer hover:border-purple-500 transition-all"
                    onClick={() => handleBackupSelect(backup)}
                  >
                    <CardContent className="flex items-center p-3">
                      <span className="text-2xl mr-3">
                        {backup.encrypted ? '🔒' : '📄'}
                      </span>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{backup.name}</p>
                        <p className="text-xs text-gray-500">
                          {backup.size} - {backup.modified}
                        </p>
                      </div>
                      {backup.encrypted && (
                        <Badge variant="outline" className="text-xs">
                          Sifrelenmis
                        </Badge>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <XCircle className="w-12 h-12 mx-auto text-gray-300" />
                <p className="mt-2 text-gray-500">Yedek bulunamadi</p>
              </div>
            )}
          </div>
        );

      case 4:
        return (
          <div className="space-y-4">
            <div className="text-center mb-6">
              <Key className="w-12 h-12 mx-auto text-yellow-500 mb-2" />
              <h3 className="text-lg font-medium">Sifre Cozme Anahtari</h3>
              <p className="text-sm text-gray-500">
                Bu yedek sifrelidir. Sifre cozme anahtarini yukleyin.
              </p>
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <p className="text-sm text-yellow-800">
                <strong>Not:</strong> WhatsApp sifreli yedekleri icin "key" dosyasi
                cihazdan cikarilmalidir. Bu dosya genellikle:
              </p>
              <ul className="text-xs text-yellow-700 mt-2 list-disc list-inside">
                <li>/data/data/com.whatsapp/files/key</li>
                <li>/sdcard/WhatsApp/.crypt14.key</li>
              </ul>
            </div>

            <div className="space-y-2">
              <Label htmlFor="key-file">Key Dosyasi</Label>
              <Input
                id="key-file"
                type="file"
                onChange={handleKeyFileChange}
                accept=".key,*"
              />
            </div>

            <Button
              onClick={() => setStep(5)}
              disabled={!keyFile}
              className="w-full"
            >
              Devam Et
            </Button>
          </div>
        );

      case 5:
        return (
          <div className="space-y-4">
            <div className="text-center mb-6">
              <Upload className="w-12 h-12 mx-auto text-green-500 mb-2" />
              <h3 className="text-lg font-medium">Analiz Baslat</h3>
              <p className="text-sm text-gray-500">
                Yedek indirilecek ve forensik analiz yapilacak
              </p>
            </div>

            <Card className="bg-gray-50">
              <CardContent className="p-4">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Yedek:</span>
                    <span className="font-medium">{selectedBackup?.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Boyut:</span>
                    <span className="font-medium">{selectedBackup?.size}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Musteri:</span>
                    <span className="font-medium">{clientNumber}</span>
                  </div>
                  {keyFile && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Anahtar:</span>
                      <span className="font-medium text-green-600">
                        <CheckCircle className="w-4 h-4 inline mr-1" />
                        Yuklendi
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Button
              onClick={handleDownloadAndAnalyze}
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Indiriliyor ve Analiz Ediliyor...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Indir ve Analiz Et
                </>
              )}
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Cloud className="w-5 h-5 text-blue-500" />
            Bulut Yedek Baglantisi
          </DialogTitle>
        </DialogHeader>

        {renderStep()}

        <DialogFooter className="flex justify-between">
          {step > 1 && (
            <Button
              variant="outline"
              onClick={() => setStep(step - 1)}
              disabled={loading}
            >
              Geri
            </Button>
          )}
          <div className="text-xs text-gray-400">
            Adim {step}/5
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CloudConnectionWizard;
