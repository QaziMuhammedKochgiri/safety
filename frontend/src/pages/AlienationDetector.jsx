import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Users, ArrowLeft, Loader2, Download, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || "/api";

const AlienationDetector = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    caseId: '',
    behaviors: '',
    parentChildInteraction: '',
    communicationPatterns: ''
  });

  const handleAnalyze = async () => {
    if (!formData.behaviors.trim()) {
      toast.error('Please describe observed behaviors');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/ai/analyze-alienation`,
        {
          case_id: formData.caseId || `case_${Date.now()}`,
          behaviors_observed: formData.behaviors,
          parent_child_interaction: formData.parentChildInteraction,
          communication_patterns: formData.communicationPatterns
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
      toast.success('Analysis complete!');
    } catch (error) {
      console.error('Alienation analysis error:', error);
      toast.error(error.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-700 border-red-300',
      severe: 'bg-orange-100 text-orange-700 border-orange-300',
      moderate: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      mild: 'bg-blue-100 text-blue-700 border-blue-300',
      none: 'bg-green-100 text-green-700 border-green-300'
    };
    return colors[severity] || colors.moderate;
  };

  const downloadReport = () => {
    if (!result) return;
    const reportText = `
Parental Alienation Analysis Report
Generated: ${new Date().toLocaleString()}

OVERALL SEVERITY: ${result.overall_severity}

DETECTED TACTICS:
${result.tactics_detected.map(t => `  - ${t.tactic}: ${t.severity} (${t.frequency})`).join('\n')}

CHILD IMPACT ASSESSMENT:
${result.child_impact_assessment}

COURT DOCUMENTATION SUGGESTIONS:
${result.court_documentation_suggestions}

IMMEDIATE RECOMMENDATIONS:
${result.immediate_recommendations.map((r, i) => `  ${i + 1}. ${r}`).join('\n')}
    `.trim();

    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `alienation-analysis-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Report downloaded!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        <div className="mb-8">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="bg-gradient-to-r from-orange-600 to-red-600 rounded-3xl shadow-2xl p-8 text-white">
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-4 rounded-2xl">
                <Users className="w-12 h-12" />
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-2">Alienation Detector</h1>
                <p className="text-orange-100 text-lg">
                  Identify parental alienation patterns with AI
                </p>
              </div>
            </div>
          </div>
        </div>

        {!result ? (
          <Card className="border-2 shadow-xl">
            <CardHeader>
              <CardTitle className="text-2xl">Describe Observed Behaviors</CardTitle>
              <CardDescription>
                Provide details about behaviors, interactions, and communication patterns
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Case ID (Optional)</label>
                <input
                  type="text"
                  value={formData.caseId}
                  onChange={(e) => setFormData({ ...formData, caseId: e.target.value })}
                  placeholder="CASE-2024-001"
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Behaviors Observed *</label>
                <textarea
                  value={formData.behaviors}
                  onChange={(e) => setFormData({ ...formData, behaviors: e.target.value })}
                  placeholder="Describe specific behaviors you've observed (e.g., child refusing contact, negative comments about parent, etc.)"
                  rows={5}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Parent-Child Interaction</label>
                <textarea
                  value={formData.parentChildInteraction}
                  onChange={(e) => setFormData({ ...formData, parentChildInteraction: e.target.value })}
                  placeholder="Describe how the child interacts with each parent..."
                  rows={4}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Communication Patterns</label>
                <textarea
                  value={formData.communicationPatterns}
                  onChange={(e) => setFormData({ ...formData, communicationPatterns: e.target.value })}
                  placeholder="Describe communication between parents and with the child..."
                  rows={4}
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={loading || !formData.behaviors.trim()}
                className="w-full h-14 text-lg bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Users className="w-5 h-5 mr-2" />
                    Analyze Patterns
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card className="border-2 shadow-xl">
              <CardContent className="p-8">
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-4">Analysis Results</h2>
                  <Badge className={`${getSeverityColor(result.overall_severity)} text-xl px-6 py-2`}>
                    {result.overall_severity.toUpperCase()}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-orange-600" />
                  Detected Tactics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.tactics_detected.map((tactic, idx) => (
                    <div key={idx} className="border-b pb-3 last:border-b-0">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">{tactic.tactic}</span>
                        <Badge className={getSeverityColor(tactic.severity)}>
                          {tactic.severity}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">Frequency: {tactic.frequency}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-blue-200 shadow-xl bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-900">Child Impact Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-blue-800">{result.child_impact_assessment}</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-purple-200 shadow-xl">
              <CardHeader>
                <CardTitle>Court Documentation Suggestions</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">{result.court_documentation_suggestions}</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-green-200 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-700">
                  <CheckCircle className="w-6 h-6" />
                  Immediate Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.immediate_recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-green-600 font-bold">{idx + 1}.</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button onClick={downloadReport} className="flex-1">
                <Download className="w-4 h-4 mr-2" />
                Download Report
              </Button>
              <Button onClick={() => setResult(null)} variant="outline" className="flex-1">
                New Analysis
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlienationDetector;
