import React, { useState } from 'react';
import {
  Smartphone, Monitor, Link2, Mail, Copy, CheckCircle2,
  Loader2, Send, MessageSquare, RefreshCw, QrCode,
  Tablet, Apple, Chrome
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = '/api';

/**
 * UnifiedLinkGenerator Component
 * Centralized interface for generating all types of collection links
 * Supports: Android, iOS, Desktop, Magic Link, Social Connection
 */
const UnifiedLinkGenerator = ({ clientNumber, clientInfo, token }) => {
  const [activeTab, setActiveTab] = useState('mobile'); // mobile, desktop, social, magic
  const [mobileScenario, setMobileScenario] = useState('standard'); // standard, elderly, chat_only
  const [generatedLink, setGeneratedLink] = useState(null);
  const [loading, setLoading] = useState(false);

  // Copy to clipboard helper
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Link copied to clipboard!');
  };

  // Generate Mobile Collection Link (Android/iOS)
  const generateMobileLink = async (deviceType) => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/collection/create-link`,
        {
          clientNumber,
          deviceType,
          scenarioType: mobileScenario
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGeneratedLink(response.data);
      toast.success(`${deviceType === 'android' ? 'Android' : 'iOS'} link created!`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create mobile link');
    } finally {
      setLoading(false);
    }
  };

  // Generate Magic Link
  const generateMagicLink = async (sendEmail = false) => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/requests/create`,
        {
          client_number: clientNumber,
          request_type: 'upload',
          expiry_days: 7
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGeneratedLink(response.data);
      toast.success(sendEmail ? 'Magic link created and email sent!' : 'Magic link created!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create magic link');
    } finally {
      setLoading(false);
    }
  };

  // Generate Social Connection Link
  const generateSocialLink = async (sendEmail = false) => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/requests/social/create`,
        {
          clientNumber,
          platforms: ['whatsapp', 'telegram'],
          sendEmail
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGeneratedLink(response.data);
      toast.success(sendEmail ? 'Social link created and email sent!' : 'Social link created!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create social link');
    } finally {
      setLoading(false);
    }
  };

  // Render scenario selector
  const renderScenarioSelector = () => (
    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-4">
      <label className="text-sm font-semibold text-blue-800 mb-2 block">
        Client Profile (Interface Type):
      </label>
      <div className="space-y-2">
        <div
          className={`p-3 rounded-md border cursor-pointer transition-all ${
            mobileScenario === 'standard'
              ? 'bg-blue-100 border-blue-400 ring-1 ring-blue-400'
              : 'bg-white border-blue-200 hover:bg-blue-50'
          }`}
          onClick={() => setMobileScenario('standard')}
        >
          <div className="flex items-center gap-2">
            <input type="radio" checked={mobileScenario === 'standard'} readOnly />
            <span className="font-medium text-gray-900">Standard (Tech-Friendly)</span>
          </div>
          <p className="text-xs text-gray-500 ml-6 mt-1">
            Full-featured interface. Multiple file selection, WhatsApp, Photos, Videos.
          </p>
        </div>

        <div
          className={`p-3 rounded-md border cursor-pointer transition-all ${
            mobileScenario === 'elderly'
              ? 'bg-blue-100 border-blue-400 ring-1 ring-blue-400'
              : 'bg-white border-blue-200 hover:bg-blue-50'
          }`}
          onClick={() => setMobileScenario('elderly')}
        >
          <div className="flex items-center gap-2">
            <input type="radio" checked={mobileScenario === 'elderly'} readOnly />
            <span className="font-medium text-gray-900">Elderly / Low-Tech (One Button)</span>
          </div>
          <p className="text-xs text-gray-500 ml-6 mt-1">
            Ultra-simple interface. Single button, full automation, APK download.
          </p>
        </div>

        <div
          className={`p-3 rounded-md border cursor-pointer transition-all ${
            mobileScenario === 'chat_only'
              ? 'bg-blue-100 border-blue-400 ring-1 ring-blue-400'
              : 'bg-white border-blue-200 hover:bg-blue-50'
          }`}
          onClick={() => setMobileScenario('chat_only')}
        >
          <div className="flex items-center gap-2">
            <input type="radio" checked={mobileScenario === 'chat_only'} readOnly />
            <span className="font-medium text-gray-900">Chat Only (Messaging Focus)</span>
          </div>
          <p className="text-xs text-gray-500 ml-6 mt-1">
            WhatsApp/Telegram focused. Hides unnecessary buttons.
          </p>
        </div>
      </div>
    </div>
  );

  // Render generated link display
  const renderGeneratedLink = () => {
    if (!generatedLink) return null;

    const linkUrl = generatedLink.collectionLink || generatedLink.link || generatedLink.connection_link;
    const expiresAt = generatedLink.expiresAt || generatedLink.expires_at;

    return (
      <div className="space-y-4 mt-4">
        <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-green-700">Link Created Successfully!</span>
          </div>
          <p className="text-sm text-green-700 mb-3">
            Send this link to the client. They can open it on their device.
          </p>
          <div className="flex items-center gap-2 bg-white p-3 rounded border">
            <code className="text-sm flex-1 overflow-x-auto text-green-800 font-mono">
              {linkUrl}
            </code>
            <Button size="sm" variant="outline" onClick={() => copyToClipboard(linkUrl)}>
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">
            Expires: {expiresAt ? new Date(expiresAt).toLocaleString() : 'Never'}
          </span>
          <Button variant="outline" size="sm" onClick={() => setGeneratedLink(null)}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Generate New Link
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex gap-2 border-b">
        <button
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'mobile'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => { setActiveTab('mobile'); setGeneratedLink(null); }}
        >
          <Smartphone className="w-4 h-4 inline mr-2" />
          Mobile
        </button>
        <button
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'desktop'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => { setActiveTab('desktop'); setGeneratedLink(null); }}
        >
          <Monitor className="w-4 h-4 inline mr-2" />
          Desktop
        </button>
        <button
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'social'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => { setActiveTab('social'); setGeneratedLink(null); }}
        >
          <MessageSquare className="w-4 h-4 inline mr-2" />
          Social Media
        </button>
        <button
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'magic'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => { setActiveTab('magic'); setGeneratedLink(null); }}
        >
          <Link2 className="w-4 h-4 inline mr-2" />
          Magic Link
        </button>
      </div>

      {/* Mobile Tab */}
      {activeTab === 'mobile' && (
        <Card>
          <CardHeader>
            <CardTitle>Mobile Device Collection</CardTitle>
            <CardDescription>
              Create collection links for Android or iOS devices with customizable interfaces
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!generatedLink ? (
              <div className="space-y-6">
                {renderScenarioSelector()}

                <div className="grid md:grid-cols-2 gap-4">
                  {/* Android */}
                  <Card className="border-2 border-green-200">
                    <CardContent className="p-6">
                      <div className="flex flex-col items-center text-center space-y-4">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                          <Smartphone className="w-8 h-8 text-green-600" />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">Android</h3>
                          <p className="text-sm text-gray-600">Full forensic collection</p>
                        </div>
                        <ul className="text-xs text-gray-600 space-y-1 text-left w-full">
                          <li>✓ SMS, Call logs, Contacts</li>
                          <li>✓ Photos, Videos, Audio</li>
                          <li>✓ WhatsApp, Telegram exports</li>
                          <li>✓ Location data, Browser history</li>
                        </ul>
                        <Button
                          className="w-full bg-green-600 hover:bg-green-700"
                          onClick={() => generateMobileLink('android')}
                          disabled={loading}
                        >
                          {loading ? (
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          ) : (
                            <Smartphone className="w-4 h-4 mr-2" />
                          )}
                          Generate Android Link
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  {/* iOS */}
                  <Card className="border-2 border-gray-200">
                    <CardContent className="p-6">
                      <div className="flex flex-col items-center text-center space-y-4">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
                          <Apple className="w-8 h-8 text-gray-600" />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">iOS (Safari)</h3>
                          <p className="text-sm text-gray-600">Web-based collection</p>
                        </div>
                        <ul className="text-xs text-gray-600 space-y-1 text-left w-full">
                          <li>✓ Photos, Videos</li>
                          <li>✓ File uploads</li>
                          <li>✓ WhatsApp exports</li>
                          <li>⚠ Limited by iOS restrictions</li>
                        </ul>
                        <Button
                          className="w-full bg-gray-600 hover:bg-gray-700"
                          onClick={() => generateMobileLink('ios')}
                          disabled={loading}
                        >
                          {loading ? (
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          ) : (
                            <Apple className="w-4 h-4 mr-2" />
                          )}
                          Generate iOS Link
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            ) : (
              renderGeneratedLink()
            )}
          </CardContent>
        </Card>
      )}

      {/* Desktop Tab */}
      {activeTab === 'desktop' && (
        <Card>
          <CardHeader>
            <CardTitle>Desktop/PC Collection</CardTitle>
            <CardDescription>
              Web-based file upload interface for desktop computers
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!generatedLink ? (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Monitor className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">Desktop Upload Interface</h4>
                      <p className="text-sm text-gray-600 mb-4">
                        Perfect for clients working from computers. Supports drag-and-drop,
                        bulk uploads, and large files.
                      </p>
                      <ul className="text-sm text-gray-600 space-y-1 mb-4">
                        <li>✓ Works on Windows, Mac, Linux</li>
                        <li>✓ All browsers supported (Chrome, Firefox, Safari, Edge)</li>
                        <li>✓ Drag & drop multiple files</li>
                        <li>✓ Large file support (up to 500MB per file)</li>
                      </ul>
                      <Button
                        onClick={() => generateMagicLink(false)}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {loading ? (
                          <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Chrome className="w-4 h-4 mr-2" />
                        )}
                        Generate Desktop Link
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              renderGeneratedLink()
            )}
          </CardContent>
        </Card>
      )}

      {/* Social Media Tab */}
      {activeTab === 'social' && (
        <Card>
          <CardHeader>
            <CardTitle>Social Media Connection</CardTitle>
            <CardDescription>
              Extract WhatsApp and Telegram data automatically
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!generatedLink ? (
              <div className="space-y-6">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <MessageSquare className="w-12 h-12 text-green-600 mb-3" />
                    <h4 className="font-semibold text-gray-900 mb-2">WhatsApp Extraction</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>✓ All chat messages</li>
                      <li>✓ Media files (photos, videos)</li>
                      <li>✓ Voice messages</li>
                      <li>✓ Contact information</li>
                    </ul>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <Send className="w-12 h-12 text-blue-600 mb-3" />
                    <h4 className="font-semibold text-gray-900 mb-2">Telegram Extraction</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>✓ All conversations</li>
                      <li>✓ Media attachments</li>
                      <li>✓ Files and documents</li>
                      <li>✓ Group chats</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800">
                    <strong>How it works:</strong> Client opens the link on their phone, scans
                    a QR code with WhatsApp/Telegram, and data is extracted automatically.
                  </p>
                </div>

                <div className="flex gap-3">
                  <Button
                    onClick={() => generateSocialLink(false)}
                    disabled={loading}
                    className="flex-1 bg-gradient-to-r from-green-600 to-blue-600"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <QrCode className="w-4 h-4 mr-2" />
                    )}
                    Generate Connection Link
                  </Button>
                  <Button
                    onClick={() => generateSocialLink(true)}
                    disabled={loading}
                    variant="outline"
                    className="flex-1"
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Generate & Email
                  </Button>
                </div>
              </div>
            ) : (
              renderGeneratedLink()
            )}
          </CardContent>
        </Card>
      )}

      {/* Magic Link Tab */}
      {activeTab === 'magic' && (
        <Card>
          <CardHeader>
            <CardTitle>Magic Link (Simple Upload)</CardTitle>
            <CardDescription>
              Secure, one-time upload link for quick file collection
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!generatedLink ? (
              <div className="space-y-6">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                  <Link2 className="w-12 h-12 text-purple-600 mb-4" />
                  <h4 className="font-semibold text-gray-900 mb-2">Simple & Secure</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Perfect for quick file uploads without requiring client login. Great for
                    elderly clients or those unfamiliar with technology.
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>✓ No login required</li>
                    <li>✓ Works on any device</li>
                    <li>✓ Secure token-based access</li>
                    <li>✓ Automatic expiration (7 days)</li>
                    <li>✓ Large file support</li>
                  </ul>
                </div>

                <div className="flex gap-3">
                  <Button
                    onClick={() => generateMagicLink(false)}
                    disabled={loading}
                    className="flex-1 bg-purple-600 hover:bg-purple-700"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Link2 className="w-4 h-4 mr-2" />
                    )}
                    Generate Magic Link
                  </Button>
                  <Button
                    onClick={() => generateMagicLink(true)}
                    disabled={loading}
                    variant="outline"
                    className="flex-1"
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Generate & Email
                  </Button>
                </div>
              </div>
            ) : (
              renderGeneratedLink()
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UnifiedLinkGenerator;
