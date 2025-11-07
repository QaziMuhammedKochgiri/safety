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

  const handleAccept = () => {
    if (allConsented) {
      // Store consent in localStorage
      localStorage.setItem('safechild-consent', JSON.stringify({
        ...consents,
        timestamp: new Date().toISOString(),
      }));
      onAccept();
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
