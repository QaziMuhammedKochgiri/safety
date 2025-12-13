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
- [ ] Safari Web App manifest
- [ ] Photo library access (consent-based)
- [ ] Contact export
- [ ] Screen recording guidance

#### Backend Integration
- [ ] /api/forensics/analyze-ios endpoint
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
- [ ] crypt14/crypt15 key extraction

#### iCloud Integration (Gelecek - Opsiyonel)
- [ ] pyicloud authentication
- [ ] 2FA handling
- [ ] Backup listing
- [ ] Selective download

#### Frontend
- [ ] Cloud connection wizard
- [ ] Backup selection UI
- [ ] Download progress

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Google Cloud API | Ücretsiz tier | Günlük limit var |
| pyicloud | Ücretsiz | Open source |
| wa-crypt-tools | Ücretsiz | Open source |

---

### Sprint 5-6: Advanced Data Recovery (Hafta 9-12)

#### SQLite WAL Analysis
- [ ] Write-Ahead Log parsing
- [ ] Deleted row recovery
- [ ] Timestamp reconstruction
- [ ] Confidence scoring

#### File Carving
- [ ] JPEG/PNG header scanning
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
- [ ] vis-timeline.js integration (MIT License)
- [ ] Zoom levels (year/month/day/hour)
- [ ] Event clustering
- [ ] Color coding by source
- [ ] Click-to-detail
- [ ] Filter panel

#### Export
- [ ] Timeline as image (PNG/SVG)
- [ ] Timeline as PDF
- [ ] Data as CSV

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| vis-timeline.js | Ücretsiz | MIT License |
| html2canvas | Ücretsiz | Export için |

---

### Sprint 9-10: Contact Network Graph (Hafta 17-20)

#### Graph Engine
- [ ] Node extraction (all contacts)
- [ ] Edge calculation (message count)
- [ ] Cluster detection (K-means)
- [ ] Centrality analysis

#### UI Components
- [ ] Cytoscape.js integration (MIT License)
- [ ] Force-directed layout
- [ ] Node sizing (by frequency)
- [ ] Edge coloring (by platform)
- [ ] Zoom/pan controls
- [ ] Node selection + details

#### Analytics
- [ ] Communication frequency heatmap
- [ ] Relationship strength scoring
- [ ] Suspicious pattern detection

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Cytoscape.js | Ücretsiz | MIT License |
| scikit-learn | Ücretsiz | K-means için |

---

### Sprint 11-12: GPS & Location Mapping (Hafta 21-24)

#### Data Extraction
- [ ] EXIF GPS from all photos
- [ ] Google Location History
- [ ] iOS Significant Locations
- [ ] Check-in data (social media)

#### Map Visualization
- [ ] Leaflet.js integration (BSD License)
- [ ] OpenStreetMap tiles (ücretsiz)
- [ ] Heatmap layer
- [ ] Timeline slider (animate movement)
- [ ] Cluster markers
- [ ] Geofence alerts

#### Analysis
- [ ] Frequent locations
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
- [ ] WhatsApp voice note extraction (.opus)
- [ ] Telegram voice extraction
- [ ] Video audio track extraction
- [ ] Format conversion (ffmpeg - ücretsiz)

#### Transcription Engine
- [ ] OpenAI Whisper LOCAL (ücretsiz, self-hosted)
- [ ] Language detection (auto)
- [ ] Timestamp alignment
- [ ] Speaker diarization (optional)

#### Search & Analysis
- [ ] Full-text search on transcripts
- [ ] Keyword highlighting
- [ ] Sentiment analysis (local model)
- [ ] AI risk assessment on audio

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| Whisper (local) | Ücretsiz | Self-hosted, GPU önerilir |
| ffmpeg | Ücretsiz | Open source |
| pyannote | Ücretsiz | Speaker diarization |

---

### Sprint 15-16: Image Analysis (Hafta 29-32)

#### Face Detection
- [ ] face_recognition library (dlib tabanlı, ücretsiz)
- [ ] Face extraction & grouping
- [ ] Age estimation (local model)
- [ ] Same-person matching

