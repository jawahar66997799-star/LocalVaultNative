from pathlib import Path
import re

# Start from the already tested v0.5.0 hardening/smoothness transformation.
base_script = Path("ci/prepare_jawahar_file_v050.py")
exec(compile(base_script.read_text(), str(base_script), "exec"), {"__name__": "__main__"})

root = Path("/tmp/localvault-src/LocalVaultNative")

# ----- Exact identity -----
gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
g = g.replace('versionCode = 6', 'versionCode = 7')
g = g.replace('versionName = "0.5.0"', 'versionName = "0.5.1"')
gradle.write_text(g)

# ----- Professional adaptive Material 3 theme -----
theme = root / "app/src/main/java/com/localvault/filemanager/ui/Theme.kt"
theme.write_text("""package com.localvault.filemanager.ui

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

private val JawaharDarkColors = darkColorScheme(
    primary = Color(0xFF9BB1FF),
    onPrimary = Color(0xFF10255D),
    primaryContainer = Color(0xFF263F79),
    onPrimaryContainer = Color(0xFFDCE4FF),
    secondary = Color(0xFFB9C3E9),
    secondaryContainer = Color(0xFF313A51),
    background = Color(0xFF0B0F17),
    onBackground = Color(0xFFE7EAF1),
    surface = Color(0xFF11161F),
    onSurface = Color(0xFFE7EAF1),
    surfaceVariant = Color(0xFF1A202C),
    onSurfaceVariant = Color(0xFFC4C7D0),
    outline = Color(0xFF8E9099),
    outlineVariant = Color(0xFF44464F),
    error = Color(0xFFFFB4AB),
    errorContainer = Color(0xFF93000A),
)

private val JawaharLightColors = lightColorScheme(
    primary = Color(0xFF405A97),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD9E2FF),
    onPrimaryContainer = Color(0xFF001A42),
    secondary = Color(0xFF565F75),
    secondaryContainer = Color(0xFFDAE2F9),
    background = Color(0xFFF9F9FF),
    onBackground = Color(0xFF1A1B20),
    surface = Color(0xFFF9F9FF),
    onSurface = Color(0xFF1A1B20),
    surfaceVariant = Color(0xFFE1E2EC),
    onSurfaceVariant = Color(0xFF45464F),
    outline = Color(0xFF757780),
    outlineVariant = Color(0xFFC5C6D0),
    error = Color(0xFFBA1A1A),
    errorContainer = Color(0xFFFFDAD6),
)

private val JawaharShapes = Shapes(
    extraSmall = RoundedCornerShape(10.dp),
    small = RoundedCornerShape(14.dp),
    medium = RoundedCornerShape(20.dp),
    large = RoundedCornerShape(28.dp),
    extraLarge = RoundedCornerShape(32.dp),
)

@Composable
fun LocalVaultTheme(content: @Composable () -> Unit) {
    val context = LocalContext.current
    val dark = isSystemInDarkTheme()
    val colors = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        if (dark) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
    } else {
        if (dark) JawaharDarkColors else JawaharLightColors
    }

    MaterialTheme(
        colorScheme = colors,
        shapes = JawaharShapes,
        content = content,
    )
}
""")

# ----- Exact visible app name + privacy-safe style -----
manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text()
m = m.replace('android:label="Jawahar File"', 'android:label="Jawahar file"')

receiver = '''
        <receiver
            android:name=".security.UninstallProtectionReceiver"
            android:description="@string/admin_description"
            android:exported="true"
            android:label="@string/admin_label"
            android:permission="android.permission.BIND_DEVICE_ADMIN">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
            </intent-filter>
        </receiver>

'''
if 'UninstallProtectionReceiver' not in m:
    m = m.replace('        <provider\n', receiver + '        <provider\n')
manifest.write_text(m)

strings = root / "app/src/main/res/values/strings.xml"
strings.write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Jawahar file</string>
    <string name="admin_label">Jawahar file uninstall protection</string>
    <string name="admin_description">Adds an Android Device Administrator deactivation step before normal uninstall. Jawahar file does not request device wipe, password-reset, camera, or other device-management policies.</string>
</resources>
""")

xml_dir = root / "app/src/main/res/xml"
(xml_dir / "device_admin.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies />
</device-admin>
""")

styles = root / "app/src/main/res/values/styles.xml"
styles.write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.LocalVault" parent="android:style/Theme.Material.NoActionBar">
        <item name="android:windowActionModeOverlay">true</item>
        <item name="android:windowDisablePreview">true</item>
        <item name="android:windowIsTranslucent">false</item>
        <item name="android:statusBarColor">@android:color/transparent</item>
        <item name="android:navigationBarColor">@android:color/transparent</item>
        <item name="android:fontFamily">sans</item>
    </style>
