import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Checkbox } from '../components/ui/checkbox';
import { Input } from '../components/ui/input';
import {
  Smartphone, ArrowLeft, Usb, Wifi, Apple, Bot,
  Lock, Scan, Download, CheckCircle, AlertCircle,
  Loader2, Image, MessageSquare, Users, Phone,
  Trash2, MapPin, Package, Info, Zap, Shield
} from 'lucide-react';

const AdminPhoneRecovery = () => {
  const { language } = useLanguage();
  const navigate = useNavigate();

  // State
  const [selectedMethod, setSelectedMethod] = useState(null); // 'usb-android', 'usb-ios', 'wireless-android', 'wireless-ios'
  const [currentStep, setCurrentStep] = useState(1); // 1: Select method, 2: Connect/Get passcode, 3: Scan, 4: Results
  const [passcode, setPasscode] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [deviceConnected, setDeviceConnected] = useState(false);
  const [scanComplete, setScanComplete] = useState(false);

  // Recovery options
  const [recoveryOptions, setRecoveryOptions] = useState({
    photos: true,
    messages: true,
    contacts: true,
    callLogs: true,
    deletedData: true,
    location: true,
    apps: true
  });

  // Mock results
  const [results, setResults] = useState({
    photos: 1247,
    videos: 89,
    messages: 5632,
    whatsapp: 3421,
    telegram: 892,
    sms: 1319,
    contacts: 247,
    callLogs: 1893,
    deletedPhotos: 342,
    deletedMessages: 1021,
    locations: 4567,
    apps: 87
  });

  const recoveryMethods = [
    {
      id: 'usb',
      title: language === 'de' ? 'USB Verbindung' : 'USB Connected',
      description: language === 'de'
        ? 'Telefon per USB-Kabel an Computer anschließen'
        : 'Connect phone via USB cable to computer',
      icon: Usb,
      color: 'from-orange-500 to-red-500',
      options: [
        { id: 'usb-android', label: 'Android', icon: Bot },
        { id: 'usb-ios', label: 'iOS', icon: Apple }
      ]
    },
    {
      id: 'wireless',
      title: language === 'de' ? 'Kabellos / Plugless' : 'Wireless / Plugless',
      description: language === 'de'
        ? 'Ohne Kabel - Nur Bildschirmsperre erforderlich'
        : 'No cable needed - Screen lock passcode only',
      icon: Wifi,
      color: 'from-blue-500 to-purple-500',
      options: [
        { id: 'wireless-android', label: 'Android', icon: Bot },
        { id: 'wireless-ios', label: 'iOS', icon: Apple }
      ]
    }
  ];

  const dataCategories = [
    {
      id: 'photos',
      label: language === 'de' ? 'Fotos & Videos' : 'Photos & Videos',
      icon: Image,
      count: results.photos + results.videos,
      deleted: results.deletedPhotos
    },
    {
      id: 'messages',
      label: language === 'de' ? 'Nachrichten (WhatsApp, Telegram, SMS)' : 'Messages (WhatsApp, Telegram, SMS)',
      icon: MessageSquare,
      count: results.messages,
      deleted: results.deletedMessages
    },
    {
      id: 'contacts',
      label: language === 'de' ? 'Kontakte' : 'Contacts',
      icon: Users,
      count: results.contacts,
      deleted: 0
    },
    {
      id: 'callLogs',
      label: language === 'de' ? 'Anrufliste' : 'Call History',
      icon: Phone,
      count: results.callLogs,
      deleted: 0
    },
    {
      id: 'deletedData',
      label: language === 'de' ? 'Gelöschte Daten Wiederherstellung' : 'Deleted Data Recovery',
      icon: Trash2,
      count: results.deletedPhotos + results.deletedMessages,
      deleted: results.deletedPhotos + results.deletedMessages
    },
    {
      id: 'location',
      label: language === 'de' ? 'Standortverlauf' : 'Location History',
      icon: MapPin,
      count: results.locations,
      deleted: 0
    },
    {
      id: 'apps',
      label: language === 'de' ? 'Apps & Daten' : 'Apps & Data',
      icon: Package,
      count: results.apps,
      deleted: 0
    }
  ];

  const handleMethodSelect = (methodId) => {
    setSelectedMethod(methodId);
    setCurrentStep(2);
  };

  const handleConnect = () => {
    if (selectedMethod?.startsWith('usb')) {
      // Simulate USB connection
      setDeviceConnected(true);
      setTimeout(() => setCurrentStep(3), 1500);
    } else {
      // Wireless - need passcode first
      if (passcode.length >= 4) {
        setDeviceConnected(true);
        setTimeout(() => setCurrentStep(3), 1500);
      }
    }
  };

  const handleStartScan = () => {
    setScanning(true);
    setScanProgress(0);

    // Simulate scanning progress
    const interval = setInterval(() => {
      setScanProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setScanning(false);
          setScanComplete(true);
          setCurrentStep(4);
          return 100;
        }
        return prev + 2;
      });
    }, 100);
  };

  const handleDownloadResults = () => {
    alert(language === 'de'
      ? 'Download-Funktion wird in der vollständigen Version verfügbar sein'
      : 'Download functionality will be available in full version');
  };

  const resetFlow = () => {
    setSelectedMethod(null);
    setCurrentStep(1);
    setPasscode('');
    setScanning(false);
    setScanProgress(0);
    setDeviceConnected(false);
    setScanComplete(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate('/admin')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Zurück' : 'Back'}
              </Button>
              <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
                  <Smartphone className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-800">
                    {language === 'de' ? 'Telefon Datenwiederherstellung' : 'Phone Data Recovery'}
                  </h1>
                  <p className="text-sm text-gray-500">
                    {language === 'de'
                      ? 'Vollständige Datenextraktion & Wiederherstellung'
                      : 'Complete data extraction & recovery'}
                  </p>
                </div>
              </div>
            </div>
            {currentStep > 1 && (
              <Button variant="outline" onClick={resetFlow}>
                {language === 'de' ? 'Neustart' : 'Reset'}
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Beta Warning */}
        <Alert className="mb-6 border-2 border-yellow-200 bg-yellow-50">
          <AlertCircle className="h-5 w-5 text-yellow-600" />
          <AlertDescription className="text-yellow-800 font-medium">
            <div className="flex items-center justify-between">
              <span>
                {language === 'de'
                  ? '🚧 BETA - Vollständige Funktionalität in Entwicklung. Erwartete Veröffentlichung: Q2 2025'
                  : '🚧 BETA - Full functionality under development. Expected release: Q2 2025'}
              </span>
              <Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-300">
                PLACEHOLDER
              </Badge>
            </div>
          </AlertDescription>
        </Alert>

        {/* Step Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center gap-4">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full font-semibold ${
                  currentStep >= step
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-400'
                }`}>
                  {step}
                </div>
                {step < 4 && (
                  <div className={`w-16 h-1 ${
                    currentStep > step ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-center gap-16 mt-2">
            <span className="text-xs text-gray-600">{language === 'de' ? 'Methode' : 'Method'}</span>
            <span className="text-xs text-gray-600">{language === 'de' ? 'Verbinden' : 'Connect'}</span>
            <span className="text-xs text-gray-600">{language === 'de' ? 'Scannen' : 'Scan'}</span>
            <span className="text-xs text-gray-600">{language === 'de' ? 'Ergebnisse' : 'Results'}</span>
          </div>
        </div>

        {/* STEP 1: Select Method */}
        {currentStep === 1 && (
          <div className="grid md:grid-cols-2 gap-6">
            {recoveryMethods.map((method) => (
              <Card key={method.id} className="border-2 hover:border-blue-500 transition-all">
                <CardHeader>
                  <div className={`w-16 h-16 bg-gradient-to-br ${method.color} rounded-2xl flex items-center justify-center mx-auto mb-4`}>
                    <method.icon className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-center text-xl">{method.title}</CardTitle>
                  <CardDescription className="text-center">{method.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {method.options.map((option) => (
                    <Button
                      key={option.id}
                      onClick={() => handleMethodSelect(option.id)}
                      className="w-full h-14 flex items-center justify-center gap-3 text-lg"
                      variant={selectedMethod === option.id ? 'default' : 'outline'}
                    >
                      <option.icon className="w-6 h-6" />
                      {option.label}
                    </Button>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* STEP 2: Connect / Get Passcode */}
        {currentStep === 2 && (
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="text-center text-2xl">
                {selectedMethod?.startsWith('usb')
                  ? (language === 'de' ? 'Gerät per USB verbinden' : 'Connect Device via USB')
                  : (language === 'de' ? 'Bildschirmsperre-Code eingeben' : 'Enter Screen Lock Passcode')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {selectedMethod?.startsWith('usb') ? (
                <div className="text-center space-y-4">
                  <div className="p-8 bg-blue-50 rounded-xl border-2 border-dashed border-blue-300">
                    <Usb className="w-16 h-16 text-blue-600 mx-auto mb-4 animate-pulse" />
                    <p className="text-lg font-medium text-gray-700">
                      {language === 'de'
                        ? 'Verbinden Sie das Gerät mit einem USB-Kabel'
                        : 'Connect the device with a USB cable'}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      {language === 'de'
                        ? 'Auf dem Gerät wird möglicherweise eine Autorisierungsanfrage angezeigt'
                        : 'Device may show an authorization request'}
                    </p>
                  </div>
                  <Button
                    onClick={handleConnect}
                    size="lg"
                    className="w-full h-14"
                  >
                    {deviceConnected
                      ? (language === 'de' ? 'Verbunden!' : 'Connected!')
                      : (language === 'de' ? 'Gerät erkennen' : 'Detect Device')}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-6 bg-purple-50 rounded-xl border-2 border-purple-200">
                    <Lock className="w-12 h-12 text-purple-600 mx-auto mb-3" />
                    <p className="text-center text-gray-700 mb-4">
                      {language === 'de'
                        ? 'Eine Benachrichtigung wird an das Gerät gesendet. Geben Sie den Bildschirmsperre-Code ein, wenn Sie dazu aufgefordert werden.'
                        : 'A notification will be sent to the device. Enter the screen lock passcode when prompted.'}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {language === 'de' ? 'Bildschirmsperre-Code' : 'Screen Lock Passcode'}
                    </label>
                    <Input
                      type="password"
                      placeholder="****"
                      value={passcode}
                      onChange={(e) => setPasscode(e.target.value)}
                      className="text-center text-2xl tracking-widest h-14"
                      maxLength={6}
                    />
                  </div>
                  <Button
                    onClick={handleConnect}
                    disabled={passcode.length < 4}
                    size="lg"
                    className="w-full h-14"
                  >
                    {language === 'de' ? 'Verbinden & Freischalten' : 'Connect & Unlock'}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* STEP 3: Scanning */}
        {currentStep === 3 && (
          <div className="max-w-4xl mx-auto space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-center text-2xl">
                  {language === 'de' ? 'Wiederherstellungsoptionen auswählen' : 'Select Recovery Options'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  {dataCategories.map((category) => (
                    <div
                      key={category.id}
                      className="flex items-start gap-3 p-4 rounded-lg border-2 hover:border-blue-500 transition-all cursor-pointer"
                      onClick={() => setRecoveryOptions(prev => ({
                        ...prev,
                        [category.id]: !prev[category.id]
                      }))}
                    >
                      <Checkbox
                        checked={recoveryOptions[category.id]}
                        onCheckedChange={(checked) => setRecoveryOptions(prev => ({
                          ...prev,
                          [category.id]: checked
                        }))}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <category.icon className="w-5 h-5 text-blue-600" />
                          <span className="font-medium text-gray-800">{category.label}</span>
                        </div>
                        {!scanning && (
                          <p className="text-xs text-gray-500">
                            {language === 'de' ? 'Geschätzt: ' : 'Estimated: '}
                            {category.count} {language === 'de' ? 'Einträge' : 'items'}
                            {category.deleted > 0 && (
                              <span className="text-red-600 ml-1">
                                (+{category.deleted} {language === 'de' ? 'gelöscht' : 'deleted'})
                              </span>
                            )}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {scanning && (
              <Card>
                <CardContent className="p-8">
                  <div className="text-center space-y-4">
                    <Loader2 className="w-16 h-16 text-blue-600 mx-auto animate-spin" />
                    <div>
                      <p className="text-lg font-semibold text-gray-800 mb-2">
                        {language === 'de' ? 'Gerät wird gescannt...' : 'Scanning device...'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {language === 'de'
                          ? 'Dies kann einige Minuten dauern. Bitte nicht trennen.'
                          : 'This may take several minutes. Please do not disconnect.'}
                      </p>
                    </div>
                    <Progress value={scanProgress} className="h-3" />
                    <p className="text-2xl font-bold text-blue-600">{scanProgress}%</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {!scanning && !scanComplete && (
              <Button
                onClick={handleStartScan}
                size="lg"
                className="w-full h-16 text-lg"
              >
                <Scan className="w-6 h-6 mr-2" />
                {language === 'de' ? 'Scannen & Wiederherstellen starten' : 'Start Scan & Recovery'}
              </Button>
            )}
          </div>
        )}

        {/* STEP 4: Results */}
        {currentStep === 4 && scanComplete && (
          <div className="max-w-4xl mx-auto space-y-6">
            <Card className="border-2 border-green-500 bg-green-50">
              <CardContent className="p-8 text-center">
                <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-green-800 mb-2">
                  {language === 'de' ? 'Wiederherstellung abgeschlossen!' : 'Recovery Complete!'}
                </h2>
                <p className="text-green-700">
                  {language === 'de'
                    ? 'Alle ausgewählten Daten wurden erfolgreich extrahiert'
                    : 'All selected data has been successfully extracted'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl">
                  {language === 'de' ? 'Wiederhergestellte Daten' : 'Recovered Data'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <Image className="w-8 h-8 text-blue-600 mb-2" />
                    <p className="text-2xl font-bold text-blue-900">{results.photos + results.videos}</p>
                    <p className="text-sm text-blue-700">{language === 'de' ? 'Fotos & Videos' : 'Photos & Videos'}</p>
                    <p className="text-xs text-red-600 mt-1">+{results.deletedPhotos} {language === 'de' ? 'gelöscht' : 'deleted'}</p>
                  </div>

                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <MessageSquare className="w-8 h-8 text-green-600 mb-2" />
                    <p className="text-2xl font-bold text-green-900">{results.messages}</p>
                    <p className="text-sm text-green-700">{language === 'de' ? 'Nachrichten' : 'Messages'}</p>
                    <p className="text-xs text-gray-600 mt-1">
                      WhatsApp: {results.whatsapp}, Telegram: {results.telegram}, SMS: {results.sms}
                    </p>
                  </div>

                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <Users className="w-8 h-8 text-purple-600 mb-2" />
                    <p className="text-2xl font-bold text-purple-900">{results.contacts}</p>
                    <p className="text-sm text-purple-700">{language === 'de' ? 'Kontakte' : 'Contacts'}</p>
                  </div>

                  <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                    <Phone className="w-8 h-8 text-orange-600 mb-2" />
                    <p className="text-2xl font-bold text-orange-900">{results.callLogs}</p>
                    <p className="text-sm text-orange-700">{language === 'de' ? 'Anrufe' : 'Call Logs'}</p>
                  </div>

                  <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <Trash2 className="w-8 h-8 text-red-600 mb-2" />
                    <p className="text-2xl font-bold text-red-900">{results.deletedPhotos + results.deletedMessages}</p>
                    <p className="text-sm text-red-700">{language === 'de' ? 'Gelöschte Daten' : 'Deleted Data'}</p>
                  </div>

                  <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
                    <MapPin className="w-8 h-8 text-teal-600 mb-2" />
                    <p className="text-2xl font-bold text-teal-900">{results.locations}</p>
                    <p className="text-sm text-teal-700">{language === 'de' ? 'GPS Positionen' : 'GPS Locations'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button
                onClick={handleDownloadResults}
                size="lg"
                className="flex-1 h-14 text-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <Download className="w-6 h-6 mr-2" />
                {language === 'de' ? 'Alle Daten herunterladen' : 'Download All Data'}
              </Button>
              <Button
                onClick={() => navigate('/admin/forensics')}
                size="lg"
                variant="outline"
                className="h-14"
              >
                {language === 'de' ? 'Zur Forensik' : 'Go to Forensics'}
              </Button>
            </div>
          </div>
        )}

        {/* Info Cards */}
        {currentStep === 1 && (
          <div className="mt-12 grid md:grid-cols-2 gap-6">
            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-900">
                  <Shield className="w-5 h-5" />
                  {language === 'de' ? 'Was können wir wiederherstellen?' : 'What can we recover?'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-blue-800">
                <p>✓ {language === 'de' ? 'Alle Fotos & Videos (auch gelöschte)' : 'All photos & videos (including deleted)'}</p>
                <p>✓ {language === 'de' ? 'WhatsApp, Telegram, SMS Nachrichten' : 'WhatsApp, Telegram, SMS messages'}</p>
                <p>✓ {language === 'de' ? 'Kontakte & Anrufliste' : 'Contacts & call history'}</p>
                <p>✓ {language === 'de' ? 'GPS Standortverlauf' : 'GPS location history'}</p>
                <p>✓ {language === 'de' ? 'App-Daten & Dokumente' : 'App data & documents'}</p>
                <p>✓ {language === 'de' ? 'Gelöschte Dateien (bis zu 30 Tage)' : 'Deleted files (up to 30 days)'}</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-purple-200 bg-purple-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-purple-900">
                  <Zap className="w-5 h-5" />
                  {language === 'de' ? 'Unser Vorteil' : 'Our Advantage'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-purple-800">
                <p>⚡ {language === 'de' ? 'USB & Kabellos - beide Methoden unterstützt' : 'USB & Wireless - both methods supported'}</p>
                <p>⚡ {language === 'de' ? 'Keine physische Anwesenheit erforderlich (Kabellos-Modus)' : 'No physical presence required (Wireless mode)'}</p>
                <p>⚡ {language === 'de' ? 'Gelöschte Daten bis zu 30 Tage wiederherstellbar' : 'Deleted data recoverable up to 30 days'}</p>
                <p>⚡ {language === 'de' ? 'Verschlüsselte & sichere Übertragung' : 'Encrypted & secure transmission'}</p>
                <p>⚡ {language === 'de' ? 'Gerichtsadmissible Berichte' : 'Court-admissible reports'}</p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPhoneRecovery;
