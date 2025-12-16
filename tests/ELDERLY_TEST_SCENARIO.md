# SafeChild Elderly User Test Scenario

## Test Amaci
Bu test senaryosu, SafeChild platformunun en zor kullanici grubu olan yasli (65-82 yas) kullanicilar tarafindan basariyla kullanilip kullanilamadigini test eder. Bu testi gecen sistem, tum kullanici gruplarini basariyla destekleyebilir.

## Test Tarihi
2025-12-13

## 20 Elderly Test Kullanicisi

| # | ID | Isim | Yas | Cihaz | Android | Dil | Teknik Seviye | Ozel Durum |
|---|-----|------|-----|-------|---------|-----|---------------|------------|
| 1 | ELD-001 | Helga Muller | 72 | Samsung A14 | 13 | DE | Cok Dusuk | Gozluk, buyuk font |
| 2 | ELD-002 | Fatma Teyze | 68 | Xiaomi Redmi 12 | 12 | TR | Dusuk | Okuma-yazma zayif |
| 3 | ELD-003 | Hans Becker | 75 | Samsung A34 | 13 | DE | Orta | Isitme cihazi |
| 4 | ELD-004 | Hatice Nine | 70 | Oppo A78 | 13 | TR/KU | Cok Dusuk | Sadece Kurtce konusuyor |
| 5 | ELD-005 | Werner Schmidt | 78 | Nokia G22 | 12 | DE | Cok Dusuk | Parkinson (titreme) |
| 6 | ELD-006 | Emine Hanim | 65 | Samsung A24 | 13 | TR | Orta | WhatsApp biliyor |
| 7 | ELD-007 | Gerhard Weber | 71 | Motorola G54 | 13 | DE | Dusuk | Buyuk parmak, kucuk buton |
| 8 | ELD-008 | Zehra Teyze | 74 | Xiaomi Redmi Note 12 | 13 | TR | Cok Dusuk | Telefon korkusu |
| 9 | ELD-009 | Ingrid Fischer | 69 | Samsung A54 | 14 | DE | Orta | Teknoloji merakli |
| 10 | ELD-010 | Mehmet Dede | 76 | Huawei Nova Y61 | 12 | TR | Dusuk | Sadece arama yapar |
| 11 | ELD-011 | Ursula Braun | 73 | Google Pixel 7a | 14 | DE | Orta | Torun yardim ediyor |
| 12 | ELD-012 | Ayse Nine | 80 | Samsung A04 | 12 | TR | Cok Dusuk | En yasli grupta |
| 13 | ELD-013 | Dieter Hoffmann | 67 | OnePlus Nord CE 3 | 13 | DE | Orta-Iyi | Emekli muhendis |
| 14 | ELD-014 | Hacer Teyze | 71 | Oppo A57 | 12 | TR | Dusuk | Sifre hatirlamiyor |
| 15 | ELD-015 | Monika Wagner | 66 | Samsung A14 | 13 | DE | Orta | Avukat yonlendirmesi |
| 16 | ELD-016 | Ibrahim Amca | 77 | Xiaomi Poco M5 | 12 | TR/AR | Cok Dusuk | Arapca-Turkce karisik |
| 17 | ELD-017 | Hildegard Schneider | 79 | Nokia G42 | 13 | DE | Cok Dusuk | Artrit (eklem agrisi) |
| 18 | ELD-018 | Gulsum Teyze | 69 | Realme C55 | 13 | TR | Dusuk | Kizi yardim ediyor |
| 19 | ELD-019 | Klaus Richter | 70 | Samsung A34 | 13 | DE | Orta | Eski IT calisan |
| 20 | ELD-020 | Sevim Nine | 82 | Samsung A04e | 12 | TR | Cok Dusuk | EN ZOR CASE |

