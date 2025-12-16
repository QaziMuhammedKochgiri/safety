import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Shield, AlertTriangle, CheckCircle, XCircle, ArrowLeft,
  Loader2, Download, FileText, TrendingUp, AlertCircle
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Risk Analyzer Page
 * AI-powered child safety risk assessment
 * "Baş Yolla" - Simple one-click analysis
 */
const RiskAnalyzer = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    caseId: '',
    caseDescription: ''
  });

  const handleAnalyze = async () => {
    if (!formData.caseDescription.trim()) {
      toast.error('Please describe your case');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/ai/analyze-risk`,
        {
          case_id: formData.caseId || `case_${Date.now()}`,
          case_description: formData.caseDescription,
          additional_context: {}
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
      toast.success('Risk analysis complete!');
    } catch (error) {
      console.error('Risk analysis error:', error);
      toast.error(error.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 8) return 'red';
    if (score >= 6) return 'orange';
    if (score >= 4) return 'yellow';
    return 'green';
  };

  const getRiskBadge = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-700 border-red-300',
      high: 'bg-orange-100 text-orange-700 border-orange-300',
      moderate: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      low: 'bg-green-100 text-green-700 border-green-300',
      minimal: 'bg-blue-100 text-blue-700 border-blue-300'
    };
    return colors[severity] || colors.moderate;
  };

  const downloadReport = () => {
    if (!result) return;

    const reportText = `
SafeChild Risk Analysis Report
Generated: ${new Date().toLocaleString()}

OVERALL RISK SCORE: ${result.overall_score}/10
SEVERITY LEVEL: ${result.severity_level}

CATEGORY SCORES:
${result.category_scores.map(cat => `  - ${cat.category}: ${cat.score}/10 (${cat.severity})`).join('\n')}

IMMEDIATE ACTIONS RECOMMENDED:
${result.immediate_actions.map((action, i) => `  ${i + 1}. ${action}`).join('\n')}

PARENT-FRIENDLY SUMMARY:
${result.parent_friendly_summary}

RISK FACTORS:
${result.risk_factors.map((factor, i) => `  ${i + 1}. ${factor}`).join('\n')}

PROTECTIVE FACTORS:
${result.protective_factors.map((factor, i) => `  ${i + 1}. ${factor}`).join('\n')}
    `.trim();

    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `risk-analysis-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Report downloaded!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        {/* Header */}
        <div className="mb-8">
          <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          <div className="bg-gradient-to-r from-red-600 to-orange-600 rounded-3xl shadow-2xl p-8 text-white">
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-4 rounded-2xl">
                <Shield className="w-12 h-12" />
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-2">Risk Analyzer</h1>
                <p className="text-red-100 text-lg">
                  AI-powered child safety risk assessment (0-10 scale)
                </p>
              </div>
            </div>
          </div>
        </div>

        {!result ? (
          /* Input Form */
          <Card className="border-2 shadow-xl">
            <CardHeader>
              <CardTitle className="text-2xl">Describe Your Case</CardTitle>
              <CardDescription>
                Tell us about your situation. The AI will analyze potential risks to child safety.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Case ID (Optional)
                </label>
                <input
                  type="text"
                  value={formData.caseId}
                  onChange={(e) => setFormData({ ...formData, caseId: e.target.value })}
                  placeholder="e.g., CASE-2024-001"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Case Description *
                </label>
                <textarea
                  value={formData.caseDescription}
                  onChange={(e) => setFormData({ ...formData, caseDescription: e.target.value })}
                  placeholder="Describe the situation in detail. Include any concerning behaviors, incidents, or patterns you've observed..."
                  rows={8}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Be as detailed as possible. The more information you provide, the more accurate the analysis.
                </p>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-yellow-800">
                    <strong>Important:</strong> This AI analysis provides guidance but does not replace
                    professional legal or psychological assessment. For emergencies, call local authorities immediately.
                  </div>
                </div>
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={loading || !formData.caseDescription.trim()}
                className="w-full h-14 text-lg bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Analyzing Risk...
                  </>
                ) : (
                  <>
                    <Shield className="w-5 h-5 mr-2" />
                    Analyze Risk - "Baş Yolla"
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ) : (
          /* Results Display */
          <div className="space-y-6">
            {/* Overall Risk Score */}
            <Card className="border-2 shadow-xl">
              <CardContent className="p-8">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-gray-800 mb-4">Overall Risk Assessment</h2>
                  <div className="flex items-center justify-center gap-8 mb-6">
                    <div>
                      <div className={`text-8xl font-bold text-${getRiskColor(result.overall_score)}-600`}>
                        {result.overall_score}
                      </div>
                      <div className="text-gray-500 text-lg">out of 10</div>
                    </div>
                    <div>
                      <Badge className={`${getRiskBadge(result.severity_level)} text-lg px-6 py-2`}>
                        {result.severity_level.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  <div className="bg-gray-100 rounded-lg p-6 text-left">
                    <h3 className="font-bold text-gray-800 mb-2">What This Means:</h3>
                    <p className="text-gray-700">{result.parent_friendly_summary}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Category Scores */}
            <Card className="border-2 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                  Risk Categories
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {result.category_scores.map((category, idx) => (
                    <div key={idx} className="border-b pb-4 last:border-b-0">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-800">{category.category}</span>
                        <div className="flex items-center gap-2">
                          <span className={`text-2xl font-bold text-${getRiskColor(category.score)}-600`}>
                            {category.score}/10
                          </span>
                          <Badge className={getRiskBadge(category.severity)}>
                            {category.severity}
                          </Badge>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`bg-${getRiskColor(category.score)}-500 h-3 rounded-full transition-all`}
                          style={{ width: `${category.score * 10}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Immediate Actions */}
            <Card className="border-2 border-red-200 shadow-xl bg-red-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-700">
                  <AlertTriangle className="w-6 h-6" />
                  Immediate Actions Recommended
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {result.immediate_actions.map((action, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <div className="bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
                        {idx + 1}
                      </div>
                      <span className="text-gray-800">{action}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Risk Factors */}
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="border-2 border-orange-200 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-700">
                    <XCircle className="w-6 h-6" />
                    Risk Factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {result.risk_factors.map((factor, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-orange-600">⚠</span>
                        <span className="text-gray-700">{factor}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card className="border-2 border-green-200 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="w-6 h-6" />
                    Protective Factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {result.protective_factors.map((factor, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-green-600">✓</span>
                        <span className="text-gray-700">{factor}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <Button
                onClick={downloadReport}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Download Report
              </Button>
              <Button
                onClick={() => setResult(null)}
                variant="outline"
                className="flex-1"
              >
                <FileText className="w-4 h-4 mr-2" />
                New Analysis
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskAnalyzer;
