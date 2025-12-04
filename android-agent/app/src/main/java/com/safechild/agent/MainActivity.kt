package com.safechild.agent

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

/**
 * SafeChild Forensic Agent - Main Activity
 * Handles deep link activation and shows consent screen
 */
class MainActivity : AppCompatActivity() {

    private var collectionToken: String? = null
    private var clientNumber: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Parse deep link if present
        handleIntent(intent)

        setupUI()
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleIntent(it) }
    }

    private fun handleIntent(intent: Intent) {
        val data: Uri? = intent.data
        if (data != null && data.host == "safechild.mom" && data.path?.startsWith("/collect/") == true) {
            // Extract token from URL: https://safechild.mom/collect/{token}
            collectionToken = data.pathSegments.getOrNull(1)

            if (collectionToken != null) {
                // Validate token with server
                validateToken()
            }
        }
    }

    private fun setupUI() {
        val titleText = findViewById<TextView>(R.id.titleText)
        val descriptionText = findViewById<TextView>(R.id.descriptionText)
        val consentText = findViewById<TextView>(R.id.consentText)
        val startButton = findViewById<Button>(R.id.startButton)
        val cancelButton = findViewById<Button>(R.id.cancelButton)

        titleText.text = "SafeChild Veri Toplama"

        descriptionText.text = """
            Bu uygulama, avukatınızın talebi doğrultusunda cihazınızdaki delilleri güvenli bir şekilde toplar.

            Toplanacak veriler:
            • WhatsApp mesajları ve medya
            • SMS mesajları
            • Arama geçmişi
            • Fotoğraflar ve videolar
            • Rehber kişileri

            Tüm veriler şifrelenerek güvenli sunuculara aktarılır ve sadece avukatınız tarafından görüntülenebilir.
        """.trimIndent()

        consentText.text = """
            Bu butona tıklayarak, yukarıda belirtilen verilerin toplanmasına ve avukatıma iletilmesine açık rıza gösteriyorum.
        """.trimIndent()

        startButton.setOnClickListener {
            if (collectionToken != null) {
                startCollection()
            } else {
                Toast.makeText(this, "Geçersiz bağlantı. Lütfen avukatınızdan yeni bir link isteyin.", Toast.LENGTH_LONG).show()
            }
        }

        cancelButton.setOnClickListener {
            finish()
        }
    }

    private fun validateToken() {
        lifecycleScope.launch {
            try {
                val api = ApiService(this@MainActivity)
                val result = api.validateCollectionToken(collectionToken!!)

                if (result.isValid) {
                    clientNumber = result.clientNumber
                    findViewById<TextView>(R.id.statusText)?.text =
                        "Bağlantı doğrulandı: ${result.clientName}"
                } else {
                    Toast.makeText(
                        this@MainActivity,
                        "Bu bağlantı geçersiz veya süresi dolmuş.",
                        Toast.LENGTH_LONG
                    ).show()
                    finish()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@MainActivity,
                    "Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    private fun startCollection() {
        val intent = Intent(this, PermissionsActivity::class.java).apply {
            putExtra("COLLECTION_TOKEN", collectionToken)
            putExtra("CLIENT_NUMBER", clientNumber)
        }
        startActivity(intent)
    }
}
