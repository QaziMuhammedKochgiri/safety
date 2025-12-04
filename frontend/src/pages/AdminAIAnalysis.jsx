import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Brain,
  AlertTriangle,
  Shield,
  Search,
  Loader2,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  Users,
  MessageSquare,
  Zap,
  RefreshCw,
  FileWarning,
  ShieldAlert,
  Heart,
  Scale,
  Eye
} from 'lucide-react';
import axios from 'axios';

const API_URL = '/api';

const AdminAIAnalysis = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();

  const [cases, setCases] = useState([]);
  const [filteredCases, setFilteredCases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [selectedCase, setSelectedCase] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [generatingSummary, setGeneratingSummary] = useState(false);

  const translations = {
    de: {
      title: 'AI Forensik-Analyse',
      subtitle: 'KI-gestutzte Evidenzanalyse',
      dashboard: 'Risk Dashboard',
      cases: 'Forensik-Falle',
      analyze: 'KI Analyse starten',
      generateSummary: 'Fallzusammenfassung',
      totalAnalyzed: 'Analysiert',
      flaggedMessages: 'Markierte Nachrichten',
      urgentCases: 'Dringende Falle',
      riskCategories: 'Risikokategorien',
      riskDistribution: 'Risikoverteilung',
      back: 'Zuruck',
      search: 'Suchen...',
      noAnalysis: 'Keine Analyse vorhanden',
      runAnalysis: 'Analyse starten',
      critical: 'Kritisch',
      high: 'Hoch',
      medium: 'Mittel',
      low: 'Niedrig',
      minimal: 'Minimal',
      threats: 'Bedrohungen',
      manipulation: 'Manipulation',
      parental_alienation: 'Elterliche Entfremdung',
      abuse_indicators: 'Missbrauchsindikatoren',
      neglect_indicators: 'Vernachlassigung',
      childSafety: 'Kindersicherheit',
      recommendations: 'Empfehlungen',
      caseSummary: 'Fallzusammenfassung',
      viewDetails: 'Details ansehen'
    },
    en: {
      title: 'AI Forensic Analysis',
      subtitle: 'AI-Powered Evidence Analysis',
      dashboard: 'Risk Dashboard',
      cases: 'Forensic Cases',
      analyze: 'Run AI Analysis',
      generateSummary: 'Generate Summary',
      totalAnalyzed: 'Total Analyzed',
      flaggedMessages: 'Flagged Messages',
      urgentCases: 'Urgent Cases',
      riskCategories: 'Risk Categories',
      riskDistribution: 'Risk Distribution',
      back: 'Back',
      search: 'Search...',
      noAnalysis: 'No analysis available',
      runAnalysis: 'Run Analysis',
      critical: 'Critical',
      high: 'High',
      medium: 'Medium',
      low: 'Low',
      minimal: 'Minimal',
      threats: 'Threats',
      manipulation: 'Manipulation',
      parental_alienation: 'Parental Alienation',
      abuse_indicators: 'Abuse Indicators',
      neglect_indicators: 'Neglect Indicators',
      childSafety: 'Child Safety',
      recommendations: 'Recommendations',
      caseSummary: 'Case Summary',
      viewDetails: 'View Details'
    }
  };

  const t = translations[language] || translations.en;

  useEffect(() => {
    fetchDashboard();
    fetchCases();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = cases.filter(c =>
        c.case_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.client_number?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredCases(filtered);
    } else {
      setFilteredCases(cases);
    }
  }, [searchTerm, cases]);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API_URL}/forensics/risk-dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboard(response.data);
    } catch (error) {
      console.error('Dashboard error:', error);
    }
  };

  const fetchCases = async () => {
    try {
      const response = await axios.get(`${API_URL}/forensics/all-cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data.cases || []);
      setFilteredCases(response.data.cases || []);
    } catch (error) {
      console.error('Cases error:', error);
      toast.error('Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  const runAIAnalysis = async (caseId) => {
    setAnalyzing(true);
    try {
      const response = await axios.post(
        `${API_URL}/forensics/ai-analyze/${caseId}`,
        { case_id: caseId, language, include_safety_assessment: true },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.success) {
        toast.success(language === 'de' ? 'KI-Analyse abgeschlossen' : 'AI Analysis completed');
        setAiAnalysis(response.data);
        fetchDashboard();
        fetchCases();
      }
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error(language === 'de' ? 'Analysefehler' : 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const fetchAIAnalysis = async (caseId) => {
    try {
      const response = await axios.get(`${API_URL}/forensics/ai-analysis/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAiAnalysis(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        setAiAnalysis(null);
      }
    }
  };

  const generateSummary = async (caseId) => {
    setGeneratingSummary(true);
    try {
      const response = await axios.post(
        `${API_URL}/forensics/ai-summary/${caseId}`,
        { case_id: caseId, language },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.success) {
        toast.success(language === 'de' ? 'Zusammenfassung erstellt' : 'Summary generated');
        fetchAIAnalysis(caseId);
      }
    } catch (error) {
      console.error('Summary error:', error);
      toast.error(language === 'de' ? 'Zusammenfassungsfehler' : 'Summary generation failed');
    } finally {
      setGeneratingSummary(false);
    }
  };

  const handleSelectCase = (caseItem) => {
    setSelectedCase(caseItem);
    if (caseItem.ai_analyzed) {
      fetchAIAnalysis(caseItem.case_id);
    } else {
      setAiAnalysis(null);
    }
  };

  const getRiskBadge = (level) => {
    const config = {
      critical: { color: 'bg-red-600 text-white', icon: AlertTriangle },
      high: { color: 'bg-orange-500 text-white', icon: AlertCircle },
      medium: { color: 'bg-yellow-500 text-white', icon: AlertCircle },
      low: { color: 'bg-blue-500 text-white', icon: Shield },
      minimal: { color: 'bg-green-500 text-white', icon: CheckCircle }
    };
    const { color, icon: Icon } = config[level] || config.minimal;
    return (
      <Badge className={`${color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {t[level] || level}
      </Badge>
    );
  };

  const getRiskCategoryIcon = (category) => {
    const icons = {
      threats: AlertTriangle,
      manipulation: Brain,
      parental_alienation: Users,
      abuse_indicators: ShieldAlert,
      neglect_indicators: Heart,
      substance_abuse: AlertCircle,
      financial_coercion: Scale,
      custody_interference: Users,
      inappropriate_content: FileWarning,
      documentation_value: FileText
    };
    return icons[category] || AlertCircle;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" className="text-white hover:bg-white/20" onClick={() => navigate('/admin')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                {t.back}
              </Button>
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <Brain className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">{t.title}</h1>
                  <p className="text-purple-200">{t.subtitle}</p>
                </div>
              </div>
            </div>
            <Button
              variant="secondary"
              onClick={() => { fetchDashboard(); fetchCases(); }}
              className="bg-white/20 hover:bg-white/30 text-white"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Dashboard Stats */}
        {dashboard && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm">{t.totalAnalyzed}</p>
                    <p className="text-3xl font-bold">{dashboard.total_analyzed}</p>
                  </div>
                  <Brain className="w-10 h-10 text-blue-200" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-orange-100 text-sm">{t.flaggedMessages}</p>
                    <p className="text-3xl font-bold">{dashboard.total_flagged_messages}</p>
                  </div>
                  <MessageSquare className="w-10 h-10 text-orange-200" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-red-100 text-sm">{t.urgentCases}</p>
                    <p className="text-3xl font-bold">{dashboard.urgent_cases?.length || 0}</p>
                  </div>
                  <AlertTriangle className="w-10 h-10 text-red-200" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100 text-sm">{t.riskCategories}</p>
                    <p className="text-3xl font-bold">{Object.keys(dashboard.risk_categories || {}).length}</p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-green-200" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Risk Distribution */}
        {dashboard?.risk_distribution && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                {t.riskDistribution}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4">
                {Object.entries(dashboard.risk_distribution).map(([level, count]) => (
                  <div key={level} className="text-center">
                    <div className={`w-full h-24 rounded-lg flex items-end justify-center p-2 ${
                      level === 'critical' ? 'bg-red-100' :
                      level === 'high' ? 'bg-orange-100' :
                      level === 'medium' ? 'bg-yellow-100' :
                      level === 'low' ? 'bg-blue-100' : 'bg-green-100'
                    }`}>
                      <div
                        className={`w-full rounded transition-all ${
                          level === 'critical' ? 'bg-red-500' :
                          level === 'high' ? 'bg-orange-500' :
                          level === 'medium' ? 'bg-yellow-500' :
                          level === 'low' ? 'bg-blue-500' : 'bg-green-500'
                        }`}
                        style={{ height: `${Math.min(100, (count / Math.max(...Object.values(dashboard.risk_distribution), 1)) * 100)}%` }}
                      />
                    </div>
                    <p className="mt-2 font-medium">{t[level] || level}</p>
                    <p className="text-2xl font-bold">{count}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid md:grid-cols-3 gap-6">
          {/* Cases List */}
          <div className="md:col-span-1">
            <Card className="h-[600px] flex flex-col">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{t.cases}</CardTitle>
                <div className="relative mt-2">
                  <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder={t.search}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-0">
                {loading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                  </div>
                ) : filteredCases.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">No cases found</p>
                  </div>
                ) : (
                  <div className="divide-y">
                    {filteredCases.map((caseItem) => (
                      <div
                        key={caseItem.case_id}
                        className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                          selectedCase?.case_id === caseItem.case_id ? 'bg-purple-50 border-l-4 border-purple-500' : ''
                        }`}
                        onClick={() => handleSelectCase(caseItem)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm truncate">
                            {caseItem.case_id?.substring(0, 20)}...
                          </span>
                          {caseItem.ai_analyzed ? (
                            getRiskBadge(caseItem.ai_risk_level)
                          ) : (
                            <Badge variant="outline" className="text-gray-500">
                              <Clock className="w-3 h-3 mr-1" />
                              Pending
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{caseItem.client_number}</span>
                          <span>{caseItem.status}</span>
                        </div>
                        {caseItem.ai_risk_score !== undefined && (
                          <div className="mt-2">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  caseItem.ai_risk_score >= 80 ? 'bg-red-500' :
                                  caseItem.ai_risk_score >= 60 ? 'bg-orange-500' :
                                  caseItem.ai_risk_score >= 40 ? 'bg-yellow-500' :
                                  caseItem.ai_risk_score >= 20 ? 'bg-blue-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${caseItem.ai_risk_score}%` }}
                              />
                            </div>
                            <p className="text-xs text-right mt-1">Risk: {caseItem.ai_risk_score}%</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Analysis Details */}
          <div className="md:col-span-2">
            <Card className="h-[600px] flex flex-col">
              {selectedCase ? (
                <>
                  <CardHeader className="border-b pb-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <Brain className="w-5 h-5 text-purple-600" />
                          {selectedCase.case_id}
                        </CardTitle>
                        <CardDescription>
                          Client: {selectedCase.client_number} | Status: {selectedCase.status}
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        {selectedCase.status === 'completed' && !selectedCase.ai_analyzed && (
                          <Button
                            onClick={() => runAIAnalysis(selectedCase.case_id)}
                            disabled={analyzing}
                            className="bg-purple-600 hover:bg-purple-700"
                          >
                            {analyzing ? (
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                              <Zap className="w-4 h-4 mr-2" />
                            )}
                            {t.analyze}
                          </Button>
                        )}
                        {selectedCase.ai_analyzed && (
                          <Button
                            variant="outline"
                            onClick={() => generateSummary(selectedCase.case_id)}
                            disabled={generatingSummary}
                          >
                            {generatingSummary ? (
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                              <FileText className="w-4 h-4 mr-2" />
                            )}
                            {t.generateSummary}
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto p-4">
                    {aiAnalysis ? (
                      <div className="space-y-6">
                        {/* Risk Overview */}
                        <div className="grid grid-cols-2 gap-4">
                          <Card className="bg-gray-50">
                            <CardContent className="p-4">
                              <p className="text-sm text-gray-500 mb-1">Overall Risk Score</p>
                              <div className="flex items-center gap-3">
                                <span className="text-3xl font-bold">
                                  {aiAnalysis.ai_results?.overall_risk_score || 0}%
                                </span>
                                {getRiskBadge(aiAnalysis.ai_results?.risk_level)}
                              </div>
                            </CardContent>
                          </Card>
                          <Card className="bg-gray-50">
                            <CardContent className="p-4">
                              <p className="text-sm text-gray-500 mb-1">Flagged Messages</p>
                              <span className="text-3xl font-bold">
                                {aiAnalysis.ai_results?.flagged_count || 0}
                              </span>
                              <span className="text-gray-500 ml-2">
                                / {aiAnalysis.ai_results?.total_analyzed || 0}
                              </span>
                            </CardContent>
                          </Card>
                        </div>

                        {/* Risk Categories */}
                        {aiAnalysis.ai_results?.risk_summary && (
                          <Card>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-base">{t.riskCategories}</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-3">
                                {Object.entries(aiAnalysis.ai_results.risk_summary)
                                  .sort(([,a], [,b]) => b - a)
                                  .map(([category, score]) => {
                                    const Icon = getRiskCategoryIcon(category);
                                    return (
                                      <div key={category} className="flex items-center gap-3">
                                        <Icon className="w-4 h-4 text-gray-500" />
                                        <span className="text-sm w-40 truncate">
                                          {t[category] || category.replace(/_/g, ' ')}
                                        </span>
                                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                                          <div
                                            className={`h-2 rounded-full transition-all ${
                                              score >= 80 ? 'bg-red-500' :
                                              score >= 60 ? 'bg-orange-500' :
                                              score >= 40 ? 'bg-yellow-500' :
                                              score >= 20 ? 'bg-blue-500' : 'bg-green-500'
                                            }`}
                                            style={{ width: `${score}%` }}
                                          />
                                        </div>
                                        <span className="text-sm font-medium w-10 text-right">{score}%</span>
                                      </div>
                                    );
                                  })}
                              </div>
                            </CardContent>
                          </Card>
                        )}

                        {/* Child Safety Assessment */}
                        {aiAnalysis.safety_assessment && (
                          <Card className="border-red-200 bg-red-50">
                            <CardHeader className="pb-2">
                              <CardTitle className="text-base flex items-center gap-2 text-red-700">
                                <ShieldAlert className="w-5 h-5" />
                                {t.childSafety}
                                <Badge className={
                                  aiAnalysis.safety_assessment.urgency_level === 'critical' ? 'bg-red-600' :
                                  aiAnalysis.safety_assessment.urgency_level === 'high' ? 'bg-orange-500' :
                                  'bg-yellow-500'
                                }>
                                  {aiAnalysis.safety_assessment.urgency_level}
                                </Badge>
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <p className="text-sm text-gray-600 mb-3">
                                Overall Safety Score: <strong>{aiAnalysis.safety_assessment.overall_safety_score}%</strong>
                              </p>
                              {aiAnalysis.safety_assessment.recommendations?.length > 0 && (
                                <div className="space-y-2">
                                  {aiAnalysis.safety_assessment.recommendations.map((rec, idx) => (
                                    <div key={idx} className="flex items-start gap-2 p-2 bg-white rounded">
                                      <AlertTriangle className={`w-4 h-4 mt-0.5 ${
                                        rec.priority === 'urgent' ? 'text-red-500' :
                                        rec.priority === 'high' ? 'text-orange-500' : 'text-yellow-500'
                                      }`} />
                                      <span className="text-sm">{rec.action}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        )}

                        {/* Recommendations */}
                        {aiAnalysis.ai_results?.recommendations?.length > 0 && (
                          <Card>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-base">{t.recommendations}</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2">
                                {aiAnalysis.ai_results.recommendations.map((rec, idx) => (
                                  <div
                                    key={idx}
                                    className={`p-3 rounded-lg border ${
                                      rec.priority === 'urgent' ? 'border-red-300 bg-red-50' :
                                      rec.priority === 'high' ? 'border-orange-300 bg-orange-50' :
                                      'border-gray-200 bg-gray-50'
                                    }`}
                                  >
                                    <div className="flex items-center justify-between mb-1">
                                      <Badge variant="outline" className="text-xs">
                                        {rec.category?.replace(/_/g, ' ')}
                                      </Badge>
                                      <span className="text-xs text-gray-500">
                                        {rec.evidence_count} evidence items
                                      </span>
                                    </div>
                                    <p className="text-sm">{rec.action}</p>
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          </Card>
                        )}

                        {/* Case Summary */}
                        {aiAnalysis[`case_summary_${language}`] && (
                          <Card>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-base">{t.caseSummary}</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="prose prose-sm max-w-none">
                                <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg">
                                  {aiAnalysis[`case_summary_${language}`]}
                                </pre>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <Brain className="w-16 h-16 text-gray-300 mb-4" />
                        <p className="text-lg font-medium mb-2">{t.noAnalysis}</p>
                        {selectedCase.status === 'completed' && (
                          <Button
                            onClick={() => runAIAnalysis(selectedCase.case_id)}
                            disabled={analyzing}
                            className="mt-4 bg-purple-600 hover:bg-purple-700"
                          >
                            {analyzing ? (
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                              <Zap className="w-4 h-4 mr-2" />
                            )}
                            {t.runAnalysis}
                          </Button>
                        )}
                      </div>
                    )}
                  </CardContent>
                </>
              ) : (
                <CardContent className="flex-1 flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">
                      {language === 'de' ? 'Wahlen Sie einen Fall aus' : 'Select a case to analyze'}
                    </p>
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAIAnalysis;
