# Phone Recovery Feature Implementation Plan

## Executive Summary

This plan implements comprehensive phone data recovery for SafeChild platform, supporting both USB-connected and wireless/web-based recovery methods for Android and iOS devices. The system will scan both active and deleted files, package everything into encrypted ZIP archives, and auto-delete after 15 days for minimal data liability.

---

## Architecture Overview (UPDATED)

### Two Recovery Scenarios

**Scenario 1: Client HAS a Computer (USB + Web Agent)**
```
Admin creates recovery link → sends to client (email/WhatsApp/chat)
                                      ↓
Client connects phone to THEIR OWN computer via USB
                                      ↓
Client opens link in Chrome/Edge browser
                                      ↓
Web-based Agent runs (using WebUSB API)
                                      ↓
Client enters screen lock passcode
                                      ↓
Agent extracts data from phone via USB
                                      ↓
Data uploaded to SafeChild server
                                      ↓
Admin downloads results
```

**Scenario 2: Client has NO Computer (Mobile-Only / Plugless)**
```
Admin creates recovery link → sends to client (WhatsApp/chat)
                                      ↓
Client taps link DIRECTLY on their phone
                                      ↓
Android: Downloads & installs APK agent
iOS: Installs MDM profile
                                      ↓
Client enters screen lock passcode
                                      ↓
Agent runs on phone, collects data internally
                                      ↓
Data uploaded to SafeChild server
                                      ↓
Admin downloads results
```

### Technical Approach

| Platform | Scenario 1 (With Computer) | Scenario 2 (Mobile Only) |
|----------|---------------------------|-------------------------|
| Android | WebUSB API in browser | APK with Device Admin permissions |
| iOS | WebUSB not supported - iTunes backup | MDM Profile (requires Apple Developer Account) |

### Key Requirements

- Comprehensive Data Recovery: Active + deleted files (up to 30 days)
- 15-Day Auto-Delete: Minimal data retention for liability protection
- Both Android & iOS: Full support for both platforms
- Large File Handling: Support 32-128GB device backups
- Chain of Custody: Full forensic-grade audit trail
- Encryption: AES-256-GCM for all stored data

---

## Phase 1: Database Schema & Models

### New MongoDB Collections

#### phone_recovery_cases

```json
{
  "case_id": "RECOVERY_SC2025001_20251217",
  "client_number": "SC2025001",
  "recovery_method": "usb | wireless",

  "recovery_code": "abc12345",
  "full_token": "uuid",
  "expires_at": "ISODate",

  "device_info": {
    "device_type": "android | ios",
    "device_model": "Samsung Galaxy S21",
    "os_version": "Android 13",
    "serial_number": "RF8R10GBBAF",
    "storage_total": 256000000000,
    "connection_type": "usb | wireless"
  },

  "data_categories": {
    "photos": true,
    "videos": true,
    "messages": true,
    "contacts": true,
    "call_logs": true,
    "deleted_data": true,
    "app_data": true
  },

  "status": "pending | backup_ready | processing | completed | failed | expired",
  "progress_percent": 0,
  "current_step": "Extracting backup...",

  "backup_file": {
    "file_name": "backup.ab",
    "file_size": 4500000000,
    "uploaded_at": "ISODate",
    "checksum_sha256": "...",
    "encrypted_path": "/app/uploads/recovery/...",
    "encryption_metadata": {}
  },

  "processed": {
    "extracted_dir": "/app/recovery_output/...",
    "statistics": {
      "photos": 15234,
      "videos": 423,
      "messages": 45678,
      "contacts": 456,
      "call_logs": 5678,
      "deleted_files": 12345,
      "app_files": 2345,
      "total_size": 42000000000
    },
    "deleted_files_recovered": 12345,
    "processing_time_seconds": 7200
  },

  "results": {
    "zip_path": "/app/recovery_output/RECOVERY_SC2025001.zip",
    "zip_size": 38000000000,
    "checksum_sha256": "...",
    "encrypted": true
  },

  "deletion_schedule": {
    "created_at": "ISODate",
    "auto_delete_at": "ISODate",
    "deleted_at": null
  },

  "chain_of_custody": [
    {
      "timestamp": "ISODate",
      "actor": "Admin: user@example.com",
      "action": "DEVICE_CONNECTED",
      "details": "..."
    }
  ],

  "created_at": "ISODate",
  "updated_at": "ISODate",
  "completed_at": "ISODate"
}
```

#### recovery_processing_jobs

