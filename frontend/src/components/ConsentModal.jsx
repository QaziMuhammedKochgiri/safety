import React, { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { MapPin, Globe, Video, FileUp, Download } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ConsentModal = ({ open, onClose, onAccept }) => {
  const { language } = useLanguage();
  const [consents, setConsents] = useState({
    location: false,
    browser: false,
    camera: false,
    files: false,
    forensic: false,
  });

  const allConsented = Object.values(consents).every(Boolean);
  const someConsented = Object.values(consents).some(Boolean);

  const handleSelectAll = () => {
    const newValue = !allConsented;
    setConsents({
      location: newValue,
      browser: newValue,
      camera: newValue,
      files: newValue,
      forensic: newValue,
    });
  };

  const handleAccept = async () => {
    if (allConsented) {
      try {
        // Get location if permission granted
        let locationData = null;
        if (consents.location && navigator.geolocation) {
          try {
            const position = await new Promise((resolve, reject) => {
              navigator.geolocation.getCurrentPosition(resolve, reject);
            });
            locationData = {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
            };
          } catch (error) {
            console.log('Location access denied or unavailable');
          }
        }

        // Generate session ID
        const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // Send consent to backend
        await axios.post(`${API}/consent`, {
          sessionId,
          permissions: consents,
          location: locationData,
          userAgent: navigator.userAgent,
          ipAddress: 'will-be-set-by-backend',
        });

        // Store consent in localStorage
        localStorage.setItem('safechild-consent', JSON.stringify({
          ...consents,
          sessionId,
          timestamp: new Date().toISOString(),
        }));
        
        onAccept();
      } catch (error) {
        console.error('Error saving consent:', error);
        // Still proceed even if backend save fails
        localStorage.setItem('safechild-consent', JSON.stringify({
          ...consents,
          timestamp: new Date().toISOString(),
        }));
        onAccept();
      }
    }
  };

  const consentItems = [
    {
      key: 'location',
      icon: MapPin,
      label: t(language, 'consentLocation'),
    },
    {
      key: 'browser',
      icon: Globe,
      label: t(language, 'consentBrowser'),
    },
    {
      key: 'camera',
      icon: Video,
      label: t(language, 'consentCamera'),
    },
    {
      key: 'files',
      icon: FileUp,
      label: t(language, 'consentFiles'),
    },
    {
      key: 'forensic',
      icon: Download,
      label: t(language, 'consentForensic'),
    },
  ];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">{t(language, 'consentRequired')}</DialogTitle>
          <DialogDescription className="text-base">
            {t(language, 'consentDescription')}
          </DialogDescription>
        </DialogHeader>

        {/* Select All Button */}
        <div className="py-4 border-b">
          <div
            onClick={handleSelectAll}
            className="flex items-center space-x-3 p-4 border-2 rounded-lg hover:border-blue-500 transition-colors cursor-pointer bg-blue-50"
          >
            <Checkbox
              id="selectAll"
              checked={allConsented}
              onCheckedChange={handleSelectAll}
              className="mt-0"
            />
            <Label
              htmlFor="selectAll"
              className="flex-1 cursor-pointer font-semibold text-lg text-blue-900"
            >
              {language === 'de' 
                ? '✓ Alle Berechtigungen auswählen' 
                : '✓ Select All Permissions'}
            </Label>
          </div>
        </div>

        <div className="space-y-4 py-4">
          {consentItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.key}
                className="flex items-start space-x-3 p-4 border-2 rounded-lg hover:border-blue-500 transition-colors"
              >
                <Checkbox
                  id={item.key}
                  checked={consents[item.key]}
                  onCheckedChange={(checked) =>
                    setConsents({ ...consents, [item.key]: checked })
                  }
                  className="mt-1"
                />
                <div className="flex-1">
                  <Label
                    htmlFor={item.key}
                    className="flex items-center space-x-2 cursor-pointer"
                  >
                    <Icon className="w-5 h-5 text-blue-600" />
                    <span className="text-base font-medium">{item.label}</span>
                  </Label>
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            {language === 'de'
              ? 'Durch die Zustimmung erklären Sie sich ausdrücklich damit einverstanden, dass wir die genannten Daten sammeln und verarbeiten dürfen. Diese Einwilligung ist freiwillig und kann jederzeit widerrufen werden.'
              : 'By consenting, you explicitly agree that we may collect and process the mentioned data. This consent is voluntary and can be withdrawn at any time.'}
          </p>
        </div>

        <DialogFooter className="flex gap-2">
          <Button variant="outline" onClick={onClose}>
            {t(language, 'declineConsent')}
          </Button>
          <Button
            onClick={handleAccept}
            disabled={!allConsented}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {t(language, 'acceptConsent')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ConsentModal;
