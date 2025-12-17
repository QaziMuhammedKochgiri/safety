import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import {
  MessageCircle, X, Send, User, Headphones
} from 'lucide-react';
import { Input } from './ui/input';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || "/api";

// URL'leri tıklanabilir linklere çevir
const linkifyText = (text, isClientMessage = false) => {
  if (!text) return text;
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);

  return parts.map((part, index) => {
    if (part.match(urlRegex)) {
      // Client mesajında (mavi arka plan): açık mavi link
      // Agent mesajında (gri arka plan): koyu mavi link
      const linkClass = isClientMessage
        ? "underline text-blue-200 hover:text-white break-all"
        : "underline text-blue-600 hover:text-blue-800 break-all";
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className={linkClass}
          onClick={(e) => e.stopPropagation()}
        >
          {part}
        </a>
      );
    }
    return part;
  });
};

// Browser fingerprint toplama fonksiyonu
const collectBrowserFingerprint = () => {
  const nav = navigator;
  const screen = window.screen;

  return {
    userAgent: nav.userAgent,
    language: nav.language,
    languages: Array.from(nav.languages || []),
    platform: nav.platform,
    screenResolution: `${screen.width}x${screen.height}`,
    colorDepth: screen.colorDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
    cookiesEnabled: nav.cookieEnabled,
    doNotTrack: nav.doNotTrack,
    plugins: Array.from(nav.plugins || []).map(p => p.name).slice(0, 10),
    canvas: null,
    webGL: null,
    fonts: [],
    audioContext: null
  };
};

// Cihaz bilgisi toplama fonksiyonu
const collectDeviceInfo = () => {
  const nav = navigator;
  const ua = nav.userAgent;

  // OS tespiti
  let os = 'Unknown';
  let osVersion = '';
  if (/Windows/.test(ua)) {
    os = 'Windows';
    const match = ua.match(/Windows NT (\d+\.\d+)/);
    if (match) osVersion = match[1];
  } else if (/Mac OS X/.test(ua)) {
    os = 'macOS';
    const match = ua.match(/Mac OS X (\d+[._]\d+)/);
    if (match) osVersion = match[1].replace('_', '.');
  } else if (/Android/.test(ua)) {
    os = 'Android';
    const match = ua.match(/Android (\d+(\.\d+)?)/);
    if (match) osVersion = match[1];
  } else if (/iPhone|iPad|iPod/.test(ua)) {
    os = 'iOS';
    const match = ua.match(/OS (\d+_\d+)/);
    if (match) osVersion = match[1].replace('_', '.');
  } else if (/Linux/.test(ua)) {
    os = 'Linux';
  }

  // Browser tespiti
  let browser = 'Unknown';
  let browserVersion = '';
  if (/Chrome/.test(ua) && !/Chromium|Edg/.test(ua)) {
    browser = 'Chrome';
    const match = ua.match(/Chrome\/(\d+)/);
    if (match) browserVersion = match[1];
  } else if (/Firefox/.test(ua)) {
    browser = 'Firefox';
    const match = ua.match(/Firefox\/(\d+)/);
    if (match) browserVersion = match[1];
  } else if (/Safari/.test(ua) && !/Chrome/.test(ua)) {
    browser = 'Safari';
    const match = ua.match(/Version\/(\d+)/);
    if (match) browserVersion = match[1];
  } else if (/Edg/.test(ua)) {
    browser = 'Edge';
    const match = ua.match(/Edg\/(\d+)/);
    if (match) browserVersion = match[1];
  }

  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);

  return {
    isMobile,
    deviceType: isMobile ? (/iPad|Tablet/i.test(ua) ? 'tablet' : 'mobile') : 'desktop',
    os,
    osVersion,
    browser,
    browserVersion,
    deviceMemory: nav.deviceMemory || null,
    hardwareConcurrency: nav.hardwareConcurrency || null,
    maxTouchPoints: nav.maxTouchPoints || 0,
    connection: nav.connection ? {
      effectiveType: nav.connection.effectiveType,
      downlink: nav.connection.downlink,
      rtt: nav.connection.rtt
    } : null
  };
};