```json
{
  "job_id": "job_uuid",
  "case_id": "RECOVERY_SC2025001_20251217",
  "status": "queued | extracting | carving | packaging | completed | failed",
  "progress_percent": 0,
  "current_step": "Recovering deleted messages...",
  "started_at": "ISODate",
  "estimated_completion": "ISODate",
  "completed_at": "ISODate",
  "errors": []
}
```

---

## Phase 2: Backend Implementation

### 2.1 System Dependencies (Docker & Python)

#### Dockerfile Updates

```dockerfile
# USB Support
RUN apt-get update && apt-get install -y \
    libusb-1.0-0-dev libusb-dev udev \
    android-tools-adb \
    libimobiledevice-dev libimobiledevice-tools \
    libplist-dev libplist-utils \
    ideviceinstaller ifuse \
    build-essential libtsk-dev

# USB device access
RUN echo 'ACTION=="add", SUBSYSTEM=="usb", MODE="0666"' > /etc/udev/rules.d/99-usb.rules
```

#### docker-compose.yml Updates

```yaml
backend:
  devices:
    - /dev/bus/usb:/dev/bus/usb
  cap_add:
    - SYS_ADMIN
  volumes:
    - phone-recovery:/tmp/phone_recovery
```

#### requirements.txt Additions

```
pyusb>=1.2.1
ppadb>=0.11.0
pymobiledevice>=1.0
progressbar2>=4.2.0
```

### 2.2 Core Modules to Create

1. **backend/forensics/usb_device_manager.py** - USB device detection, authorization
2. **backend/forensics/android_extractor.py** - Android device extraction via ADB
3. **backend/forensics/ios_extractor.py** - iOS device extraction via libimobiledevice
4. **backend/forensics/recovery/backup_extractor.py** - Generic backup format parsing
5. **backend/services/recovery_processor.py** - Main processing pipeline orchestrator
6. **backend/routers/usb_recovery.py** - USB recovery API endpoints
7. **backend/routers/wireless_recovery.py** - Wireless recovery API endpoints

### 2.3 API Endpoints

#### USB Recovery (Admin-only)
```
GET    /usb-recovery/devices              # List connected USB devices
POST   /usb-recovery/devices/{id}/auth    # Authorize device
GET    /usb-recovery/devices/{id}/info    # Get device details
POST   /usb-recovery/start                # Start USB extraction
GET    /usb-recovery/cases/{id}/status    # Get live progress
GET    /usb-recovery/cases/{id}/download  # Download results ZIP
```

#### Wireless Recovery
```
POST   /recovery/create-link              # Create recovery link for client
GET    /recovery/list                     # List all recovery requests
GET    /recovery/validate/{code}          # Validate recovery code
POST   /recovery/upload-backup            # Upload backup file (chunked)
GET    /recovery/status/{code}            # Get processing status
GET    /recovery/download/{code}          # Download results (admin only)
```

---

## Phase 3: Frontend Implementation

### 3.1 Admin UI - AdminPhoneRecovery.jsx

**Section 1:** Create Recovery Link (Wireless Recovery)
**Section 2:** USB Device Panel (USB Recovery)
**Section 3:** Active Recovery Jobs
**Section 4:** Completed Recoveries

### 3.2 Client UI - PhoneRecoveryClient.jsx (NEW)

5-Step Workflow:
1. Welcome & Validation
2. Instructions & Download (APK or iOS guide)
3. Backup Upload (chunked, 100MB chunks)
4. Processing Status (poll every 5 seconds)
5. Completion & Statistics

---

## Phase 4: Android Agent Enhancement

### Recovery Module Files
- `RecoveryTokenManager.kt` - Token parsing and validation
- `BackupCreationManager.kt` - Backup creation logic
- `BackupUploadService.kt` - Chunked file upload

### APK Distribution
- Deep Link: `safechild://recover/{code}`
- Web Link: `https://safechild.mom/recover/{code}`

---

## Phase 5: Data Processing Details

### 5.1 Android Backup Extraction
- Parse .ab (ADB backup) format
- zlib decompression + TAR extraction
- Extract app databases (WhatsApp, Telegram, SMS)

### 5.2 iOS Backup Extraction
- Parse Manifest.db SQLite database
- Map file hashes to domain names
- Extract app containers

### 5.3 Deleted File Recovery
- File carving using magic byte signatures
- SQLite WAL recovery for deleted messages

---

## Phase 6: Auto-Deletion Implementation

