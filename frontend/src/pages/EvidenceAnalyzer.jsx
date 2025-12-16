import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Package, ArrowLeft, Loader2, Download } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EvidenceAnalyzer = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [evidenceList, setEvidenceList] = useState('');

  const handleAnalyze = async () => {
    if (!evidenceList.trim()) {
      toast.error('Please describe your evidence');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/ai/analyze-evidence`,
        {
          case_id: `case_${Date.now()}`,
          evidence_items: evidenceList.split('\n').filter(e => e.trim()).map((e, idx) => ({
            evidence_id: `ev_${idx}`,
            evidence_type: 'document',
            description: e.trim(),
            date_obtained: new Date().toISOString()
          }))
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
      toast.success('Evidence analyzed!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getRelevanceColor = (relevance) => {
    const colors = {
      critical: 'bg-red-100 text-red-700',
      high: 'bg-orange-100 text-orange-700',
      moderate: 'bg-yellow-100 text-yellow-700',
      low: 'bg-blue-100 text-blue-700',
      minimal: 'bg-gray-100 text-gray-700'
    };
    return colors[relevance] || colors.moderate;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />Back
        </Button>
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-3xl shadow-2xl p-8 text-white mb-8">
          <div className="flex items-center gap-4">
            <div className="bg-white/20 p-4 rounded-2xl">
              <Package className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-2">Evidence Analyzer</h1>
              <p className="text-indigo-100 text-lg">Organize and analyze your evidence for court</p>
            </div>
          </div>
        </div>

        {!result ? (
          <Card className="border-2 shadow-xl">
            <CardHeader>
              <CardTitle>List Your Evidence</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <textarea
                value={evidenceList}
                onChange={(e) => setEvidenceList(e.target.value)}
                placeholder="List each piece of evidence on a new line:&#10;- Text message from ex-spouse threatening custody&#10;- Photo of child's bruise from incident on May 15&#10;- Police report from June 1&#10;- School records showing attendance issues..."
                rows={12}
                className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <Button
                onClick={handleAnalyze}
                disabled={loading || !evidenceList.trim()}
                className="w-full h-14 text-lg bg-gradient-to-r from-indigo-600 to-purple-600"
              >
                {loading ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Analyzing...</> :
                <><Package className="w-5 h-5 mr-2" />Analyze Evidence</>}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader><CardTitle>Analyzed Evidence Items</CardTitle></CardHeader>
              <CardContent>
                {result.analyzed_items.map((item, idx) => (
                  <div key={idx} className="mb-4 p-4 border rounded-lg">
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold">{item.description || item.evidence_id}</span>
                      <Badge className={getRelevanceColor(item.relevance)}>{item.relevance}</Badge>
                    </div>
                    <p className="text-sm text-gray-600">{item.legal_significance}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Button onClick={() => setResult(null)} variant="outline" className="w-full">
              New Analysis
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidenceAnalyzer;