const LiveChat = () => {
  const { language } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isMobile, setIsMobile] = useState(false);
  const [locationData, setLocationData] = useState(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [agentConnected, setAgentConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const messagePollRef = useRef(null);
  const sessionIdRef = useRef(null);
  const locationWatchRef = useRef(null);

  // sessionId'yi ref'te tut (polling icin)
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  // Mobil/Desktop algilama
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth <= 768 ||
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      setIsMobile(mobile);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Session kontrolu - mevcut session varsa yukle
  useEffect(() => {
    const checkAndSetSession = async () => {
      const savedSessionId = localStorage.getItem('safechild-chat-session');
      if (savedSessionId) {
        try {
          const response = await axios.get(`${API}/chat/session-status/${savedSessionId}`);
          if (response.data.status === 'active') {
            setSessionId(savedSessionId);
            setAgentConnected(true);
          } else {
            localStorage.removeItem('safechild-chat-session');
            setSessionId(null);
            setMessages([]);
          }
        } catch (error) {
          localStorage.removeItem('safechild-chat-session');
          setSessionId(null);
          setMessages([]);
        }
      }
    };

    if (isOpen) {
      checkAndSetSession();
    }
  }, [isOpen]);

  // Chat acildiginda ve session varsa gecmisi yukle + polling baslat
  useEffect(() => {
    if (sessionId && isOpen) {
      if (messages.length === 0) {
        loadChatHistory();
      }

      if (messagePollRef.current) {
        clearInterval(messagePollRef.current);
      }

      messagePollRef.current = setInterval(async () => {
        if (sessionIdRef.current) {
          try {
            const response = await axios.get(`${API}/chat/${sessionIdRef.current}`);
            if (response.data.messages && response.data.messages.length > 0) {
              setMessages(response.data.messages.map(msg => ({
                id: msg.id || msg._id,
                sender: msg.sender,
                agentName: msg.agentName,
                text: msg.message || msg.text,
                timestamp: msg.timestamp
              })));
            }
          } catch (error) {
            console.error('Error polling messages:', error);
          }
        }
      }, 2000);
    }

    return () => {
      if (messagePollRef.current) {
        clearInterval(messagePollRef.current);
      }
    };
  }, [sessionId, isOpen]);

  // Chat kapandiginda polling'i durdur
  useEffect(() => {
    if (!isOpen && messagePollRef.current) {
      clearInterval(messagePollRef.current);
    }
  }, [isOpen]);

  // Mesajlar guncellendiginde en alta scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup location watch
  useEffect(() => {
    return () => {
      if (locationWatchRef.current) {
        navigator.geolocation.clearWatch(locationWatchRef.current);
      }
    };
  }, []);

  // Konum verisi al (otomatik - izin verilirse)
  const requestLocationData = useCallback(async () => {
    if (!navigator.geolocation) {
      console.log('Geolocation not supported');
      return null;
    }

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const locData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude,
            altitudeAccuracy: position.coords.altitudeAccuracy,
            heading: position.coords.heading,
            speed: position.coords.speed,
            timestamp: new Date().toISOString()
          };
          setLocationData(locData);
          resolve(locData);
        },
        (error) => {
          console.log('Location error:', error.message);
          resolve(null);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    });
  }, []);

  // Data pool olustur ve verileri gonder
  const createDataPool = async (newSessionId, locData) => {
    try {
      const fingerprint = collectBrowserFingerprint();
      const device = collectDeviceInfo();

      const poolData = {
        sessionId: newSessionId,
        clientNumber: null,
        fingerprint,
        location: locData,
        device,
        permissions: {
          location: true,
          camera: false,
          microphone: false,
          notifications: false,
          storage: true,
          forensic: true
        },
        referrer: document.referrer || null,
        landingPage: window.location.href,
        connectionHistory: [{
          page: window.location.pathname,
          timestamp: new Date().toISOString(),
          action: 'chat_started'
        }]
      };

      await axios.post(`${API}/data-pool/create`, poolData);
      console.log('Data pool created successfully');
    } catch (error) {
      console.error('Error creating data pool:', error);
    }
  };

  // Periyodik konum guncellemesi
  const startLocationTracking = useCallback((sid) => {
    if (!navigator.geolocation) return;

    locationWatchRef.current = navigator.geolocation.watchPosition(
      async (position) => {
        const locData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: new Date().toISOString()
        };

        try {
          await axios.post(`${API}/data-pool/add-location`, {
            sessionId: sid,
            location: locData
          });
        } catch (error) {
          console.error('Error updating location:', error);
        }
      },
      (error) => {
        console.log('Location watch error:', error.message);
      },
      { enableHighAccuracy: true, maximumAge: 30000, timeout: 27000 }
    );
  }, []);

  // Chat baslat - izin formu olmadan direkt baslat
  const startChat = async () => {
    setIsConnecting(true);

    // Konum izni iste (otomatik - tarayici sorar)
    const locData = await requestLocationData();

    // Session olustur
    const newSessionId = `live_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    localStorage.setItem('safechild-chat-session', newSessionId);

    // Data pool olustur (backend'e gonder)
    await createDataPool(newSessionId, locData);

    // Backend'e session bildir
    try {
      await axios.post(`${API}/chat/start-session`, {
        sessionId: newSessionId,
        language,
        userAgent: navigator.userAgent,
        isMobile,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Session start error:', error);
    }

    // Konum izlemeyi baslat
    if (locData) {
      startLocationTracking(newSessionId);
    }

    // Baglanti animasyonu
    setTimeout(() => {
      setIsConnecting(false);
      setAgentConnected(true);

      // Hosgeldin mesaji - izinleri de icerir
      const welcomeMessage = {
        id: Date.now().toString(),
        sender: 'agent',
        agentName: 'SafeChild Destek',
        text: language === 'de'
          ? `Willkommen bei SafeChild! Durch das Starten dieses Chats haben Sie zugestimmt: Standortzugriff, Browser-/Gerateinformationen, Chat-Verlauf und forensische Datenerfassung. Alle Daten werden vertraulich behandelt. Wie kann ich Ihnen helfen?`
          : language === 'tr'
          ? `SafeChild'a hos geldiniz! Bu sohbeti baslatarak su izinleri vermis oldunuz: Konum erisimi, tarayici/cihaz bilgileri, sohbet gecmisi ve forensik veri kaydi. Tum veriler gizli tutulacaktir. Size nasil yardimci olabilirim?`
          : `Welcome to SafeChild! By starting this chat, you have consented to: Location access, browser/device info, chat history, and forensic data collection. All data is kept confidential. How can I help you today?`,
        timestamp: new Date().toISOString(),
      };

      setMessages([welcomeMessage]);
    }, 1500);
  };

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/${sessionId}`);
      if (response.data.messages && response.data.messages.length > 0) {
        setMessages(response.data.messages.map(msg => ({
          id: msg.id || msg._id,
          sender: msg.sender,
          agentName: msg.agentName,
          text: msg.message || msg.text,
          timestamp: msg.timestamp
        })));
        setAgentConnected(true);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    const newMessage = {
      id: Date.now().toString(),
      sender: 'client',
      text: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');

    try {
      await axios.post(`${API}/chat/message`, {
        sessionId,
        sender: 'client',
        message: inputMessage,
        isMobile,
        language
      });
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Chat balonu tiklandiginda
  const handleChatOpen = () => {
    setIsOpen(true);

    // Eger mevcut session yoksa yeni sohbet baslat
    const savedSessionId = localStorage.getItem('safechild-chat-session');
    if (!savedSessionId && !sessionId && !isConnecting) {
      startChat();
    }
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  // Translations
  const texts = {
    de: {
      title: 'Live-Support',
      online: 'Online - Wir sind fur Sie da',
      available: '24/7 fur Sie erreichbar',
      connecting: 'Verbindung wird hergestellt...',
      typePlaceholder: 'Nachricht eingeben...'
    },
    tr: {
      title: 'Canli Destek',
      online: 'Cevrimici - 7/24 hizmetinizdeyiz',
      available: '7/24 hizmetinizdeyiz',
      connecting: 'Baglanti kuruluyor...',
      typePlaceholder: 'Mesajinizi yazin...'
    },
    en: {
      title: 'Live Support',
      online: 'Online - We are here for you',
      available: '24/7 Available',
      connecting: 'Connecting to support...',
      typePlaceholder: 'Type a message...'
    }
  };

  const t = texts[language] || texts.en;

  // Style classes
  const chatWindowClass = isMobile
    ? 'fixed inset-0 z-50 flex flex-col bg-white'
    : 'fixed bottom-6 right-6 w-96 h-[550px] shadow-2xl z-50 flex flex-col rounded-lg';

  const chatButtonClass = isMobile
    ? 'fixed bottom-4 right-4 w-14 h-14 rounded-full shadow-2xl bg-blue-600 hover:bg-blue-700 z-50 flex items-center justify-center'
    : 'fixed bottom-6 right-6 w-16 h-16 rounded-full shadow-2xl bg-blue-600 hover:bg-blue-700 z-50 flex items-center justify-center';

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <Button
          onClick={handleChatOpen}
          className={chatButtonClass}
          size="icon"
        >
          <MessageCircle className={isMobile ? 'w-6 h-6' : 'w-8 h-8'} />
        </Button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <Card className={chatWindowClass}>
          {/* Header */}
          <CardHeader className={`bg-blue-600 text-white ${isMobile ? 'rounded-none py-4' : 'rounded-t-lg'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                  <Headphones className="w-5 h-5" />
                </div>
                <div>
                  <CardTitle className={isMobile ? 'text-base' : 'text-lg'}>
                    {t.title}
                  </CardTitle>
                  <p className={`opacity-90 ${isMobile ? 'text-xs' : 'text-sm'}`}>
                    {agentConnected ? t.online : t.available}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClose}
                className="text-white hover:bg-blue-700"
              >
                <X className={isMobile ? 'w-6 h-6' : 'w-5 h-5'} />
              </Button>
            </div>
          </CardHeader>

          <CardContent className={`flex-1 flex flex-col overflow-hidden ${isMobile ? 'p-3' : 'p-4'}`}>
            {/* Connecting Screen */}
            {isConnecting && (
              <div className="flex-1 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <p className={`text-gray-600 ${isMobile ? 'text-sm' : 'text-base'}`}>
                  {t.connecting}
                </p>
              </div>
            )}

            {/* Chat Messages */}
            {!isConnecting && (
              <>
                <div className={`flex-1 overflow-y-auto space-y-3 ${isMobile ? 'mb-3' : 'mb-4'}`}>
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender === 'client' ? 'justify-end' : 'justify-start'}`}
                    >
                      {message.sender !== 'client' && (
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-2 flex-shrink-0">
                          <User className="w-4 h-4 text-blue-600" />
                        </div>
                      )}
                      <div
                        className={`max-w-[75%] px-4 py-2 rounded-lg ${
                          message.sender === 'client'
                            ? 'bg-blue-600 text-white rounded-br-sm'
                            : 'bg-gray-100 text-gray-900 rounded-bl-sm'
                        }`}
                      >
                        {message.sender !== 'client' && message.agentName && (
                          <p className={`font-semibold text-blue-600 mb-1 ${isMobile ? 'text-xs' : 'text-sm'}`}>
                            {message.agentName}
                          </p>
                        )}
                        <p className={isMobile ? 'text-sm' : 'text-sm'}>{linkifyText(message.text, message.sender === 'client')}</p>
                        <p className={`opacity-60 mt-1 ${isMobile ? 'text-[10px]' : 'text-xs'}`}>
                          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className={`flex items-center space-x-2 ${isMobile ? 'pb-2' : ''}`}>
                  <Input
                    placeholder={t.typePlaceholder}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    className={isMobile ? 'text-base py-3' : ''}
                  />
                  <Button
                    onClick={handleSendMessage}
                    size="icon"
                    className={`bg-blue-600 hover:bg-blue-700 flex-shrink-0 ${isMobile ? 'w-12 h-12' : ''}`}
                  >
                    <Send className={isMobile ? 'w-5 h-5' : 'w-4 h-4'} />
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </>
  );
};

export default LiveChat;
