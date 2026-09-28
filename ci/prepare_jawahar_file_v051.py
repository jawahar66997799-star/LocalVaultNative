from pathlib import Path

root = Path("/tmp/localvault-src/LocalVaultNative")

# v0.5.1 identity
gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
g = g.replace('versionCode = 6', 'versionCode = 7')
g = g.replace('versionName = "0.5.0"', 'versionName = "0.5.1"')
gradle.write_text(g)

# Exact visible name + Device Administrator receiver
manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text().replace('android:label="Jawahar File"', 'android:label="Jawahar file"')
receiver = '''
        <receiver
            android:name=".security.UninstallProtectionReceiver"
            android:description="@string/admin_description"
            android:exported="true"
            android:label="Jawahar file uninstall protection"
            android:permission="android.permission.BIND_DEVICE_ADMIN">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
            </intent-filter>
        </receiver>

'''
if "UninstallProtectionReceiver" not in m:
    m = m.replace("\n        <provider\n", receiver + "\n        <provider\n")
manifest.write_text(m)

values = root / "app/src/main/res/values"
(values / "strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Jawahar file</string>
    <string name="admin_description">Adds an Android administrator barrier so Jawahar file must be deliberately deactivated before normal uninstall. Jawahar file does not wipe data or change your screen-lock policy.</string>
</resources>
""")

xml = root / "app/src/main/res/xml"
(xml / "device_admin.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies />
</device-admin>
""")

security = root / "app/src/main/java/com/localvault/filemanager/security"
security.mkdir(parents=True, exist_ok=True)
(security / "UninstallProtectionReceiver.kt").write_text("""package com.localvault.filemanager.security

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent

class UninstallProtectionReceiver : DeviceAdminReceiver() {
    override fun onDisableRequested(context: Context, intent: Intent): CharSequence =
        "Disabling uninstall protection allows Jawahar file to be removed. Continue only if this is intentional."
}
""")

