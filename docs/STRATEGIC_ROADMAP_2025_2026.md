# SafeChild Stratejik Yol Haritası 2025-2026

**Son Güncelleme:** 2025-12-13
**Proje Türü:** Open Source (MIT License)
**Finansman:** Vakıf Destekli + Bağışlar
**Hedef:** Çocuk velayeti davalarında ailelere ücretsiz dijital forensik destek

---

## 📋 Proje Felsefesi

```
✓ 100% Ücretsiz - Clientlerden asla ücret alınmaz
✓ Open Source - Topluluk katkısına açık
✓ Vakıf Destekli - Sürdürülebilir finansman
✓ Ücretsiz Servisler - Mümkün oldukça self-hosted/free-tier
✓ Bağış Tabanlı - Gönüllü destekler kabul edilir
```

---

## 🎯 VİZYON

```
2025 Sonu: Rakiplerle EŞİT seviye (Feature Parity)
2026 Sonu: Child Custody Forensics alanında EN İYİ open-source çözüm
```

---

# 📈 PHASE 1: RAKİPLERLE EŞİT SEVİYE (0-12 Ay)

## 🗓️ Q1 2025 (Ocak-Mart): FOUNDATION

### Sprint 1-2: iOS Desteği (Hafta 1-4)

#### iTunes Backup Parser
- [x] biplist, plistlib kurulumu (Python stdlib - ücretsiz) ✅ 2025-12-13
- [x] Manifest.db parsing ✅ 2025-12-13
- [x] Info.plist extraction ✅ 2025-12-13
- [x] WhatsApp iOS backup (ChatStorage.sqlite) ✅ 2025-12-13
- [x] SMS/iMessage (sms.db) ✅ 2025-12-13
- [x] Contacts (AddressBook.sqlitedb) ✅ 2025-12-13
- [x] Call history (CallHistory.storedata) ✅ 2025-12-13

#### iOS Agent (PWA - Ücretsiz)
- [x] Safari Web App manifest ✅ 2025-12-13 (manifest.json + IOSAgent.jsx)
- [x] Photo library access (consent-based) ✅ 2025-12-13
- [x] Contact export ✅ 2025-12-13
- [ ] Screen recording guidance

#### Backend Integration
- [x] /api/forensics/analyze-ios endpoint ✅ 2025-12-13 (ios_forensics.py)
- [x] iOS-specific parsers ✅ 2025-12-13 (ios_backup.py oluşturuldu)
- [ ] Unified report format

**Kullanılan Araçlar:**
| Araç | Maliyet | Alternatif |
|------|---------|------------|
| Python biplist | Ücretsiz | stdlib |
| libimobiledevice | Ücretsiz | Open source |
| idevicebackup2 | Ücretsiz | Open source |

---

### Sprint 3-4: Cloud Backup Integration (Hafta 5-8)

#### Google Drive Integration
- [x] OAuth2 flow (consent-based) ✅ 2025-12-13 (google_drive.py)
- [x] WhatsApp backup discovery ✅ 2025-12-13
- [x] Backup download & decrypt ✅ 2025-12-13
- [x] crypt14/crypt15 key extraction ✅ 2025-12-13 (whatsapp_decrypt.py)

#### iCloud Integration (Gelecek - Opsiyonel)
- [ ] pyicloud authentication
- [ ] 2FA handling
- [ ] Backup listing
- [ ] Selective download

#### Frontend
- [x] Cloud connection wizard ✅ 2025-12-13 (CloudConnectionWizard.jsx)
- [x] Backup selection UI ✅ 2025-12-13
- [x] Download progress ✅ 2025-12-13

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Google Cloud API | Ücretsiz tier | Günlük limit var |
| pyicloud | Ücretsiz | Open source |
| wa-crypt-tools | Ücretsiz | Open source |

---

### Sprint 5-6: Advanced Data Recovery (Hafta 9-12)