### MongoDB TTL Index
```python
await db.phone_recovery_cases.create_index(
    [("deletion_schedule.auto_delete_at", 1)],
    expireAfterSeconds=0,
    name="auto_delete_index"
)
```

### Cleanup Scheduler
- Daily at 2 AM
- Secure file deletion
- Chain of custody logging

---

## Critical Files Summary

### Backend (New Files)
1. `backend/forensics/usb_device_manager.py`
2. `backend/forensics/android_extractor.py`
3. `backend/forensics/ios_extractor.py`
4. `backend/forensics/recovery/backup_extractor.py`
5. `backend/services/recovery_processor.py`
6. `backend/routers/usb_recovery.py`
7. `backend/routers/wireless_recovery.py`
8. `backend/services/cleanup_scheduler.py`

### Backend (Modified Files)
9. `backend/models.py`
10. `backend/server.py`
11. `backend/forensics/recovery/file_carving.py`
12. `Dockerfile`
13. `docker-compose.yml`

### Frontend (New Files)
14. `frontend/src/pages/PhoneRecoveryClient.jsx`

### Frontend (Modified Files)
15. `frontend/src/pages/AdminPhoneRecovery.jsx`
16. `frontend/src/App.js`
17. `frontend/src/lib/api.js`

### Android Agent (Modified)
18. `RecoveryTokenManager.kt`
19. `BackupCreationManager.kt`
20. `BackupUploadService.kt`

---

## Security Considerations

1. **Authentication & Authorization** - Admin JWT + Token-based access
2. **Data Encryption** - AES-256-GCM at rest
3. **Chain of Custody** - Full audit trail
4. **Auto-Deletion** - 15-day retention via TTL index
5. **Device Authorization** - ADB/iOS trust verification

---

## Implementation Checklist

### Phase 1: Foundation - COMPLETED
- [x] Update Dockerfile with USB and device dependencies
- [x] Update docker-compose.yml with USB passthrough
- [x] Add new dependencies to requirements.txt
- [x] Create MongoDB collections and indexes
- [x] Create PhoneRecoveryCase model in models.py
- [x] Create RecoveryProcessingJob model

### Phase 2: USB Recovery Backend - COMPLETED
- [x] Create usb_device_manager.py
- [x] Create android_extractor.py
- [x] Create ios_extractor.py
- [x] Create usb_recovery.py router
- [x] Register router in server.py
- [ ] Test USB device detection on VPS (requires deployment)

### Phase 3: Wireless Recovery Backend - COMPLETED
- [x] Create wireless_recovery.py router
- [x] Implement recovery link creation
- [x] Implement chunked file upload
- [x] Implement token validation
- [x] Add WebUSB agent endpoints (device-connected, start-extraction, upload-data, finalize)
- [x] Add mobile agent endpoints (start-agent, ios-profile, apk-download-link)

### Phase 4: Processing Pipeline - COMPLETED
- [x] Enhanced file_carving.py with async wrapper
- [x] Integrated recovery processing in routers
- [x] Implemented results packaging (ZIP)

### Phase 5: Frontend - COMPLETED
- [x] Create PhoneRecoveryClient.jsx (client UI with 2 scenarios)
- [x] Create WebUSBRecoveryAgent.jsx component
- [x] AdminPhoneRecovery.jsx (existing placeholder)
- [x] Add routes to App.js
- [x] Turkish language UI

### Phase 6: Auto-Deletion - COMPLETED
- [x] Create cleanup_scheduler.py
- [x] Setup MongoDB TTL index in server.py
- [ ] Test auto-deletion (requires deployment)

### Phase 7: Android APK Agent - DOCUMENTED
- [x] Create architecture documentation (docs/android-recovery-agent.md)
- [ ] Implement RecoveryTokenManager.kt
- [ ] Implement DataExtractionManager.kt
- [ ] Implement UploadManager.kt
- [ ] Implement extractors (Photo, Video, Contact, WhatsApp, etc.)
- [ ] Build and sign APK

### Phase 8: iOS MDM Profile - PLACEHOLDER
- [x] Create MDM profile generation endpoint
- [ ] Obtain Apple Developer Enterprise account
- [ ] Implement proper MDM profile signing
- [ ] Implement iOS data extraction via MDM

### Phase 9: Testing & Deployment - PENDING
- [ ] End-to-end USB recovery test (WebUSB)
- [ ] End-to-end wireless recovery test (APK/MDM)
- [ ] Large file upload test (10GB+)
- [ ] Security audit
- [ ] Deploy to production
