import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Loader2,
  CheckCircle2,
  Smartphone,
  Send,
  Shield,
  AlertCircle,
  Clock,
  Phone,
  Copy,
  Check
} from 'lucide-react';
import axios from 'axios';

const API_URL = '/api';

const ClientSocialConnect = () => {
  const { token } = useParams();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requestInfo, setRequestInfo] = useState(null);

  // Platform and phone number
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneError, setPhoneError] = useState('');

  // Session states
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [pairingCode, setPairingCode] = useState(null);
  const [codeCopied, setCodeCopied] = useState(false);

  // Load request info on mount
  useEffect(() => {
    loadRequestInfo();
  }, [token]);

  const loadRequestInfo = async () => {
    try {
      const response = await axios.get(`${API_URL}/requests/social/${token}`);
      setRequestInfo(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('invalid');
      } else if (err.response?.status === 410) {
        setError('expired');
      } else {
        setError('error');
      }
    } finally {
      setLoading(false);
    }
  };

  // Validate phone number (basic validation)
  const validatePhoneNumber = (number) => {
    // Remove all non-digits except +
    const cleaned = number.replace(/[^\d+]/g, '');
    // Should start with + and country code, minimum 10 digits
    if (!cleaned.startsWith('+')) {
      return 'Phone number must start with country code (e.g., +49 for Germany)';
    }
    if (cleaned.length < 11) {
      return 'Please enter a valid phone number with country code';
    }
    return '';
  };

  // Handle phone number change
  const handlePhoneChange = (e) => {
    const value = e.target.value;
    setPhoneNumber(value);
    if (value.length > 3) {
      setPhoneError(validatePhoneNumber(value));
    } else {
      setPhoneError('');
    }
  };

  // Start session with pairing code
  const startSession = async (platform) => {
    // Validate phone for WhatsApp
    if (platform === 'whatsapp') {
      const error = validatePhoneNumber(phoneNumber);
      if (error) {
        setPhoneError(error);
        return;
      }
    }

    setSelectedPlatform(platform);
    setStatus('initializing');
    setPairingCode(null);

    try {
      const endpoint = platform === 'telegram'
        ? `${API_URL}/telegram/session/start`
        : `${API_URL}/whatsapp/session/start`;

      const payload = {
        clientNumber: requestInfo.clientNumber,
        platform,
        token
      };

      // For WhatsApp, use pairing code
      if (platform === 'whatsapp') {
        payload.usePairingCode = true;
        payload.phoneNumber = phoneNumber;
      }

      const response = await axios.post(endpoint, payload);
      setSessionId(response.data.sessionId);
      setStatus('waiting');
    } catch (err) {
      console.error('Session start error:', err);
      setStatus('error');
    }
  };

  // Poll session status
  useEffect(() => {
    if (!sessionId || status === 'completed' || status === 'error') return;

    const interval = setInterval(async () => {
      try {
        const endpoint = selectedPlatform === 'telegram'
          ? `${API_URL}/telegram/session/${sessionId}/status`
          : `${API_URL}/whatsapp/session/${sessionId}/status`;

        const response = await axios.get(endpoint);
        const data = response.data;

        // Handle pairing code
        if (data.status === 'pairing_code_ready' && data.pairingCode) {
          setPairingCode(data.pairingCode);
          setStatus('pairing_code_ready');
        }
        // Handle QR (fallback for Telegram or if pairing fails)
        else if ((data.status === 'qr_ready' || data.status === 'waiting_for_scan') && data.qr) {
          // For now, just show error - we need pairing code for mobile
          setStatus('qr_fallback');
        }
        else if (data.status === 'connected' || data.status === 'extracting') {
          setStatus('extracting');
          setPairingCode(null);
        }
        else if (data.status === 'completed') {
          setStatus('completed');
          setPairingCode(null);
          // Notify backend about completion
          try {
            await axios.post(`${API_URL}/requests/social/${token}/complete`, {
              platform: selectedPlatform,
              sessionId: sessionId
            });
          } catch (e) {
            console.error('Failed to notify completion:', e);
          }
          clearInterval(interval);
        }
        else if (data.status === 'timeout' || data.status === 'failed') {
          setStatus('error');
          setPairingCode(null);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionId, status, selectedPlatform, token]);

  // Reset session
  const resetSession = () => {
    setSelectedPlatform(null);
    setSessionId(null);
    setStatus('idle');
    setPairingCode(null);
    setPhoneNumber('');
    setPhoneError('');
  };

  // Copy pairing code
  const copyPairingCode = async () => {
    if (!pairingCode) return;
    try {
      await navigator.clipboard.writeText(pairingCode);
      setCodeCopied(true);
      setTimeout(() => setCodeCopied(false), 3000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Error states
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              {error === 'invalid' && 'Invalid Link'}
              {error === 'expired' && 'Link Expired'}
              {error === 'error' && 'Something went wrong'}
            </h2>
            <p className="text-gray-600">
              {error === 'invalid' && 'This link is not valid. Please contact your lawyer for a new link.'}
              {error === 'expired' && 'This link has expired. Please contact your lawyer for a new link.'}
              {error === 'error' && 'An error occurred. Please try again later.'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 py-8 px-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <Shield className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Secure Data Connection
          </h1>
          <p className="text-gray-600">
            Hello {requestInfo?.clientName || 'Valued Client'}, please connect your messaging app to securely share data with your legal team.
          </p>
        </div>

        {/* Main Card */}
        <Card className="border-2 shadow-lg">
          <CardHeader className="text-center border-b bg-gray-50">
            <CardTitle className="text-lg">Connect Your Account</CardTitle>
            <CardDescription>
              Your data will be securely encrypted and only accessible by your legal team.
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-6">
            {/* Platform Selection with Phone Input */}
            {status === 'idle' && !selectedPlatform && (
              <div className="space-y-6">
                {requestInfo?.platforms?.includes('whatsapp') && (
                  <div className="space-y-4 p-4 border-2 border-green-200 rounded-lg bg-green-50">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                        <Smartphone className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">WhatsApp</h3>
                        <p className="text-sm text-gray-600">Connect using your phone number</p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-sm font-medium">
                        Your WhatsApp Phone Number
                      </Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="phone"
                          type="tel"
                          placeholder="+49 123 456 7890"
                          value={phoneNumber}
                          onChange={handlePhoneChange}
                          className="pl-10"
                        />
                      </div>
                      {phoneError && (
                        <p className="text-sm text-red-500">{phoneError}</p>
                      )}
                      <p className="text-xs text-gray-500">
                        Enter your number with country code (e.g., +49 for Germany, +90 for Turkey)
                      </p>
                    </div>

                    <Button
                      className="w-full h-12 bg-green-600 hover:bg-green-700"
                      onClick={() => startSession('whatsapp')}
                      disabled={!phoneNumber || phoneError}
                    >
                      <Smartphone className="w-5 h-5 mr-2" />
                      Connect WhatsApp
                    </Button>
                  </div>
                )}

                {requestInfo?.platforms?.includes('telegram') && (
                  <div className="p-4 border-2 border-blue-200 rounded-lg bg-blue-50">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                        <Send className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">Telegram</h3>
                        <p className="text-sm text-gray-600">Requires scanning QR code</p>
                      </div>
                    </div>
                    <Alert className="mb-4 bg-yellow-50 border-yellow-200">
                      <AlertCircle className="h-4 w-4 text-yellow-600" />
                      <AlertDescription className="text-yellow-800 text-sm">
                        Telegram requires a computer to scan the QR code.
                      </AlertDescription>
                    </Alert>
                    <Button
                      variant="outline"
                      className="w-full h-12 border-blue-300 text-blue-600 hover:bg-blue-100"
                      onClick={() => startSession('telegram')}
                    >
                      <Send className="w-5 h-5 mr-2" />
                      Connect Telegram
                    </Button>
                  </div>
                )}

                <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                  <Clock className="w-4 h-4" />
                  <span>Link expires: {new Date(requestInfo?.expiresAt).toLocaleString()}</span>
                </div>
              </div>
            )}

            {/* Initializing */}
            {(status === 'initializing' || status === 'waiting') && (
              <div className="text-center py-8">
                <Loader2 className="h-12 w-12 animate-spin mx-auto text-blue-600 mb-4" />
                <p className="text-gray-600">Preparing secure connection...</p>
                <p className="text-sm text-gray-500 mt-2">This may take a moment</p>
              </div>
            )}

            {/* Pairing Code Ready */}
            {status === 'pairing_code_ready' && pairingCode && (
              <div className="text-center py-4">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Enter this code in WhatsApp
                  </h3>
                  <p className="text-sm text-gray-600">
                    Open WhatsApp on your phone and enter the code below
                  </p>
                </div>

                {/* Large Pairing Code Display */}
                <div
                  className="bg-gray-900 text-white py-6 px-4 rounded-xl mb-4 cursor-pointer hover:bg-gray-800 transition-colors"
                  onClick={copyPairingCode}
                >
                  <div className="text-4xl font-mono tracking-[0.5em] font-bold">
                    {pairingCode.split('').map((char, i) => (
                      <span key={i} className={i === 3 ? 'ml-4' : ''}>
                        {char}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center justify-center gap-2 mt-3 text-gray-400 text-sm">
                    {codeCopied ? (
                      <>
                        <Check className="w-4 h-4 text-green-400" />
                        <span className="text-green-400">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        <span>Tap to copy</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Instructions */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-left mb-4">
                  <h4 className="font-semibold text-green-800 mb-2">How to enter the code:</h4>
                  <ol className="text-sm text-green-700 space-y-1">
                    <li>1. Open <strong>WhatsApp</strong> on your phone</li>
                    <li>2. Go to <strong>Settings</strong> → <strong>Linked Devices</strong></li>
                    <li>3. Tap <strong>Link a Device</strong></li>
                    <li>4. Tap <strong>Link with phone number instead</strong></li>
                    <li>5. Enter the 8-character code above</li>
                  </ol>
                </div>

                <Button variant="outline" size="sm" onClick={resetSession}>
                  Cancel
                </Button>
              </div>
            )}

            {/* QR Fallback (for Telegram or if pairing fails) */}
            {status === 'qr_fallback' && (
              <div className="text-center py-8">
                <Alert className="mb-4 bg-yellow-50 border-yellow-200">
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-yellow-800">
                    {selectedPlatform === 'telegram'
                      ? 'Telegram requires scanning a QR code. Please open this link on a computer.'
                      : 'Pairing code is not available. Please try again or open this link on a computer to scan the QR code.'}
                  </AlertDescription>
                </Alert>
                <Button onClick={resetSession}>
                  Try Again
                </Button>
              </div>
            )}

            {/* Extracting */}
            {status === 'extracting' && (
              <div className="text-center py-8">
                <div className="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Loader2 className="h-10 w-10 animate-spin text-yellow-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Extracting Data...
                </h3>
                <p className="text-gray-600 text-sm max-w-xs mx-auto">
                  Please wait while we securely retrieve your messages. This may take a few minutes.
                </p>
              </div>
            )}

            {/* Completed */}
            {status === 'completed' && (
              <div className="text-center py-8">
                <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="h-12 w-12 text-green-600" />
                </div>
                <h3 className="text-2xl font-bold text-green-700 mb-2">
                  Success!
                </h3>
                <p className="text-gray-600 mb-4">
                  Your {selectedPlatform === 'whatsapp' ? 'WhatsApp' : 'Telegram'} data has been securely transferred to your legal team.
                </p>

                {/* Option to connect another platform */}
                {requestInfo?.platforms?.length > 1 && (
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={resetSession}
                  >
                    Connect Another App
                  </Button>
                )}
              </div>
            )}

            {/* Error */}
            {status === 'error' && (
              <div className="text-center py-8">
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>
                    Connection failed or timed out. Please try again.
                  </AlertDescription>
                </Alert>
                <Button onClick={resetSession}>
                  Try Again
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Security Notice */}
        <div className="mt-6 text-center text-xs text-gray-500">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Shield className="w-4 h-4" />
            <span className="font-medium">End-to-End Encrypted</span>
          </div>
          <p>Your data is encrypted and only accessible by your legal team at SafeChild.</p>
        </div>
      </div>
    </div>
  );
};

export default ClientSocialConnect;