## Teknik Seviye Dagilimi
- **Cok Dusuk (8 kisi - 40%)**: Telefonu zar zor kullanan, yardima ihtiyac duyan
- **Dusuk (6 kisi - 30%)**: Sadece temel islemleri (arama, mesaj) yapabilen
- **Orta (5 kisi - 25%)**: WhatsApp, foto cekme gibi uygulamalari kullanabilen
- **Orta-Iyi (1 kisi - 5%)**: Teknik gecmisi olan, sorunsuz kullanan

## Dil Dagilimi
- **Almanca (DE)**: 10 kullanici
- **Turkce (TR)**: 7 kullanici
- **Cok Dilli (TR/KU, TR/AR)**: 2 kullanici
- **Sadece Kurtce**: 1 kullanici

## Cihaz Dagilimi
- **Samsung**: 8 cihaz (A04, A04e, A14x2, A24, A34x2, A54)
- **Xiaomi**: 3 cihaz (Redmi 12, Redmi Note 12, Poco M5)
- **Nokia**: 2 cihaz (G22, G42)
- **Oppo**: 2 cihaz (A57, A78)
- **Diger**: 5 cihaz (Motorola, Huawei, Google, OnePlus, Realme)

## Test Akisi

### Adim 1: Client Olusturma (Admin)
```
Admin Panel → Clients → New Client
- Ad Soyad gir
- Telefon numarasi gir
- Dil sec (DE/TR/KU/AR)
- Dava tipi sec
- "Create & Send Link" tikla
```

### Adim 2: Magic Link Gonderimi (Otomatik)
```
SMS/WhatsApp ile link gonderilir:
TR: "SafeChild: Delil toplama icin tiklayin: https://safechild.mom/c/XXXXXX"
DE: "SafeChild: Klicken Sie hier fur die Beweissammlung: https://safechild.mom/c/XXXXXX"
```

### Adim 3: Link Tiklama (Elderly User)
```
Kullanici mesaji acar → Linke tiklar → Browser acilir
Landing page yuklenr:
- Buyuk "INDIR" butonu (mavi, ekranin %80'i)
- Kullanicinin dilinde basit talimatlar
- Resimli adim adim rehber
```

### Adim 4: APK Indirme (Elderly User)
```
"INDIR" butonuna tiklar → APK indirilir
Dosya adi: safechild-agent-XXXXXX.apk (token embedded)
```

### Adim 5: Kurulum Izni (Elderly User)
```
Android "Bilinmeyen kaynaklardan kurulum" uyarisi:
- "Ayarlar" tikla
- "Bu kaynaga izin ver" toggle'ini ac
- Geri don ve "Kur" tikla
```

### Adim 6: APK Kurulum (Elderly User)
```
"Kur" butonuna tiklar → Uygulama kurulur
"Ac" butonuna tiklar → Uygulama baslar
```

### Adim 7: Otomatik Veri Toplama (Android Agent)
```
Uygulama acildiginda OTOMATIK olarak:
1. Token'i okur (embedded asset)
2. Izinleri ister (SMS, Rehber, Depolama)
3. Veri toplar:
   - SMS mesajlari
   - WhatsApp chatleri
   - Rehber
   - Arama gecmisi
   - Medya dosyalari (foto/video)
4. Progress bar gosterir
5. Otomatik upload baslar
```

### Adim 8: Upload ve Tamamlama (Android Agent)
```
Veriler sunucuya yuklenir:
- Chunked upload (buyuk dosyalar icin)
- Retry mekanizmasi (baglanti koparsa)
- Basari mesaji: "Tamamlandi! Bu uygulamayi silebilirsiniz."
```

### Adim 9: Veri Inceleme (Admin)
```
Admin Panel → Clients → [Client Adi] → Forensics
- SMS listesi
- WhatsApp mesajlari
- Rehber
- Arama gecmisi
- Medya galeri
- AI Analiz sonuclari
```

## Basari Kriterleri

