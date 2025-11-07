import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Download, Shield, FileText, CheckCircle, AlertCircle, Smartphone, Cloud, Lock } from 'lucide-react';

const ForensicSoftware = () => {
  const { language } = useLanguage();

  const features = [
    {
      icon: Smartphone,
      title: language === 'de' ? 'Multi-Gerät Support' : 'Multi-Device Support',
      description: language === 'de' ? 'iOS, Android, Computer' : 'iOS, Android, Computer'
    },
    {
      icon: Cloud,
      title: language === 'de' ? 'Cloud Extraktion' : 'Cloud Extraction',
      description: language === 'de' ? 'iCloud, Google Drive, Dropbox' : 'iCloud, Google Drive, Dropbox'
    },
    {
      icon: FileText,
      title: language === 'de' ? 'Gerichtsfeste Berichte' : 'Court-Admissible Reports',
      description: language === 'de' ? 'PDF mit Hash-Verifizierung' : 'PDF with hash verification'
    },
    {
      icon: Lock,
      title: language === 'de' ? 'GDPR Konform' : 'GDPR Compliant',
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
              ? 'Professionelle Forensik-Software f\u00fcr rechtliche Beweissicherung in internationalen Kindschaftsrechts-F\u00e4llen'
              : 'Professional forensic software for legal evidence collection in international child custody cases'}
          </p>
        </div>

        <Alert className="mb-8 max-w-4xl mx-auto border-2 border-yellow-200 bg-yellow-50">
          <AlertCircle className="h-5 w-5 text-yellow-600" />
          <AlertDescription className="text-yellow-800 font-medium">
            {language === 'de'
              ? '\ud83d\udea7 Software befindet sich in Entwicklung. Beta-Version Q2 2025 verf\u00fcgbar.'
              : '\ud83d\udea7 Software is under development. Beta version available Q2 2025.'}
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
                  language === 'de' ? 'Gel\u00f6schte Daten Wiederherstellung' : 'Deleted data recovery',
                  language === 'de' ? 'Timeline-Rekonstruktion' : 'Timeline reconstruction',
                  language === 'de' ? 'GPS & Standort-Analyse' : 'GPS & location analysis',
                  language === 'de' ? 'Foto EXIF-Daten' : 'Photo EXIF data',
                  language === 'de' ? 'E-Mail & Kontakte' : 'Email & contacts',
                  language === 'de' ? 'Cloud Backup Zugriff' : 'Cloud backup access',
                  language === 'de' ? 'Verschl\u00fcsselter Bericht' : 'Encrypted reports'
                ].map((item, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    <span className="text-sm">{item}</span>
                  </div>\n                ))}\n              </div>\n            </CardContent>\n          </Card>\n\n          <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white">\n            <CardHeader>\n              <CardTitle className="text-2xl">\n                {language === 'de' ? 'Jetzt Vorbestellen' : 'Pre-Order Now'}\n              </CardTitle>\n              <CardDescription>\n                {language === 'de' ? 'Erhalten Sie fr\u00fchen Zugang zur Beta-Version' : 'Get early access to beta version'}\n              </CardDescription>\n            </CardHeader>\n            <CardContent className="space-y-6">\n              <div>\n                <p className="text-sm text-gray-600 mb-4">\n                  {language === 'de'\n                    ? 'Registrieren Sie sich f\u00fcr die Warteliste und erhalten Sie:'\n                    : 'Register for the waitlist and receive:'}\n                </p>\n                <ul className="space-y-2">\n                  <li className="flex items-center space-x-2 text-sm">\n                    <CheckCircle className="w-4 h-4 text-blue-600" />\n                    <span>{language === 'de' ? '50% Rabatt auf die erste Lizenz' : '50% off first license'}</span>\n                  </li>\n                  <li className="flex items-center space-x-2 text-sm">\n                    <CheckCircle className="w-4 h-4 text-blue-600" />\n                    <span>{language === 'de' ? 'Kostenlose Schulung (2 Stunden)' : 'Free training (2 hours)'}</span>\n                  </li>\n                  <li className="flex items-center space-x-2 text-sm">\n                    <CheckCircle className="w-4 h-4 text-blue-600" />\n                    <span>{language === 'de' ? 'Priority Support' : 'Priority support'}</span>\n                  </li>\n                </ul>\n              </div>\n\n              <div className="bg-white rounded-lg p-4 border-2">\n                <div className="text-center mb-4">\n                  <div className="text-3xl font-bold text-blue-600">\u20ac99</div>\n                  <div className="text-sm text-gray-600">\n                    {language === 'de' ? 'Pro Fall-Analyse' : 'Per case analysis'}\n                  </div>\n                  <div className="text-xs text-gray-500 line-through">\n                    {language === 'de' ? 'Normal \u20ac199' : 'Regular \u20ac199'}\n                  </div>\n                </div>\n              </div>\n\n              <Button className="w-full bg-blue-600 hover:bg-blue-700" size="lg" disabled>\n                <Download className="w-5 h-5 mr-2" />\n                {language === 'de' ? 'In Entwicklung - Q2 2025' : 'In Development - Q2 2025'}\n              </Button>\n\n              <p className="text-xs text-center text-gray-500">\n                {language === 'de'\n                  ? 'Kontaktieren Sie uns f\u00fcr weitere Informationen'\n                  : 'Contact us for more information'}\n              </p>\n            </CardContent>\n          </Card>\n        </div>\n\n        <Card className="mt-12 max-w-4xl mx-auto border-2 border-red-200 bg-red-50">\n          <CardContent className="p-6">\n            <div className="flex items-start space-x-3">\n              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />\n              <div>\n                <h3 className="font-bold text-red-900 mb-2">\n                  {language === 'de' ? 'Rechtlicher Hinweis' : 'Legal Disclaimer'}\n                </h3>\n                <p className="text-sm text-red-800">\n                  {language === 'de'\n                    ? 'Diese Software darf nur mit ausdr\u00fccklicher schriftlicher Einwilligung des Ger\u00e4teinhabers und unter rechtlicher Aufsicht verwendet werden. Missbrauch kann strafrechtliche Konsequenzen nach sich ziehen. Nutzer m\u00fcssen alle anwendbaren Gesetze ihrer Jurisdiktion einhalten.'\n                    : 'This software may only be used with explicit written consent from the device owner and under legal supervision. Misuse may result in criminal prosecution. Users must comply with all applicable laws in their jurisdiction.'}\n                </p>\n              </div>\n            </div>\n          </CardContent>\n        </Card>\n\n        <div className="mt-12 max-w-4xl mx-auto">\n          <h2 className="text-2xl font-bold text-center mb-8">\n            {language === 'de' ? 'Technische Spezifikationen' : 'Technical Specifications'}\n          </h2>\n          <div className="grid md:grid-cols-3 gap-6">\n            <Card>\n              <CardHeader>\n                <CardTitle className="text-lg">Platform</CardTitle>\n              </CardHeader>\n              <CardContent>\n                <p className="text-sm text-gray-600">Windows, macOS, Linux</p>\n                <p className="text-xs text-gray-500 mt-2">Electron-based application</p>\n              </CardContent>\n            </Card>\n            <Card>\n              <CardHeader>\n                <CardTitle className="text-lg">Security</CardTitle>\n              </CardHeader>\n              <CardContent>\n                <p className="text-sm text-gray-600">AES-256 encryption</p>\n                <p className="text-xs text-gray-500 mt-2">SHA-256 hash verification</p>\n              </CardContent>\n            </Card>\n            <Card>\n              <CardHeader>\n                <CardTitle className="text-lg">Compliance</CardTitle>\n              </CardHeader>\n              <CardContent>\n                <p className="text-sm text-gray-600">GDPR, Chain of Custody</p>\n                <p className="text-xs text-gray-500 mt-2">Court-admissible reports</p>\n              </CardContent>\n            </Card>\n          </div>\n        </div>\n      </div>\n    </div>\n  );\n};\n\nexport default ForensicSoftware;\n"}