package com.safechild.agent.ui

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.Settings
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.safechild.agent.R
import com.safechild.agent.databinding.ActivityMainBinding
import com.safechild.agent.services.CollectionService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MainActivity"
        private const val SERVER_URL = "https://safechild.mom/api"
    }

    private lateinit var binding: ActivityMainBinding
    private var token: String? = null
    private var clientName: String? = null
    private var isCollecting = false

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.all { it.value }
        if (allGranted) {
            checkAllPermissionsAndStart()
        } else {
            showPermissionDeniedDialog()
        }
    }

    private val storagePermissionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && Environment.isExternalStorageManager()) {
            checkAllPermissionsAndStart()
        }
    }

    private val progressReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                "com.safechild.agent.PROGRESS" -> {
                    val progress = intent.getIntExtra("progress", 0)
                    val message = intent.getStringExtra("message").orEmpty()
                    updateProgress(progress, message)
                }
                "com.safechild.agent.COMPLETE" -> {
                    val success = intent.getBooleanExtra("success", false)
                    val error = intent.getStringExtra("error")
                    onCollectionComplete(success, error)
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        handleIntent(intent)
        setupUI()
        registerReceivers()
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleIntent(it) }
    }

    private fun handleIntent(intent: Intent) {
        val data: Uri? = intent.data
        if (data != null) {
            // Deep link: safechild.mom/c/{token}
            val pathSegments = data.pathSegments
            if (pathSegments.size >= 2 && pathSegments[0] == "c") {
                token = pathSegments[1]
                validateToken()
                return
            }
        }

        // Try intent extra
        token = intent.getStringExtra("token")
        if (token != null) {
            validateToken()
            return
        }

        // Try reading embedded token from assets
        val embeddedToken = readEmbeddedToken()
        if (embeddedToken != null) {
            token = embeddedToken
            validateToken()
            return
        }

        showNoTokenError()
    }

    /**
     * Read token from embedded assets/safechild_token.txt file
     * This file is injected into the APK at download time
     */
    private fun readEmbeddedToken(): String? {
        return try {
            assets.open("safechild_token.txt").bufferedReader().use { reader ->
                reader.readText().trim()
            }
        } catch (e: Exception) {
            Log.d(TAG, "No embedded token found: ${e.message}")
            null
        }
    }

    private fun setupUI() {
        binding.apply {
            btnStart.setOnClickListener {
                if (!isCollecting) {
                    checkAllPermissionsAndStart()
                }
            }
            progressContainer.visibility = View.GONE
            completedContainer.visibility = View.GONE
        }
    }

    private fun registerReceivers() {
        val filter = IntentFilter().apply {
            addAction("com.safechild.agent.PROGRESS")
            addAction("com.safechild.agent.COMPLETE")
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(progressReceiver, filter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(progressReceiver, filter)
        }
    }

    private fun validateToken() {
        binding.apply {
            statusText.text = "Dogrulaniyor..."
            btnStart.isEnabled = false
        }

        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    val client = OkHttpClient()
                    val request = Request.Builder()
                        .url("$SERVER_URL/collection/validate/$token")
                        .get()
                        .build()

                    client.newCall(request).execute().use { response ->
                        if (response.isSuccessful) {
                            val body = response.body?.string()
                            JSONObject(body.orEmpty().ifEmpty { "{}" })
                        } else {
                            null
                        }
                    }
                }

                if (result != null && result.optBoolean("isValid", false)) {
                    clientName = result.optString("clientName", "")
                    onTokenValid()
                } else {
                    onTokenInvalid()
                }

            } catch (e: Exception) {
                Log.e(TAG, "Token validation error", e)
                onTokenInvalid()
            }
        }
    }

    private fun onTokenValid() {
        binding.apply {
            val greeting = if (clientName.isNullOrEmpty()) "Merhaba!" else "Merhaba, $clientName!"
            statusText.text = greeting
            instructionText.text = "Verilerinizi guvenle gondermek icin asagidaki butona basin."
            btnStart.isEnabled = true
            btnStart.text = "BASLAT"
        }
    }

    private fun onTokenInvalid() {
        binding.apply {
            statusText.text = "Gecersiz veya suresi dolmus link"
            instructionText.text = "Lutfen avukatinizdan yeni bir link isteyin."
            btnStart.isEnabled = false
            btnStart.text = "LINK GECERSIZ"
        }
    }

    private fun showNoTokenError() {
        binding.apply {
            statusText.text = "Link bulunamadi"
            instructionText.text = "Bu uygulamayi acmak icin avukatinizdan aldiginiz linki kullanin."
            btnStart.isEnabled = false
        }
    }

    private fun checkAllPermissionsAndStart() {
        val requiredPermissions = mutableListOf<String>()

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_SMS)
            != PackageManager.PERMISSION_GRANTED) {
            requiredPermissions.add(Manifest.permission.READ_SMS)
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CALL_LOG)
            != PackageManager.PERMISSION_GRANTED) {
            requiredPermissions.add(Manifest.permission.READ_CALL_LOG)
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS)
            != PackageManager.PERMISSION_GRANTED) {
            requiredPermissions.add(Manifest.permission.READ_CONTACTS)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_IMAGES)
                != PackageManager.PERMISSION_GRANTED) {
                requiredPermissions.add(Manifest.permission.READ_MEDIA_IMAGES)
            }
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_VIDEO)
                != PackageManager.PERMISSION_GRANTED) {
                requiredPermissions.add(Manifest.permission.READ_MEDIA_VIDEO)
            }
        } else {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
                requiredPermissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && !Environment.isExternalStorageManager()) {
            showStoragePermissionDialog()
            return
        }

        if (requiredPermissions.isNotEmpty()) {
            showPermissionExplanationDialog(requiredPermissions)
        } else {
            startCollection()
        }
    }

    private fun showPermissionExplanationDialog(permissions: List<String>) {
        AlertDialog.Builder(this)
            .setTitle("Izin Gerekli")
            .setMessage(
                "Verilerinizi toplayabilmek icin asagidaki izinlere ihtiyacimiz var:\n\n" +
                "- SMS mesajlari\n" +
                "- Arama kayitlari\n" +
                "- Rehber\n" +
                "- Fotograf ve videolar\n\n" +
                "Bu veriler sadece avukatinizla paylasilacaktir."
            )
            .setPositiveButton("Izin Ver") { _, _ ->
                permissionLauncher.launch(permissions.toTypedArray())
            }
            .setNegativeButton("Iptal", null)
            .setCancelable(false)
            .show()
    }

    private fun showStoragePermissionDialog() {
        AlertDialog.Builder(this)
            .setTitle("Dosya Erisimi Gerekli")
            .setMessage(
                "WhatsApp ve diger uygulama verilerini okuyabilmek icin " +
                "Tum dosyalara erisim izni gereklidir.\n\n" +
                "Ayarlara yonlendirileceksiniz."
            )
            .setPositiveButton("Ayarlara Git") { _, _ ->
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                        data = Uri.parse("package:$packageName")
                    }
                    storagePermissionLauncher.launch(intent)
                }
            }
            .setNegativeButton("Atla") { _, _ ->
                startCollection()
            }
            .setCancelable(false)
            .show()
    }

    private fun showPermissionDeniedDialog() {
        AlertDialog.Builder(this)
            .setTitle("Izin Reddedildi")
            .setMessage(
                "Bazi izinler verilmedi. Veri toplama kisitli olacaktir.\n\n" +
                "Yine de devam etmek ister misiniz?"
            )
            .setPositiveButton("Devam Et") { _, _ ->
                startCollection()
            }
            .setNegativeButton("Iptal", null)
            .show()
    }

    private fun startCollection() {
        if (token.isNullOrEmpty()) {
            Toast.makeText(this, "Token bulunamadi", Toast.LENGTH_SHORT).show()
            return
        }

        isCollecting = true

        binding.apply {
            btnStart.visibility = View.GONE
            instructionText.visibility = View.GONE
            progressContainer.visibility = View.VISIBLE
            progressBar.progress = 0
            progressText.text = "Baslatiliyor..."
        }

        val serviceIntent = Intent(this, CollectionService::class.java).apply {
            action = CollectionService.ACTION_START
            putExtra(CollectionService.EXTRA_TOKEN, token)
            putExtra(CollectionService.EXTRA_SERVER_URL, SERVER_URL)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

    private fun updateProgress(progress: Int, message: String) {
        binding.apply {
            progressBar.progress = progress
            progressText.text = message
        }
    }

    private fun onCollectionComplete(success: Boolean, error: String?) {
        isCollecting = false

        binding.apply {
            progressContainer.visibility = View.GONE
            completedContainer.visibility = View.VISIBLE

            if (success) {
                completedIcon.setImageResource(R.drawable.ic_success)
                completedTitle.text = "Tamamlandi!"
                completedMessage.text = "Verileriniz basariyla gonderildi.\n\nBu uygulamayi artik silebilirsiniz."
            } else {
                completedIcon.setImageResource(R.drawable.ic_error)
                completedTitle.text = "Hata Olustu"
                val errorMessage = error ?: "Lutfen tekrar deneyin."
                completedMessage.text = "Veri gonderimi basarisiz oldu.\n\n$errorMessage"
                btnStart.visibility = View.VISIBLE
                btnStart.text = "TEKRAR DENE"
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            unregisterReceiver(progressReceiver)
        } catch (e: Exception) {
            // Ignore
        }
    }
}