#### Image Categorization
- [ ] Scene classification (local CLIP model)
- [ ] Object detection (YOLO - ücretsiz)
- [ ] Text extraction (Tesseract OCR - ücretsiz)
- [ ] Duplicate finder (perceptual hash)

#### Safety Features
- [ ] PhotoDNA-benzeri hash matching (open source impl)
- [ ] Explicit content detection (local NSFW model)
- [ ] Auto-blur sensitive content
- [ ] Alert workflow

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
- [ ] Ollama kurulumu (ücretsiz)
- [ ] Llama 2 / Mistral model (ücretsiz)
- [ ] Local inference setup
- [ ] Fallback to Claude API (bağış varsa)

#### Enhanced Risk Detection
- [ ] Multi-language support (local models)
- [ ] Cultural context awareness
- [ ] Sarcasm/irony detection
- [ ] Intent classification

#### Parental Alienation Detection
- [ ] Manipulation tactics taxonomy
- [ ] Evidence scoring (1-10)
- [ ] Pattern timeline
- [ ] Expert witness report format

#### Court-Ready Summaries
- [ ] Executive summary generator
- [ ] Evidence highlight extraction
- [ ] Counter-argument anticipation
- [ ] Legal citation suggestions

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
- [ ] WeasyPrint PDF generation (ücretsiz)
- [ ] Professional templates
- [ ] Digital signature (cryptography lib)
- [ ] Hash verification page
- [ ] Chain of custody section
- [ ] Multi-language (DE/EN/TR)

#### Legal Compliance
- [ ] GDPR compliance checklist
- [ ] Expert witness statement template
- [ ] Evidence authentication page
- [ ] Court filing format (Germany/Turkey)

#### Export Options
- [ ] PDF (primary)
- [ ] DOCX (python-docx - ücretsiz)
- [ ] E001 format (EU standard)
- [ ] Cellebrite XML (interoperability)

**Kullanılan Araçlar:**
| Araç | Maliyet | Not |
|------|---------|-----|
| WeasyPrint | Ücretsiz | PDF generation |
| python-docx | Ücretsiz | DOCX export |
| cryptography | Ücretsiz | Digital signatures |

---

### Sprint 21-22: Multi-Device Comparison (Hafta 41-44)

#### Device Pairing
- [ ] Parent-child device matching
- [ ] Timeline synchronization
- [ ] Contact overlap detection
- [ ] Message thread matching