</resources>
""")

# Cleaner branded launcher: folder + lock, no text.
launcher = root / "app/src/main/res/drawable/ic_launcher.xml"
launcher.write_text("""<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#101725" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#8FA8FF" android:pathData="M17,33c0,-6 4,-10 10,-10h19l8,9h27c6,0 10,4 10,10v36c0,6 -4,10 -10,10h-54c-6,0 -10,-4 -10,-10z"/>
    <path android:fillColor="#F5F7FF" android:pathData="M28,47h52c4,0 7,3 7,7v23c0,4 -3,7 -7,7h-52c-4,0 -7,-3 -7,-7v-23c0,-4 3,-7 7,-7z"/>
    <path android:fillColor="#405A97" android:pathData="M58,61h20v16h-20z"/>
    <path android:fillColor="#405A97" android:pathData="M62,61v-5c0,-5 3,-9 6,-9s6,4 6,9v5h-4v-5c0,-2 -1,-4 -2,-4s-2,2 -2,4v5z"/>
    <path android:fillColor="#D9E2FF" android:pathData="M66,68a2,2 0,1 1,4 0a2,2 0,0 1,-4 0z"/>
</vector>
""")

# ----- Device-admin receiver -----
security_dir = root / "app/src/main/java/com/localvault/filemanager/security"
security_dir.mkdir(parents=True, exist_ok=True)
(security_dir / "UninstallProtectionReceiver.kt").write_text("""package com.localvault.filemanager.security

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent

class UninstallProtectionReceiver : DeviceAdminReceiver() {
    override fun onDisableRequested(context: Context, intent: Intent): CharSequence =
        "Turning this off removes Jawahar file's additional uninstall barrier. Continue only if you intend to allow the app to be removed."
}
""")

# ----- Strong entry lock + opt-in Android uninstall barrier -----
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
    private var externalFlowInProgress = false
    private var uninstallProtectionEnabled by mutableStateOf(false)
    private var biometricPrompt: BiometricPrompt? = null

    private val devicePolicyManager by lazy {
        getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
    }

    private val adminComponent by lazy {
        ComponentName(this, UninstallProtectionReceiver::class.java)
    }

    private val folderPicker =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
            externalFlowInProgress = false
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
            externalFlowInProgress = false
            if (uris.isNotEmpty()) vm.importFiles(uris)
        }

    private val adminActivation =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            externalFlowInProgress = false
            updateUninstallProtectionState()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        enableEdgeToEdge()
        updateUninstallProtectionState()

        setContent {
            LocalVaultTheme {
                if (!unlocked) {
                    SecurityGate(
                        authenticationAvailable = authenticationAvailable,
                        message = authenticationMessage,
                        onUnlock = ::authenticate,
                        onSetUpSecurity = ::openSecuritySettings,
                        onExit = { finishAndRemoveTask() },
                    )
                } else {
                    FileManagerScreen(
                        vm = vm,
                        onRequestFullAccess = ::chooseFolder,
                        onChooseFolder = ::chooseFolder,
                        onImportFiles = ::chooseImportFiles,
                        uninstallProtectionEnabled = uninstallProtectionEnabled,
                        onEnableUninstallProtection = ::enableUninstallProtection,
                        onDisableUninstallProtection = ::disableUninstallProtection,
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        updateUninstallProtectionState()
        if (!unlocked && !externalFlowInProgress) {
            window.decorView.post { authenticate() }
        }
    }

    override fun onStop() {
        if (!isChangingConfigurations && !externalFlowInProgress) {
            unlocked = false
            authenticationInFlight = false
        }
        super.onStop()
    }

    private fun chooseFolder() {
        externalFlowInProgress = true
        folderPicker.launch(null)
    }

    private fun chooseImportFiles() {
        externalFlowInProgress = true
        importPicker.launch(arrayOf("*/*"))
    }

    private fun authenticators(): Int =
        BiometricManager.Authenticators.BIOMETRIC_STRONG or
            BiometricManager.Authenticators.DEVICE_CREDENTIAL

    private fun authenticate() {
        if (unlocked || authenticationInFlight || isFinishing || isDestroyed) return

        val biometricManager = BiometricManager.from(this)
        val canAuthenticate = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            biometricManager.canAuthenticate(authenticators()) == BiometricManager.BIOMETRIC_SUCCESS
        } else {
            val keyguard = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
            @Suppress("DEPRECATION")
            biometricManager.canAuthenticate() == BiometricManager.BIOMETRIC_SUCCESS ||
                keyguard.isDeviceSecure
        }

        if (!canAuthenticate) {
            authenticationAvailable = false
            authenticationMessage =
                "A secure device screen lock or strong biometric is required before Jawahar file can open."
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
                    unlocked = true
                    authenticationMessage = "Authenticated."
                    maybeOfferUninstallProtection()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    authenticationInFlight = false
                    unlocked = false
                    authenticationMessage = when (errorCode) {
                        BiometricPrompt.ERROR_LOCKOUT,
                        BiometricPrompt.ERROR_LOCKOUT_PERMANENT ->
                            "Authentication is temporarily locked by Android. Use your device credential when Android allows it."
                        BiometricPrompt.ERROR_NO_BIOMETRICS,
                        BiometricPrompt.ERROR_NO_DEVICE_CREDENTIAL ->
                            "Set up a secure device credential or strong biometric first."
                        else -> "Authentication required to open Jawahar file."
                    }
                }

                override fun onAuthenticationFailed() {
                    authenticationMessage = "Not recognized. Try again."
                }
            }
        )
        biometricPrompt = prompt

        val builder = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Unlock Jawahar file")
            .setSubtitle("Strong biometric or device credential required")
            .setConfirmationRequired(true)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            builder.setAllowedAuthenticators(authenticators())
        } else {
            @Suppress("DEPRECATION")
            builder.setDeviceCredentialAllowed(true)
        }

        prompt.authenticate(builder.build())
    }

    private fun openSecuritySettings() {
        externalFlowInProgress = true
        val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Intent(Settings.ACTION_BIOMETRIC_ENROLL).apply {
                putExtra(Settings.EXTRA_BIOMETRIC_AUTHENTICATORS_ALLOWED, authenticators())
            }
        } else {
            Intent(Settings.ACTION_SECURITY_SETTINGS)
        }
        runCatching { startActivity(intent) }
            .onFailure {
                externalFlowInProgress = false
                startActivity(Intent(Settings.ACTION_SETTINGS))
            }
    }

    private fun updateUninstallProtectionState() {
        uninstallProtectionEnabled = devicePolicyManager.isAdminActive(adminComponent)
    }

    private fun maybeOfferUninstallProtection() {
        updateUninstallProtectionState()
        if (uninstallProtectionEnabled) return
        val prefs = getSharedPreferences("jawahar_file_security", MODE_PRIVATE)
        if (prefs.getBoolean("uninstall_protection_prompted", false)) return
        prefs.edit().putBoolean("uninstall_protection_prompted", true).apply()
        window.decorView.postDelayed({
            if (!isFinishing && unlocked) enableUninstallProtection()
        }, 450L)
    }

    private fun enableUninstallProtection() {
        if (devicePolicyManager.isAdminActive(adminComponent)) {
            uninstallProtectionEnabled = true
            return
        }
        externalFlowInProgress = true
        val intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN).apply {
            putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent)
            putExtra(
                DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                "Adds Android's administrator deactivation step before normal uninstall. Jawahar file requests no wipe, password-reset, camera, or password-management policy."
            )
        }
        adminActivation.launch(intent)
    }

    private fun disableUninstallProtection() {
        if (!unlocked) return
        if (devicePolicyManager.isAdminActive(adminComponent)) {
            devicePolicyManager.removeActiveAdmin(adminComponent)
        }
        window.decorView.postDelayed(::updateUninstallProtectionState, 350L)
    }
}
""")

# ----- Exact professional lock screen wording -----
security_screen = root / "app/src/main/java/com/localvault/filemanager/ui/SecurityScreen.kt"
ss = security_screen.read_text()
ss = ss.replace("Jawahar File", "Jawahar file")
ss = ss.replace(
    'Text("Locked", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)',
    'Text("Protected", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)'
)
security_screen.write_text(ss)