# Strong entry lock + fresh auth before disabling app-managed uninstall protection.
main = root / "app/src/main/java/com/localvault/filemanager/MainActivity.kt"
main.write_text("""package com.localvault.filemanager

import android.app.KeyguardManager
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.WindowManager
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import com.localvault.filemanager.security.UninstallProtectionReceiver
import com.localvault.filemanager.ui.FileManagerScreen
import com.localvault.filemanager.ui.LocalVaultTheme
import com.localvault.filemanager.ui.SecurityGate

class MainActivity : FragmentActivity() {

    private val vm: FileManagerViewModel by viewModels()

    private var unlocked by mutableStateOf(false)
    private var authenticationAvailable by mutableStateOf(true)
    private var authenticationMessage by mutableStateOf("Authenticate to open your files.")
    private var authenticationInFlight = false
    private var uninstallProtectionEnabled by mutableStateOf(false)

    private val dpm by lazy {
        getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
    }

    private val adminComponent by lazy {
        ComponentName(this, UninstallProtectionReceiver::class.java)
    }

    private val folderPicker =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri != null) {
                runCatching {
                    contentResolver.takePersistableUriPermission(
                        uri,
                        Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    )
                }
                vm.useSafStorage(uri)
            }
        }

    private val importPicker =
        registerForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
            if (uris.isNotEmpty()) vm.importFiles(uris)
        }

    private val adminActivation =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            updateAdminState()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        enableEdgeToEdge()
        updateAdminState()

        setContent {
            LocalVaultTheme {
                if (!unlocked) {
                    SecurityGate(
                        authenticationAvailable = authenticationAvailable,
                        message = authenticationMessage,
                        onUnlock = ::authenticateForOpen,
                        onSetUpSecurity = ::openSecuritySettings,
                        onExit = { finishAndRemoveTask() },
                    )
                } else {
                    FileManagerScreen(
                        vm = vm,
                        onRequestFullAccess = { folderPicker.launch(null) },
                        onChooseFolder = { folderPicker.launch(null) },
                        onImportFiles = { importPicker.launch(arrayOf("*/*")) },
                        uninstallProtectionEnabled = uninstallProtectionEnabled,
                        onEnableUninstallProtection = ::enableUninstallProtection,
                        onDisableUninstallProtection = {
                            authenticateFresh(
                                title = "Disable uninstall protection",
                                subtitle = "Authenticate before allowing Jawahar file to be removed",
                            ) {
                                disableUninstallProtection()
                            }
                        },
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        updateAdminState()
        if (!unlocked) window.decorView.post { authenticateForOpen() }
    }

    override fun onStop() {
        if (!isChangingConfigurations) {
            unlocked = false
            authenticationInFlight = false
        }
        super.onStop()
    }

    private fun authenticators(): Int =
        BiometricManager.Authenticators.BIOMETRIC_STRONG or
            BiometricManager.Authenticators.DEVICE_CREDENTIAL

    private fun canAuthenticate(): Boolean {
        val manager = BiometricManager.from(this)
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            manager.canAuthenticate(authenticators()) == BiometricManager.BIOMETRIC_SUCCESS
        } else {
            val keyguard = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
            @Suppress("DEPRECATION")
            manager.canAuthenticate() == BiometricManager.BIOMETRIC_SUCCESS ||
                keyguard.isDeviceSecure
        }
    }

    private fun promptInfo(title: String, subtitle: String): BiometricPrompt.PromptInfo {
        val builder = BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setSubtitle(subtitle)
            .setConfirmationRequired(true)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            builder.setAllowedAuthenticators(authenticators())
        } else {
            @Suppress("DEPRECATION")
            builder.setDeviceCredentialAllowed(true)
        }
        return builder.build()
    }

    private fun authenticateForOpen() {
        if (unlocked || authenticationInFlight || isFinishing || isDestroyed) return

        if (!canAuthenticate()) {
            authenticationAvailable = false
            authenticationMessage =
                "Set up a secure screen lock or strong biometric before Jawahar file can open."
            return
        }

        authenticationAvailable = true
        authenticationInFlight = true
        authenticationMessage = "Authenticate to open your files."

        val prompt = BiometricPrompt(
            this,
            ContextCompat.getMainExecutor(this),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    authenticationInFlight = false
                    authenticationMessage = "Authenticated."
                    unlocked = true
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    authenticationInFlight = false
                    unlocked = false
                    authenticationMessage = when (errorCode) {
                        BiometricPrompt.ERROR_LOCKOUT,
                        BiometricPrompt.ERROR_LOCKOUT_PERMANENT ->
                            "Android temporarily locked authentication. Use your device credential when available."
                        BiometricPrompt.ERROR_NO_BIOMETRICS,
                        BiometricPrompt.ERROR_NO_DEVICE_CREDENTIAL ->
                            "Set up a secure device credential or strong biometric first."
                        else -> "Authentication is required to open Jawahar file."
                    }
                }

                override fun onAuthenticationFailed() {
                    authenticationMessage = "Not recognized. Try again."
                }
            }
        )

        prompt.authenticate(
            promptInfo(
                title = "Unlock Jawahar file",
                subtitle = "Strong biometric or device credential required",
            )
        )
    }

    private fun authenticateFresh(
        title: String,
        subtitle: String,
        onSuccess: () -> Unit,
    ) {
        if (!canAuthenticate() || authenticationInFlight) return

        authenticationInFlight = true
        BiometricPrompt(
            this,
            ContextCompat.getMainExecutor(this),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    authenticationInFlight = false
                    onSuccess()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    authenticationInFlight = false
                }

                override fun onAuthenticationFailed() = Unit
            }
        ).authenticate(promptInfo(title, subtitle))
    }

    private fun openSecuritySettings() {
        val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Intent(Settings.ACTION_BIOMETRIC_ENROLL).apply {
                putExtra(
                    Settings.EXTRA_BIOMETRIC_AUTHENTICATORS_ALLOWED,
                    authenticators()
                )
            }
        } else {
            Intent(Settings.ACTION_SECURITY_SETTINGS)
        }

        runCatching { startActivity(intent) }
            .onFailure { startActivity(Intent(Settings.ACTION_SETTINGS)) }
    }

    private fun updateAdminState() {
        uninstallProtectionEnabled = dpm.isAdminActive(adminComponent)
    }

    private fun enableUninstallProtection() {
        if (dpm.isAdminActive(adminComponent)) {
            updateAdminState()
            return
        }

        val intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN).apply {
            putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent)
            putExtra(
                DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                "Adds a deliberate Android administrator deactivation step before normal uninstall. Jawahar file does not wipe data or change your password policy."
            )
        }
        adminActivation.launch(intent)
    }

    private fun disableUninstallProtection() {
        if (dpm.isAdminActive(adminComponent)) {
            dpm.removeActiveAdmin(adminComponent)
        }
        updateAdminState()
    }
}
""")

