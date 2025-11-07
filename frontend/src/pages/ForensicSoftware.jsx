import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Shield, Smartphone, Database, Lock, Download, CheckCircle, AlertCircle
} from 'lucide-react';

const ForensicSoftware = () => {
  const { language } = useLanguage();

  const features = [
    {
      icon: Smartphone,
      title: language === 'de' ? 'Datenextraktion' : 'Data Extraction',
      description: language === 'de' ? 'WhatsApp, Telegram & mehr' : 'WhatsApp, Telegram & more'
    },
    {
      icon: Database,
      title: language === 'de' ? 'Datenwiederherstellung' : 'Data Recovery',
      description: language === 'de' ? 'Gelöschte Dateien finden' : 'Find deleted files'
    },
    {
      icon: Lock,
      title: language === 'de' ? 'Verschlüsselt' : 'Encrypted',
      description: language === 'de' ? 'AES-256 Verschlüsselung' : 'AES-256 encryption'
    },
    {
      icon: Shield,
      title: language === 'de' ? 'Datenschutz' : 'Privacy',
      description: language === 'de' ? 'Volle Datenschutz-Compliance' : 'Full privacy compliance'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-12">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-600 to-blue-800 rounded-full mb-6">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            SafeChild Forensic Software
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            {language === 'de' 
              ? 'Professionelle Forensik-Software für rechtliche Beweissicherung in internationalen Kindschaftsrechts-Fällen'
              : 'Professional forensic software for legal evidence collection in international child custody cases'}
          </p>
        </div>

        <Alert className="mb-8 max-w-4xl mx-auto border-2 border-yellow-200 bg-yellow-50">
          <AlertCircle className="h-5 w-5 text-yellow-600" />
          <AlertDescription className="text-yellow-800 font-medium">
            {language === 'de'
              ? '🚧 Software befindet sich in Entwicklung. Beta-Version Q2 2025 verfügbar.'
              : '🚧 Software is under development. Beta version available Q2 2025.'}
          </AlertDescription>
        </Alert>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {features.map((feature, index) => (
            <Card key={index} className="border-2 hover:border-blue-500 transition-all">
              <CardHeader className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-8 h-8 text-blue-600" />
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 text-center">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="text-2xl">
                {language === 'de' ? 'Funktionen' : 'Capabilities'}
              </CardTitle>
              <CardDescription>
                {language === 'de' ? 'Basierend auf Cellebrite & Magnet AXIOM Standards' : 'Based on Cellebrite & Magnet AXIOM standards'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  language === 'de' ? 'WhatsApp/Telegram Nachrichten Extraktion' : 'WhatsApp/Telegram message extraction',
                  language === 'de' ? 'Gelöschte Daten Wiederherstellung' : 'Deleted data recovery',
                  language === 'de' ? 'Timeline-Rekonstruktion' : 'Timeline reconstruction',
                  language === 'de' ? 'GPS & Standort-Analyse' : 'GPS & location analysis',
                  language === 'de' ? 'Foto EXIF-Daten' : 'Photo EXIF data',
                  language === 'de' ? 'E-Mail & Kontakte' : 'Email & contacts',
                  language === 'de' ? 'Cloud Backup Zugriff' : 'Cloud backup access',
                  language === 'de' ? 'Verschlüsselter Bericht' : 'Encrypted reports'
                ].map((item, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    <span className="text-sm">{item}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white">
            <CardHeader>
              <CardTitle className="text-2xl">
                {language === 'de' ? 'Jetzt Vorbestellen' : 'Pre-Order Now'}
              </CardTitle>
              <CardDescription>
                {language === 'de' ? 'Erhalten Sie frühen Zugang zur Beta-Version' : 'Get early access to beta version'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  {language === 'de'
                    ? 'Registrieren Sie sich für die Warteliste und erhalten Sie:'
                    : 'Register for the waitlist and receive:'}
                </p>
                <ul className="space-y-2">
                  <li className="flex items-center space-x-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-blue-600" />
                    <span>{language === 'de' ? '50% Rabatt auf die erste Lizenz' : '50% off first license'}</span>
                  </li>
                  <li className="flex items-center space-x-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-blue-600" />
                    <span>{language === 'de' ? 'Kostenlose Schulung (2 Stunden)' : 'Free training (2 hours)'}</span>
                  </li>
                  <li className="flex items-center space-x-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-blue-600" />
                    <span>{language === 'de' ? 'Priority Support' : 'Priority support'}</span>
                  </li>
                </ul>
              </div>

              <div className="bg-white rounded-lg p-4 border-2">
                <div className="text-center mb-4">
                  <div className="text-3xl font-bold text-blue-600">€99</div>
                  <div className="text-sm text-gray-600">
                    {language === 'de' ? 'Pro Fall-Analyse' : 'Per case analysis'}
                  </div>
                  <div className="text-xs text-gray-500 line-through">
                    {language === 'de' ? 'Normal €199' : 'Regular €199'}
                  </div>
                </div>
              </div>

              <Button className="w-full bg-blue-600 hover:bg-blue-700" size="lg" disabled>
                <Download className="w-5 h-5 mr-2" />
                {language === 'de' ? 'In Entwicklung - Q2 2025' : 'In Development - Q2 2025'}
              </Button>

              <p className="text-xs text-center text-gray-500">
                {language === 'de'
                  ? 'Kontaktieren Sie uns für weitere Informationen'
                  : 'Contact us for more information'}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-12 max-w-4xl mx-auto border-2 border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-bold text-red-900 mb-2">
                  {language === 'de' ? 'Rechtlicher Hinweis' : 'Legal Disclaimer'}
                </h3>
                <p className="text-sm text-red-800">
                  {language === 'de'
                    ? 'Diese Software darf nur mit ausdrücklicher schriftlicher Einwilligung des Geräteinhabers und unter rechtlicher Aufsicht verwendet werden. Missbrauch kann strafrechtliche Konsequenzen nach sich ziehen. Nutzer müssen alle anwendbaren Gesetze ihrer Jurisdiktion einhalten.'
                    : 'This software may only be used with explicit written consent from the device owner and under legal supervision. Misuse may result in criminal prosecution. Users must comply with all applicable laws in their jurisdiction.'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="mt-12 max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">
            {language === 'de' ? 'Technische Spezifikationen' : 'Technical Specifications'}
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Platform</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">Windows, macOS, Linux</p>
                <p className="text-xs text-gray-500 mt-2">Electron-based application</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Security</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">AES-256 encryption</p>
                <p className="text-xs text-gray-500 mt-2">SHA-256 hash verification</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Compliance</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">GDPR, Chain of Custody</p>
                <p className="text-xs text-gray-500 mt-2">Court-admissible reports</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForensicSoftware;
