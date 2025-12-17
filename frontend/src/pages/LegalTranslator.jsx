import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Languages, ArrowLeft, Loader2, Download, Copy, ArrowRightLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || "/api";

const LegalTranslator = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    sourceLanguage: 'en',
    targetLanguage: 'tr',
    text: '',
    documentType: 'legal'
  });

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'tr', label: 'Turkish (Türkçe)' },
    { value: 'de', label: 'German (Deutsch)' }
  ];

  const handleTranslate = async () => {
    if (!formData.text.trim()) {
      toast.error('Please enter text to translate');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/ai/translate`,
        {
          source_language: formData.sourceLanguage,
          target_language: formData.targetLanguage,
          text: formData.text,
          document_type: formData.documentType
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
      toast.success('Translation complete!');
    } catch (error) {
      console.error('Translation error:', error);
      toast.error(error.response?.data?.detail || 'Translation failed');
    } finally {
      setLoading(false);
    }
  };

  const swapLanguages = () => {
    setFormData({
      ...formData,
      sourceLanguage: formData.targetLanguage,
      targetLanguage: formData.sourceLanguage
    });
  };

  const copyTranslation = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.translated_text);
    toast.success('Translation copied!');
  };

  const downloadTranslation = () => {
    if (!result) return;
    const blob = new Blob([result.translated_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `translation-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Translation downloaded!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-teal-50 to-blue-50">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        <div className="mb-8">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-3xl shadow-2xl p-8 text-white">
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-4 rounded-2xl">
                <Languages className="w-12 h-12" />
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-2">Legal Translator</h1>
                <p className="text-green-100 text-lg">
                  AI-powered legal document translation with cultural context
                </p>
              </div>
            </div>
          </div>
        </div>

        <Card className="border-2 shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl">Translate Legal Document</CardTitle>
            <CardDescription>
              Professional translation preserving legal terminology
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4">
              <select
                value={formData.sourceLanguage}
                onChange={(e) => setFormData({ ...formData, sourceLanguage: e.target.value })}
                className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {languages.map(lang => (
                  <option key={lang.value} value={lang.value}>{lang.label}</option>
                ))}
              </select>

              <Button
                variant="outline"
                size="sm"
                onClick={swapLanguages}
                className="flex-shrink-0"
              >
                <ArrowRightLeft className="w-4 h-4" />
              </Button>

              <select
                value={formData.targetLanguage}
                onChange={(e) => setFormData({ ...formData, targetLanguage: e.target.value })}
                className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {languages.map(lang => (
                  <option key={lang.value} value={lang.value}>{lang.label}</option>
                ))}
              </select>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium mb-2">Source Text</label>
                <textarea
                  value={formData.text}
                  onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                  placeholder="Enter legal text to translate..."
                  rows={12}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Translation</label>
                <div className="relative">
                  <textarea
                    value={result?.translated_text || ''}
                    readOnly
                    placeholder="Translation will appear here..."
                    rows={12}
                    className="w-full px-4 py-3 border rounded-lg bg-gray-50"
                  />
                  {result && (
                    <div className="absolute top-2 right-2 flex gap-2">
                      <Button variant="ghost" size="sm" onClick={copyTranslation}>
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={downloadTranslation}>
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <Button
              onClick={handleTranslate}
              disabled={loading || !formData.text.trim()}
              className="w-full h-14 text-lg bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Translating...
                </>
              ) : (
                <>
                  <Languages className="w-5 h-5 mr-2" />
                  Translate
                </>
              )}
            </Button>

            {result?.terminology_notes && result.terminology_notes.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-2">Terminology Notes:</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  {result.terminology_notes.map((note, idx) => (
                    <li key={idx}>• {note}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LegalTranslator;
