from pathlib import Path
import re

root = Path("/tmp/localvault-src/LocalVaultNative")

# Gradle / package identity
p = root / "app/build.gradle.kts"
s = p.read_text()
s = s.replace('applicationId = "com.localvault.filemanager"', 'applicationId = "com.jawahar.file"')
s = s.replace('compileSdk = 37', 'compileSdk = 36')
s = s.replace('targetSdk = 37', 'targetSdk = 36')
s = s.replace('versionCode = 4', 'versionCode = 6')
s = s.replace('versionName = "0.4.0"', 'versionName = "0.5.0"')
s = s.replace('compose-bom:2026.09.00', 'compose-bom:2025.06.00')
s = s.replace('core-ktx:1.19.1', 'core-ktx:1.16.0')
s = s.replace('activity-compose:1.13.0', 'activity-compose:1.10.1')
s = s.replace('lifecycle-runtime-ktx:2.11.0', 'lifecycle-runtime-ktx:2.9.1')
s = s.replace('lifecycle-viewmodel-compose:2.11.0', 'lifecycle-viewmodel-compose:2.9.1')
s = s.replace('lifecycle-viewmodel-ktx:2.11.0', 'lifecycle-viewmodel-ktx:2.9.1')
s = s.replace(
    '    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.9.1")\n',
    '    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.9.1")\n'
    '    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.1")\n'
    '    implementation("androidx.biometric:biometric:1.1.0")\n'
    '    implementation("androidx.fragment:fragment-ktx:1.8.8")\n'
)
s = s.replace(
    'isMinifyEnabled = false\n            signingConfigs.findByName("release")?.let { signingConfig = it }',
    'isMinifyEnabled = false\n            isDebuggable = false\n            signingConfig = signingConfigs.getByName("debug")'
)
p.write_text(s)

# SAF-only privacy hardened manifest
manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text()
m = re.sub(
    r'\n\s*<!-- LocalVault\'s private/sideloaded full-access mode\..*?-->\s*\n\s*<uses-permission android:name="android\.permission\.MANAGE_EXTERNAL_STORAGE"\s*/>\s*\n',
    '\n', m, flags=re.S,
)
m = re.sub(
    r'\s*<uses-permission android:name="android\.permission\.MANAGE_EXTERNAL_STORAGE"\s*/>\s*',
    '\n', m,
)
m = m.replace('android:label="LocalVault"', 'android:label="@string/app_name"')
m = m.replace(
    'android:supportsRtl="true"',
    'android:supportsRtl="true"\n'
    '        android:usesCleartextTraffic="false"\n'
    '        android:fullBackupContent="false"\n'
    '        android:dataExtractionRules="@xml/data_extraction_rules"'
)
manifest.write_text(m)

values = root / "app/src/main/res/values"
(values / "strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Jawahar File</string>
</resources>
""")

xml_dir = root / "app/src/main/res/xml"
(xml_dir / "data_extraction_rules.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="root" path="." />
        <exclude domain="file" path="." />
        <exclude domain="database" path="." />
        <exclude domain="sharedpref" path="." />
        <exclude domain="external" path="." />
    </cloud-backup>
    <device-transfer>
        <exclude domain="root" path="." />
        <exclude domain="file" path="." />
        <exclude domain="database" path="." />
        <exclude domain="sharedpref" path="." />
        <exclude domain="external" path="." />
    </device-transfer>
</data-extraction-rules>
""")

# Strong system-authentication gate
ui_dir = root / "app/src/main/java/com/localvault/filemanager/ui"
(ui_dir / "SecurityScreen.kt").write_text("""package com.localvault.filemanager.ui

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
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(
            Modifier.fillMaxSize().padding(horizontal = 28.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Surface(
                shape = RoundedCornerShape(28.dp),
                color = MaterialTheme.colorScheme.primaryContainer,
                modifier = Modifier.size(92.dp),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(Icons.Default.Lock, null, modifier = Modifier.size(46.dp), tint = MaterialTheme.colorScheme.onPrimaryContainer)
                }
            }
            Spacer(Modifier.height(24.dp))
            Text("Jawahar File", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.ExtraBold)
            Spacer(Modifier.height(8.dp))
            Text("Locked", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            Text(
                message,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = .68f),
            )
            Spacer(Modifier.height(28.dp))
            if (authenticationAvailable) {
                Button(onClick = onUnlock, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Fingerprint, null)
                    Spacer(Modifier.width(10.dp))
                    Text("Unlock securely")
                }
            } else {
                Button(onClick = onSetUpSecurity, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Security, null)
                    Spacer(Modifier.width(10.dp))
                    Text("Set up device security")
                }
            }
            Spacer(Modifier.height(12.dp))
            TextButton(onClick = onExit) { Text("Close app") }
            Spacer(Modifier.height(20.dp))
            Text(
                "Uses Android's strong biometric or device credential. Jawahar File never stores your fingerprint, face data, or lock-screen PIN.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = .45f),
            )
        }
    }
}
""")