| Metrik | Hedef | Minimum | Aciklama |
|--------|-------|---------|----------|
| Link Tiklama | %100 | %95 | Tum kullanicilar linke tiklamali |
| APK Indirme | %95 | %90 | 19/20 kullanici indirmeli |
| Izin Verme | %90 | %85 | 18/20 kullanici izin vermeli |
| APK Kurulum | %90 | %85 | 18/20 kullanici kurmali |
| Veri Toplama | %100 | %95 | Kuranlar icin tam veri toplanmali |
| Upload Basarisi | %100 | %95 | Toplanan veri tamamen yuklenmeli |
| **Toplam E2E** | **%85** | **%80** | **17/20 tam basarili olmali** |

## Kritik Test Caseleri (Bunlar Gecmeli!)

### 1. Sevim Nine (ELD-020) - EN ZOR
- 82 yasinda, en yasli kullanici
- Samsung A04e - en dusuk spec cihaz
- Turkce, Cok Dusuk teknik seviye
- **Gecerse**: Sistem yasli-dostu

### 2. Ayse Nine (ELD-012) - ZOR
- 80 yasinda
- Samsung A04 - dusuk spec
- Turkce, Cok Dusuk teknik seviye
- **Gecerse**: Ekstrem yaslilar destekleniyor

### 3. Werner Schmidt (ELD-005) - MOTOR BECERI
- 78 yasinda, Parkinson hastasi
- Nokia G22
- Almanca, Cok Dusuk
- **Gecerse**: Motor engelli kullanicilar destekleniyor

### 4. Hatice Nine (ELD-004) - DIL BARIYERI
- 70 yasinda, sadece Kurtce konusuyor
- Oppo A78
- TR/KU, Cok Dusuk
- **Gecerse**: Cok dilli destek calisiyor

### 5. Hildegard Schneider (ELD-017) - FIZIKSEL ENGEL
- 79 yasinda, Artrit (eklem agrisi)
- Nokia G42
- Almanca, Cok Dusuk
- **Gecerse**: Fiziksel engelli kullanicilar destekleniyor

## Mock Data Gereksinimleri

Her test kullanicisi icin:
- 50-200 SMS mesaji
- 20-100 WhatsApp mesaji (text + media)
- 30-80 rehber kaydi
- 20-50 arama gecmisi
- 10-30 foto/video

### Icerik Turleri
1. **Normal aile iletisimi** (60%)
2. **Supehli mesajlar** (20%)
   - Tehdit iceren
   - Manipulasyon
   - Cocugu kacirma planlari
3. **Avukat/mahkeme yazismalari** (10%)
4. **Diger** (10%)

## Test Calistirilmasi

```bash
# 1. Test client'larini olustur
python tests/create_test_clients.py

# 2. Mock data olustur
python tests/generate_mock_data.py

# 3. Magic linkleri uret
python tests/generate_magic_links.py

# 4. E2E testi calistir (simule)
python tests/run_e2e_simulation.py

# 5. Sonuclari raporla
python tests/generate_test_report.py
```

## Beklenen Ciktilar

### Test Raporu
```
SafeChild Elderly User Test Report
===================================
Test Date: 2025-12-13
Total Users: 20
Successful E2E: 17/20 (85%)

Detailed Results:
-----------------
ELD-001 Helga Muller: ✅ PASS (all steps)
ELD-002 Fatma Teyze: ✅ PASS (all steps)
...
ELD-020 Sevim Nine: ✅ PASS (all steps) ← CRITICAL SUCCESS!

Failed Cases:
-------------
None (ideal) or detailed failure analysis

Recommendations:
----------------
- [Any UX improvements needed]
```

## Test Sonrasi Aksiyon

### Basarili (%85+)
- Production deployment onaylanir
- Marketing materyalleri guncellenir: "Yasli-dostu tasarim"

### Kismi Basari (%70-84%)
- UX iyilestirmeleri yapilir
- Buyuk butonlar, daha basit dil
- Test tekrarlanir

### Basarisiz (<%70)
- Major UX revizyonu gerekli
- Elderly focus group olusturulur
- 2 hafta icerisinde re-test

---

**Test Hazirlayan**: Claude AI Assistant
**Onaylayan**: [Admin]
**Son Guncelleme**: 2025-12-13