#### SQLite WAL Analysis
- [x] Write-Ahead Log parsing ✅ 2025-12-13 (sqlite_wal.py)
- [x] Deleted row recovery ✅ 2025-12-13
- [x] Timestamp reconstruction ✅ 2025-12-13
- [x] Confidence scoring ✅ 2025-12-13

#### File Carving
- [x] JPEG/PNG header scanning ✅ 2025-12-13 (file_carving.py)
- [ ] Video fragment recovery
- [ ] Audio message recovery
- [ ] Thumbnail extraction

#### Freespace Analysis
- [ ] Unallocated block scanning
- [ ] Fragment matching
- [ ] Recovery report

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Sleuth Kit (pytsk3) | Ücretsiz | Zaten entegre |
| Scalpel | Ücretsiz | Open source |
| Foremost | Ücretsiz | Open source |

---

## 🗓️ Q2 2025 (Nisan-Haziran): VISUALIZATION

### Sprint 7-8: Interactive Timeline (Hafta 13-16)

#### Timeline Engine
- [ ] Multi-source event merge
- [ ] Conflict resolution
- [ ] Gap detection
- [ ] Anomaly highlighting

#### UI Components (React)
- [x] vis-timeline.js integration (MIT License) ✅ 2025-12-13 (CaseTimeline.jsx, ForensicTimeline.jsx)
- [x] Zoom levels (year/month/day/hour) ✅ 2025-12-13
- [x] Event clustering ✅ 2025-12-13
- [x] Color coding by source ✅ 2025-12-13
- [x] Click-to-detail ✅ 2025-12-13
- [x] Filter panel ✅ 2025-12-13

#### Export
- [x] Timeline as image (PNG/SVG) ✅ 2025-12-13 (timeline_export.py)
- [x] Timeline as PDF ✅ 2025-12-13 (reportlab integration)
- [x] Data as CSV ✅ 2025-12-13

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| vis-timeline.js | Ücretsiz | MIT License |
| html2canvas | Ücretsiz | Export için |

---

### Sprint 9-10: Contact Network Graph (Hafta 17-20)

#### Graph Engine
- [x] Node extraction (all contacts) ✅ 2025-12-13 (contact_network.py)
- [x] Edge calculation (message count) ✅ 2025-12-13
- [x] Cluster detection (K-means) ✅ 2025-12-13
- [x] Centrality analysis ✅ 2025-12-13

#### UI Components
- [x] Cytoscape.js integration (MIT License) ✅ 2025-12-13 (ContactNetworkGraph.jsx)
- [x] Force-directed layout ✅ 2025-12-13 (COSE layout)
- [x] Node sizing (by frequency) ✅ 2025-12-13
- [x] Edge coloring (by platform) ✅ 2025-12-13
- [x] Zoom/pan controls ✅ 2025-12-13
- [x] Node selection + details ✅ 2025-12-13

#### Analytics
- [ ] Communication frequency heatmap
- [x] Relationship strength scoring ✅ 2025-12-13 (centrality)
- [x] Suspicious pattern detection ✅ 2025-12-13 (one-way comm, high freq)

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Cytoscape.js | Ücretsiz | MIT License |
| scikit-learn | Ücretsiz | K-means için |

---

### Sprint 11-12: GPS & Location Mapping (Hafta 21-24)

#### Data Extraction
- [x] EXIF GPS from all photos ✅ 2025-12-13 (location_mapping.py)
- [x] Google Location History ✅ 2025-12-13
- [x] iOS Significant Locations ✅ 2025-12-13
- [ ] Check-in data (social media)

#### Map Visualization
- [x] Leaflet.js integration (BSD License) ✅ 2025-12-13 (LocationMap.jsx)
- [x] OpenStreetMap tiles (ücretsiz) ✅ 2025-12-13
- [x] Heatmap layer ✅ 2025-12-13 (leaflet.heat)
- [x] Timeline slider (animate movement) ✅ 2025-12-13
- [x] Cluster markers ✅ 2025-12-13
- [ ] Geofence alerts

