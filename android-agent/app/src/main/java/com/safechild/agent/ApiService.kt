package com.safechild.agent

import android.content.Context
import com.google.gson.Gson
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.TimeUnit
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * API Service for communicating with SafeChild backend
 */
class ApiService(private val context: Context) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(300, TimeUnit.SECONDS) // Long timeout for uploads
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private val baseUrl = BuildConfig.SERVER_URL

    /**
     * Validate collection token with server
     */
    fun validateCollectionToken(token: String): TokenValidationResult {
        val request = Request.Builder()
            .url("$baseUrl/collection/validate/$token")
            .get()
            .build()

        return try {
            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val body = response.body?.string()
                gson.fromJson(body, TokenValidationResult::class.java)
            } else {
                TokenValidationResult(false, null, null, "Invalid token")
            }
        } catch (e: Exception) {
            TokenValidationResult(false, null, null, e.message)
        }
    }

    /**
     * Upload collected data to server
     */
    fun uploadCollectedData(
        token: String,
        clientNumber: String,
        data: CollectedData
    ): UploadResult {
        try {
            // Create a temporary directory for the upload package
            val tempDir = File(context.cacheDir, "upload_${System.currentTimeMillis()}")
            tempDir.mkdirs()

            // Save data as JSON files
            saveJsonFile(tempDir, "sms.json", data.smsMessages)
            saveJsonFile(tempDir, "contacts.json", data.contacts)
            saveJsonFile(tempDir, "call_log.json", data.callLogs)
            saveJsonFile(tempDir, "whatsapp_info.json", data.whatsappData)
            saveJsonFile(tempDir, "media_list.json", data.mediaFiles)

            // Create metadata
            val metadata = CollectionMetadata(
                clientNumber = clientNumber,
                token = token,
                timestamp = System.currentTimeMillis(),
                deviceInfo = getDeviceInfo(),
                collectedTypes = listOf(
                    if (data.smsMessages.isNotEmpty()) "sms" else null,
                    if (data.contacts.isNotEmpty()) "contacts" else null,
                    if (data.callLogs.isNotEmpty()) "call_log" else null,
                    if (data.whatsappData != null) "whatsapp" else null,
                    if (data.mediaFiles.isNotEmpty()) "media" else null
                ).filterNotNull(),
                statistics = CollectionStats(
                    smsCount = data.smsMessages.size,
                    contactsCount = data.contacts.size,
                    callLogCount = data.callLogs.size,
                    mediaCount = data.mediaFiles.size,
                    whatsappBackupFound = data.whatsappData?.backupFound ?: false
                )
            )
            saveJsonFile(tempDir, "metadata.json", metadata)

            // Create ZIP archive
            val zipFile = File(context.cacheDir, "collection_$clientNumber.zip")
            createZipArchive(tempDir, zipFile)

            // Upload ZIP file
            val requestBody = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("token", token)
                .addFormDataPart("clientNumber", clientNumber)
                .addFormDataPart(
                    "file",
                    zipFile.name,
                    zipFile.asRequestBody("application/zip".toMediaType())
                )
                .build()

            val request = Request.Builder()
                .url("$baseUrl/collection/upload")
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()

            // Cleanup temp files
            tempDir.deleteRecursively()
            zipFile.delete()

            return if (response.isSuccessful) {
                UploadResult(true, null)
            } else {
                UploadResult(false, "Server error: ${response.code}")
            }

        } catch (e: Exception) {
            e.printStackTrace()
            return UploadResult(false, e.message)
        }
    }

    /**
     * Upload individual media files (for large files)
     */
    fun uploadMediaFile(token: String, filePath: String): Boolean {
        val file = File(filePath)
        if (!file.exists() || !file.canRead()) return false

        try {
            val requestBody = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("token", token)
                .addFormDataPart(
                    "media",
                    file.name,
                    file.asRequestBody(getMimeType(file).toMediaType())
                )
                .build()

            val request = Request.Builder()
                .url("$baseUrl/collection/upload-media")
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()
            return response.isSuccessful
        } catch (e: Exception) {
            e.printStackTrace()
            return false
        }
    }

    private fun saveJsonFile(dir: File, filename: String, data: Any?) {
        if (data == null) return
        val file = File(dir, filename)
        file.writeText(gson.toJson(data))
    }

    private fun createZipArchive(sourceDir: File, zipFile: File) {
        ZipOutputStream(FileOutputStream(zipFile)).use { zos ->
            sourceDir.listFiles()?.forEach { file ->
                if (file.isFile) {
                    val entry = ZipEntry(file.name)
                    zos.putNextEntry(entry)
                    file.inputStream().use { it.copyTo(zos) }
                    zos.closeEntry()
                }
            }
        }
    }

    private fun getDeviceInfo(): DeviceInfo {
        return DeviceInfo(
            manufacturer = android.os.Build.MANUFACTURER,
            model = android.os.Build.MODEL,
            androidVersion = android.os.Build.VERSION.RELEASE,
            sdkVersion = android.os.Build.VERSION.SDK_INT
        )
    }

    private fun getMimeType(file: File): String {
        return when (file.extension.lowercase()) {
            "jpg", "jpeg" -> "image/jpeg"
            "png" -> "image/png"
            "gif" -> "image/gif"
            "mp4" -> "video/mp4"
            "3gp" -> "video/3gpp"
            "pdf" -> "application/pdf"
            else -> "application/octet-stream"
        }
    }
}

// Data classes for API communication
data class TokenValidationResult(
    val isValid: Boolean,
    val clientNumber: String?,
    val clientName: String?,
    val error: String? = null
)

data class UploadResult(
    val success: Boolean,
    val error: String?
)

data class CollectionMetadata(
    val clientNumber: String,
    val token: String,
    val timestamp: Long,
    val deviceInfo: DeviceInfo,
    val collectedTypes: List<String>,
    val statistics: CollectionStats
)

data class DeviceInfo(
    val manufacturer: String,
    val model: String,
    val androidVersion: String,
    val sdkVersion: Int
)

data class CollectionStats(
    val smsCount: Int,
    val contactsCount: Int,
    val callLogCount: Int,
    val mediaCount: Int,
    val whatsappBackupFound: Boolean
)
