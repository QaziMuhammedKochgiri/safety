import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Checkbox } from "../components/ui/checkbox";
import { Progress } from "../components/ui/progress";
import { ScrollArea } from "../components/ui/scroll-area";
import { Separator } from "../components/ui/separator";
import {
  FileText,
  Folder,
  FolderOpen,
  File,
  FileImage,
  FileVideo,
  FileAudio,
  Download,
  Eye,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Package,
  Gavel,
  Scale,
  Shield,
  Lock,
  Link2,
  ChevronRight,
  ChevronDown,
  Plus,
  Minus,
  RefreshCw,
  Search,
  Filter,
  Settings,
  Printer,
  Share2,
  Upload,
  Archive,
  BookOpen,
  ListChecks,
  Hash,
  Calendar,
  User,
  Building
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "/api";

// Evidence Item Component
const EvidenceItem = ({ item, selected, onToggle, onPreview }) => {
  const getIcon = () => {
    switch (item.type) {
      case 'image': return <FileImage className="h-5 w-5 text-blue-500" />;
      case 'video': return <FileVideo className="h-5 w-5 text-purple-500" />;
      case 'audio': return <FileAudio className="h-5 w-5 text-green-500" />;
      default: return <File className="h-5 w-5 text-gray-500" />;
    }
  };

  const getRelevanceBadge = () => {
    if (item.relevance >= 80) return <Badge className="bg-green-100 text-green-700">Sehr relevant</Badge>;
    if (item.relevance >= 60) return <Badge className="bg-blue-100 text-blue-700">Relevant</Badge>;
    if (item.relevance >= 40) return <Badge className="bg-yellow-100 text-yellow-700">Mäßig relevant</Badge>;
    return <Badge className="bg-gray-100 text-gray-700">Gering relevant</Badge>;
  };

  return (
    <div className={`p-4 border rounded-lg transition-all ${selected ? 'border-teal-500 bg-teal-50' : 'border-gray-200 hover:border-gray-300'}`}>
      <div className="flex items-start gap-4">
        <Checkbox
          checked={selected}
          onCheckedChange={onToggle}
          className="mt-1"
        />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {getIcon()}
            <span className="font-medium">{item.title}</span>
            {getRelevanceBadge()}
          </div>
          <p className="text-sm text-gray-600 mb-2">{item.description}</p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {item.date}
            </span>
            <span className="flex items-center gap-1">
              <Hash className="h-3 w-3" />
              {item.evidence_id}
            </span>
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              {item.source}
            </span>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={() => onPreview(item)}>
          <Eye className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

// Document Section Component
const DocumentSection = ({ section, expanded, onToggle, documents, onDocumentToggle, selectedDocs }) => {
  return (
    <div className="border rounded-lg overflow-hidden">
      <div
        className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          {expanded ? <FolderOpen className="h-5 w-5 text-teal-600" /> : <Folder className="h-5 w-5 text-gray-500" />}
          <div>
            <h4 className="font-medium">{section.name}</h4>
            <p className="text-sm text-gray-500">{section.count} Dokumente</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">{section.required ? "Erforderlich" : "Optional"}</Badge>
          {expanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
        </div>
      </div>

      {expanded && (
        <div className="p-4 space-y-3 border-t">
          {documents.map(doc => (
            <div
              key={doc.id}
              className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                selectedDocs.includes(doc.id) ? 'bg-teal-50 border border-teal-200' : 'bg-gray-50 hover:bg-gray-100'
              }`}
            >
              <Checkbox
                checked={selectedDocs.includes(doc.id)}
                onCheckedChange={() => onDocumentToggle(doc.id)}
              />
              <File className="h-4 w-4 text-gray-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">{doc.name}</p>
                <p className="text-xs text-gray-500">{doc.pages} Seiten</p>
              </div>
              <Badge variant="secondary" className="text-xs">{doc.format}</Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Chain of Custody Item
const ChainOfCustodyItem = ({ event, isLast }) => {
  const getEventIcon = () => {
    switch (event.action) {
      case 'created': return <Plus className="h-4 w-4 text-green-500" />;
      case 'modified': return <RefreshCw className="h-4 w-4 text-blue-500" />;
      case 'accessed': return <Eye className="h-4 w-4 text-gray-500" />;
      case 'transferred': return <Share2 className="h-4 w-4 text-purple-500" />;
      case 'verified': return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
          {getEventIcon()}
        </div>
        {!isLast && <div className="w-0.5 h-full bg-gray-200 mt-2" />}
      </div>
      <div className="flex-1 pb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="font-medium text-sm">{event.action_label}</span>
          <span className="text-xs text-gray-500">{event.timestamp}</span>
        </div>
        <p className="text-sm text-gray-600">{event.description}</p>
        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            {event.user}
          </span>
          <span className="flex items-center gap-1">
            <Hash className="h-3 w-3" />
            {event.hash?.substring(0, 16)}...
          </span>
        </div>
      </div>
    </div>
  );
};

// Format Preview Component
const FormatPreview = ({ format, onSelect, selected }) => {
  const getFormatInfo = () => {
    switch (format) {
      case 'german_court':
        return {
          name: 'Deutsches Gericht',
          icon: <Gavel className="h-6 w-6" />,
          description: 'Formatiert nach deutschen Gerichtsstandards (ZPO)',
          sections: ['Klageantrag', 'Sachverhalt', 'Beweismittel', 'Anlagen']
        };
      case 'turkish_court':
        return {
          name: 'Türkisches Gericht',
          icon: <Scale className="h-6 w-6" />,
          description: 'Formatiert nach türkischen Gerichtsstandards',
          sections: ['Dava Dilekçesi', 'Deliller', 'Ekler']
        };
      case 'hague_convention':
        return {
          name: 'Haager Übereinkommen',
          icon: <Building className="h-6 w-6" />,
          description: 'Internationales Format nach Haager Kindesentführungsübereinkommen',
          sections: ['Application Form', 'Evidence Package', 'Declarations']
        };
      case 'eu_regulation':
        return {
          name: 'EU-Verordnung',
          icon: <Shield className="h-6 w-6" />,
          description: 'Nach EU-Verordnung Nr. 2201/2003 (Brüssel IIa)',
          sections: ['Certificate', 'Evidence', 'Appendices']
        };
      default:
        return {
          name: 'Standard',
          icon: <FileText className="h-6 w-6" />,
          description: 'Allgemeines Dokumentenformat',
          sections: ['Zusammenfassung', 'Beweise', 'Anlagen']
        };
    }
  };

  const info = getFormatInfo();

  return (
    <div
      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
        selected ? 'border-teal-500 bg-teal-50' : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={() => onSelect(format)}
    >
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${selected ? 'bg-teal-100 text-teal-700' : 'bg-gray-100 text-gray-600'}`}>
          {info.icon}
        </div>
        <div>
          <h4 className="font-semibold">{info.name}</h4>
          <p className="text-sm text-gray-600">{info.description}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {info.sections.map(section => (
          <Badge key={section} variant="secondary" className="text-xs">{section}</Badge>
        ))}
      </div>
    </div>
  );
};

export default function AdminCourtPackage() {
  const { user, token } = useAuth();
  const { t, language } = useLanguage();

  // State
  const [activeTab, setActiveTab] = useState("generate");
  const [selectedCase, setSelectedCase] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);

  // Evidence selection
  const [evidence, setEvidence] = useState([]);
  const [selectedEvidence, setSelectedEvidence] = useState([]);
  const [evidenceFilter, setEvidenceFilter] = useState("all");

  // Document sections
  const [expandedSections, setExpandedSections] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);

  // Format selection
  const [selectedFormat, setSelectedFormat] = useState("german_court");
  const [packageOptions, setPackageOptions] = useState({
    includeTimeline: true,
    includeChainOfCustody: true,
    includeExpertOpinions: true,
    includeTranslations: false,
    redactPersonalInfo: true,
    addWatermark: true
  });

  // Generated package
  const [generatedPackage, setGeneratedPackage] = useState(null);
  const [chainOfCustody, setChainOfCustody] = useState([]);

  // Available packages
  const [savedPackages, setSavedPackages] = useState([]);

  // Load data on mount
  useEffect(() => {
    loadCases();
    loadSavedPackages();
  }, []);

  useEffect(() => {
    if (selectedCase) {
      loadEvidence();
      loadChainOfCustody();
    }
  }, [selectedCase]);

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

  const loadEvidence = async () => {
    try {
      const response = await axios.get(`${API_URL}/court-package/evidence/${selectedCase}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEvidence(response.data.evidence || mockEvidence);
    } catch (error) {
      console.error("Error loading evidence:", error);
      setEvidence(mockEvidence);
    }
  };

  const loadSavedPackages = async () => {
    try {
      const response = await axios.get(`${API_URL}/court-package/packages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSavedPackages(response.data.packages || mockSavedPackages);
    } catch (error) {
      console.error("Error loading packages:", error);
      setSavedPackages(mockSavedPackages);
    }
  };

  const loadChainOfCustody = async () => {
    try {
      const response = await axios.get(`${API_URL}/court-package/chain-of-custody/${selectedCase}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChainOfCustody(response.data.events || mockChainOfCustody);
    } catch (error) {
      console.error("Error loading chain of custody:", error);
      setChainOfCustody(mockChainOfCustody);
    }
  };

  const generatePackage = async () => {
    if (!selectedCase) {
      toast.error("Bitte wählen Sie einen Fall aus");
      return;
    }

    if (selectedEvidence.length === 0) {
      toast.error("Bitte wählen Sie mindestens ein Beweisstück aus");
      return;
    }

    setGenerating(true);
    setGenerationProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const response = await axios.post(
        `${API_URL}/court-package/generate`,
        {
          case_id: selectedCase,
          target_format: selectedFormat,
          evidence_ids: selectedEvidence,
          options: packageOptions
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      clearInterval(progressInterval);
      setGenerationProgress(100);

      setGeneratedPackage(response.data);
      toast.success("Gerichtspaket erfolgreich generiert");

      // Switch to preview tab
      setTimeout(() => {
        setActiveTab("preview");
        setGenerating(false);
        setGenerationProgress(0);
      }, 500);

    } catch (error) {
      console.error("Error generating package:", error);
      toast.error("Paketerstellung fehlgeschlagen");
      setGenerating(false);
      setGenerationProgress(0);
    }
  };

  const downloadPackage = async (packageId, format) => {
    try {
      const response = await axios.get(
        `${API_URL}/court-package/download/${packageId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { format },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `court-package-${packageId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success(`Paket als ${format.toUpperCase()} heruntergeladen`);
    } catch (error) {
      console.error("Error downloading package:", error);
      toast.error("Download fehlgeschlagen");
    }
  };

  const toggleEvidenceSelection = (id) => {
    setSelectedEvidence(prev =>
      prev.includes(id) ? prev.filter(e => e !== id) : [...prev, id]
    );
  };

  const toggleSection = (sectionId) => {
    setExpandedSections(prev =>
      prev.includes(sectionId) ? prev.filter(s => s !== sectionId) : [...prev, sectionId]
    );
  };

  const toggleDocSelection = (docId) => {
    setSelectedDocs(prev =>
      prev.includes(docId) ? prev.filter(d => d !== docId) : [...prev, docId]
    );
  };

  // Mock data
  const mockEvidence = [
    {
      id: "EV001",
      title: "WhatsApp-Chatverlauf März 2024",
      description: "Vollständiger Nachrichtenverlauf mit Entfremdungsmustern",
      type: "document",
      date: "2024-03-15",
      evidence_id: "EV-2024-001",
      source: "WhatsApp Export",
      relevance: 95
    },
    {
      id: "EV002",
      title: "Video: Übergabesituation",
      description: "Videoaufnahme zeigt emotionale Reaktion des Kindes",
      type: "video",
      date: "2024-02-28",
      evidence_id: "EV-2024-002",
      source: "Handy-Aufnahme",
      relevance: 88
    },
    {
      id: "EV003",
      title: "Psychologisches Gutachten",
      description: "Sachverständigengutachten zu Entfremdungsmerkmalen",
      type: "document",
      date: "2024-03-20",
      evidence_id: "EV-2024-003",
      source: "Dr. Weber, Gutachter",
      relevance: 98
    },
    {
      id: "EV004",
      title: "Sprachaufnahmen mit Kind",
      description: "Dokumentierte Aussagen des Kindes",
      type: "audio",
      date: "2024-03-10",
      evidence_id: "EV-2024-004",
      source: "Therapiesitzung",
      relevance: 75
    },
    {
      id: "EV005",
      title: "E-Mail-Korrespondenz",
      description: "Kommunikation zwischen Elternteilen",
      type: "document",
      date: "2024-01-15",
      evidence_id: "EV-2024-005",
      source: "E-Mail Export",
      relevance: 65
    }
  ];

  const mockDocumentSections = [
    { id: "intro", name: "Einleitung & Sachverhalt", count: 3, required: true },
    { id: "evidence", name: "Beweismittelverzeichnis", count: 12, required: true },
    { id: "analysis", name: "Analyse & Gutachten", count: 4, required: true },
    { id: "timeline", name: "Chronologische Darstellung", count: 1, required: false },
    { id: "appendix", name: "Anlagen", count: 8, required: false }
  ];

  const mockChainOfCustody = [
    {
      id: 1,
      action: "created",
      action_label: "Beweismittel erfasst",
      timestamp: "2024-03-15 14:32",
      description: "WhatsApp-Chatverlauf forensisch gesichert",
      user: "Admin",
      hash: "a7f8d9e2c1b4a5f6..."
    },
    {
      id: 2,
      action: "verified",
      action_label: "Integrität verifiziert",
      timestamp: "2024-03-15 14:45",
      description: "SHA-256 Hash validiert",
      user: "System",
      hash: "a7f8d9e2c1b4a5f6..."
    },
    {
      id: 3,
      action: "accessed",
      action_label: "Zugriff dokumentiert",
      timestamp: "2024-03-16 09:15",
      description: "Beweismittel zur Analyse geöffnet",
      user: "Dr. Müller",
      hash: "a7f8d9e2c1b4a5f6..."
    },
    {
      id: 4,
      action: "transferred",
      action_label: "Übertragung an Gericht",
      timestamp: "2024-03-20 11:00",
      description: "Beweismittel dem Gerichtspaket hinzugefügt",
      user: "Admin",
      hash: "b8c9d0e1f2a3b4c5..."
    }
  ];

  const mockSavedPackages = [
    {
      id: "PKG-001",
      case_number: "FAM-2024-0123",
      format: "german_court",
      created_at: "2024-03-15",
      status: "completed",
      documents: 15,
      size: "24.5 MB"
    },
    {
      id: "PKG-002",
      case_number: "FAM-2024-0089",
      format: "hague_convention",
      created_at: "2024-03-10",
      status: "completed",
      documents: 22,
      size: "45.2 MB"
    }
  ];

  const filteredEvidence = evidence.filter(item => {
    if (evidenceFilter === "all") return true;
    if (evidenceFilter === "high") return item.relevance >= 80;
    if (evidenceFilter === "selected") return selectedEvidence.includes(item.id);
    return item.type === evidenceFilter;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-600 to-teal-800 text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Package className="h-8 w-8" />
                Gerichtspaket-Generator
              </h1>
              <p className="text-teal-100 mt-2">
                Erstellen Sie gerichtsfertige Dokumentenpakete mit vollständiger Beweiskette
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                className="border-white text-white hover:bg-teal-700"
                onClick={() => downloadPackage(generatedPackage?.id, 'pdf')}
                disabled={!generatedPackage}
              >
                <Download className="h-4 w-4 mr-2" />
                PDF Export
              </Button>
              <Button
                className="bg-white text-teal-700 hover:bg-teal-50"
                onClick={generatePackage}
                disabled={generating || selectedEvidence.length === 0}
              >
                {generating ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4 mr-2" />
                )}
                Paket erstellen
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Case Selection & Progress */}
        <Card className="mb-6">
          <CardContent className="pt-6">
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
                    <SelectItem value="DEMO-001">DEMO-001 - Familie Müller</SelectItem>
                    <SelectItem value="DEMO-002">DEMO-002 - Familie Schmidt</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="md:col-span-2">
                {generating && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Generiere Gerichtspaket...</span>
                      <span>{generationProgress}%</span>
                    </div>
                    <Progress value={generationProgress} className="h-2" />
                    <p className="text-xs text-gray-500">
                      {generationProgress < 30 && "Sammle Beweismittel..."}
                      {generationProgress >= 30 && generationProgress < 60 && "Erstelle Dokumentstruktur..."}
                      {generationProgress >= 60 && generationProgress < 90 && "Generiere Beweiskette..."}
                      {generationProgress >= 90 && "Finalisiere Paket..."}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-5 w-full max-w-3xl">
            <TabsTrigger value="generate" className="flex items-center gap-2">
              <Package className="h-4 w-4" />
              Erstellen
            </TabsTrigger>
            <TabsTrigger value="evidence" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Beweismittel
            </TabsTrigger>
            <TabsTrigger value="format" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Format
            </TabsTrigger>
            <TabsTrigger value="custody" className="flex items-center gap-2">
              <Link2 className="h-4 w-4" />
              Beweiskette
            </TabsTrigger>
            <TabsTrigger value="preview" className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Vorschau
            </TabsTrigger>
          </TabsList>

          {/* Generate Tab */}
          <TabsContent value="generate" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Evidence Selection Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Ausgewählte Beweismittel
                  </CardTitle>
                  <CardDescription>
                    {selectedEvidence.length} von {evidence.length} Beweismitteln ausgewählt
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedEvidence.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>Keine Beweismittel ausgewählt</p>
                        <p className="text-sm">Gehen Sie zum Tab "Beweismittel"</p>
                      </div>
                    ) : (
                      evidence
                        .filter(e => selectedEvidence.includes(e.id))
                        .map(item => (
                          <div key={item.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                            <div className="flex-1">
                              <p className="font-medium text-sm">{item.title}</p>
                              <p className="text-xs text-gray-500">{item.evidence_id}</p>
                            </div>
                            <Badge variant="secondary">{item.relevance}%</Badge>
                          </div>
                        ))
                    )}
                  </div>
                </CardContent>
                <CardFooter>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => setActiveTab("evidence")}
                  >
                    Beweismittel bearbeiten
                  </Button>
                </CardFooter>
              </Card>

              {/* Package Options */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Paketoptionen
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      { key: "includeTimeline", label: "Chronologische Zeitleiste einschließen", icon: Clock },
                      { key: "includeChainOfCustody", label: "Beweiskette dokumentieren", icon: Link2 },
                      { key: "includeExpertOpinions", label: "Gutachten einbinden", icon: BookOpen },
                      { key: "includeTranslations", label: "Übersetzungen hinzufügen", icon: FileText },
                      { key: "redactPersonalInfo", label: "Persönliche Daten schwärzen", icon: Shield },
                      { key: "addWatermark", label: "Wasserzeichen hinzufügen", icon: Lock }
                    ].map(option => (
                      <div key={option.key} className="flex items-center gap-3">
                        <Checkbox
                          checked={packageOptions[option.key]}
                          onCheckedChange={(checked) =>
                            setPackageOptions(prev => ({ ...prev, [option.key]: checked }))
                          }
                        />
                        <option.icon className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">{option.label}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6 text-center">
                  <div className="text-3xl font-bold text-teal-600">{selectedEvidence.length}</div>
                  <div className="text-sm text-gray-500">Beweismittel</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <div className="text-3xl font-bold text-teal-600">
                    {mockDocumentSections.reduce((sum, s) => sum + s.count, 0)}
                  </div>
                  <div className="text-sm text-gray-500">Dokumente</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <div className="text-3xl font-bold text-teal-600">
                    {selectedFormat === 'german_court' ? 'DE' : selectedFormat === 'hague_convention' ? 'INT' : 'EU'}
                  </div>
                  <div className="text-sm text-gray-500">Format</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <div className="text-3xl font-bold text-green-600">
                    <CheckCircle2 className="h-8 w-8 mx-auto" />
                  </div>
                  <div className="text-sm text-gray-500">Bereit</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Evidence Tab */}
          <TabsContent value="evidence" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Beweismittelauswahl</CardTitle>
                    <CardDescription>
                      Wählen Sie die Beweismittel für das Gerichtspaket
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select value={evidenceFilter} onValueChange={setEvidenceFilter}>
                      <SelectTrigger className="w-40">
                        <Filter className="h-4 w-4 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Alle</SelectItem>
                        <SelectItem value="high">Hochrelevant</SelectItem>
                        <SelectItem value="selected">Ausgewählt</SelectItem>
                        <SelectItem value="document">Dokumente</SelectItem>
                        <SelectItem value="video">Videos</SelectItem>
                        <SelectItem value="audio">Audio</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredEvidence.map(item => (
                    <EvidenceItem
                      key={item.id}
                      item={item}
                      selected={selectedEvidence.includes(item.id)}
                      onToggle={() => toggleEvidenceSelection(item.id)}
                      onPreview={(item) => console.log("Preview:", item)}
                    />
                  ))}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setSelectedEvidence([])}>
                  Auswahl aufheben
                </Button>
                <Button variant="outline" onClick={() => setSelectedEvidence(evidence.map(e => e.id))}>
                  Alle auswählen
                </Button>
              </CardFooter>
            </Card>
          </TabsContent>

          {/* Format Tab */}
          <TabsContent value="format" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Gerichtsformat wählen</CardTitle>
                <CardDescription>
                  Wählen Sie das passende Format für das Zielsystem
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {['german_court', 'turkish_court', 'hague_convention', 'eu_regulation'].map(format => (
                    <FormatPreview
                      key={format}
                      format={format}
                      selected={selectedFormat === format}
                      onSelect={setSelectedFormat}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Document Structure */}
            <Card>
              <CardHeader>
                <CardTitle>Dokumentstruktur</CardTitle>
                <CardDescription>
                  Abschnitte des generierten Pakets
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockDocumentSections.map(section => (
                    <DocumentSection
                      key={section.id}
                      section={section}
                      expanded={expandedSections.includes(section.id)}
                      onToggle={() => toggleSection(section.id)}
                      documents={[
                        { id: `${section.id}-1`, name: `${section.name} - Hauptdokument`, pages: 12, format: 'PDF' },
                        { id: `${section.id}-2`, name: `${section.name} - Anhang`, pages: 5, format: 'PDF' }
                      ]}
                      selectedDocs={selectedDocs}
                      onDocumentToggle={toggleDocSelection}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Chain of Custody Tab */}
          <TabsContent value="custody" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Link2 className="h-5 w-5" />
                  Beweiskette (Chain of Custody)
                </CardTitle>
                <CardDescription>
                  Lückenlose Dokumentation aller Beweismittelzugriffe
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-0">
                  {chainOfCustody.map((event, index) => (
                    <ChainOfCustodyItem
                      key={event.id}
                      event={event}
                      isLast={index === chainOfCustody.length - 1}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Integrity Verification */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Integritätsnachweis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <CheckCircle2 className="h-8 w-8 text-green-600" />
                    <div>
                      <h4 className="font-semibold text-green-800">Alle Beweismittel verifiziert</h4>
                      <p className="text-sm text-green-700">
                        SHA-256 Hashes aller Dokumente wurden erfolgreich validiert.
                        Keine Manipulationen erkannt.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <span className="text-gray-500">Letzte Verifikation:</span>
                      <span className="font-medium ml-2">Heute, 15:42</span>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <span className="text-gray-500">Verifikations-Hash:</span>
                      <span className="font-mono text-xs ml-2">f8a9b2c1...</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Paketvorschau</CardTitle>
                    <CardDescription>
                      Vorschau des generierten Gerichtspakets
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Printer className="h-4 w-4 mr-2" />
                      Drucken
                    </Button>
                    <Button variant="outline" size="sm">
                      <Share2 className="h-4 w-4 mr-2" />
                      Teilen
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {generatedPackage ? (
                  <div className="space-y-6">
                    {/* Package Info */}
                    <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-teal-600">Paket-ID:</span>
                          <p className="font-medium">{generatedPackage.id}</p>
                        </div>
                        <div>
                          <span className="text-teal-600">Format:</span>
                          <p className="font-medium">{selectedFormat}</p>
                        </div>
                        <div>
                          <span className="text-teal-600">Dokumente:</span>
                          <p className="font-medium">{selectedEvidence.length}</p>
                        </div>
                        <div>
                          <span className="text-teal-600">Erstellt:</span>
                          <p className="font-medium">Gerade eben</p>
                        </div>
                      </div>
                    </div>

                    {/* Preview Frame */}
                    <div className="border rounded-lg h-96 bg-white flex items-center justify-center">
                      <div className="text-center text-gray-500">
                        <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                        <p className="font-medium">Dokumentvorschau</p>
                        <p className="text-sm">PDF-Vorschau wird hier angezeigt</p>
                      </div>
                    </div>

                    {/* Download Options */}
                    <div className="flex items-center justify-center gap-4">
                      <Button onClick={() => downloadPackage(generatedPackage.id, 'pdf')}>
                        <Download className="h-4 w-4 mr-2" />
                        Als PDF herunterladen
                      </Button>
                      <Button variant="outline" onClick={() => downloadPackage(generatedPackage.id, 'zip')}>
                        <Archive className="h-4 w-4 mr-2" />
                        Als ZIP herunterladen
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Package className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="font-medium">Kein Paket generiert</p>
                    <p className="text-sm mb-4">
                      Wählen Sie Beweismittel aus und klicken Sie auf "Paket erstellen"
                    </p>
                    <Button onClick={() => setActiveTab("generate")}>
                      Zur Paketerstellung
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Previous Packages */}
            <Card>
              <CardHeader>
                <CardTitle>Frühere Pakete</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {savedPackages.map(pkg => (
                    <div key={pkg.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <Package className="h-8 w-8 text-teal-600" />
                        <div>
                          <p className="font-medium">{pkg.case_number}</p>
                          <p className="text-sm text-gray-500">
                            {pkg.documents} Dokumente • {pkg.size} • {pkg.created_at}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{pkg.format}</Badge>
                        <Button variant="ghost" size="sm" onClick={() => downloadPackage(pkg.id, 'pdf')}>
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