#### Analysis
- [x] Frequent locations ✅ 2025-12-13 (detect_clusters)
- [ ] Travel patterns
- [ ] Location anomalies
- [ ] Address reverse geocoding (Nominatim - ücretsiz)

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Leaflet.js | Ücretsiz | BSD License |
| OpenStreetMap | Ücretsiz | Tile server |
| Nominatim | Ücretsiz | Self-host edilebilir |

---

## 🗓️ Q3 2025 (Temmuz-Eylül): AI & DETECTION

### Sprint 13-14: Speech-to-Text (Hafta 25-28)

#### Audio Processing
- [x] WhatsApp voice note extraction (.opus) ✅ 2025-12-13 (speech_to_text.py)
- [x] Telegram voice extraction ✅ 2025-12-13
- [x] Video audio track extraction ✅ 2025-12-13 (ffmpeg)
- [x] Format conversion (ffmpeg - ücretsiz) ✅ 2025-12-13

#### Transcription Engine
- [x] OpenAI Whisper LOCAL (ücretsiz, self-hosted) ✅ 2025-12-13 (WhisperTranscriber)
- [x] Language detection (auto) ✅ 2025-12-13
- [x] Timestamp alignment ✅ 2025-12-13 (TranscriptSegment)
- [ ] Speaker diarization (optional)

#### Search & Analysis
- [x] Full-text search on transcripts ✅ 2025-12-13 (transcription.py router)
- [x] Keyword highlighting ✅ 2025-12-13 (TranscriptionViewer.jsx)
- [x] Sentiment analysis (local model) ✅ 2025-12-13 (TranscriptAnalyzer)
- [x] AI risk assessment on audio ✅ 2025-12-13 (RISK_KEYWORDS)

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Whisper (local) | Ücretsiz | Self-hosted, GPU önerilir |
| ffmpeg | Ücretsiz | Open source |
| pyannote | Ücretsiz | Speaker diarization |

---

### Sprint 15-16: Image Analysis (Hafta 29-32)

#### Face Detection
- [x] face_recognition library (dlib tabanlı, ücretsiz) ✅ 2025-12-13 (FaceDetector)
- [x] Face extraction & grouping ✅ 2025-12-13 (cluster_faces)
- [x] Age estimation (local model) ✅ 2025-12-13 (heuristic-based)
- [x] Same-person matching ✅ 2025-12-13 (match_faces)

#### Image Categorization
- [x] Scene classification (local CLIP model) ✅ 2025-12-13 (ImageCategorizer)
- [x] Object detection (YOLO - ücretsiz) ✅ 2025-12-13 (optional yolov8)
- [x] Text extraction (Tesseract OCR - ücretsiz) ✅ 2025-12-13 (OCRExtractor)
- [x] Duplicate finder (perceptual hash) ✅ 2025-12-13 (imagehash)

#### Safety Features
- [x] PhotoDNA-benzeri hash matching (open source impl) ✅ 2025-12-13 (SafetyChecker)
- [ ] Explicit content detection (local NSFW model)
- [ ] Auto-blur sensitive content
- [x] Alert workflow ✅ 2025-12-13 (SafetyLevel enum)

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| face_recognition | Ücretsiz | dlib tabanlı |
| YOLO | Ücretsiz | Object detection |
| Tesseract | Ücretsiz | OCR |
| imagehash | Ücretsiz | Perceptual hash |
| CLIP | Ücretsiz | Scene classification |

---

### Sprint 17-18: Advanced AI Analysis (Hafta 33-36)

#### Self-Hosted LLM Option
- [x] Ollama kurulumu (ücretsiz) ✅ 2025-12-13 (OllamaClient)
- [x] Llama 2 / Mistral model (ücretsiz) ✅ 2025-12-13 (configurable model)
- [x] Local inference setup ✅ 2025-12-13 (LLMRouter)
- [x] Fallback to Claude API (bağış varsa) ✅ 2025-12-13 (ClaudeClient)

