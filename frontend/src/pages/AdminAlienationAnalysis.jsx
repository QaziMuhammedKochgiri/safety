import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  ArrowLeft, Brain, AlertTriangle, TrendingUp, FileText,
  Search, Filter, ChevronDown, ChevronRight, Clock, Users,
  MessageSquare, Activity, Download, RefreshCw
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Severity gauge component
const SeverityGauge = ({ score, level }) => {
  const getColor = (s) => {
    if (s >= 8) return 'text-red-600 bg-red-100';
    if (s >= 6) return 'text-orange-600 bg-orange-100';
    if (s >= 4) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getWidth = () => `${Math.min(score * 10, 100)}%`;

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-gray-700">Severity Score</span>
        <span className={`px-2 py-1 rounded-full text-sm font-bold ${getColor(score)}`}>
          {score.toFixed(1)} / 10
        </span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            score >= 8 ? 'bg-red-500' :
            score >= 6 ? 'bg-orange-500' :
            score >= 4 ? 'bg-yellow-500' : 'bg-green-500'
          }`}
          style={{ width: getWidth() }}
        />
      </div>
      <p className="text-xs text-gray-500 capitalize">{level} Risk Level</p>
    </div>
  );
};

// Tactic category card
const TacticCategoryCard = ({ category, count, onClick }) => {
  const getCategoryIcon = (cat) => {
    const icons = {
      badmouthing: <MessageSquare className="w-5 h-5" />,
      limiting_contact: <Users className="w-5 h-5" />,
      erasing_parent: <AlertTriangle className="w-5 h-5" />,
      creating_fear: <AlertTriangle className="w-5 h-5" />,
      forcing_rejection: <Brain className="w-5 h-5" />,
      undermining_authority: <Activity className="w-5 h-5" />,
      emotional_manipulation: <Brain className="w-5 h-5" />,
    };
    return icons[cat] || <Brain className="w-5 h-5" />;
  };

  const getCategoryColor = (cat) => {
    const colors = {
      badmouthing: 'bg-purple-100 text-purple-700 border-purple-300',
      limiting_contact: 'bg-blue-100 text-blue-700 border-blue-300',
      erasing_parent: 'bg-red-100 text-red-700 border-red-300',
      creating_fear: 'bg-orange-100 text-orange-700 border-orange-300',
      forcing_rejection: 'bg-pink-100 text-pink-700 border-pink-300',
      undermining_authority: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      emotional_manipulation: 'bg-indigo-100 text-indigo-700 border-indigo-300',
    };
    return colors[cat] || 'bg-gray-100 text-gray-700 border-gray-300';
  };

  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg border-2 cursor-pointer hover:shadow-md transition-all ${getCategoryColor(category)}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getCategoryIcon(category)}
          <span className="font-medium capitalize">{category.replace(/_/g, ' ')}</span>
        </div>
        <span className="text-2xl font-bold">{count}</span>
      </div>
    </div>
  );
};

// Match result card
const MatchResultCard = ({ match, expanded, onToggle }) => {
  return (
    <Card className="border-l-4 border-l-red-500">
      <CardHeader
        className="cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <div>
              <CardTitle className="text-base">{match.tactic_name}</CardTitle>
              <CardDescription className="capitalize">{match.category.replace(/_/g, ' ')}</CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className={`px-2 py-1 rounded text-sm font-medium ${
              match.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
              match.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {(match.confidence * 100).toFixed(0)}% confidence
            </span>
            <span className={`px-2 py-1 rounded text-sm font-medium ${
              match.severity >= 8 ? 'bg-red-100 text-red-700' :
              match.severity >= 5 ? 'bg-orange-100 text-orange-700' :
              'bg-yellow-100 text-yellow-700'
            }`}>
              Severity {match.severity}/10
            </span>
          </div>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="pt-0">
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-1">Matched Text</h4>
              <p className="text-sm bg-yellow-50 p-3 rounded border border-yellow-200">
                "{match.matched_text}"
              </p>
            </div>
            {match.context && (
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">Context</h4>
                <p className="text-sm text-gray-600">{match.context}</p>
              </div>
            )}
            {match.literature_refs?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">Literature References</h4>
                <ul className="text-sm text-gray-600 list-disc pl-4">
                  {match.literature_refs.map((ref, idx) => (
                    <li key={idx}>{ref}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
};

const AdminAlienationAnalysis = () => {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const navigate = useNavigate();

  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [tactics, setTactics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedMatches, setExpandedMatches] = useState({});
  const [categoryFilter, setCategoryFilter] = useState(null);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      toast.error('Admin access required');
      navigate('/login');
      return;
    }
    fetchCases();
    fetchTactics();
  }, [user, token]);

  const fetchCases = async () => {
    try {
      const response = await axios.get(`${API}/cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data);
    } catch (error) {
      console.error('Failed to fetch cases:', error);
    }
  };

  const fetchTactics = async () => {
    try {
      const response = await axios.get(`${API}/alienation/tactics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTactics(response.data);
    } catch (error) {
      console.error('Failed to fetch tactics:', error);
    }
  };

  const analyzeCase = async (caseId) => {
    setLoading(true);
    try {
      // Get case messages
      const messagesResponse = await axios.get(`${API}/cases/${caseId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const messages = messagesResponse.data.map(m => ({
        id: m._id || m.id,
        content: m.content || m.text,
        sender: m.sender || m.from,
        timestamp: m.timestamp || m.created_at,
        platform: m.platform || 'unknown'
      }));

      // Analyze messages
      const response = await axios.post(`${API}/alienation/analyze`, {
        case_id: caseId,
        messages: messages,
        include_timeline: true,
        include_severity: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setAnalysisResult(response.data);
      setSelectedCase(caseId);
      toast.success('Analysis complete');
    } catch (error) {
      console.error('Analysis failed:', error);
      toast.error('Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    if (!selectedCase) return;

    setLoading(true);
    try {
      const response = await axios.get(`${API}/alienation/report/${selectedCase}`, {
        params: { language: language === 'de' ? 'de' : 'en' },
        headers: { Authorization: `Bearer ${token}` }
      });

      // Download report
      const blob = new Blob([response.data.report_html], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `alienation-report-${selectedCase}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast.success('Report generated');
    } catch (error) {
      console.error('Report generation failed:', error);
      toast.error('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const toggleMatchExpand = (matchId) => {
    setExpandedMatches(prev => ({
      ...prev,
      [matchId]: !prev[matchId]
    }));
  };

  const filteredMatches = analysisResult?.matches?.filter(m => {
    if (categoryFilter && m.category !== categoryFilter) return false;
    if (searchQuery && !m.matched_text.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  }) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Button
                variant="ghost"
                onClick={() => navigate('/admin')}
                className="text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                {language === 'de' ? 'Zurück' : 'Back'}
              </Button>
              <Brain className="w-8 h-8" />
              <div>
                <h1 className="text-xl font-bold">
                  {language === 'de' ? 'Elterliche Entfremdung' : 'Parental Alienation Analysis'}
                </h1>
                <p className="text-sm opacity-90">
                  {language === 'de' ? 'KI-gestützte Taktik-Erkennung' : 'AI-Powered Tactic Detection'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Panel - Case Selection */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  {language === 'de' ? 'Fälle auswählen' : 'Select Case'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {cases.length === 0 ? (
                    <p className="text-gray-500 text-sm">
                      {language === 'de' ? 'Keine Fälle gefunden' : 'No cases found'}
                    </p>
                  ) : (
                    cases.map(c => (
                      <div
                        key={c._id || c.id}
                        onClick={() => analyzeCase(c._id || c.id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedCase === (c._id || c.id)
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="font-medium">{c.name || c.title || `Case ${c._id || c.id}`}</div>
                        <div className="text-sm text-gray-500">
                          {c.client_name || c.clientName || 'Unknown client'}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Tactics Database */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Brain className="w-5 h-5 mr-2" />
                  {language === 'de' ? 'Taktik-Datenbank' : 'Tactics Database'}
                </CardTitle>
                <CardDescription>
                  {tactics.length} {language === 'de' ? 'bekannte Taktiken' : 'known tactics'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {tactics.slice(0, 10).map(t => (
                    <div key={t.id} className="p-2 rounded border border-gray-200 hover:bg-gray-50">
                      <div className="font-medium text-sm">{t.name}</div>
                      <div className="text-xs text-gray-500 capitalize">
                        {t.category.replace(/_/g, ' ')} • Severity {t.severity}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Analysis Results */}
          <div className="lg:col-span-2">
            {loading ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <RefreshCw className="w-12 h-12 mx-auto mb-4 text-purple-600 animate-spin" />
                  <p className="text-gray-600">
                    {language === 'de' ? 'Analysiere Nachrichten...' : 'Analyzing messages...'}
                  </p>
                </CardContent>
              </Card>
            ) : analysisResult ? (
              <div className="space-y-6">
                {/* Summary Card */}
                <Card className="border-2 border-purple-200">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>
                        {language === 'de' ? 'Analyse-Ergebnis' : 'Analysis Result'}
                      </CardTitle>
                      <Button onClick={generateReport} disabled={loading}>
                        <Download className="w-4 h-4 mr-2" />
                        {language === 'de' ? 'Bericht erstellen' : 'Generate Report'}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">
                      <SeverityGauge
                        score={analysisResult.severity_score}
                        level={analysisResult.severity_level}
                      />
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Messages Analyzed</span>
                          <span className="font-medium">{analysisResult.total_messages}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Patterns Detected</span>
                          <span className="font-medium text-red-600">{analysisResult.total_matches}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Categories</span>
                          <span className="font-medium">{Object.keys(analysisResult.categories || {}).length}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Category Breakdown */}
                <Card>
                  <CardHeader>
                    <CardTitle>
                      {language === 'de' ? 'Kategorie-Aufschlüsselung' : 'Category Breakdown'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {Object.entries(analysisResult.categories || {}).map(([cat, count]) => (
                        <TacticCategoryCard
                          key={cat}
                          category={cat}
                          count={count}
                          onClick={() => setCategoryFilter(categoryFilter === cat ? null : cat)}
                        />
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Recommendations */}
                {analysisResult.recommendations?.length > 0 && (
                  <Card className="border-l-4 border-l-orange-500">
                    <CardHeader>
                      <CardTitle className="flex items-center text-orange-700">
                        <AlertTriangle className="w-5 h-5 mr-2" />
                        {language === 'de' ? 'Empfehlungen' : 'Recommendations'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {analysisResult.recommendations.map((rec, idx) => (
                          <li key={idx} className="flex items-start">
                            <ChevronRight className="w-4 h-4 mt-1 mr-2 text-orange-500" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Detected Patterns */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>
                        {language === 'de' ? 'Erkannte Muster' : 'Detected Patterns'}
                        <span className="ml-2 text-sm font-normal text-gray-500">
                          ({filteredMatches.length} {language === 'de' ? 'Treffer' : 'matches'})
                        </span>
                      </CardTitle>
                      <div className="flex items-center space-x-2">
                        <Input
                          placeholder={language === 'de' ? 'Suchen...' : 'Search...'}
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-48"
                        />
                        {categoryFilter && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCategoryFilter(null)}
                          >
                            Clear filter
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {filteredMatches.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">
                          {language === 'de' ? 'Keine Treffer gefunden' : 'No matches found'}
                        </p>
                      ) : (
                        filteredMatches.map((match, idx) => (
                          <MatchResultCard
                            key={idx}
                            match={match}
                            expanded={expandedMatches[idx]}
                            onToggle={() => toggleMatchExpand(idx)}
                          />
                        ))
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">
                    {language === 'de' ? 'Keinen Fall ausgewählt' : 'No Case Selected'}
                  </h3>
                  <p className="text-gray-500">
                    {language === 'de'
                      ? 'Wählen Sie einen Fall aus der Liste, um die Analyse zu starten'
                      : 'Select a case from the list to start analysis'}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAlienationAnalysis;
