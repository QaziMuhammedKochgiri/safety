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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Users,
  UserPlus,
  UserCheck,
  Star,
  StarHalf,
  MapPin,
  Phone,
  Mail,
  Globe,
  Calendar,
  Clock,
  FileText,
  Award,
  Briefcase,
  GraduationCap,
  Building,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  MessageSquare,
  Video,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Upload,
  Plus,
  Minus,
  ChevronRight,
  BookOpen,
  Scale,
  Brain,
  Heart,
  Languages,
  Target,
  Zap,
  TrendingUp
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// Expert Card Component
const ExpertCard = ({ expert, onView, onEdit, onDelete, onMatch }) => {
  const getSpecialtyBadgeColor = (specialty) => {
    const colors = {
      psychology: 'bg-purple-100 text-purple-700',
      forensics: 'bg-blue-100 text-blue-700',
      law: 'bg-green-100 text-green-700',
      social_work: 'bg-yellow-100 text-yellow-700',
      child_psychiatry: 'bg-red-100 text-red-700',
      translation: 'bg-cyan-100 text-cyan-700'
    };
    return colors[specialty] || 'bg-gray-100 text-gray-700';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={expert.avatar} />
            <AvatarFallback className="bg-rose-100 text-rose-700 text-lg">
              {expert.name.split(' ').map(n => n[0]).join('')}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-lg">{expert.name}</h3>
                <p className="text-sm text-gray-600">{expert.title}</p>
              </div>
              <div className="flex items-center gap-1">
                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                <span className="font-medium">{expert.rating}</span>
                <span className="text-gray-400 text-sm">({expert.reviews_count})</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mt-3">
              {expert.specialties.map((specialty, i) => (
                <Badge key={i} className={getSpecialtyBadgeColor(specialty.type)}>
                  {specialty.name}
                </Badge>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-2 mt-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {expert.location}
              </div>
              <div className="flex items-center gap-1">
                <Languages className="h-4 w-4" />
                {expert.languages.join(', ')}
              </div>
              <div className="flex items-center gap-1">
                <Briefcase className="h-4 w-4" />
                {expert.experience} Jahre
              </div>
              <div className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                {expert.cases_count} Fälle
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <div className="flex items-center gap-2">
            <Badge variant={expert.available ? "default" : "secondary"}>
              {expert.available ? "Verfügbar" : "Beschäftigt"}
            </Badge>
            {expert.verified && (
              <Badge variant="outline" className="border-green-500 text-green-700">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Verifiziert
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => onView(expert)}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onEdit(expert)}>
              <Edit className="h-4 w-4" />
            </Button>
            <Button size="sm" onClick={() => onMatch(expert)}>
              <Target className="h-4 w-4 mr-1" />
              Zuordnen
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Consultation Request Card
const ConsultationCard = ({ consultation, onAccept, onDecline, onComplete }) => {
  const getStatusBadge = () => {
    switch (consultation.status) {
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-700">Ausstehend</Badge>;
      case 'accepted':
        return <Badge className="bg-blue-100 text-blue-700">Angenommen</Badge>;
      case 'in_progress':
        return <Badge className="bg-purple-100 text-purple-700">In Bearbeitung</Badge>;
      case 'completed':
        return <Badge className="bg-green-100 text-green-700">Abgeschlossen</Badge>;
      case 'cancelled':
        return <Badge className="bg-red-100 text-red-700">Abgebrochen</Badge>;
      default:
        return <Badge variant="secondary">{consultation.status}</Badge>;
    }
  };

  return (
    <div className="p-4 border rounded-lg hover:border-rose-300 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold">{consultation.case_title}</h4>
          <p className="text-sm text-gray-600">Mandant: {consultation.client_name}</p>
        </div>
        {getStatusBadge()}
      </div>

      <p className="text-sm text-gray-600 mb-3">{consultation.description}</p>

      <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
        <span className="flex items-center gap-1">
          <Calendar className="h-4 w-4" />
          {consultation.requested_date}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="h-4 w-4" />
          {consultation.duration}
        </span>
        <span className="flex items-center gap-1">
          <Users className="h-4 w-4" />
          {consultation.expert_name}
        </span>
      </div>

      <div className="flex items-center justify-between pt-3 border-t">
        <span className="text-sm font-medium text-rose-600">
          {consultation.hourly_rate}€/Stunde
        </span>
        <div className="flex items-center gap-2">
          {consultation.status === 'pending' && (
            <>
              <Button variant="outline" size="sm" onClick={() => onDecline(consultation)}>
                Ablehnen
              </Button>
              <Button size="sm" onClick={() => onAccept(consultation)}>
                Annehmen
              </Button>
            </>
          )}
          {consultation.status === 'in_progress' && (
            <Button size="sm" onClick={() => onComplete(consultation)}>
              Abschließen
            </Button>
          )}
          {consultation.status === 'accepted' && (
            <Button size="sm" variant="outline">
              <Video className="h-4 w-4 mr-1" />
              Videoanruf
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

// Knowledge Article Card
const KnowledgeArticleCard = ({ article, onView }) => {
  return (
    <div
      className="p-4 border rounded-lg cursor-pointer hover:border-rose-300 hover:shadow-md transition-all"
      onClick={() => onView(article)}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-rose-100 flex items-center justify-center">
          <BookOpen className="h-5 w-5 text-rose-600" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold">{article.title}</h4>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{article.summary}</p>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>{article.author}</span>
            <span>{article.date}</span>
            <span>{article.reading_time} Min. Lesezeit</span>
          </div>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 mt-3">
        {article.tags.map((tag, i) => (
          <Badge key={i} variant="outline" className="text-xs">
            {tag}
          </Badge>
        ))}
      </div>
    </div>
  );
};

export default function AdminExpertNetwork() {
  const { user, token } = useAuth();
  const { t, language } = useLanguage();

  // State
  const [activeTab, setActiveTab] = useState("experts");
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [specialtyFilter, setSpecialtyFilter] = useState("all");

  // Experts
  const [experts, setExperts] = useState([]);
  const [selectedExpert, setSelectedExpert] = useState(null);
  const [showExpertDialog, setShowExpertDialog] = useState(false);
  const [showAddExpertDialog, setShowAddExpertDialog] = useState(false);

  // Consultations
  const [consultations, setConsultations] = useState([]);
  const [consultationFilter, setConsultationFilter] = useState("all");

  // Matching
  const [matchingCase, setMatchingCase] = useState(null);
  const [matchResults, setMatchResults] = useState([]);
  const [showMatchDialog, setShowMatchDialog] = useState(false);

  // Knowledge base
  const [articles, setArticles] = useState([]);

  // New expert form
  const [newExpert, setNewExpert] = useState({
    name: "",
    title: "",
    email: "",
    phone: "",
    location: "",
    specialties: [],
    languages: [],
    experience: "",
    bio: ""
  });

  // Load data on mount
  useEffect(() => {
    loadExperts();
    loadConsultations();
    loadArticles();
  }, []);

  const loadExperts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/experts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setExperts(response.data.experts || mockExperts);
    } catch (error) {
      console.error("Error loading experts:", error);
      setExperts(mockExperts);
    } finally {
      setLoading(false);
    }
  };

  const loadConsultations = async () => {
    try {
      const response = await axios.get(`${API_URL}/experts/consultations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConsultations(response.data.consultations || mockConsultations);
    } catch (error) {
      console.error("Error loading consultations:", error);
      setConsultations(mockConsultations);
    }
  };

  const loadArticles = async () => {
    try {
      const response = await axios.get(`${API_URL}/experts/knowledge`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setArticles(response.data.articles || mockArticles);
    } catch (error) {
      console.error("Error loading articles:", error);
      setArticles(mockArticles);
    }
  };

  const matchExpertToCase = async (caseId) => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/experts/match`,
        {
          case_id: caseId,
          required_specialties: ["psychology", "forensics"],
          preferred_languages: ["de", "tr"],
          urgency: "normal"
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMatchResults(response.data.matches || mockMatchResults);
      setShowMatchDialog(true);
      toast.success("Experten-Matching abgeschlossen");
    } catch (error) {
      console.error("Error matching experts:", error);
      setMatchResults(mockMatchResults);
      setShowMatchDialog(true);
      toast.success("Experten-Matching abgeschlossen (Demo)");
    } finally {
      setLoading(false);
    }
  };

  const createExpert = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/experts`,
        newExpert,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success("Experte erfolgreich hinzugefügt");
      setShowAddExpertDialog(false);
      loadExperts();
    } catch (error) {
      console.error("Error creating expert:", error);
      toast.error("Fehler beim Hinzufügen des Experten");
    }
  };

  const acceptConsultation = async (consultation) => {
    try {
      await axios.post(
        `${API_URL}/experts/consultations/${consultation.id}/accept`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Beratung angenommen");
      loadConsultations();
    } catch (error) {
      toast.success("Beratung angenommen (Demo)");
    }
  };

  const declineConsultation = async (consultation) => {
    try {
      await axios.post(
        `${API_URL}/experts/consultations/${consultation.id}/decline`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.info("Beratung abgelehnt");
      loadConsultations();
    } catch (error) {
      toast.info("Beratung abgelehnt (Demo)");
    }
  };

  const completeConsultation = async (consultation) => {
    try {
      await axios.post(
        `${API_URL}/experts/consultations/${consultation.id}/complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Beratung abgeschlossen");
      loadConsultations();
    } catch (error) {
      toast.success("Beratung abgeschlossen (Demo)");
    }
  };

  // Mock data
  const mockExperts = [
    {
      id: "EXP001",
      name: "Dr. Sarah Weber",
      title: "Kinderpsychologin",
      avatar: null,
      rating: 4.9,
      reviews_count: 127,
      location: "Berlin",
      languages: ["Deutsch", "Englisch"],
      experience: 15,
      cases_count: 234,
      specialties: [
        { type: "psychology", name: "Kinderpsychologie" },
        { type: "forensics", name: "Forensische Psychologie" }
      ],
      available: true,
      verified: true
    },
    {
      id: "EXP002",
      name: "Prof. Dr. Mehmet Yilmaz",
      title: "Forensischer Psychiater",
      avatar: null,
      rating: 4.8,
      reviews_count: 89,
      location: "München",
      languages: ["Deutsch", "Türkisch", "Englisch"],
      experience: 22,
      cases_count: 312,
      specialties: [
        { type: "child_psychiatry", name: "Kinder- und Jugendpsychiatrie" },
        { type: "forensics", name: "Forensische Psychiatrie" }
      ],
      available: true,
      verified: true
    },
    {
      id: "EXP003",
      name: "Julia Schneider",
      title: "Diplom-Sozialarbeiterin",
      avatar: null,
      rating: 4.7,
      reviews_count: 65,
      location: "Hamburg",
      languages: ["Deutsch", "Arabisch"],
      experience: 8,
      cases_count: 145,
      specialties: [
        { type: "social_work", name: "Kinder- und Jugendhilfe" },
        { type: "psychology", name: "Traumatherapie" }
      ],
      available: false,
      verified: true
    },
    {
      id: "EXP004",
      name: "RA Dr. Thomas Müller",
      title: "Fachanwalt für Familienrecht",
      avatar: null,
      rating: 4.9,
      reviews_count: 203,
      location: "Frankfurt",
      languages: ["Deutsch", "Englisch", "Französisch"],
      experience: 18,
      cases_count: 456,
      specialties: [
        { type: "law", name: "Familienrecht" },
        { type: "law", name: "Internationales Privatrecht" }
      ],
      available: true,
      verified: true
    }
  ];

  const mockConsultations = [
    {
      id: "CON001",
      case_title: "Sorgerechtsstreit Müller/Schmidt",
      client_name: "Anna Müller",
      description: "Gutachterliche Stellungnahme zu Entfremdungsmustern",
      expert_name: "Dr. Sarah Weber",
      status: "pending",
      requested_date: "2024-03-25",
      duration: "2 Stunden",
      hourly_rate: 180
    },
    {
      id: "CON002",
      case_title: "Kindeswohlgefährdung Fall Yilmaz",
      client_name: "Mehmet Yilmaz",
      description: "Psychiatrische Begutachtung des Kindes",
      expert_name: "Prof. Dr. Mehmet Yilmaz",
      status: "in_progress",
      requested_date: "2024-03-20",
      duration: "4 Stunden",
      hourly_rate: 220
    },
    {
      id: "CON003",
      case_title: "Umgangsregelung Schmidt",
      client_name: "Peter Schmidt",
      description: "Rechtliche Beratung zu Umgangsrecht",
      expert_name: "RA Dr. Thomas Müller",
      status: "completed",
      requested_date: "2024-03-15",
      duration: "1.5 Stunden",
      hourly_rate: 250
    }
  ];

  const mockMatchResults = [
    {
      expert: mockExperts[0],
      score: 95,
      reasons: [
        "Spezialisierung auf Kinderpsychologie",
        "Erfahrung mit Entfremdungsfällen",
        "Sprachliche Übereinstimmung"
      ]
    },
    {
      expert: mockExperts[1],
      score: 88,
      reasons: [
        "Forensische Expertise",
        "Türkische Sprachkenntnisse",
        "Umfangreiche Fallgeschichte"
      ]
    }
  ];

  const mockArticles = [
    {
      id: "ART001",
      title: "Erkennung von Entfremdungsmustern bei Kindern",
      summary: "Ein umfassender Leitfaden zur Identifikation und Dokumentation von Entfremdungsverhalten in Sorgerechtsstreitigkeiten.",
      author: "Dr. Sarah Weber",
      date: "2024-03-01",
      reading_time: 12,
      tags: ["Entfremdung", "Diagnostik", "Kinderpsychologie"]
    },
    {
      id: "ART002",
      title: "Forensische Audioanalyse im Familienrecht",
      summary: "Methoden und Best Practices für die Analyse von Audiobeweismitteln in familienrechtlichen Verfahren.",
      author: "Prof. Dr. Mehmet Yilmaz",
      date: "2024-02-15",
      reading_time: 18,
      tags: ["Forensik", "Audio", "Beweismittel"]
    },
    {
      id: "ART003",
      title: "Internationale Kindesentführung: Rechtliche Grundlagen",
      summary: "Überblick über das Haager Übereinkommen und dessen Anwendung in der Praxis.",
      author: "RA Dr. Thomas Müller",
      date: "2024-01-28",
      reading_time: 22,
      tags: ["Recht", "International", "Haager Übereinkommen"]
    }
  ];

  const filteredExperts = experts.filter(expert => {
    const matchesSearch = expert.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         expert.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSpecialty = specialtyFilter === "all" ||
                            expert.specialties.some(s => s.type === specialtyFilter);
    return matchesSearch && matchesSpecialty;
  });

  const filteredConsultations = consultations.filter(c => {
    if (consultationFilter === "all") return true;
    return c.status === consultationFilter;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-rose-600 to-rose-800 text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Users className="h-8 w-8" />
                Experten-Netzwerk
              </h1>
              <p className="text-rose-100 mt-2">
                Verwalten Sie Sachverständige, Gutachter und Fachexperten
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                className="border-white text-white hover:bg-rose-700"
                onClick={() => matchExpertToCase("DEMO-001")}
              >
                <Target className="h-4 w-4 mr-2" />
                Experten-Matching
              </Button>
              <Button
                className="bg-white text-rose-700 hover:bg-rose-50"
                onClick={() => setShowAddExpertDialog(true)}
              >
                <UserPlus className="h-4 w-4 mr-2" />
                Experte hinzufügen
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-rose-100 flex items-center justify-center">
                  <Users className="h-6 w-6 text-rose-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{experts.length}</div>
                  <div className="text-sm text-gray-500">Experten</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <UserCheck className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {experts.filter(e => e.available).length}
                  </div>
                  <div className="text-sm text-gray-500">Verfügbar</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <MessageSquare className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {consultations.filter(c => c.status === 'pending').length}
                  </div>
                  <div className="text-sm text-gray-500">Offene Anfragen</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center">
                  <Star className="h-6 w-6 text-yellow-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">4.8</div>
                  <div className="text-sm text-gray-500">Durchschn. Bewertung</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-4 w-full max-w-xl">
            <TabsTrigger value="experts" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Experten
            </TabsTrigger>
            <TabsTrigger value="consultations" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Beratungen
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Wissensbasis
            </TabsTrigger>
            <TabsTrigger value="reviews" className="flex items-center gap-2">
              <Star className="h-4 w-4" />
              Bewertungen
            </TabsTrigger>
          </TabsList>

          {/* Experts Tab */}
          <TabsContent value="experts" className="space-y-6">
            {/* Search and Filter */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex flex-wrap gap-4">
                  <div className="flex-1 min-w-64">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Experten suchen..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <Select value={specialtyFilter} onValueChange={setSpecialtyFilter}>
                    <SelectTrigger className="w-48">
                      <Filter className="h-4 w-4 mr-2" />
                      <SelectValue placeholder="Fachgebiet" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Alle Fachgebiete</SelectItem>
                      <SelectItem value="psychology">Psychologie</SelectItem>
                      <SelectItem value="forensics">Forensik</SelectItem>
                      <SelectItem value="law">Recht</SelectItem>
                      <SelectItem value="social_work">Sozialarbeit</SelectItem>
                      <SelectItem value="child_psychiatry">Kinder- und Jugendpsychiatrie</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Expert Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredExperts.map(expert => (
                <ExpertCard
                  key={expert.id}
                  expert={expert}
                  onView={(e) => { setSelectedExpert(e); setShowExpertDialog(true); }}
                  onEdit={(e) => console.log("Edit:", e)}
                  onDelete={(e) => console.log("Delete:", e)}
                  onMatch={(e) => matchExpertToCase("DEMO-001")}
                />
              ))}
            </div>

            {filteredExperts.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <Users className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="font-medium">Keine Experten gefunden</p>
                <p className="text-sm">Versuchen Sie andere Suchkriterien</p>
              </div>
            )}
          </TabsContent>

          {/* Consultations Tab */}
          <TabsContent value="consultations" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Beratungsanfragen</CardTitle>
                  <Select value={consultationFilter} onValueChange={setConsultationFilter}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Alle</SelectItem>
                      <SelectItem value="pending">Ausstehend</SelectItem>
                      <SelectItem value="in_progress">In Bearbeitung</SelectItem>
                      <SelectItem value="completed">Abgeschlossen</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredConsultations.map(consultation => (
                    <ConsultationCard
                      key={consultation.id}
                      consultation={consultation}
                      onAccept={acceptConsultation}
                      onDecline={declineConsultation}
                      onComplete={completeConsultation}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Knowledge Base Tab */}
          <TabsContent value="knowledge" className="space-y-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Fachbeiträge & Wissen</h2>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Artikel hinzufügen
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {articles.map(article => (
                <KnowledgeArticleCard
                  key={article.id}
                  article={article}
                  onView={(a) => console.log("View article:", a)}
                />
              ))}
            </div>
          </TabsContent>

          {/* Reviews Tab */}
          <TabsContent value="reviews" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Bewertungsübersicht</CardTitle>
                <CardDescription>
                  Bewertungen und Feedback für alle Experten
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {experts.map(expert => (
                    <div key={expert.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <Avatar>
                          <AvatarFallback className="bg-rose-100 text-rose-700">
                            {expert.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <h4 className="font-semibold">{expert.name}</h4>
                          <p className="text-sm text-gray-600">{expert.title}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <div className="flex items-center gap-1">
                            <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
                            <span className="text-lg font-bold">{expert.rating}</span>
                          </div>
                          <p className="text-xs text-gray-500">{expert.reviews_count} Bewertungen</p>
                        </div>
                        <Button variant="outline" size="sm">
                          Details
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

      {/* Expert Detail Dialog */}
      <Dialog open={showExpertDialog} onOpenChange={setShowExpertDialog}>
        <DialogContent className="max-w-2xl">
          {selectedExpert && (
            <>
              <DialogHeader>
                <DialogTitle>{selectedExpert.name}</DialogTitle>
                <DialogDescription>{selectedExpert.title}</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <Avatar className="h-20 w-20">
                    <AvatarFallback className="bg-rose-100 text-rose-700 text-2xl">
                      {selectedExpert.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="flex items-center gap-2">
                      <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
                      <span className="font-bold">{selectedExpert.rating}</span>
                      <span className="text-gray-500">({selectedExpert.reviews_count} Bewertungen)</span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {selectedExpert.location}
                      </span>
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-4 w-4" />
                        {selectedExpert.experience} Jahre Erfahrung
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Fachgebiete</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedExpert.specialties.map((s, i) => (
                      <Badge key={i}>{s.name}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Sprachen</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedExpert.languages.map((lang, i) => (
                      <Badge key={i} variant="outline">{lang}</Badge>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-rose-600">{selectedExpert.cases_count}</div>
                    <div className="text-sm text-gray-500">Bearbeitete Fälle</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {selectedExpert.available ? "Ja" : "Nein"}
                    </div>
                    <div className="text-sm text-gray-500">Verfügbar</div>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowExpertDialog(false)}>
                  Schließen
                </Button>
                <Button>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Kontaktieren
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Expert Dialog */}
      <Dialog open={showAddExpertDialog} onOpenChange={setShowAddExpertDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Neuen Experten hinzufügen</DialogTitle>
            <DialogDescription>
              Fügen Sie einen neuen Sachverständigen oder Gutachter hinzu
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Name</Label>
              <Input
                value={newExpert.name}
                onChange={(e) => setNewExpert({...newExpert, name: e.target.value})}
                placeholder="Dr. Max Mustermann"
              />
            </div>
            <div>
              <Label>Titel/Position</Label>
              <Input
                value={newExpert.title}
                onChange={(e) => setNewExpert({...newExpert, title: e.target.value})}
                placeholder="Kinderpsychologe"
              />
            </div>
            <div>
              <Label>E-Mail</Label>
              <Input
                type="email"
                value={newExpert.email}
                onChange={(e) => setNewExpert({...newExpert, email: e.target.value})}
                placeholder="experte@example.com"
              />
            </div>
            <div>
              <Label>Telefon</Label>
              <Input
                value={newExpert.phone}
                onChange={(e) => setNewExpert({...newExpert, phone: e.target.value})}
                placeholder="+49 123 456789"
              />
            </div>
            <div>
              <Label>Standort</Label>
              <Input
                value={newExpert.location}
                onChange={(e) => setNewExpert({...newExpert, location: e.target.value})}
                placeholder="Berlin"
              />
            </div>
            <div>
              <Label>Erfahrung (Jahre)</Label>
              <Input
                type="number"
                value={newExpert.experience}
                onChange={(e) => setNewExpert({...newExpert, experience: e.target.value})}
                placeholder="10"
              />
            </div>
            <div className="col-span-2">
              <Label>Biografie</Label>
              <Textarea
                value={newExpert.bio}
                onChange={(e) => setNewExpert({...newExpert, bio: e.target.value})}
                placeholder="Kurze Beschreibung..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddExpertDialog(false)}>
              Abbrechen
            </Button>
            <Button onClick={createExpert}>
              <UserPlus className="h-4 w-4 mr-2" />
              Experte hinzufügen
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Match Results Dialog */}
      <Dialog open={showMatchDialog} onOpenChange={setShowMatchDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Experten-Matching Ergebnisse</DialogTitle>
            <DialogDescription>
              Beste Übereinstimmungen für Ihren Fall
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {matchResults.map((result, i) => (
              <div key={i} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarFallback className="bg-rose-100 text-rose-700">
                        {result.expert.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h4 className="font-semibold">{result.expert.name}</h4>
                      <p className="text-sm text-gray-600">{result.expert.title}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-rose-600">{result.score}%</div>
                    <p className="text-xs text-gray-500">Übereinstimmung</p>
                  </div>
                </div>
                <div className="space-y-1">
                  {result.reasons.map((reason, j) => (
                    <div key={j} className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {reason}
                    </div>
                  ))}
                </div>
                <Button className="w-full mt-3">
                  <Target className="h-4 w-4 mr-2" />
                  Diesem Fall zuordnen
                </Button>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMatchDialog(false)}>
              Schließen
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
