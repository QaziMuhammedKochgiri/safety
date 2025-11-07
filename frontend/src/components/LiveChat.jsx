import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { MessageCircle, X, Send } from 'lucide-react';
import ConsentModal from './ConsentModal';
import { Input } from './ui/input';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LiveChat = () => {
  const { language } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [showConsent, setShowConsent] = useState(false);
  const [hasConsent, setHasConsent] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    // Check if user has already given consent
    const savedConsent = localStorage.getItem('safechild-consent');
    if (savedConsent) {
      const consentData = JSON.parse(savedConsent);
      setHasConsent(true);
      setSessionId(consentData.sessionId || `session_${Date.now()}`);
    }
  }, []);

  useEffect(() => {
    // Load chat history when session is available
    if (sessionId && isOpen && messages.length === 0) {
      loadChatHistory();
    }
  }, [sessionId, isOpen]);

  const handleChatOpen = () => {
    if (!hasConsent) {
      setShowConsent(true);
    } else {
      setIsOpen(true);
      // Add welcome message if no messages yet
      if (messages.length === 0) {
        setMessages([{
          id: 1,
          sender: 'bot',
          text: language === 'de'
            ? 'Willkommen! Wie können wir Ihnen helfen?'
            : 'Welcome! How can we help you?',
          timestamp: new Date(),
        }]);
      }
    }
  };

  const loadChatHistory = async () => {
    if (!sessionId) return;
    
    try {
      const response = await axios.get(`${API}/chat/${sessionId}`);
      if (response.data.messages && response.data.messages.length > 0) {
        setMessages(response.data.messages);
      } else {
        // Add welcome message if no history
        const welcomeMessage = {
          id: Date.now().toString(),
          sender: 'bot',
          text: language === 'de'
            ? 'Willkommen! Wie können wir Ihnen helfen?'
            : 'Welcome! How can we help you?',
          timestamp: new Date().toISOString(),
        };
        setMessages([welcomeMessage]);
        // Save welcome message to backend
        await axios.post(`${API}/chat/message`, {
          sessionId,
          sender: 'bot',
          message: welcomeMessage.text,
        });
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const handleConsentAccept = () => {
    const savedConsent = localStorage.getItem('safechild-consent');
    const consentData = JSON.parse(savedConsent);
    const newSessionId = consentData.sessionId || `session_${Date.now()}`;
    
    setHasConsent(true);
    setSessionId(newSessionId);
    setShowConsent(false);
    setIsOpen(true);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    const newMessage = {
      id: Date.now().toString(),
      sender: 'client',
      text: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages([...messages, newMessage]);
    setInputMessage('');

    try {
      // Send message to backend
      await axios.post(`${API}/chat/message`, {
        sessionId,
        sender: 'client',
        message: inputMessage,
      });

      // Simulate bot response
      setTimeout(async () => {
        const botResponse = {
          id: Date.now().toString(),
          sender: 'bot',
          text: language === 'de'
            ? 'Vielen Dank für Ihre Nachricht. Ein Mitarbeiter wird sich in Kürze bei Ihnen melden.'
            : 'Thank you for your message. A team member will be with you shortly.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, botResponse]);
        
        // Save bot response to backend
        await axios.post(`${API}/chat/message`, {
          sessionId,
          sender: 'bot',
          message: botResponse.text,
        });
      }, 1000);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <Button
          onClick={handleChatOpen}
          className="fixed bottom-6 right-6 w-16 h-16 rounded-full shadow-2xl bg-blue-600 hover:bg-blue-700 z-50 flex items-center justify-center"
          size="icon"
        >
          <MessageCircle className="w-8 h-8" />
        </Button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <Card className="fixed bottom-6 right-6 w-96 h-[500px] shadow-2xl z-50 flex flex-col">
          <CardHeader className="bg-blue-600 text-white rounded-t-lg">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{t(language, 'chatTitle')}</CardTitle>
                <p className="text-sm opacity-90">{t(language, 'chatDescription')}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
                className="text-white hover:bg-blue-700"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-4 overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-2 rounded-lg ${
                      message.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm">{message.text}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Input */}
            <div className="flex items-center space-x-2">
              <Input
                placeholder={language === 'de' ? 'Nachricht eingeben...' : 'Type a message...'}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              />
              <Button
                onClick={handleSendMessage}
                size="icon"
                className="bg-blue-600 hover:bg-blue-700 flex-shrink-0"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Consent Modal */}
      <ConsentModal
        open={showConsent}
        onClose={() => setShowConsent(false)}
        onAccept={handleConsentAccept}
      />
    </>
  );
};

export default LiveChat;
