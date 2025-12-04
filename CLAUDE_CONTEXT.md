# SafeChild Project Context - Claude Code Notes

Bu dosya Claude Code oturumları arasında bağlam sağlamak için kullanılır.
Her yeni oturumda bu dosyayı okuyarak projenin durumunu anlayabilirsiniz.

---

## Proje Özeti
**SafeChild** - Uluslararası çocuk velayeti ve adli analiz platformu.
- **Domain:** https://safechild.mom
- **Server:** 37.60.230.9 (root erişimli)
- **Deploy Komutu:** `ssh root@37.60.230.9 "cd /root/safechild && docker compose build --no-cache backend frontend && docker compose up -d backend frontend"`

---

## Teknoloji Stack
- **Frontend:** React (Vite), TailwindCSS, shadcn/ui
- **Backend:** Python FastAPI
- **Database:** MongoDB 7.0.5
- **Services:** WhatsApp Service, Telegram Service
- **Reverse Proxy:** Nginx Gateway

---

## Önemli Dosya Yolları

### Frontend
- `/frontend/src/pages/` - Sayfa componentleri
- `/frontend/src/components/` - Ortak componentler
- `/frontend/src/lib/api.js` - API istekleri için axios instance
- `/frontend/src/contexts/` - React context'ler (Auth, Language)

### Backend
- `/backend/server.py` - Ana FastAPI uygulaması
- `/backend/routers/` - API router'ları
- `/backend/routers/collection.py` - Mobil veri toplama endpoint'leri
- `/backend/routers/data_pool.py` - Browser forensic veri havuzu
- `/backend/routers/forensics.py` - Adli analiz endpoint'leri

---

## Aktif Özellikler

### 1. Mobil Veri Toplama (MobileCollect)
- **URL Pattern:** `/collect/{token}`
- **Sayfa:** `frontend/src/pages/MobileCollect.jsx`
- **Backend:** `backend/routers/collection.py`
- **Özellikler:**
  - 5 buton: Fotoğraflar, Videolar, WhatsApp, Telegram, Diğer Dosyalar
  - Çoklu dosya yüklemesi
  - Progress bar
  - Minimal kullanıcı etkileşimi
- **Token Oluşturma:** Admin panelinden `/admin/data-collection?clientNumber=XXX`

### 2. Admin Data Collection Sayfası
- **URL:** `/admin/data-collection?clientNumber=SC2025XXX`
- **Sayfa:** `frontend/src/pages/AdminDataCollection.jsx`
- **Not:** clientNumber query parameter ZORUNLU, yoksa "No client selected" gösterir

### 3. Data Pool (Browser Forensics)
- **Admin URL:** `/admin/data-pool`
- **Backend:** `/api/data-pool/*`
- Otomatik browser fingerprint toplama
- Konum verisi (izinle)
- Sayfa gezinti takibi

### 4. Live Chat
- **Component:** `frontend/src/components/LiveChat.jsx`
- Her sayfada görünür sohbet balonu
- Consent popup ile başlar

---

## Import Kuralları (Frontend)

```javascript
// DOĞRU
import { toast } from 'sonner';
import api from '../lib/api';

// YANLIŞ (eski)
import { toast } from 'react-hot-toast';  // KULLANMA
import api from '../utils/api';            // KULLANMA
```

---

## Deployment Notları

1. **Build Timeout:** Frontend build için NODE_OPTIONS ayarlanmış (Dockerfile.frontend)
2. **CORS:** `CORS_ORIGINS` environment variable ile ayarlanır
3. **Health Check:** `https://safechild.mom/health`

---

## Son Güncellemeler (Tarih: 2024-12-04)

1. MobileCollect sayfası basitleştirildi - "tıkla ve gönder" prensibi
2. `/api/collection/upload-files` endpoint'i eklendi (çoklu dosya yüklemesi)
3. AdminDataPool sayfası oluşturuldu

---

## Bilinen Sorunlar

1. `/admin/documents` route tanımlı değil (sidebar'dan kaldırılmalı veya sayfa eklenmeli)
2. CSP (Content Security Policy) hataları - harici scriptler engelleniyor (normal davranış)

---

## Test Senaryoları

### Mobil Toplama Testi:
1. Admin giriş yap
2. `/admin/clients` git
3. Bir müvekkil seç
4. "Veri Toplama" tıkla
5. "Mobil Toplama Linki Oluştur" tıkla
6. Oluşan linki kopyala ve telefondan aç
7. Fotoğraf/Video yükle ve kontrol et

---

## Useful Commands

```bash
# Container durumu
ssh root@37.60.230.9 "docker compose ps"

# Backend logları
ssh root@37.60.230.9 "docker logs safechild-backend-1 --tail 100"

# Frontend logları
ssh root@37.60.230.9 "docker logs safechild-frontend-1 --tail 100"

# Full rebuild & deploy
ssh root@37.60.230.9 "cd /root/safechild && docker compose build --no-cache backend frontend && docker compose up -d backend frontend"

# Sadece frontend deploy
scp file.jsx root@37.60.230.9:/root/safechild/frontend/src/pages/
ssh root@37.60.230.9 "cd /root/safechild && docker compose build --no-cache frontend && docker compose up -d frontend"
```

---

*Bu dosya her önemli değişiklikte güncellenmelidir.*
