import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Slider } from "../components/ui/slider";
import {
  AlertTriangle,
  Shield,
  TrendingUp,
  TrendingDown,
  Activity,
  Brain,
  Target,
  Lightbulb,
  Clock,
  ChevronRight,
  ChevronDown,
  BarChart3,
  LineChart,
  PieChart,
  Zap,
  RefreshCw,
  Download,
  FileText,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Users,
  Calendar,
  Settings
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "/api";

// Risk Level Indicator Component
const RiskLevelIndicator = ({ level, score }) => {
  const getColor = () => {
    if (score >= 80) return "bg-red-500";
    if (score >= 60) return "bg-orange-500";
    if (score >= 40) return "bg-yellow-500";
    if (score >= 20) return "bg-blue-500";
    return "bg-green-500";
  };

  const getTextColor = () => {
    if (score >= 80) return "text-red-600";
    if (score >= 60) return "text-orange-600";
    if (score >= 40) return "text-yellow-600";
    if (score >= 20) return "text-blue-600";
    return "text-green-600";
  };

  return (
    <div className="flex flex-col items-center">
      <div className={`w-24 h-24 rounded-full ${getColor()} flex items-center justify-center shadow-lg`}>
        <span className="text-white text-2xl font-bold">{score}%</span>
      </div>
      <span className={`mt-2 font-semibold ${getTextColor()}`}>{level}</span>
    </div>
  );
};

// Risk Factor Card Component
const RiskFactorCard = ({ factor, onExpand, isExpanded }) => {
  const getImpactColor = () => {
    if (factor.impact === "critical") return "border-l-red-500 bg-red-50";
    if (factor.impact === "high") return "border-l-orange-500 bg-orange-50";
    if (factor.impact === "medium") return "border-l-yellow-500 bg-yellow-50";
    return "border-l-blue-500 bg-blue-50";
  };

  const getImpactBadge = () => {
    if (factor.impact === "critical") return <Badge className="bg-red-100 text-red-700">Kritisch</Badge>;
    if (factor.impact === "high") return <Badge className="bg-orange-100 text-orange-700">Hoch</Badge>;
    if (factor.impact === "medium") return <Badge className="bg-yellow-100 text-yellow-700">Mittel</Badge>;
    return <Badge className="bg-blue-100 text-blue-700">Niedrig</Badge>;
  };

  return (
    <div
      className={`border-l-4 ${getImpactColor()} rounded-r-lg p-4 cursor-pointer transition-all hover:shadow-md`}
      onClick={onExpand}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-gray-600" />
            <h4 className="font-semibold">{factor.name}</h4>
            {getImpactBadge()}
          </div>
          <p className="text-sm text-gray-600">{factor.description}</p>

          {isExpanded && (
            <div className="mt-4 space-y-3 animate-in slide-in-from-top-2">
              <div className="bg-white rounded-lg p-3">
                <h5 className="text-sm font-medium mb-2">Evidenz:</h5>
                <ul className="text-sm text-gray-600 space-y-1">
                  {factor.evidence?.map((e, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <ChevronRight className="h-4 w-4 mt-0.5 text-gray-400" />
                      {e}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-white rounded-lg p-3">
                <h5 className="text-sm font-medium mb-2">Empfohlene Maßnahmen:</h5>
                <ul className="text-sm text-gray-600 space-y-1">
                  {factor.recommendations?.map((r, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Lightbulb className="h-4 w-4 mt-0.5 text-yellow-500" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-gray-700">{factor.weight}%</span>
          {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
        </div>
      </div>
    </div>
  );
};

// Intervention Card Component
const InterventionCard = ({ intervention }) => {
  const getPriorityColor = () => {
    if (intervention.priority === "urgent") return "border-red-500 bg-red-50";
    if (intervention.priority === "high") return "border-orange-500 bg-orange-50";
    if (intervention.priority === "medium") return "border-yellow-500 bg-yellow-50";
    return "border-green-500 bg-green-50";
  };

  const getStatusIcon = () => {
    if (intervention.status === "completed") return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    if (intervention.status === "in_progress") return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />;
    if (intervention.status === "pending") return <Clock className="h-5 w-5 text-yellow-500" />;
    return <AlertCircle className="h-5 w-5 text-gray-500" />;
  };

  return (
    <div className={`border-2 ${getPriorityColor()} rounded-lg p-4`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <h4 className="font-semibold">{intervention.title}</h4>
        </div>
        <Badge variant="outline">{intervention.type}</Badge>
      </div>

      <p className="text-sm text-gray-600 mb-3">{intervention.description}</p>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-gray-500">
            <Calendar className="h-4 w-4" />
            {intervention.timeline}
          </span>
          <span className="flex items-center gap-1 text-gray-500">
            <Users className="h-4 w-4" />
            {intervention.responsible}
          </span>
        </div>
        <span className={`font-medium ${intervention.effectiveness_score >= 70 ? 'text-green-600' : 'text-yellow-600'}`}>
          {intervention.effectiveness_score}% Wirksamkeit
        </span>
      </div>
    </div>
  );
};

// Trend Indicator Component
const TrendIndicator = ({ direction, value }) => {
  if (direction === "up") {
    return (
      <span className="flex items-center text-red-600">
        <ArrowUpRight className="h-4 w-4" />
        +{value}%
      </span>
    );
  }
  if (direction === "down") {
    return (
      <span className="flex items-center text-green-600">
        <ArrowDownRight className="h-4 w-4" />
        -{value}%
      </span>
    );
  }
  return (
    <span className="flex items-center text-gray-600">
      <Minus className="h-4 w-4" />
      {value}%
    </span>
  );
};

// What-If Scenario Component
const WhatIfScenario = ({ scenario, onApply }) => {
  return (
    <div className="border rounded-lg p-4 hover:border-amber-500 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold">{scenario.name}</h4>
          <p className="text-sm text-gray-600">{scenario.description}</p>
        </div>
        <Zap className="h-5 w-5 text-amber-500" />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className={`text-sm font-medium ${scenario.risk_change < 0 ? 'text-green-600' : 'text-red-600'}`}>
            Risikoänderung: {scenario.risk_change > 0 ? '+' : ''}{scenario.risk_change}%
          </span>
        </div>
        <Button size="sm" variant="outline" onClick={() => onApply(scenario)}>
          Anwenden
        </Button>
      </div>
    </div>
  );
};

export default function AdminRiskPredictor() {
  const { user, token } = useAuth();
  const { t, language } = useLanguage();

  // State
  const [activeTab, setActiveTab] = useState("analysis");
  const [selectedCase, setSelectedCase] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Analysis results
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [riskFactors, setRiskFactors] = useState([]);
  const [interventions, setInterventions] = useState([]);
  const [trajectory, setTrajectory] = useState(null);
  const [expandedFactor, setExpandedFactor] = useState(null);

  // What-If state
  const [whatIfScenarios, setWhatIfScenarios] = useState([]);
  const [customScenario, setCustomScenario] = useState({
    name: "",
    changes: {}
  });

  // Explanation state
  const [explanation, setExplanation] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);

  // Load cases on mount
  useEffect(() => {
    loadCases();
    loadRiskFactors();
  }, []);

  const loadCases = async () => {
    try {
      const response = await axios.get(`${API_URL}/cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data.cases || []);
    } catch (error) {
      console.error("Error loading cases:", error);
    }
  };

  const loadRiskFactors = async () => {
    try {
      const response = await axios.get(`${API_URL}/risk-predictor/factors`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRiskFactors(response.data.factors || []);
    } catch (error) {
      console.error("Error loading risk factors:", error);
    }
  };

  const runAnalysis = async () => {
    if (!selectedCase) {
      toast.error("Bitte wählen Sie einen Fall aus");
      return;
    }

    setAnalyzing(true);
    try {
      // Run main analysis
      const analysisResponse = await axios.post(
        `${API_URL}/risk-predictor/analyze`,
        {
          case_id: selectedCase,
          include_trajectory: true,
          prediction_horizon: 90
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setRiskAnalysis(analysisResponse.data);

      // Load interventions
      const interventionsResponse = await axios.get(
        `${API_URL}/risk-predictor/interventions/${selectedCase}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setInterventions(interventionsResponse.data.interventions || []);

      // Load trajectory
      const trajectoryResponse = await axios.get(
        `${API_URL}/risk-predictor/trajectory/${selectedCase}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTrajectory(trajectoryResponse.data);

      toast.success("Risikoanalyse abgeschlossen");
    } catch (error) {
      console.error("Error running analysis:", error);
      toast.error("Analyse fehlgeschlagen");
    } finally {
      setAnalyzing(false);
    }
  };

  const getExplanation = async (factorId) => {
    try {
      const response = await axios.post(
        `${API_URL}/risk-predictor/explain`,
        {
          case_id: selectedCase,
          factor_id: factorId,
          detail_level: "comprehensive"
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setExplanation(response.data);
      setShowExplanation(true);
    } catch (error) {
      console.error("Error getting explanation:", error);
      toast.error("Erklärung konnte nicht geladen werden");
    }
  };

  const runWhatIfAnalysis = async (scenario) => {
    try {
      const response = await axios.post(
        `${API_URL}/risk-predictor/what-if`,
        {
          case_id: selectedCase,
          scenario_changes: scenario.changes,
          compare_to_current: true
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success(`Szenario "${scenario.name}" analysiert`);
      // Update UI with scenario results
      if (response.data.projected_risk) {
        setRiskAnalysis(prev => ({
          ...prev,
          scenario_risk: response.data.projected_risk
        }));
      }
    } catch (error) {
      console.error("Error running what-if analysis:", error);
      toast.error("Szenario-Analyse fehlgeschlagen");
    }
  };

  const exportReport = async () => {
    if (!riskAnalysis) {
      toast.error("Keine Analyse zum Exportieren vorhanden");
      return;
    }

    try {
      const response = await axios.get(
        `${API_URL}/risk-predictor/report/${selectedCase}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `risk-report-${selectedCase}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success("Bericht exportiert");
    } catch (error) {
      console.error("Error exporting report:", error);
      toast.error("Export fehlgeschlagen");
    }
  };

  // Mock data for demo
  const mockRiskFactors = [
    {
      id: 1,
      name: "Eltern-Kind-Entfremdung",
      impact: "critical",
      weight: 35,
      description: "Anzeichen einer systematischen Entfremdung wurden erkannt",
      evidence: [
        "Kind zeigt extreme Ablehnung gegenüber einem Elternteil",
        "Unrealistische Vorwürfe ohne faktische Grundlage",
        "Plötzliche Verhaltensänderung nach Besuchen"
      ],
      recommendations: [
        "Therapeutische Intervention empfohlen",
        "Überwachte Besuchszeiten einführen",
        "Familienmediation in Betracht ziehen"
      ]
    },
    {
      id: 2,
      name: "Emotionale Vernachlässigung",
      impact: "high",
      weight: 25,
      description: "Hinweise auf mangelnde emotionale Unterstützung",
      evidence: [
        "Kind zeigt Bindungsstörungen",
        "Mangelnde Reaktion auf emotionale Bedürfnisse",
        "Fehlende Validierung der Gefühle des Kindes"
      ],
      recommendations: [
        "Eltern-Kind-Bindungstherapie",
        "Erziehungsberatung empfohlen",
        "Regelmäßige psychologische Beurteilung"
      ]
    },
    {
      id: 3,
      name: "Instabile Wohnsituation",
      impact: "medium",
      weight: 20,
      description: "Häufige Wohnortwechsel beeinträchtigen die Stabilität",
      evidence: [
        "Drei Umzüge in den letzten 12 Monaten",
        "Keine feste Schulzugehörigkeit",
        "Unterbrochene soziale Bindungen"
      ],
      recommendations: [
        "Stabile Wohnsituation priorisieren",
        "Schulwechsel vermeiden",
        "Soziale Kontinuität sicherstellen"
      ]
    },
    {
      id: 4,
      name: "Kommunikationsdefizite zwischen Eltern",
      impact: "medium",
      weight: 15,
      description: "Mangelnde Kommunikation zwischen den Erziehungsberechtigten",
      evidence: [
        "Konflikte bei Übergaben",
        "Kind wird als Bote missbraucht",
        "Unterschiedliche Erziehungsansätze"
      ],
      recommendations: [
        "Paralleles Eltern-Coaching",
        "Kommunikations-App nutzen",
        "Klare schriftliche Vereinbarungen"
      ]
    }
  ];

  const mockInterventions = [
    {
      id: 1,
      title: "Therapeutische Begleitung des Kindes",
      type: "Therapie",
      priority: "urgent",
      status: "in_progress",
      description: "Regelmäßige Einzeltherapie zur Bearbeitung der Entfremdungserfahrungen",
      timeline: "Wöchentlich, 6 Monate",
      responsible: "Dr. Müller",
      effectiveness_score: 85
    },
    {
      id: 2,
      title: "Überwachte Besuchszeiten",
      type: "Schutzmaßnahme",
      priority: "high",
      status: "completed",
      description: "Professionell begleitete Besuche zur Sicherstellung des Kindeswohls",
      timeline: "Bi-wöchentlich",
      responsible: "Jugendamt",
      effectiveness_score: 78
    },
    {
      id: 3,
      title: "Eltern-Mediation",
      type: "Mediation",
      priority: "medium",
      status: "pending",
      description: "Strukturierte Gespräche zur Verbesserung der Eltern-Kommunikation",
      timeline: "Monatlich, 3 Monate",
      responsible: "Mediationszentrum",
      effectiveness_score: 65
    }
  ];

  const mockWhatIfScenarios = [
    {
      id: 1,
      name: "Therapeutische Intervention",
      description: "Kind erhält regelmäßige therapeutische Unterstützung",
      changes: { therapy: true, duration: 180 },
      risk_change: -25
    },
    {
      id: 2,
      name: "Stabile Wohnsituation",
      description: "Kind lebt dauerhaft bei einem Elternteil",
      changes: { stable_housing: true },
      risk_change: -15
    },
    {
      id: 3,
      name: "Vollständiger Kontaktabbruch",
      description: "Kein Kontakt zum entfremdenden Elternteil",
      changes: { no_contact: true },
      risk_change: -35
    },
    {
      id: 4,
      name: "Eskalation des Konflikts",
      description: "Weitere Verschlechterung der Elternbeziehung",
      changes: { conflict_escalation: true },
      risk_change: +20
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-600 to-amber-800 text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Shield className="h-8 w-8" />
                Risikoprediktion & Prävention
              </h1>
              <p className="text-amber-100 mt-2">
                KI-gestützte Risikoanalyse und Präventionsempfehlungen für Kinderschutz
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                className="border-white text-white hover:bg-amber-700"
                onClick={exportReport}
                disabled={!riskAnalysis}
              >
                <Download className="h-4 w-4 mr-2" />
                Bericht exportieren
              </Button>
              <Button
                className="bg-white text-amber-700 hover:bg-amber-50"
                onClick={runAnalysis}
                disabled={!selectedCase || analyzing}
              >
                {analyzing ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Brain className="h-4 w-4 mr-2" />
                )}
                Analyse starten
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Case Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Fallauswahl
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Fall auswählen</Label>
                <Select value={selectedCase} onValueChange={setSelectedCase}>
                  <SelectTrigger>
                    <SelectValue placeholder="Fall auswählen..." />
                  </SelectTrigger>
                  <SelectContent>
                    {cases.map(c => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.case_number} - {c.client_name}
                      </SelectItem>
                    ))}
                    {/* Demo cases */}
                    <SelectItem value="DEMO-001">DEMO-001 - Familie Müller</SelectItem>
                    <SelectItem value="DEMO-002">DEMO-002 - Familie Schmidt</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Analysezeitraum</Label>
                <Select defaultValue="90">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">Letzte 30 Tage</SelectItem>
                    <SelectItem value="90">Letzte 90 Tage</SelectItem>
                    <SelectItem value="180">Letzte 6 Monate</SelectItem>
                    <SelectItem value="365">Letztes Jahr</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Prädiktionshorizont</Label>
                <Select defaultValue="90">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">30 Tage voraus</SelectItem>
                    <SelectItem value="90">90 Tage voraus</SelectItem>
                    <SelectItem value="180">6 Monate voraus</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-4 w-full max-w-2xl">
            <TabsTrigger value="analysis" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Analyse
            </TabsTrigger>
            <TabsTrigger value="factors" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Risikofaktoren
            </TabsTrigger>
            <TabsTrigger value="interventions" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Interventionen
            </TabsTrigger>
            <TabsTrigger value="scenarios" className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Was-wäre-wenn
            </TabsTrigger>
          </TabsList>

          {/* Analysis Tab */}
          <TabsContent value="analysis" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Risk Overview */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle>Gesamtrisiko</CardTitle>
                  <CardDescription>Aktueller Risikostand</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col items-center">
                  <RiskLevelIndicator
                    level={riskAnalysis?.risk_level || "Hoch"}
                    score={riskAnalysis?.risk_score || 72}
                  />

                  <div className="w-full mt-6 space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Trend (30 Tage)</span>
                      <TrendIndicator direction="up" value={5} />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Konfidenz</span>
                      <span className="font-medium">87%</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Letzte Aktualisierung</span>
                      <span className="text-gray-500">Heute, 14:32</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Breakdown */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Risikoverteilung nach Kategorie</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      { name: "Psychologisches Risiko", value: 78, color: "bg-red-500" },
                      { name: "Soziales Risiko", value: 65, color: "bg-orange-500" },
                      { name: "Bildungsrisiko", value: 45, color: "bg-yellow-500" },
                      { name: "Gesundheitsrisiko", value: 30, color: "bg-blue-500" },
                      { name: "Physisches Risiko", value: 20, color: "bg-green-500" }
                    ].map(category => (
                      <div key={category.name}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{category.name}</span>
                          <span className="text-sm text-gray-600">{category.value}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`${category.color} h-2 rounded-full transition-all`}
                            style={{ width: `${category.value}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Trajectory Chart Placeholder */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LineChart className="h-5 w-5" />
                  Risikotrajektorie
                </CardTitle>
                <CardDescription>
                  Prädizierte Risikoentwicklung über die nächsten 90 Tage
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-gray-100 rounded-lg">
                  <div className="text-center text-gray-500">
                    <LineChart className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Risikotrajektorie-Diagramm</p>
                    <p className="text-sm">Analyse starten, um Visualisierung zu laden</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Key Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Zentrale Erkenntnisse
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2 text-red-700 font-semibold mb-2">
                      <AlertCircle className="h-5 w-5" />
                      Höchste Priorität
                    </div>
                    <p className="text-sm text-gray-700">
                      Entfremdungsmuster zeigen kritische Entwicklung.
                      Sofortige therapeutische Intervention empfohlen.
                    </p>
                  </div>

                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center gap-2 text-amber-700 font-semibold mb-2">
                      <TrendingUp className="h-5 w-5" />
                      Verschlechterungstrend
                    </div>
                    <p className="text-sm text-gray-700">
                      Risikoscore hat sich in den letzten 30 Tagen um 8% erhöht.
                      Verstärkte Überwachung empfohlen.
                    </p>
                  </div>

                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 text-green-700 font-semibold mb-2">
                      <CheckCircle2 className="h-5 w-5" />
                      Positive Faktoren
                    </div>
                    <p className="text-sm text-gray-700">
                      Stabile Schulleistungen und positive Peer-Beziehungen
                      wirken als Schutzfaktoren.
                    </p>
                  </div>

                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 text-blue-700 font-semibold mb-2">
                      <Lightbulb className="h-5 w-5" />
                      Empfehlung
                    </div>
                    <p className="text-sm text-gray-700">
                      Fokus auf therapeutische Interventionen und Stärkung
                      der Eltern-Kind-Beziehung zum nicht-entfremdenden Elternteil.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Risk Factors Tab */}
          <TabsContent value="factors" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  Identifizierte Risikofaktoren
                </CardTitle>
                <CardDescription>
                  Detaillierte Aufschlüsselung aller erkannten Risikofaktoren mit Evidenz und Empfehlungen
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockRiskFactors.map(factor => (
                    <RiskFactorCard
                      key={factor.id}
                      factor={factor}
                      isExpanded={expandedFactor === factor.id}
                      onExpand={() => setExpandedFactor(
                        expandedFactor === factor.id ? null : factor.id
                      )}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Factor Weights */}
            <Card>
              <CardHeader>
                <CardTitle>Faktorgewichtung</CardTitle>
                <CardDescription>
                  Anteil jedes Faktors am Gesamtrisiko
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-48 flex items-center justify-center bg-gray-100 rounded-lg">
                  <div className="text-center text-gray-500">
                    <PieChart className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Kreisdiagramm der Faktorgewichtung</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Interventions Tab */}
          <TabsContent value="interventions" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Intervention Stats */}
              <Card>
                <CardHeader>
                  <CardTitle>Interventions-Übersicht</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Aktive Interventionen</span>
                      <Badge className="bg-blue-100 text-blue-700">3</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Abgeschlossen</span>
                      <Badge className="bg-green-100 text-green-700">2</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Ausstehend</span>
                      <Badge className="bg-yellow-100 text-yellow-700">1</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Durchschn. Wirksamkeit</span>
                      <span className="font-semibold text-green-600">76%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Intervention List */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    Empfohlene Interventionen
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockInterventions.map(intervention => (
                      <InterventionCard key={intervention.id} intervention={intervention} />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Intervention Effectiveness */}
            <Card>
              <CardHeader>
                <CardTitle>Wirksamkeitsanalyse</CardTitle>
                <CardDescription>
                  Historische Wirksamkeit verschiedener Interventionstypen
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {[
                    { type: "Therapie", effectiveness: 82, cases: 45 },
                    { type: "Mediation", effectiveness: 68, cases: 32 },
                    { type: "Überwachung", effectiveness: 75, cases: 28 },
                    { type: "Coaching", effectiveness: 71, cases: 22 }
                  ].map(item => (
                    <div key={item.type} className="p-4 border rounded-lg text-center">
                      <div className="text-2xl font-bold text-amber-600">{item.effectiveness}%</div>
                      <div className="text-sm font-medium">{item.type}</div>
                      <div className="text-xs text-gray-500">{item.cases} Fälle</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* What-If Scenarios Tab */}
          <TabsContent value="scenarios" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Was-wäre-wenn Szenarien
                </CardTitle>
                <CardDescription>
                  Simulieren Sie verschiedene Szenarien und deren Auswirkungen auf das Risiko
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {mockWhatIfScenarios.map(scenario => (
                    <WhatIfScenario
                      key={scenario.id}
                      scenario={scenario}
                      onApply={runWhatIfAnalysis}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Custom Scenario Builder */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Eigenes Szenario erstellen
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Szenarioname</Label>
                    <Input
                      placeholder="z.B. Intensive Therapie + stabile Wohnsituation"
                      value={customScenario.name}
                      onChange={(e) => setCustomScenario({...customScenario, name: e.target.value})}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Therapeutische Unterstützung</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Auswählen..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Keine</SelectItem>
                          <SelectItem value="weekly">Wöchentlich</SelectItem>
                          <SelectItem value="intensive">Intensiv (2x/Woche)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>Wohnsituation</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Auswählen..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="current">Aktuell beibehalten</SelectItem>
                          <SelectItem value="stable">Stabil bei einem Elternteil</SelectItem>
                          <SelectItem value="shared">Wechselmodell</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>Elternkontakt</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Auswählen..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="current">Aktuell beibehalten</SelectItem>
                          <SelectItem value="supervised">Überwacht</SelectItem>
                          <SelectItem value="limited">Eingeschränkt</SelectItem>
                          <SelectItem value="none">Kein Kontakt</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>Elternmediation</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Auswählen..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Keine</SelectItem>
                          <SelectItem value="monthly">Monatlich</SelectItem>
                          <SelectItem value="biweekly">Alle 2 Wochen</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <Button className="w-full">
                    <Brain className="h-4 w-4 mr-2" />
                    Szenario analysieren
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Scenario Comparison */}
            <Card>
              <CardHeader>
                <CardTitle>Szenariovergleich</CardTitle>
                <CardDescription>
                  Vergleichen Sie die Auswirkungen verschiedener Szenarien auf das Gesamtrisiko
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-48 flex items-center justify-center bg-gray-100 rounded-lg">
                  <div className="text-center text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Szenario-Vergleichsdiagramm</p>
                    <p className="text-sm">Szenarien analysieren, um Vergleich anzuzeigen</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