#### Enhanced Risk Detection
- [x] Multi-language support (local models) ✅ 2025-12-13 (TR+EN patterns)
- [x] Cultural context awareness ✅ 2025-12-13 (RiskDetector)
- [x] Sarcasm/irony detection ✅ 2025-12-13 (LLM-based analysis)
- [x] Intent classification ✅ 2025-12-13 (RiskCategory enum)

#### Parental Alienation Detection
- [x] Manipulation tactics taxonomy ✅ 2025-12-13 (AlienationTactic - 10 tactics)
- [x] Evidence scoring (1-10) ✅ 2025-12-13 (severity_score)
- [x] Pattern timeline ✅ 2025-12-13 (evidence_context tracking)
- [x] Expert witness report format ✅ 2025-12-13 (CourtReportGenerator)

#### Court-Ready Summaries
- [x] Executive summary generator ✅ 2025-12-13 (generate_court_summary)
- [x] Evidence highlight extraction ✅ 2025-12-13 (extract_key_evidence)
- [x] Counter-argument anticipation ✅ 2025-12-13 (anticipate_counter_arguments)
- [x] Legal citation suggestions ✅ 2025-12-13 (generate_recommendations)

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Ollama | Ücretsiz | Local LLM runner |
| Llama 2 / Mistral | Ücretsiz | Open weights |
| Claude API | Pay-as-you-go | Bağış varsa fallback |

---

## 🗓️ Q4 2025 (Ekim-Aralık): PROFESSIONAL FEATURES

### Sprint 19-20: Court-Ready Reports (Hafta 37-40)

#### Report Engine
- [x] WeasyPrint PDF generation (ücretsiz) ✅ 2025-12-13 (PDFGenerator)
- [x] Professional templates ✅ 2025-12-13 (ReportTemplate with CSS)
- [x] Digital signature (cryptography lib) ✅ 2025-12-13 (DigitalSigner)
- [x] Hash verification page ✅ 2025-12-13 (content_hash SHA-256)
- [x] Chain of custody section ✅ 2025-12-13 (ChainOfCustody dataclass)
- [x] Multi-language (DE/EN/TR) ✅ 2025-12-13 (ReportLanguage enum)

#### Legal Compliance
- [x] GDPR compliance checklist ✅ 2025-12-13 (GDPRChecklist 10 items)
- [x] Expert witness statement template ✅ 2025-12-13 (ExpertWitnessTemplate)
- [x] Evidence authentication page ✅ 2025-12-13 (EvidenceAuthenticationPage)
- [x] Court filing format (Germany/Turkey) ✅ 2025-12-13 (CourtFilingFormat)

#### Export Options
- [x] PDF (primary) ✅ 2025-12-13 (PDFGenerator with WeasyPrint)
- [x] DOCX (python-docx - ücretsiz) ✅ 2025-12-13 (DOCXGenerator)
- [x] E001 format (EU standard) ✅ 2025-12-13 (E001Exporter)
- [x] Cellebrite XML (interoperability) ✅ 2025-12-13 (CellebriteExporter)

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| WeasyPrint | Ücretsiz | PDF generation |
| python-docx | Ücretsiz | DOCX export |
| cryptography | Ücretsiz | Digital signatures |

---

### Sprint 21-22: Multi-Device Comparison (Hafta 41-44)

#### Device Pairing
- [x] Parent-child device matching ✅ 2025-12-13
- [x] Timeline synchronization ✅ 2025-12-13
- [x] Contact overlap detection ✅ 2025-12-13
- [x] Message thread matching ✅ 2025-12-13

