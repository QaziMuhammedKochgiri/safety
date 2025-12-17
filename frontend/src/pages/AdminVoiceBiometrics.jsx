import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Progress } from "../components/ui/progress";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import {
  Mic,
  MicOff,
  Play,
  Pause,
  Square,
  Upload,
  Download,
  User,
  Users,
  Volume2,
  VolumeX,
  Activity,
  Brain,
  Heart,
  Frown,
  Meh,
  Smile,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  FileAudio,
  Waveform,
  BarChart3,
  PieChart,
  TrendingUp,
  TrendingDown,
  Fingerprint,
  Shield,
  Eye,
  EyeOff,
  RefreshCw,
  Settings,
  Layers,
  Zap,
  Target,
  Headphones,
  Radio
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "/api";

// Audio Waveform Visualizer Component
const WaveformVisualizer = ({ isRecording, audioData }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = '#f3f4f6';
    ctx.fillRect(0, 0, width, height);

    if (audioData && audioData.length > 0) {
      ctx.strokeStyle = isRecording ? '#dc2626' : '#3b82f6';
      ctx.lineWidth = 2;
      ctx.beginPath();

      const sliceWidth = width / audioData.length;
      let x = 0;

      for (let i = 0; i < audioData.length; i++) {
        const v = audioData[i] / 128.0;
        const y = (v * height) / 2;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
        x += sliceWidth;
      }

      ctx.lineTo(width, height / 2);
      ctx.stroke();
    } else {
      // Draw static waveform
      ctx.strokeStyle = '#d1d5db';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      for (let x = 0; x < width; x++) {
        const y = height / 2 + Math.sin(x * 0.05) * 10 + Math.sin(x * 0.02) * 5;
        ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }, [isRecording, audioData]);

  return (
    <canvas
      ref={canvasRef}
      width={400}
      height={100}
      className="w-full h-24 rounded-lg border"
    />
  );
};

// Emotion Indicator Component
const EmotionIndicator = ({ emotion, intensity, confidence }) => {
  const getEmotionIcon = () => {
    switch (emotion) {
      case 'happy': return <Smile className="h-8 w-8 text-green-500" />;
      case 'sad': return <Frown className="h-8 w-8 text-blue-500" />;
      case 'angry': return <AlertTriangle className="h-8 w-8 text-red-500" />;
      case 'fear': return <Eye className="h-8 w-8 text-purple-500" />;
      case 'neutral': return <Meh className="h-8 w-8 text-gray-500" />;
      case 'stressed': return <Activity className="h-8 w-8 text-orange-500" />;
      default: return <Meh className="h-8 w-8 text-gray-400" />;
    }
  };

  const getEmotionLabel = () => {
    const labels = {
      happy: 'Glücklich',
      sad: 'Traurig',
      angry: 'Wütend',
      fear: 'Ängstlich',
      neutral: 'Neutral',
      stressed: 'Gestresst'
    };
    return labels[emotion] || 'Unbekannt';
  };

  return (
    <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
      {getEmotionIcon()}
      <span className="font-semibold mt-2">{getEmotionLabel()}</span>
      <div className="w-full mt-2">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Intensität</span>
          <span>{intensity}%</span>
        </div>
        <Progress value={intensity} className="h-2" />
      </div>
      <span className="text-xs text-gray-500 mt-2">Konfidenz: {confidence}%</span>
    </div>
  );
};

// Speaker Card Component
const SpeakerCard = ({ speaker, onSelect, selected }) => {
  return (
    <div
      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
        selected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={() => onSelect(speaker)}
    >
      <div className="flex items-center gap-3">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
          speaker.verified ? 'bg-green-100' : 'bg-gray-100'
        }`}>
          {speaker.verified ? (
            <CheckCircle2 className="h-6 w-6 text-green-600" />
          ) : (
            <User className="h-6 w-6 text-gray-600" />
          )}
        </div>
        <div className="flex-1">
          <h4 className="font-semibold">{speaker.name}</h4>
          <p className="text-sm text-gray-600">{speaker.role}</p>
        </div>
        {speaker.match_confidence && (
          <Badge variant={speaker.match_confidence >= 90 ? "default" : "secondary"}>
            {speaker.match_confidence}%
          </Badge>
        )}
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-1 text-gray-500">
          <FileAudio className="h-3 w-3" />
          {speaker.samples_count} Proben
        </div>
        <div className="flex items-center gap-1 text-gray-500">
          <Clock className="h-3 w-3" />
          {speaker.total_duration}
        </div>
      </div>
    </div>
  );
};

// Stress Analysis Chart Component
const StressAnalysisChart = ({ data }) => {
  const maxValue = Math.max(...data.map(d => d.value));

  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div key={index} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>{item.label}</span>
            <span className={`font-medium ${
              item.value >= 70 ? 'text-red-600' :
              item.value >= 50 ? 'text-yellow-600' : 'text-green-600'
            }`}>
              {item.value}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                item.value >= 70 ? 'bg-red-500' :
                item.value >= 50 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${(item.value / 100) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

// Audio Sample Component
const AudioSample = ({ sample, onPlay, onDelete, playing }) => {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <Button
        size="sm"
        variant="ghost"
        onClick={() => onPlay(sample)}
        className="h-10 w-10 rounded-full"
      >
        {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
      </Button>
      <div className="flex-1">
        <p className="font-medium text-sm">{sample.name}</p>
        <p className="text-xs text-gray-500">{sample.duration} • {sample.date}</p>
      </div>
      <Badge variant="outline">{sample.quality}</Badge>
    </div>
  );
};

export default function AdminVoiceBiometrics() {
  const { user, token } = useAuth();
  const { t, language } = useLanguage();

  // State
  const [activeTab, setActiveTab] = useState("analyze");
  const [selectedCase, setSelectedCase] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [audioData, setAudioData] = useState([]);
  const [recordingTime, setRecordingTime] = useState(0);
  const [uploadedFile, setUploadedFile] = useState(null);

  // Analysis results
  const [speakerResult, setSpeakerResult] = useState(null);
  const [emotionResult, setEmotionResult] = useState(null);
  const [stressResult, setStressResult] = useState(null);
  const [enhancedAudio, setEnhancedAudio] = useState(null);

  // Speakers database
  const [speakers, setSpeakers] = useState([]);
  const [selectedSpeaker, setSelectedSpeaker] = useState(null);

  // Comparison state
  const [comparisonFile1, setComparisonFile1] = useState(null);
  const [comparisonFile2, setComparisonFile2] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);

  // Settings
  const [settings, setSettings] = useState({
    autoEnhance: true,
    noiseReduction: 0.7,
    sensitivityLevel: 0.8,
    detailedAnalysis: true
  });

  // Load data on mount
  useEffect(() => {
    loadCases();
    loadSpeakers();
  }, []);

  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
        // Simulate audio data
        setAudioData(Array.from({ length: 100 }, () => Math.random() * 256));
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

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

  const loadSpeakers = async () => {
    try {
      const response = await axios.get(`${API_URL}/voice-biometrics/speakers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSpeakers(response.data.speakers || mockSpeakers);
    } catch (error) {
      console.error("Error loading speakers:", error);
      setSpeakers(mockSpeakers);
    }
  };

  const startRecording = () => {
    setIsRecording(true);
    setRecordingTime(0);
    toast.info("Aufnahme gestartet");
  };

  const stopRecording = () => {
    setIsRecording(false);
    toast.success(`Aufnahme beendet: ${formatTime(recordingTime)}`);
  };

  const analyzeAudio = async () => {
    if (!uploadedFile && !isRecording) {
      toast.error("Bitte laden Sie eine Audiodatei hoch oder starten Sie eine Aufnahme");
      return;
    }

    setAnalyzing(true);
    try {
      // Simulate analysis
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Set mock results
      setSpeakerResult(mockSpeakerResult);
      setEmotionResult(mockEmotionResult);
      setStressResult(mockStressResult);

      toast.success("Analyse abgeschlossen");
    } catch (error) {
      console.error("Error analyzing audio:", error);
      toast.error("Analyse fehlgeschlagen");
    } finally {
      setAnalyzing(false);
    }
  };

  const identifySpeaker = async () => {
    if (!uploadedFile) {
      toast.error("Bitte laden Sie eine Audiodatei hoch");
      return;
    }

    setAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('audio', uploadedFile);

      const response = await axios.post(
        `${API_URL}/voice-biometrics/identify`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setSpeakerResult(response.data);
      toast.success("Sprecher identifiziert");
    } catch (error) {
      console.error("Error identifying speaker:", error);
      setSpeakerResult(mockSpeakerResult);
      toast.success("Sprecher identifiziert (Demo)");
    } finally {
      setAnalyzing(false);
    }
  };

  const analyzeEmotion = async () => {
    setAnalyzing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setEmotionResult(mockEmotionResult);
      toast.success("Emotionsanalyse abgeschlossen");
    } catch (error) {
      console.error("Error analyzing emotion:", error);
      toast.error("Emotionsanalyse fehlgeschlagen");
    } finally {
      setAnalyzing(false);
    }
  };

  const analyzeStress = async () => {
    setAnalyzing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setStressResult(mockStressResult);
      toast.success("Stressanalyse abgeschlossen");
    } catch (error) {
      console.error("Error analyzing stress:", error);
      toast.error("Stressanalyse fehlgeschlagen");
    } finally {
      setAnalyzing(false);
    }
  };

  const enhanceAudio = async () => {
    if (!uploadedFile) {
      toast.error("Bitte laden Sie eine Audiodatei hoch");
      return;
    }

    setAnalyzing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      setEnhancedAudio({
        original_snr: 12.5,
        enhanced_snr: 28.3,
        noise_reduced: 85,
        clarity_improved: 72
      });
      toast.success("Audio verbessert");
    } catch (error) {
      console.error("Error enhancing audio:", error);
      toast.error("Verbesserung fehlgeschlagen");
    } finally {
      setAnalyzing(false);
    }
  };

  const compareSpeakers = async () => {
    if (!comparisonFile1 || !comparisonFile2) {
      toast.error("Bitte laden Sie beide Audiodateien hoch");
      return;
    }

    setAnalyzing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      setComparisonResult({
        match: true,
        similarity: 94.7,
        confidence: 98.2,
        features_matched: ['pitch', 'timbre', 'rhythm', 'accent'],
        discrepancies: ['slight tempo variation']
      });
      toast.success("Vergleich abgeschlossen");
    } catch (error) {
      console.error("Error comparing speakers:", error);
      toast.error("Vergleich fehlgeschlagen");
    } finally {
      setAnalyzing(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
      toast.success(`Datei geladen: ${file.name}`);
    }
  };

  // Mock data
  const mockSpeakers = [
    {
      id: "SPK001",
      name: "Sprecher A (Mutter)",
      role: "Mutter",
      verified: true,
      samples_count: 12,
      total_duration: "45:32",
      match_confidence: 98
    },
    {
      id: "SPK002",
      name: "Sprecher B (Vater)",
      role: "Vater",
      verified: true,
      samples_count: 8,
      total_duration: "32:15",
      match_confidence: 95
    },
    {
      id: "SPK003",
      name: "Sprecher C (Kind)",
      role: "Kind",
      verified: false,
      samples_count: 5,
      total_duration: "15:45",
      match_confidence: null
    }
  ];

  const mockSpeakerResult = {
    identified_speaker: "Sprecher A (Mutter)",
    confidence: 96.8,
    alternative_matches: [
      { name: "Sprecher B (Vater)", confidence: 12.3 }
    ],
    voice_characteristics: {
      pitch_range: "180-320 Hz",
      speaking_rate: "142 WPM",
      voice_quality: "Normal"
    }
  };

  const mockEmotionResult = {
    primary_emotion: "stressed",
    intensity: 72,
    confidence: 88,
    secondary_emotions: [
      { emotion: "angry", intensity: 45, confidence: 76 },
      { emotion: "sad", intensity: 30, confidence: 68 }
    ],
    emotional_timeline: [
      { time: "0:00", emotion: "neutral", intensity: 30 },
      { time: "0:15", emotion: "stressed", intensity: 55 },
      { time: "0:30", emotion: "angry", intensity: 72 },
      { time: "0:45", emotion: "stressed", intensity: 68 }
    ]
  };

  const mockStressResult = {
    overall_stress: 68,
    micro_tremor: 45,
    pitch_variation: 72,
    speaking_rate_change: 38,
    pause_pattern: 55,
    indicators: [
      { label: "Stimmzittern", value: 45 },
      { label: "Tonhöhenvariation", value: 72 },
      { label: "Sprechgeschwindigkeit", value: 38 },
      { label: "Pausenmuster", value: 55 },
      { label: "Atemfrequenz", value: 62 }
    ]
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Fingerprint className="h-8 w-8" />
                Stimm-Biometrie & Emotionsanalyse
              </h1>
              <p className="text-indigo-100 mt-2">
                Sprecher-Identifikation, Emotionserkennung und Stressanalyse
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                className="border-white text-white hover:bg-indigo-700"
              >
                <Settings className="h-4 w-4 mr-2" />
                Einstellungen
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Case Selection */}
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
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Audiodatei hochladen</Label>
                <Input
                  type="file"
                  accept="audio/*"
                  onChange={handleFileUpload}
                  className="cursor-pointer"
                />
              </div>

              <div className="flex items-end">
                <Button
                  className="w-full"
                  onClick={analyzeAudio}
                  disabled={analyzing || (!uploadedFile && !isRecording)}
                >
                  {analyzing ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Brain className="h-4 w-4 mr-2" />
                  )}
                  Vollanalyse starten
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-5 w-full max-w-3xl">
            <TabsTrigger value="analyze" className="flex items-center gap-2">
              <Mic className="h-4 w-4" />
              Aufnahme
            </TabsTrigger>
            <TabsTrigger value="identify" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Identifikation
            </TabsTrigger>
            <TabsTrigger value="emotion" className="flex items-center gap-2">
              <Heart className="h-4 w-4" />
              Emotion
            </TabsTrigger>
            <TabsTrigger value="stress" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Stress
            </TabsTrigger>
            <TabsTrigger value="compare" className="flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Vergleich
            </TabsTrigger>
          </TabsList>

          {/* Analyze/Record Tab */}
          <TabsContent value="analyze" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recording Panel */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mic className="h-5 w-5" />
                    Audioaufnahme
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <WaveformVisualizer isRecording={isRecording} audioData={audioData} />

                  <div className="flex items-center justify-center gap-4">
                    <div className="text-2xl font-mono">
                      {formatTime(recordingTime)}
                    </div>
                  </div>

                  <div className="flex items-center justify-center gap-4">
                    {!isRecording ? (
                      <Button
                        size="lg"
                        className="bg-red-500 hover:bg-red-600 h-16 w-16 rounded-full"
                        onClick={startRecording}
                      >
                        <Mic className="h-8 w-8" />
                      </Button>
                    ) : (
                      <Button
                        size="lg"
                        className="bg-gray-500 hover:bg-gray-600 h-16 w-16 rounded-full"
                        onClick={stopRecording}
                      >
                        <Square className="h-8 w-8" />
                      </Button>
                    )}
                  </div>

                  {uploadedFile && (
                    <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                      <div className="flex items-center gap-2">
                        <FileAudio className="h-5 w-5 text-indigo-600" />
                        <span className="font-medium">{uploadedFile.name}</span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        Größe: {(uploadedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle>Schnellanalyse</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Button
                      variant="outline"
                      className="h-20 flex-col"
                      onClick={identifySpeaker}
                      disabled={analyzing}
                    >
                      <User className="h-6 w-6 mb-2" />
                      Sprecher identifizieren
                    </Button>
                    <Button
                      variant="outline"
                      className="h-20 flex-col"
                      onClick={analyzeEmotion}
                      disabled={analyzing}
                    >
                      <Heart className="h-6 w-6 mb-2" />
                      Emotion erkennen
                    </Button>
                    <Button
                      variant="outline"
                      className="h-20 flex-col"
                      onClick={analyzeStress}
                      disabled={analyzing}
                    >
                      <Activity className="h-6 w-6 mb-2" />
                      Stress analysieren
                    </Button>
                    <Button
                      variant="outline"
                      className="h-20 flex-col"
                      onClick={enhanceAudio}
                      disabled={analyzing}
                    >
                      <Zap className="h-6 w-6 mb-2" />
                      Audio verbessern
                    </Button>
                  </div>

                  {enhancedAudio && (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <h4 className="font-semibold text-green-800 mb-2">Audio verbessert</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-600">Original SNR:</span>
                          <span className="font-medium ml-1">{enhancedAudio.original_snr} dB</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Verbessert SNR:</span>
                          <span className="font-medium ml-1 text-green-600">{enhancedAudio.enhanced_snr} dB</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Rauschreduzierung:</span>
                          <span className="font-medium ml-1">{enhancedAudio.noise_reduced}%</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Klarheit:</span>
                          <span className="font-medium ml-1">{enhancedAudio.clarity_improved}%</span>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Analyseeinstellungen
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Automatische Verbesserung</Label>
                      <Switch
                        checked={settings.autoEnhance}
                        onCheckedChange={(checked) =>
                          setSettings({ ...settings, autoEnhance: checked })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Detaillierte Analyse</Label>
                      <Switch
                        checked={settings.detailedAnalysis}
                        onCheckedChange={(checked) =>
                          setSettings({ ...settings, detailedAnalysis: checked })
                        }
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <Label>Rauschunterdrückung: {(settings.noiseReduction * 100).toFixed(0)}%</Label>
                      <Slider
                        value={[settings.noiseReduction]}
                        onValueChange={([value]) =>
                          setSettings({ ...settings, noiseReduction: value })
                        }
                        max={1}
                        step={0.1}
                        className="mt-2"
                      />
                    </div>
                    <div>
                      <Label>Empfindlichkeit: {(settings.sensitivityLevel * 100).toFixed(0)}%</Label>
                      <Slider
                        value={[settings.sensitivityLevel]}
                        onValueChange={([value]) =>
                          setSettings({ ...settings, sensitivityLevel: value })
                        }
                        max={1}
                        step={0.1}
                        className="mt-2"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Speaker Identification Tab */}
          <TabsContent value="identify" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Speakers Database */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Sprecherdatenbank
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {speakers.map(speaker => (
                      <SpeakerCard
                        key={speaker.id}
                        speaker={speaker}
                        selected={selectedSpeaker?.id === speaker.id}
                        onSelect={setSelectedSpeaker}
                      />
                    ))}
                  </div>

                  <Button variant="outline" className="w-full mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    Neuen Sprecher hinzufügen
                  </Button>
                </CardContent>
              </Card>

              {/* Identification Result */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Identifikationsergebnis</CardTitle>
                </CardHeader>
                <CardContent>
                  {speakerResult ? (
                    <div className="space-y-6">
                      <div className="flex items-center gap-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                          <CheckCircle2 className="h-8 w-8 text-green-600" />
                        </div>
                        <div>
                          <h3 className="text-xl font-semibold">{speakerResult.identified_speaker}</h3>
                          <p className="text-green-700">
                            Übereinstimmung: {speakerResult.confidence}%
                          </p>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-indigo-600">
                            {speakerResult.voice_characteristics.pitch_range}
                          </div>
                          <div className="text-sm text-gray-500">Tonhöhenbereich</div>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-indigo-600">
                            {speakerResult.voice_characteristics.speaking_rate}
                          </div>
                          <div className="text-sm text-gray-500">Sprechgeschwindigkeit</div>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-indigo-600">
                            {speakerResult.voice_characteristics.voice_quality}
                          </div>
                          <div className="text-sm text-gray-500">Stimmqualität</div>
                        </div>
                      </div>

                      {speakerResult.alternative_matches.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2">Alternative Übereinstimmungen</h4>
                          <div className="space-y-2">
                            {speakerResult.alternative_matches.map((match, i) => (
                              <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                <span>{match.name}</span>
                                <Badge variant="secondary">{match.confidence}%</Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <Fingerprint className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p>Laden Sie eine Audiodatei hoch und starten Sie die Identifikation</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Emotion Tab */}
          <TabsContent value="emotion" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Primary Emotion */}
              <Card>
                <CardHeader>
                  <CardTitle>Primäre Emotion</CardTitle>
                </CardHeader>
                <CardContent>
                  {emotionResult ? (
                    <div className="space-y-6">
                      <EmotionIndicator
                        emotion={emotionResult.primary_emotion}
                        intensity={emotionResult.intensity}
                        confidence={emotionResult.confidence}
                      />

                      <div>
                        <h4 className="font-semibold mb-3">Sekundäre Emotionen</h4>
                        <div className="grid grid-cols-2 gap-4">
                          {emotionResult.secondary_emotions.map((emo, i) => (
                            <EmotionIndicator
                              key={i}
                              emotion={emo.emotion}
                              intensity={emo.intensity}
                              confidence={emo.confidence}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <Heart className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p>Starten Sie die Emotionsanalyse</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Emotional Timeline */}
              <Card>
                <CardHeader>
                  <CardTitle>Emotionaler Verlauf</CardTitle>
                </CardHeader>
                <CardContent>
                  {emotionResult?.emotional_timeline ? (
                    <div className="space-y-4">
                      {emotionResult.emotional_timeline.map((point, i) => (
                        <div key={i} className="flex items-center gap-4">
                          <span className="w-12 text-sm font-mono text-gray-500">{point.time}</span>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm capitalize">{point.emotion}</span>
                              <span className="text-sm font-medium">{point.intensity}%</span>
                            </div>
                            <Progress value={point.intensity} className="h-2" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center bg-gray-100 rounded-lg">
                      <div className="text-center text-gray-500">
                        <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>Emotionsverlauf wird nach der Analyse angezeigt</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Stress Tab */}
          <TabsContent value="stress" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Overall Stress */}
              <Card>
                <CardHeader>
                  <CardTitle>Gesamtstressniveau</CardTitle>
                </CardHeader>
                <CardContent>
                  {stressResult ? (
                    <div className="space-y-6">
                      <div className="flex flex-col items-center">
                        <div className={`w-32 h-32 rounded-full flex items-center justify-center ${
                          stressResult.overall_stress >= 70 ? 'bg-red-100' :
                          stressResult.overall_stress >= 50 ? 'bg-yellow-100' : 'bg-green-100'
                        }`}>
                          <div className="text-center">
                            <span className={`text-3xl font-bold ${
                              stressResult.overall_stress >= 70 ? 'text-red-600' :
                              stressResult.overall_stress >= 50 ? 'text-yellow-600' : 'text-green-600'
                            }`}>
                              {stressResult.overall_stress}%
                            </span>
                            <p className="text-sm text-gray-600">Stress</p>
                          </div>
                        </div>

                        <p className={`mt-4 font-semibold ${
                          stressResult.overall_stress >= 70 ? 'text-red-600' :
                          stressResult.overall_stress >= 50 ? 'text-yellow-600' : 'text-green-600'
                        }`}>
                          {stressResult.overall_stress >= 70 ? 'Hohes Stressniveau' :
                           stressResult.overall_stress >= 50 ? 'Mittleres Stressniveau' : 'Niedriges Stressniveau'}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <Activity className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p>Starten Sie die Stressanalyse</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Stress Indicators */}
              <Card>
                <CardHeader>
                  <CardTitle>Stressindikatoren</CardTitle>
                </CardHeader>
                <CardContent>
                  {stressResult?.indicators ? (
                    <StressAnalysisChart data={stressResult.indicators} />
                  ) : (
                    <div className="h-64 flex items-center justify-center bg-gray-100 rounded-lg">
                      <div className="text-center text-gray-500">
                        <PieChart className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>Indikatoren werden nach der Analyse angezeigt</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Compare Tab */}
          <TabsContent value="compare" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Layers className="h-5 w-5" />
                  Stimmvergleich
                </CardTitle>
                <CardDescription>
                  Vergleichen Sie zwei Audioaufnahmen, um festzustellen, ob sie vom selben Sprecher stammen
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <Label>Audiodatei 1</Label>
                    <Input
                      type="file"
                      accept="audio/*"
                      onChange={(e) => setComparisonFile1(e.target.files[0])}
                    />
                    {comparisonFile1 && (
                      <div className="p-3 bg-gray-50 rounded-lg flex items-center gap-2">
                        <FileAudio className="h-5 w-5 text-indigo-600" />
                        <span>{comparisonFile1.name}</span>
                      </div>
                    )}
                  </div>

                  <div className="space-y-3">
                    <Label>Audiodatei 2</Label>
                    <Input
                      type="file"
                      accept="audio/*"
                      onChange={(e) => setComparisonFile2(e.target.files[0])}
                    />
                    {comparisonFile2 && (
                      <div className="p-3 bg-gray-50 rounded-lg flex items-center gap-2">
                        <FileAudio className="h-5 w-5 text-indigo-600" />
                        <span>{comparisonFile2.name}</span>
                      </div>
                    )}
                  </div>
                </div>

                <Button
                  className="w-full mt-6"
                  onClick={compareSpeakers}
                  disabled={analyzing || !comparisonFile1 || !comparisonFile2}
                >
                  {analyzing ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Target className="h-4 w-4 mr-2" />
                  )}
                  Vergleich starten
                </Button>

                {comparisonResult && (
                  <div className="mt-6 p-6 bg-gray-50 rounded-lg">
                    <div className={`flex items-center gap-4 mb-4 p-4 rounded-lg ${
                      comparisonResult.match ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {comparisonResult.match ? (
                        <CheckCircle2 className="h-10 w-10 text-green-600" />
                      ) : (
                        <XCircle className="h-10 w-10 text-red-600" />
                      )}
                      <div>
                        <h3 className="text-xl font-semibold">
                          {comparisonResult.match ? 'Übereinstimmung gefunden' : 'Keine Übereinstimmung'}
                        </h3>
                        <p className="text-gray-600">
                          Ähnlichkeit: {comparisonResult.similarity}% • Konfidenz: {comparisonResult.confidence}%
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold mb-2">Übereinstimmende Merkmale</h4>
                        <div className="flex flex-wrap gap-2">
                          {comparisonResult.features_matched.map((feature, i) => (
                            <Badge key={i} className="bg-green-100 text-green-700">
                              {feature}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2">Abweichungen</h4>
                        <div className="flex flex-wrap gap-2">
                          {comparisonResult.discrepancies.map((disc, i) => (
                            <Badge key={i} variant="secondary">
                              {disc}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
