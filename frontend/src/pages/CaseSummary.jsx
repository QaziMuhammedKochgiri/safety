import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Scale, ArrowLeft, Loader2, Download, Copy } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || "/api";

const CaseSummary = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    caseDetails: '',
    evidence: '',
    goals: ''
  });

  const handleGenerate = async () => {
    if (!formData.caseDetails.trim()) {
      toast.error('Please provide case details');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/ai/generate-case-summary`,
        {
          case_id: `case_${Date.now()}`,
          case_facts: formData.caseDetails,
          evidence_summary: formData.evidence,
          desired_outcome: formData.goals
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
      toast.success('Case summary generated!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const copySummary = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied!');
  };

  const downloadSummary = () => {
    if (!result) return;
    const fullSummary = `
CASE SUMMARY - COMPLETE PACKAGE

ELEVATOR PITCH:
${result.elevator_pitch}

ONE-PAGE SUMMARY:
${result.one_page_summary}

DETAILED SUMMARY:
${result.detailed_summary}

LEGAL BASIS:
${result.legal_basis}

KEY ARGUMENTS:
${result.key_arguments.map((arg, i) => `${i + 1}. ${arg}`).join('\n')}

PROPOSED FINDINGS OF FACT:
${result.proposed_findings_of_fact}
    `.trim();

    const blob = new Blob([fullSummary], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `case-summary-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Summary downloaded!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-amber-50 to-orange-50">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />Back
        </Button>
        <div className="bg-gradient-to-r from-yellow-600 to-orange-600 rounded-3xl shadow-2xl p-8 text-white mb-8">
          <div className="flex items-center gap-4">
            <div className="bg-white/20 p-4 rounded-2xl">
              <Scale className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-2">Case Summary Generator</h1>
              <p className="text-yellow-100 text-lg">Complete case package for court</p>
            </div>
          </div>
        </div>

        {!result ? (
          <Card className="border-2 shadow-xl">
            <CardHeader><CardTitle>Case Information</CardTitle></CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Case Facts & Background *</label>
                <textarea
                  value={formData.caseDetails}
                  onChange={(e) => setFormData({ ...formData, caseDetails: e.target.value })}
                  placeholder="Describe your case in detail..."
                  rows={6}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Evidence Summary</label>
                <textarea
                  value={formData.evidence}
                  onChange={(e) => setFormData({ ...formData, evidence: e.target.value })}
                  placeholder="Summarize your evidence..."
                  rows={4}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Desired Outcome</label>
                <textarea
                  value={formData.goals}
                  onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
                  placeholder="What are you asking the court for?"
                  rows={3}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
                />
              </div>
              <Button
                onClick={handleGenerate}
                disabled={loading || !formData.caseDetails.trim()}
                className="w-full h-14 text-lg bg-gradient-to-r from-yellow-600 to-orange-600"
              >
                {loading ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Generating...</> :
                <><Scale className="w-5 h-5 mr-2" />Generate Complete Summary</>}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Elevator Pitch (2-3 Sentences)</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => copySummary(result.elevator_pitch)}>
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-lg text-gray-700">{result.elevator_pitch}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>One-Page Summary</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => copySummary(result.one_page_summary)}>
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <pre className="whitespace-pre-wrap text-sm">{result.one_page_summary}</pre>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Key Arguments</CardTitle></CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.key_arguments?.map((arg, idx) => (
                    <li key={idx} className="flex gap-2">
                      <span className="font-bold">{idx + 1}.</span>
                      <span>{arg}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button onClick={downloadSummary} className="flex-1">
                <Download className="w-4 h-4 mr-2" />Download Complete Package
              </Button>
              <Button onClick={() => setResult(null)} variant="outline" className="flex-1">
                New Summary
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CaseSummary;