#### Discrepancy Detection
- [x] Deleted message detection (A has, B doesn't) ✅ 2025-12-13
- [x] Edit history comparison ✅ 2025-12-13
- [x] Time gap analysis ✅ 2025-12-13
- [x] Screenshot vs original ✅ 2025-12-13

#### Visualization
- [x] Side-by-side timeline ✅ 2025-12-13
- [x] Diff view for conversations ✅ 2025-12-13
- [x] Conflict highlighting ✅ 2025-12-13

---

### Sprint 23-24: Dashboard Enhancement (Hafta 45-48)

#### Dashboard Redesign
- [x] KPI cards (cases, alerts, pending) ✅ 2025-12-13
- [x] Real-time activity feed ✅ 2025-12-13
- [x] Quick action buttons ✅ 2025-12-13
- [x] Notification center ✅ 2025-12-13

#### Case Management
- [x] Case assignment workflow ✅ 2025-12-13
- [x] Status tracking (Kanban) ✅ 2025-12-13
- [x] Due date alerts ✅ 2025-12-13
- [x] Team collaboration ✅ 2025-12-13

#### Analytics
- [x] Case completion metrics ✅ 2025-12-13
- [x] Risk distribution charts ✅ 2025-12-13
- [x] Client satisfaction tracking ✅ 2025-12-13

---

# 📈 PHASE 2: RAKİPLERDEN ÖNDE (13-24 Ay)

## 🗓️ Q1 2026: CHILD CUSTODY SPECIALIZATION

### Parental Alienation Expert System

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] 50+ manipulation tactic tanımı ✅ (tactics_database.py)
- [x] Literature-backed scoring ✅ (severity_scorer.py)
- [x] Pattern matching (NLP) ✅ (pattern_matcher.py)
- [x] Severity scoring (1-10) ✅ (severity_scorer.py)
- [x] Alienation timeline analyzer ✅ (timeline_analyzer.py)
- [x] Expert witness report format (EN/DE/TR) ✅ (expert_report.py)

#### Frontend (BEKLIYOR)
- [ ] AdminAlienationAnalysis.jsx sayfası
- [ ] TacticsCategoryCard.jsx komponenti
- [ ] SeverityGauge.jsx komponenti
- [ ] AlienationTimeline.jsx (vis-timeline.js)
- [ ] EvidenceDetailPanel.jsx
- [ ] LiteratureReferences.jsx
- [ ] AlienationReportExport.jsx modal

#### API Router
- [ ] POST /api/alienation/analyze
- [ ] GET /api/alienation/tactics
- [ ] GET /api/alienation/report/{case_id}
- [ ] GET /api/alienation/timeline/{case_id}

### Child Safety Risk Predictor

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] 25+ risk faktör tanımı ✅ (risk_model.py)
- [x] Feature extraction ✅ (feature_extractor.py)
- [x] Outcome correlation ✅ (outcome_correlator.py)
- [x] Intervention recommendation ✅ (intervention_recommender.py)
- [x] Explainable AI ✅ (explainer.py)

#### Frontend (BEKLIYOR)
- [ ] AdminRiskPredictor.jsx sayfası
- [ ] RiskScoreGauge.jsx komponenti
- [ ] RiskTrajectoryChart.jsx (Recharts)
- [ ] RiskFactorCard.jsx (expandable)
- [ ] ExplainableAIPanel.jsx
- [ ] WhatIfScenario.jsx
- [ ] InterventionRecommender.jsx

#### API Router
- [ ] POST /api/risk/analyze
- [ ] GET /api/risk/factors
- [ ] GET /api/risk/interventions/{case_id}
- [ ] POST /api/risk/explain

---

## 🗓️ Q2 2026: AUTOMATION & EFFICIENCY

### Automated Evidence Collection Agent

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] Background sync engine ✅ (collection_engine.py)
- [x] Scheduler with cron expressions ✅ (scheduler.py)
- [x] Change detection algorithm ✅ (change_detector.py)
- [x] Alert system with severity levels ✅ (alert_system.py)
- [x] Weekly digest generator ✅ (digest_generator.py)