main = root / "app/src/main/java/com/localvault/filemanager/MainActivity.kt"
main.write_text("""package com.localvault.filemanager

import android.app.KeyguardManager
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
import com.localvault.filemanager.ui.FileManagerScreen
import com.localvault.filemanager.ui.LocalVaultTheme
import com.localvault.filemanager.ui.SecurityGate

class MainActivity : FragmentActivity() {

    private val vm: FileManagerViewModel by viewModels()

    private var unlocked by mutableStateOf(false)
    private var authenticationAvailable by mutableStateOf(true)
    private var authenticationMessage by mutableStateOf("Authenticate to open your files.")
    private var authenticationInFlight = false
    private var biometricPrompt: BiometricPrompt? = null

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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        enableEdgeToEdge()

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
                        onRequestFullAccess = { folderPicker.launch(null) },
                        onChooseFolder = { folderPicker.launch(null) },
                        onImportFiles = { importPicker.launch(arrayOf("*/*")) },
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (!unlocked) window.decorView.post { authenticate() }
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
                "A secure device screen lock or strong biometric is required before Jawahar File can open."
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
                        else -> "Authentication required to open Jawahar File."
                    }
                }

                override fun onAuthenticationFailed() {
                    authenticationMessage = "Not recognized. Try again."
                }
            }
        )
        biometricPrompt = prompt

        val builder = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Unlock Jawahar File")
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
        val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Intent(Settings.ACTION_BIOMETRIC_ENROLL).apply {
                putExtra(Settings.EXTRA_BIOMETRIC_AUTHENTICATORS_ALLOWED, authenticators())
            }
        } else {
            Intent(Settings.ACTION_SECURITY_SETTINGS)
        }
        runCatching { startActivity(intent) }
            .onFailure { startActivity(Intent(Settings.ACTION_SETTINGS)) }
    }
}
""")

# Disable direct-storage mode completely.
vm = root / "app/src/main/java/com/localvault/filemanager/FileManagerViewModel.kt"
v = vm.read_text()
v = re.sub(
    r'fun canUseDirectStorage\(\): Boolean =\s*\n?\s*Build\.VERSION\.SDK_INT >= Build\.VERSION_CODES\.R && Environment\.isExternalStorageManager\(\)',
    'fun canUseDirectStorage(): Boolean = false',
    v,
)
v = v.replace('while (list.size > MAX_RECENT) list.removeLast()', 'while (list.size > MAX_RECENT) list.removeAt(list.lastIndex)')
vm.write_text(v)

# Lifecycle-safe state and rendering optimizations.
screen = root / "app/src/main/java/com/localvault/filemanager/ui/FileManagerScreen.kt"
s = screen.read_text()
s = s.replace(
    'import android.graphics.pdf.PdfRenderer\n',
    'import android.graphics.pdf.PdfRenderer\nimport android.util.LruCache\n'
)
s = s.replace(
    'import androidx.compose.runtime.*\n',
    'import androidx.compose.runtime.*\nimport androidx.lifecycle.compose.collectAsStateWithLifecycle\n'
)
s = s.replace(
    '    val state by vm.ui.collectAsState()',
    '    val state by vm.ui.collectAsStateWithLifecycle()'
)

# Clean SAF-only access screen.
start = s.index('@Composable\nprivate fun AccessScreen(')
end = s.index('@Composable\nprivate fun AccessCard(', start)
access = '''@Composable
private fun AccessScreen(onRequestFullAccess: () -> Unit, onChooseFolder: () -> Unit) {
    Surface(Modifier.fillMaxSize()) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
            verticalArrangement = Arrangement.Center
        ) {
            Surface(
                color = MaterialTheme.colorScheme.primaryContainer,
                shape = RoundedCornerShape(22.dp),
                modifier = Modifier.size(80.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        Icons.Default.Folder,
                        null,
                        modifier = Modifier.size(44.dp),
                        tint = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }
            Spacer(Modifier.height(20.dp))
            Text(
                "Jawahar File",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.ExtraBold
            )
            Spacer(Modifier.height(7.dp))
            Text(
                "Choose the folder you want Jawahar File to manage. Android grants access only to the location you explicitly select.",
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = .7f)
            )
            Spacer(Modifier.height(28.dp))
            AccessCard(
                icon = Icons.Default.FolderOpen,
                title = "Choose storage folder",
                body = "Pick Internal storage, Download, Documents, an SD-card folder, or another location Android permits. Read/write access is remembered across restarts.",
                button = "Choose folder",
                onClick = onChooseFolder,
            )
            Spacer(Modifier.height(18.dp))
            Text(
                "Jawahar File does not request Android's broad all-files permission. Your selected storage stays under Android's system permission control.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = .5f)
            )
        }
    }
}

'''
s = s[:start] + access + s[end:]