# ----- Professional file-manager UI refinements -----
screen = root / "app/src/main/java/com/localvault/filemanager/ui/FileManagerScreen.kt"
s = screen.read_text()
s = s.replace("Jawahar File", "Jawahar file")
s = s.replace(
'''    onImportFiles: () -> Unit,
) {''',
'''    onImportFiles: () -> Unit,
    uninstallProtectionEnabled: Boolean = false,
    onEnableUninstallProtection: () -> Unit = {},
    onDisableUninstallProtection: () -> Unit = {},
) {'''
)
s = s.replace(
'''                onChangeStorage = {
                    vm.disconnect()
                    scope.launch { drawerState.close() }
                }
            )''',
'''                onChangeStorage = {
                    vm.disconnect()
                    scope.launch { drawerState.close() }
                },
                uninstallProtectionEnabled = uninstallProtectionEnabled,
                onToggleUninstallProtection = {
                    if (uninstallProtectionEnabled) onDisableUninstallProtection()
                    else onEnableUninstallProtection()
                    scope.launch { drawerState.close() }
                },
            )'''
)
s = s.replace(
'''private fun AppDrawer(
    state: FileManagerUiState,
    onMode: (ScreenMode) -> Unit,
    onChangeStorage: () -> Unit,
) {''',
'''private fun AppDrawer(
    state: FileManagerUiState,
    onMode: (ScreenMode) -> Unit,
    onChangeStorage: () -> Unit,
    uninstallProtectionEnabled: Boolean,
    onToggleUninstallProtection: () -> Unit,
) {'''
)

# Professional drawer header/subtitle.
s = s.replace(
    'Text("Private native file manager", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurface.copy(alpha = .55f))',
    'Text("Private • Secure • Local", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)'
)

# Security card above storage/change-access controls.
needle = '''        Spacer(Modifier.weight(1f))
        TextButton(
            onClick = onChangeStorage,
            modifier = Modifier.padding(12.dp)
        ) {'''
security_card = '''        Spacer(Modifier.weight(1f))

        Surface(
            shape = RoundedCornerShape(20.dp),
            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = .62f),
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp)
        ) {
            Row(
                Modifier.fillMaxWidth().padding(14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(14.dp),
                    color = if (uninstallProtectionEnabled)
                        MaterialTheme.colorScheme.primaryContainer
                    else
                        MaterialTheme.colorScheme.surface,
                    modifier = Modifier.size(42.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            if (uninstallProtectionEnabled) Icons.Default.VerifiedUser else Icons.Outlined.Security,
                            null,
                            tint = if (uninstallProtectionEnabled)
                                MaterialTheme.colorScheme.onPrimaryContainer
                            else
                                MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text("Uninstall protection", fontWeight = FontWeight.SemiBold)
                    Text(
                        if (uninstallProtectionEnabled) "Android administrator barrier is active"
                        else "Add an extra Android deactivation step",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Switch(
                    checked = uninstallProtectionEnabled,
                    onCheckedChange = { onToggleUninstallProtection() }
                )
            }
        }

        TextButton(
            onClick = onChangeStorage,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
        ) {'''
if needle not in s:
    raise RuntimeError("Drawer footer pattern not found")
s = s.replace(needle, security_card)

# Cleaner search field with filled surface and subtle border.
old_search_tail = '''        singleLine = true,
        shape = RoundedCornerShape(18.dp),
        modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 8.dp)
    )'''
new_search_tail = '''        singleLine = true,
        shape = RoundedCornerShape(24.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = .48f),
            unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = .36f),
            focusedBorderColor = MaterialTheme.colorScheme.primary.copy(alpha = .62f),
            unfocusedBorderColor = MaterialTheme.colorScheme.outlineVariant.copy(alpha = .45f),
        ),
        modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 8.dp)
    )'''
s = s.replace(old_search_tail, new_search_tail)

# Consistent top-bar surface.
s = s.replace(
'''                    TopAppBar(
                        navigationIcon = {''',
'''                    TopAppBar(
                        colors = TopAppBarDefaults.topAppBarColors(
                            containerColor = MaterialTheme.colorScheme.surface,
                            scrolledContainerColor = MaterialTheme.colorScheme.surface,
                        ),
                        navigationIcon = {''',
1
)

# Softer dividers.
s = s.replace(
    'HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = .25f))',
    'HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = .45f))'
)

# More polished grid rhythm.
s = s.replace(
    'columns = GridCells.Adaptive(150.dp),',
    'columns = GridCells.Adaptive(156.dp),'
)
s = s.replace(
    'horizontalArrangement = Arrangement.spacedBy(8.dp),',
    'horizontalArrangement = Arrangement.spacedBy(10.dp),',
1
)
s = s.replace(
    'verticalArrangement = Arrangement.spacedBy(8.dp),',
    'verticalArrangement = Arrangement.spacedBy(10.dp),',
1
)

screen.write_text(s)

print("Prepared Jawahar file v0.5.1 professional secure build")