#### Frontend (BEKLIYOR)
- [ ] AdminEvidenceScheduler.jsx sayfası
- [ ] ScheduleManager.jsx komponenti
- [ ] ChangeAlertList.jsx komponenti
- [ ] DigestPreview.jsx
- [ ] CronExpressionBuilder.jsx

#### API Router
- [ ] POST /api/evidence-agent/schedule
- [ ] GET /api/evidence-agent/schedules
- [ ] GET /api/evidence-agent/changes/{case_id}
- [ ] GET /api/evidence-agent/alerts
- [ ] GET /api/evidence-agent/digest/{case_id}

### One-Click Court Package

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] Evidence selection wizard ✅ (evidence_selector.py)
- [x] Relevance scoring ✅ (relevance_scorer.py)
- [x] Redundancy removal ✅ (redundancy_remover.py)
- [x] Exhibit manager with Bates numbering ✅ (exhibit_manager.py)
- [x] Document compiler (PDF/DOCX/HTML) ✅ (document_compiler.py)
- [x] German/Turkish/EU E001 formats ✅ (court_formats.py)

#### Frontend (BEKLIYOR)
- [ ] AdminCourtPackage.jsx sayfası
- [ ] CourtPackageWizard.jsx (multi-step wizard)
- [ ] EvidenceSelector.jsx (drag & drop)
- [ ] RelevanceScoreIndicator.jsx
- [ ] CourtFormatSelector.jsx
- [ ] PackagePreview.jsx (PDF önizleme)
- [ ] ExhibitManager.jsx
- [ ] ChainOfCustodyBadge.jsx

#### API Router
- [ ] POST /api/court/generate
- [ ] GET /api/court/formats
- [ ] POST /api/court/select-evidence
- [ ] GET /api/court/preview/{package_id}
- [ ] POST /api/court/export/{format}

---

## 🗓️ Q3 2026: ADVANCED AI

### Multilingual AI with Cultural Context

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] Language detection ✅ (language_detector.py)
- [x] Legal idiom translation ✅ (idiom_translator.py)
- [x] Cultural context analysis ✅ (cultural_context.py)
- [x] Cultural analyzer ✅ (cultural_analyzer.py)
- [x] Legal terminology (DE/TR/EU/UK/US) ✅ (legal_terminology.py)

#### Frontend (BEKLIYOR)
- [ ] AdminMultilingual.jsx sayfası
- [ ] LanguageDetectionPanel.jsx
- [ ] CulturalContextIndicator.jsx
- [ ] LegalTerminologyLookup.jsx
- [ ] TranslationPreview.jsx

#### API Router
- [ ] POST /api/multilingual/detect
- [ ] POST /api/multilingual/translate
- [ ] GET /api/multilingual/terminology
- [ ] POST /api/multilingual/cultural-context

### Voice Biometrics (Local Processing)

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] Voice feature extraction (MFCC, spectral) ✅ (voice_features.py)
- [x] Speaker identification & diarization ✅ (speaker_identifier.py)
- [x] 12-emotion detection ✅ (emotion_analyzer.py)
- [x] Stress detection (with disclaimers) ✅ (stress_detector.py)
- [x] Audio enhancement ✅ (audio_enhancer.py)
- [x] Forensic voice comparison ✅ (voice_comparison.py)

#### Frontend (BEKLIYOR)
- [ ] AdminVoiceBiometrics.jsx sayfası
- [ ] AudioWaveformPlayer.jsx (wavesurfer.js)
- [ ] SpeakerDiarization.jsx
- [ ] EmotionAnalysisChart.jsx
- [ ] StressTimeline.jsx
- [ ] VoiceComparisonPanel.jsx
- [ ] AudioEnhancer.jsx

#### API Router
- [ ] POST /api/voice/analyze
- [ ] POST /api/voice/identify
- [ ] POST /api/voice/emotion
- [ ] POST /api/voice/stress
- [ ] POST /api/voice/enhance
- [ ] POST /api/voice/compare