#### Discrepancy Detection
- [ ] Deleted message detection (A has, B doesn't)
- [ ] Edit history comparison
- [ ] Time gap analysis
- [ ] Screenshot vs original

#### Visualization
- [ ] Side-by-side timeline
- [ ] Diff view for conversations
- [ ] Conflict highlighting

---

### Sprint 23-24: Dashboard Enhancement (Hafta 45-48)

#### Dashboard Redesign
- [ ] KPI cards (cases, alerts, pending)
- [ ] Real-time activity feed
- [ ] Quick action buttons
- [ ] Notification center

#### Case Management
- [ ] Case assignment workflow
- [ ] Status tracking (Kanban)
- [ ] Due date alerts
- [ ] Team collaboration

#### Analytics
- [ ] Case completion metrics
- [ ] Risk distribution charts
- [ ] Client satisfaction tracking

---

# 📈 PHASE 2: RAKİPLERDEN ÖNDE (13-24 Ay)

## 🗓️ Q1 2026: CHILD CUSTODY SPECIALIZATION

### Parental Alienation Expert System
- [ ] 50+ manipulation tactic tanımı
- [ ] Literature-backed scoring
- [ ] Case law references database
- [ ] Expert psychologist validation (gönüllü)
- [ ] Pattern matching (NLP)
- [ ] Severity scoring (1-10)
- [ ] Evidence strength indicator
- [ ] Counter-example detection
- [ ] Alienation timeline view
- [ ] Tactic categorization
- [ ] Quote extraction with context
- [ ] Expert witness format

### Child Safety Risk Predictor
- [ ] Historical case data (anonymized)
- [ ] Risk factor weighting
- [ ] Outcome correlation
- [ ] Model validation
- [ ] Escalation pattern detection
- [ ] Warning sign timeline
- [ ] Intervention recommendation
- [ ] Risk trajectory graph
- [ ] Alert thresholds
- [ ] Explainable AI requirements

---

## 🗓️ Q2 2026: AUTOMATION & EFFICIENCY

### Automated Evidence Collection Agent
- [ ] Background sync (daily/weekly)
- [ ] Incremental backup (only new data)
- [ ] Battery-efficient mode
- [ ] Stealth mode option
- [ ] Automatic WhatsApp backup detection
- [ ] Change detection algorithm
- [ ] Version history
- [ ] New high-risk message → instant alert
- [ ] Pattern change detection
- [ ] Weekly digest email (self-hosted SMTP)

### One-Click Court Package
- [ ] Evidence selection wizard
- [ ] Relevance scoring
- [ ] Redundancy removal
- [ ] Page limit compliance
- [ ] Cover page with index
- [ ] Numbered exhibits
- [ ] Chain of custody certificate
- [ ] German court format
- [ ] Turkish court format
- [ ] EU standard (E001)

---

## 🗓️ Q3 2026: ADVANCED AI

### Multilingual AI with Cultural Context
- [ ] Kurdish (Kurmanji + Sorani) support
- [ ] Arabic dialects (Iraqi, Syrian, Gulf)
- [ ] Turkish slang/abbreviations
- [ ] German legal terminology
- [ ] Mixed-language conversations
- [ ] Honor culture indicators
- [ ] Religious reference detection
- [ ] Regional idiom database
- [ ] Family dynamics patterns
- [ ] Diaspora-specific patterns
- [ ] Immigration threat detection
- [ ] Child abduction risk assessment
- [ ] UI in 10+ languages

### Voice Biometrics (Local Processing)
- [ ] Voice print extraction (pyAudioAnalysis)
- [ ] Multi-speaker separation
- [ ] Unknown speaker flagging
- [ ] Confidence scoring
- [ ] Stress detection
- [ ] Fear/anxiety indicators
- [ ] Aggression patterns
- [ ] Child voice age estimation
- [ ] Distress indicators
- [ ] Scripted vs spontaneous detection
- [ ] Edit detection
- [ ] Metadata analysis

---

## 🗓️ Q4 2026: ECOSYSTEM & SCALE

### Community Expert Network (Volunteer-Based)
- [ ] Expert registration (gönüllü)
- [ ] Credential verification
- [ ] Specialty matching
- [ ] Availability calendar
- [ ] Child psychologists
- [ ] Digital forensics experts
- [ ] Social workers
- [ ] Translators/interpreters
- [ ] Case sharing (secure)
- [ ] Report co-authoring
- [ ] Video consultation (Jitsi - ücretsiz)

### Mobile-First PWA
- [ ] Offline-first architecture
- [ ] Push notifications (web-push - ücretsiz)
- [ ] App-like experience
- [ ] Install prompts
- [ ] Touch-optimized UI
- [ ] Swipe navigation
- [ ] Quick actions
- [ ] Biometric login
- [ ] Desktop dashboard
- [ ] Tablet timeline view
- [ ] Phone quick view
- [ ] Accessibility (WCAG 2.1)
- [ ] <3s load time
- [ ] Image optimization
- [ ] Code splitting

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
| Q1 | iOS + Cloud + Recovery | 🟨 35% (iOS parser + GDrive tamamlandı) |
| Q2 | Timeline + Graph + Maps | ⬜ 0% |
| Q3 | Speech + Image + AI | ⬜ 0% |
| Q4 | Reports + Multi-device | ⬜ 0% |

## Phase 2 Tamamlanma (2026)

| Çeyrek | Hedef | Durum |
|--------|-------|-------|
| Q1 | Alienation + Risk Predictor | ⬜ 0% |
| Q2 | Automation + Court Package | ⬜ 0% |
| Q3 | Multilingual AI + Voice | ⬜ 0% |
| Q4 | Expert Network + PWA | ⬜ 0% |

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