s = s.replace('"LocalVault"', '"Jawahar File"')
s = s.replace("Build LocalVault's local index", "Build Jawahar File's local index")
s = s.replace("LocalVault keeps the newest copy", "Jawahar File keeps the newest copy")
s = s.replace("LocalVault Trash", "Jawahar File Trash")
s = s.replace("Pick a folder and LocalVault keeps", "Pick a folder and Jawahar File keeps")
s = s.replace(
    'Text("Native file manager", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurface.copy(alpha = .55f))',
    'Text("Private native file manager", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurface.copy(alpha = .55f))'
)

# Avoid sorting/filtering large lists on unrelated recompositions.
s = s.replace(
'''    val entries = vm.visibleEntries()
    when {''',
'''    val entries = remember(
        state.screenMode, state.entries, state.favorites, state.recent, state.trash,
        state.duplicateGroups, state.indexedEntries, state.selectedCategory, state.showHidden,
        state.query, state.sortMode, state.sortAscending
    ) { vm.visibleEntries() }
    when {'''
)

# Lazy container reuse hints.
s = s.replace(
    'gridItems(entries, key = { it.locator }) { entry ->',
    'gridItems(entries, key = { it.locator }, contentType = { if (it.isDirectory) "folder" else fileKind(it.name, it.mimeType, false) }) { entry ->'
)
s = s.replace(
    'items(entries, key = { it.locator }) { entry ->',
    'items(entries, key = { it.locator }, contentType = { if (it.isDirectory) "folder" else fileKind(it.name, it.mimeType, false) }) { entry ->',
    1
)

cache = '''
private object ThumbnailCache {
    private val maxKb =
        ((Runtime.getRuntime().maxMemory() / 1024L) / 16L).coerceIn(4_096L, 32_768L).toInt()

    private val cache = object : LruCache<String, Bitmap>(maxKb) {
        override fun sizeOf(key: String, value: Bitmap): Int =
            (value.byteCount / 1024).coerceAtLeast(1)
    }

    fun get(key: String): Bitmap? = cache.get(key)
    fun put(key: String, bitmap: Bitmap) {
        cache.put(key, bitmap)
    }
}

'''
pos = s.index('@Composable\nprivate fun FileVisual')
s = s[:pos] + cache + s[pos:]

old = '''    if (isImage && uri != null) {
        val context = LocalContext.current
        val bitmap by produceState<Bitmap?>(initialValue = null, uri, entry.modified, entry.size) {
            value = withContext(Dispatchers.IO) { decodeSampledBitmap(context, uri, maxDimension = 320) }
        }'''
new = '''    if (isImage && uri != null) {
        val context = LocalContext.current
        val cacheKey = "${uri}|${entry.modified}|${entry.size}"
        val bitmap by produceState<Bitmap?>(initialValue = ThumbnailCache.get(cacheKey), cacheKey) {
            if (value == null) {
                value = withContext(Dispatchers.IO) {
                    decodeSampledBitmap(context, uri, maxDimension = 320)
                }
                value?.let { ThumbnailCache.put(cacheKey, it) }
            }
        }'''
s = s.replace(old, new)
screen.write_text(s)

file_utils = root / "app/src/main/java/com/localvault/filemanager/util/FileUtils.kt"
fu = file_utils.read_text()
if "import java.util.Locale" not in fu:
    fu = fu.replace("package com.localvault.filemanager.util\\n", "package com.localvault.filemanager.util\\n\\nimport java.util.Locale\\n")
fu = fu.replace('String.format("%.1f %s", value, units[group])', 'String.format(Locale.getDefault(), "%.1f %s", value, units[group])')
file_utils.write_text(fu)

trash = root / "app/src/main/java/com/localvault/filemanager/service/TrashService.kt"
t = trash.read_text().replace(
    "LocalVault's Trash folder cannot be trashed.",
    "Jawahar File's Trash folder cannot be trashed."
)
trash.write_text(t)

print("Prepared Jawahar File v0.5.0")
