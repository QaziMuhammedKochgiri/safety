import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  FileText, ArrowLeft, Loader2, Download, CheckCircle, Copy
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PetitionGenerator = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    petitionType: 'custody',
    jurisdiction: 'turkey',
    language: 'en',
    caseDetails: '',
    clientName: '',
    opposingPartyName: '',
    childrenInfo: ''
  });

  const petitionTypes = [
    { value: 'custody', label: 'Custody Petition' },
    { value: 'protection_order', label: 'Protection Order' },
    { value: 'emergency_custody', label: 'Emergency Custody' },
    { value: 'modification', label: 'Custody Modification' },
    { value: 'enforcement', label: 'Custody Enforcement' },
    { value: 'visitation', label: 'Visitation Rights' }
  ];

  const jurisdictions = [
    { value: 'turkey', label: 'Turkey (TMK)' },
    { value: 'germany', label: 'Germany (BGB)' },
    { value: 'eu', label: 'European Union (Brussels IIa)' },
    { value: 'us', label: 'United States (UCCJEA)' },
    { value: 'uk', label: 'United Kingdom' }
  ];

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'tr', label: 'Turkish' },
    { value: 'de', label: 'German' }
  ];

  const handleGenerate = async () => {
    if (!formData.caseDetails.trim()) {
      toast.error('Please provide case details');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/ai/generate-petition`,
        {
          petition_type: formData.petitionType,
          jurisdiction: formData.jurisdiction,
          language: formData.language,
          case_details: formData.caseDetails,
          client_name: formData.clientName,
          opposing_party_name: formData.opposingPartyName,
          children_info: formData.childrenInfo
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
      toast.success('Petition generated successfully!');
    } catch (error) {
      console.error('Petition generation error:', error);
      toast.error(error.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const downloadPetition = () => {
    if (!result) return;
    const timestamp = Date.now();
    const blob = new Blob([result.petition_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `petition-${timestamp}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Petition downloaded!');
  };

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.petition_text);
    toast.success('Copied to clipboard!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-50">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        <div className="mb-8">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-3xl shadow-2xl p-8 text-white">
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-4 rounded-2xl">
                <FileText className="w-12 h-12" />
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-2">Petition Generator</h1>
                <p className="text-blue-100 text-lg">
                  Generate court-ready legal documents instantly
                </p>
              </div>
            </div>
          </div>
        </div>

        {!result ? (
          <Card className="border-2 shadow-xl">
            <CardHeader>
              <CardTitle className="text-2xl">Document Details</CardTitle>
              <CardDescription>
                Fill in the information below to generate a professional petition
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Petition Type</label>
                  <select
                    value={formData.petitionType}
                    onChange={(e) => setFormData({ ...formData, petitionType: e.target.value })}
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {petitionTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Jurisdiction</label>
                  <select
                    value={formData.jurisdiction}
                    onChange={(e) => setFormData({ ...formData, jurisdiction: e.target.value })}
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {jurisdictions.map(j => (
                      <option key={j.value} value={j.value}>{j.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Language</label>
                  <select
                    value={formData.language}
                    onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {languages.map(lang => (
                      <option key={lang.value} value={lang.value}>{lang.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Your Name</label>
                  <input
                    type="text"
                    value={formData.clientName}
                    onChange={(e) => setFormData({ ...formData, clientName: e.target.value })}
                    placeholder="Jane Doe"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Opposing Party Name</label>
                  <input
                    type="text"
                    value={formData.opposingPartyName}
                    onChange={(e) => setFormData({ ...formData, opposingPartyName: e.target.value })}
                    placeholder="John Doe"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Children Info</label>
                  <input
                    type="text"
                    value={formData.childrenInfo}
                    onChange={(e) => setFormData({ ...formData, childrenInfo: e.target.value })}
                    placeholder="Sarah, 8 years old"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Case Details *</label>
                <textarea
                  value={formData.caseDetails}
                  onChange={(e) => setFormData({ ...formData, caseDetails: e.target.value })}
                  placeholder="Provide detailed information about your case, including relevant facts, incidents, and what you're requesting from the court..."
                  rows={8}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <Button
                onClick={handleGenerate}
                disabled={loading || !formData.caseDetails.trim()}
                className="w-full h-14 text-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5 mr-2" />
                    Generate Petition
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card className="border-2 shadow-xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    Petition Generated Successfully
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button onClick={copyToClipboard} variant="outline">
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </Button>
                    <Button onClick={downloadPetition}>
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 rounded-lg p-6 max-h-[600px] overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm font-mono">
                    {result.petition_text}
                  </pre>
                </div>
              </CardContent>
            </Card>

            <Button
              onClick={() => setResult(null)}
              variant="outline"
              className="w-full"
            >
              Generate New Petition
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PetitionGenerator;
