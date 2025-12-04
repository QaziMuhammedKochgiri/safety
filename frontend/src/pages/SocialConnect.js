import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, Smartphone, Send } from "lucide-react";
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

const SocialConnect = () => {
  const { user } = useAuth();
  const { language } = useLanguage();

  // Default platform is WhatsApp
  const [platform, setPlatform] = useState("whatsapp"); // 'whatsapp' | 'telegram'
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [qrCode, setQrCode] = useState(null);
  const [status, setStatus] = useState("idle"); 

  // Start session with platform and clientNumber
  const startSession = async () => {
    try {
      setLoading(true);
      setStatus("initializing");
      setQrCode(null);

      const clientNumber = user?.clientNumber || 'GUEST';
      const endpoint = platform === 'telegram' ? '/api/telegram/session/start' : '/api/whatsapp/session/start';

      const res = await axios.post(endpoint, {
        clientNumber,
        platform
      });

      setSessionId(res.data.sessionId);
    } catch (error) {
      console.error("Session error:", error);
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  // Status polling - check every 2 seconds
  useEffect(() => {
    let interval;
    if (sessionId && status !== 'completed' && status !== 'timeout' && status !== 'error') {
      interval = setInterval(async () => {
        try {
          const endpoint = platform === 'telegram'
            ? `/api/telegram/session/${sessionId}/status`
            : `/api/whatsapp/session/${sessionId}/status`;
          const res = await axios.get(endpoint);
          const s = res.data.status;

          if ((s === 'waiting_for_scan' || s === 'qr_ready') && res.data.qr) {
            setQrCode(res.data.qr);
            setStatus('waiting_for_scan');
          } else if (s === 'connected' || s === 'extracting') {
            setStatus('extracting');
            setQrCode(null);
          } else if (s === 'completed') {
            setStatus('completed');
            setQrCode(null);
            clearInterval(interval);
          } else if (s === 'timeout' || s === 'failed') {
            setStatus('error');
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [sessionId, status, platform]);

  // Translations
  const t = {
    connection: language === 'de' ? 'Verbindung' : 'Connection',
    startConnection: language === 'de' ? 'Verbindung starten' : 'Start Connection',
    whatsappDesc: language === 'de'
      ? 'Klicken Sie auf die Schaltfläche, um die WhatsApp Web-Schnittstelle zu starten und den QR-Code zu generieren.'
      : 'Click the button to start the WhatsApp Web interface and generate the QR code.',
    telegramDesc: language === 'de'
      ? 'Klicken Sie auf die Schaltfläche für eine sichere Telegram Web-Verbindung.'
      : 'Click the button for a secure Telegram Web connection.',
    preparingBrowser: language === 'de' ? 'Sicherer Browser wird vorbereitet...' : 'Preparing secure browser...',
    scanFromDevice: language === 'de' ? 'Mit Ihrem Gerät scannen' : 'Scan from your device',
    whatsappScanInstr: language === 'de'
      ? 'Telefon > WhatsApp > Einstellungen > Verknüpfte Geräte > Gerät verknüpfen'
      : 'Phone > WhatsApp > Settings > Linked Devices > Link a Device',
    telegramScanInstr: language === 'de'
      ? 'Telegram > Einstellungen > Geräte > Desktop-Gerät verknüpfen'
      : 'Telegram > Settings > Devices > Link Desktop Device',
    extractingData: language === 'de' ? 'Daten werden extrahiert...' : 'Extracting data...',
    extractingDesc: language === 'de'
      ? 'Bitte warten Sie, während wir Ihre Nachrichten abrufen. Dies kann einige Minuten dauern.'
      : 'Please wait while we retrieve your messages. This may take a few minutes.',
    connectionSuccess: language === 'de' ? 'Verbindung erfolgreich!' : 'Connection Successful!',
    dataReady: language === 'de' ? 'Daten sind bereit für die Analyse.' : 'Data is ready for analysis.',
    startAnalysis: language === 'de' ? 'Analyse starten' : 'Start Analysis',
    errorMessage: language === 'de'
      ? 'Verbindung ist abgelaufen oder ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.'
      : 'Connection timed out or an error occurred. Please try again.',
    tryAgain: language === 'de' ? 'Erneut versuchen' : 'Try Again'
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 space-y-6">
      <Card className="w-full max-w-md border-2 shadow-lg">
        <CardHeader className="text-center bg-slate-50 border-b pb-6">
          <CardTitle className="flex items-center justify-center gap-2 text-xl">
            {platform === 'whatsapp' ? (
              <Smartphone className="w-6 h-6 text-green-600" />
            ) : (
              <Send className="w-6 h-6 text-blue-500" />
            )}
            {platform === 'whatsapp' ? 'WhatsApp' : 'Telegram'} {t.connection}
          </CardTitle>

          {/* Platform selection buttons */}
          <div className="flex justify-center gap-3 mt-4">
            <Button
              variant={platform === 'whatsapp' ? 'default' : 'outline'}
              size="sm"
              onClick={() => { setPlatform('whatsapp'); setStatus('idle'); setSessionId(null); }}
              className={`${platform === 'whatsapp' ? 'bg-green-600 hover:bg-green-700' : 'border-green-200 text-green-700 hover:bg-green-50'}`}
            >
              WhatsApp
            </Button>
            <Button
              variant={platform === 'telegram' ? 'default' : 'outline'}
              size="sm"
              onClick={() => { setPlatform('telegram'); setStatus('idle'); setSessionId(null); }}
              className={`${platform === 'telegram' ? 'bg-blue-500 hover:bg-blue-600' : 'border-blue-200 text-blue-600 hover:bg-blue-50'}`}
            >
              Telegram
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="flex flex-col items-center p-8 min-h-[300px] justify-center">

          {/* STATUS: IDLE */}
          {status === 'idle' && (
            <div className="text-center space-y-4 animate-in fade-in">
              <div className={`p-4 rounded-full bg-opacity-10 w-20 h-20 mx-auto flex items-center justify-center mb-4 ${platform === 'whatsapp' ? 'bg-green-500 text-green-600' : 'bg-blue-500 text-blue-500'}`}>
                {platform === 'whatsapp' ? <Smartphone size={40} /> : <Send size={40} />}
              </div>
              <p className="text-muted-foreground text-sm px-4">
                {platform === 'whatsapp' ? t.whatsappDesc : t.telegramDesc}
              </p>
              <Button onClick={startSession} disabled={loading} size="lg" className="w-full">
                {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : t.startConnection}
              </Button>
            </div>
          )}

          {/* STATUS: INITIALIZING */}
          {status === 'initializing' && (
            <div className="text-center space-y-4">
              <Loader2 className="h-10 w-10 animate-spin text-slate-400 mx-auto" />
              <p className="text-sm text-slate-500">{t.preparingBrowser}</p>
            </div>
          )}

          {/* STATUS: WAITING FOR SCAN */}
          {status === 'waiting_for_scan' && qrCode && (
            <div className="text-center space-y-4 animate-in zoom-in duration-300">
              <div className="p-4 bg-white border-2 border-slate-200 rounded-xl shadow-sm inline-block">
                <img src={qrCode} alt="QR Code" className="w-64 h-64 object-contain" />
              </div>

              <div className="space-y-2">
                <p className="font-semibold text-slate-800">{t.scanFromDevice}</p>
                <div className="text-xs text-slate-500 max-w-[250px] mx-auto">
                  {platform === 'whatsapp' ? t.whatsappScanInstr : t.telegramScanInstr}
                </div>
              </div>
            </div>
          )}

          {/* STATUS: EXTRACTING */}
          {status === 'extracting' && (
            <div className="text-center space-y-4 animate-in fade-in">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">{t.extractingData}</h3>
                <p className="text-slate-500 mt-2 text-sm max-w-[280px] mx-auto">
                  {t.extractingDesc}
                </p>
              </div>
            </div>
          )}

          {/* STATUS: COMPLETED */}
          {status === 'completed' && (
            <div className="text-center space-y-4 animate-in slide-in-from-bottom-4">
              <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-12 h-12 text-green-600" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-slate-900">{t.connectionSuccess}</h3>
                <p className="text-slate-500 mt-2">
                  {platform === 'whatsapp' ? 'WhatsApp' : 'Telegram'} {t.dataReady}
                </p>
              </div>
              <Button className="w-full mt-4 bg-slate-900 text-white hover:bg-slate-800">
                {t.startAnalysis}
              </Button>
            </div>
          )}

          {/* STATUS: ERROR */}
          {status === 'error' && (
            <Alert variant="destructive">
              <AlertDescription>{t.errorMessage}</AlertDescription>
              <Button variant="outline" size="sm" onClick={() => setStatus('idle')} className="mt-2 w-full">
                {t.tryAgain}
              </Button>
            </Alert>
          )}

        </CardContent>
      </Card>
    </div>
  );
};

export default SocialConnect;