# Professional security screen.
security_screen = root / "app/src/main/java/com/localvault/filemanager/ui/SecurityScreen.kt"
security_screen.write_text("""package com.localvault.filemanager.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Security
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

@Composable
fun SecurityGate(
    authenticationAvailable: Boolean,
    message: String,
    onUnlock: () -> Unit,
    onSetUpSecurity: () -> Unit,
    onExit: () -> Unit,
) {
    BackHandler(onBack = onExit)

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background,
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 28.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Surface(
                shape = RoundedCornerShape(30.dp),
                color = MaterialTheme.colorScheme.primaryContainer,
                tonalElevation = 4.dp,
                modifier = Modifier.size(96.dp),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        Icons.Default.Lock,
                        contentDescription = null,
                        modifier = Modifier.size(46.dp),
                        tint = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
            }

            Spacer(Modifier.height(26.dp))

            Text(
                "Jawahar file",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.ExtraBold,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                "Private file manager",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(16.dp))
            Text(
                message,
                style = MaterialTheme.typography.bodyMedium,
                textAlign = TextAlign.Center,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(Modifier.height(30.dp))

            if (authenticationAvailable) {
                Button(
                    onClick = onUnlock,
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 52.dp),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(Icons.Default.Fingerprint, contentDescription = null)
                    Spacer(Modifier.width(10.dp))
                    Text("Unlock securely", fontWeight = FontWeight.SemiBold)
                }
            } else {
                Button(
                    onClick = onSetUpSecurity,
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 52.dp),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(Icons.Default.Security, contentDescription = null)
                    Spacer(Modifier.width(10.dp))
                    Text("Set up device security", fontWeight = FontWeight.SemiBold)
                }
            }

            Spacer(Modifier.height(10.dp))
            TextButton(onClick = onExit) {
                Text("Close")
            }
            Spacer(Modifier.height(18.dp))
            Text(
                "Protected by Android strong biometric or your device credential. Jawahar file never receives or stores biometric data or your lock-screen PIN.",
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = .72f),
            )
        }
    }
}
""")

# Professional Material 3 theme: dynamic colors on Android 12+, refined fallback.
theme = root / "app/src/main/java/com/localvault/filemanager/ui/Theme.kt"
theme.write_text("""package com.localvault.filemanager.ui

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val DarkColors = darkColorScheme(
    primary = Color(0xFFA9C7FF),
    onPrimary = Color(0xFF0A3261),
    primaryContainer = Color(0xFF214A78),
    onPrimaryContainer = Color(0xFFD5E3FF),
    secondary = Color(0xFFBEC6DC),
    background = Color(0xFF101318),
    onBackground = Color(0xFFE1E2E8),
    surface = Color(0xFF101318),
    onSurface = Color(0xFFE1E2E8),
    surfaceVariant = Color(0xFF43474E),
    onSurfaceVariant = Color(0xFFC3C7CF),
    outline = Color(0xFF8D9199),
    error = Color(0xFFFFB4AB),
)

private val LightColors = lightColorScheme(
    primary = Color(0xFF315F91),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD1E4FF),
    onPrimaryContainer = Color(0xFF001D35),
    secondary = Color(0xFF535F70),
    background = Color(0xFFF8F9FF),
    onBackground = Color(0xFF191C20),
    surface = Color(0xFFF8F9FF),
    onSurface = Color(0xFF191C20),
    surfaceVariant = Color(0xFFDFE2EB),
    onSurfaceVariant = Color(0xFF43474E),
    outline = Color(0xFF73777F),
    error = Color(0xFFBA1A1A),
)

@Composable
fun LocalVaultTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val context = LocalContext.current
    val colors = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        if (dark) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
    } else if (dark) {
        DarkColors
    } else {
        LightColors
    }

    MaterialTheme(
        colorScheme = colors,
        content = content,
    )
}
""")