---

## 🗓️ Q4 2026: ECOSYSTEM & SCALE

### Community Expert Network (Volunteer-Based)

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] Expert profile management (18 specializations) ✅ (expert_profile.py)
- [x] AI case-expert matching ✅ (case_matcher.py)
- [x] Consultation management ✅ (consultation.py)
- [x] Review & quality scoring ✅ (review_system.py)
- [x] Knowledge base (articles, precedents, FAQs) ✅ (knowledge_base.py)
- [x] Pro bono coordination ✅ (pro_bono.py)

#### Frontend (BEKLIYOR)
- [ ] AdminExpertNetwork.jsx sayfası
- [ ] ExpertCard.jsx komponenti
- [ ] ExpertProfileModal.jsx
- [ ] ConsultationScheduler.jsx
- [ ] CaseMatchingPanel.jsx
- [ ] ReviewStars.jsx
- [ ] KnowledgeBaseSearch.jsx
- [ ] ProBonoEligibility.jsx

#### API Router
- [ ] GET /api/experts
- [ ] POST /api/experts
- [ ] GET /api/experts/{id}
- [ ] POST /api/experts/match
- [ ] POST /api/consultations
- [ ] GET /api/consultations/{case_id}
- [ ] GET /api/knowledge-base

### Mobile-First PWA

#### Backend (TAMAMLANDI ✅ 2025-12-13)
- [x] Offline manager (cache, sync, conflict resolution) ✅ (offline_manager.py)
- [x] Push notification service (14 types, quiet hours) ✅ (push_notifications.py)
- [x] Device manager (capabilities, security) ✅ (device_manager.py)
- [x] Mobile evidence capture (forensic integrity) ✅ (mobile_evidence.py)
- [x] App shell manager (manifest, navigation) ✅ (app_shell.py)
- [x] Secure storage (AES-GCM encryption) ✅ (secure_storage.py)

#### Frontend (BEKLIYOR)
- [ ] MobileLayout.jsx (touch-optimized)
- [ ] SwipeNavigation.jsx
- [ ] PushNotificationSettings.jsx
- [ ] OfflineIndicator.jsx
- [ ] BiometricLogin.jsx
- [ ] QuickCaptureButton.jsx
- [ ] MobileDashboard.jsx

#### PWA Configuration
- [ ] Service Worker yapılandırması
- [ ] manifest.json optimizasyonu
- [ ] Workbox cache stratejileri
- [ ] Background sync
- [ ] App install prompt

---

# 💰 KAYNAK VE ALTERNATİF PLANI

## Ücretsiz Servis Alternatifleri

| Ücretli Servis | Ücretsiz Alternatif | Not |
|----------------|---------------------|-----|
| AWS Rekognition | face_recognition + YOLO | Self-hosted |
| OpenAI Whisper API | Whisper local | GPU önerilir |
| Claude API | Ollama + Llama/Mistral | Self-hosted |
| Google Maps API | Leaflet + OSM | Fully free |
| Twilio SMS | Self-hosted SMTP | Email alerts |
| Firebase | Supabase free tier | 500MB DB |
| Vercel Pro | Coolify self-hosted | VPS üzerinde |
| Sentry Pro | Self-hosted Sentry | Monitoring |

## Donanım Gereksinimleri (Self-Hosting)

### Minimum VPS (Mevcut)
- 4 vCPU, 8GB RAM, 100GB SSD
- Mevcut: 37.60.230.9
- Maliyet: ~€20/ay

### Önerilen (AI özellikler için)
- 8 vCPU, 32GB RAM, 500GB SSD
- GPU: RTX 3060 veya T4 (Whisper + LLM için)
- Maliyet: ~€50-100/ay (Hetzner dedicated)

### Alternatif: Hibrit Model
- Basit işlemler: Mevcut VPS
- AI inference: Kullanıcının lokali (download model)
- Bu sayede sunucu maliyeti artmaz

---

## Vakıf/Hibe Kaynakları

| Kaynak | Uygunluk | Potansiyel |
|--------|----------|------------|
| NLnet Foundation | Open source | €5K-50K |
| Mozilla MOSS | Child safety | €10K-50K |
| Open Technology Fund | Digital rights | $10K-100K |
| EU Horizon | Child protection | €50K-200K |
| Digital Freedom Fund | Legal tech | €10K-30K |
| Ford Foundation | Social justice | $25K-100K |
| Oak Foundation | Child abuse prevention | $50K-200K |

## Bağış Platformları

- [ ] GitHub Sponsors entegrasyonu
- [ ] Open Collective hesabı
- [ ] Ko-fi / Buy Me a Coffee
- [ ] Crypto bağış adresleri (BTC, ETH)
- [ ] Patreon (opsiyonel)

---

# 📊 İLERLEME TAKİBİ

## Phase 1 Tamamlanma (2025)

| Çeyrek | Hedef | Durum |
|--------|-------|-------|
| Q1 | iOS + Cloud + Recovery | 🟨 65% (iOS + GDrive + WAL + Cloud Wizard) |
| Q2 | Timeline + Graph + Maps | ⬜ 0% |
| Q3 | Speech + Image + AI | ⬜ 0% |
| Q4 | Reports + Multi-device | ⬜ 0% |

## Phase 2 Tamamlanma (2026)

| Çeyrek | Hedef | Backend | Frontend | Durum |
|--------|-------|---------|----------|-------|
| Q1 | Alienation + Risk Predictor | ✅ 100% | ⬜ 0% | 🟨 50% |
| Q2 | Automation + Court Package | ✅ 100% | ⬜ 0% | 🟨 50% |
| Q3 | Multilingual AI + Voice | ✅ 100% | ⬜ 0% | 🟨 50% |
| Q4 | Expert Network + PWA | ✅ 100% | ⬜ 0% | 🟨 50% |

**Phase 2 Backend: 100% TAMAMLANDI (52 Python dosyası, 28,102 satır)**
**Phase 2 Frontend: BEKLİYOR (8 yeni sayfa, 40+ komponent)**

---

# ✅ HIZLI BAŞLANGIÇ CHECKLIST

## Bu Hafta Yapılacaklar (Sprint 0)

- [x] biplist, plistlib test script ✅ 2025-12-13 (ios_backup.py)
- [x] iTunes backup klasör yapısı analizi ✅ 2025-12-13
- [x] İlk WhatsApp.sqlite parsing prototype ✅ 2025-12-13
- [ ] vis-timeline.js demo entegrasyonu
- [ ] Leaflet.js + OSM test
- [ ] Whisper local kurulum testi
- [ ] face_recognition kütüphane testi
- [ ] GitHub Sponsors başvurusu
- [ ] NLnet Foundation hibe başvurusu hazırlığı

---

# 🎯 BAŞARI KRİTERLERİ

## 2025 Sonu

- [ ] iOS backup parsing %100 çalışır
- [ ] Cloud backup (WhatsApp) entegrasyonu tamamlanır
- [ ] Interactive timeline production-ready
- [ ] Contact network graph tamamlanır
- [ ] GPS mapping çalışır
- [ ] Speech-to-text (Whisper local) çalışır
- [ ] Image analysis (local models) çalışır
- [ ] Court-ready PDF reports generate edilir
- [ ] En az 1 vakıf hibesi alınır

## 2026 Sonu

- [ ] Parental alienation detection %80+ doğruluk
- [ ] 10+ dil desteği
- [ ] PWA tüm platformlarda çalışır
- [ ] 100+ aktif gönüllü uzman
- [ ] 1000+ aile yardım almış
- [ ] GitHub'da 500+ star

---

**Versiyon:** 1.0
**Lisans:** MIT
**İletişim:** [GitHub Issues](https://github.com/QaziMuhammedKochgiri/safety/issues)