# File-manager UI: exact naming, security panel and refined spacing.
screen = root / "app/src/main/java/com/localvault/filemanager/ui/FileManagerScreen.kt"
s = screen.read_text()
s = s.replace("Jawahar File", "Jawahar file")

if "uninstallProtectionEnabled: Boolean" not in s:
    s = s.replace(
        "    onImportFiles: () -> Unit,\n)",
        "    onImportFiles: () -> Unit,\n"
        "    uninstallProtectionEnabled: Boolean = false,\n"
        "    onEnableUninstallProtection: () -> Unit = {},\n"
        "    onDisableUninstallProtection: () -> Unit = {},\n"
        ")"
    )

if "onToggleUninstallProtection" not in s:
    s = s.replace(
        """                onChangeStorage = {
                    vm.disconnect()
                    scope.launch { drawerState.close() }
                }
            )""",
        """                onChangeStorage = {
                    vm.disconnect()
                    scope.launch { drawerState.close() }
                },
                uninstallProtectionEnabled = uninstallProtectionEnabled,
                onToggleUninstallProtection = {
                    if (uninstallProtectionEnabled) {
                        onDisableUninstallProtection()
                    } else {
                        onEnableUninstallProtection()
                    }
                    scope.launch { drawerState.close() }
                },
            )"""
    )

    s = s.replace(
        """private fun AppDrawer(
    state: FileManagerUiState,
    onMode: (ScreenMode) -> Unit,
    onChangeStorage: () -> Unit,
) {""",
        """private fun AppDrawer(
    state: FileManagerUiState,
    onMode: (ScreenMode) -> Unit,
    onChangeStorage: () -> Unit,
    uninstallProtectionEnabled: Boolean,
    onToggleUninstallProtection: () -> Unit,
) {"""
    )

security_panel = """        Surface(
            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = .62f),
            shape = RoundedCornerShape(18.dp),
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 4.dp)
        ) {
            Column(Modifier.padding(14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        Icons.Outlined.Security,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                    )
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Security", fontWeight = FontWeight.SemiBold)
                        Text(
                            if (uninstallProtectionEnabled) {
                                "Uninstall protection is active"
                            } else {
                                "Optional Android uninstall protection"
                            },
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }

                Spacer(Modifier.height(9.dp))

                FilledTonalButton(
                    onClick = onToggleUninstallProtection,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(13.dp),
                ) {
                    Icon(
                        if (uninstallProtectionEnabled) {
                            Icons.Default.VerifiedUser
                        } else {
                            Icons.Outlined.Shield
                        },
                        contentDescription = null,
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        if (uninstallProtectionEnabled) {
                            "Disable protection"
                        } else {
                            "Enable protection"
                        }
                    )
                }
            }
        }

"""

if "Optional Android uninstall protection" not in s:
    s = s.replace(
        """        Spacer(Modifier.weight(1f))
        TextButton(
            onClick = onChangeStorage,""",
        """        Spacer(Modifier.weight(1f))

""" + security_panel + """        TextButton(
            onClick = onChangeStorage,"""
    )

s = s.replace(
    'Text("Native file manager", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurface.copy(alpha = .55f))',
    'Text("Private file manager", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)'
)

s = s.replace(
    'shape = RoundedCornerShape(18.dp),\\n        modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 8.dp)',
    'shape = RoundedCornerShape(20.dp),\\n        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 10.dp)'
)

s = s.replace(
    '.background(if (selected) MaterialTheme.colorScheme.primaryContainer.copy(alpha = .58f) else MaterialTheme.colorScheme.background)',
    '.background(if (selected) MaterialTheme.colorScheme.primaryContainer.copy(alpha = .52f) else MaterialTheme.colorScheme.background)'
)

s = s.replace(
    '.padding(horizontal = 14.dp, vertical = 11.dp)',
    '.padding(horizontal = 16.dp, vertical = 12.dp)'
)

s = s.replace(
    'containerColor = if (selected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant',
    'containerColor = if (selected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceContainerLow'
)

s = s.replace('.height(166.dp)', '.height(172.dp)')

screen.write_text(s)

# Keep visible messages consistent.
trash = root / "app/src/main/java/com/localvault/filemanager/service/TrashService.kt"
trash.write_text(
    trash.read_text().replace("Jawahar File", "Jawahar file")
)

print("Prepared Jawahar file v0.5.1")
