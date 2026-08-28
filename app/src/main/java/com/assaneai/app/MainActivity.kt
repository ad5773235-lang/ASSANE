package com.assaneai.app

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.util.Base64
import androidx.activity.result.contract.ActivityResultContracts
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.Image
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.Code
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.Memory
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Terminal
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.AttachFile
import androidx.compose.material.icons.filled.Image as ImageIcon
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.assaneai.app.data.BackendClient
import com.assaneai.app.data.RegistrationChallenge
import com.assaneai.app.data.BackendException
import com.assaneai.app.data.Session
import com.assaneai.app.model.AssaneDeployment
import com.assaneai.app.model.AssaneEvent
import com.assaneai.app.model.AssanePreferences
import com.assaneai.app.model.AssaneTask
import com.assaneai.app.model.AssaneTier
import com.assaneai.app.model.AssaneUser
import com.assaneai.app.ui.theme.AssaneAITheme
import com.assaneai.app.ui.theme.AssaneBackground
import com.assaneai.app.ui.theme.AssaneBlue
import com.assaneai.app.ui.theme.AssaneMuted
import com.assaneai.app.ui.theme.AssaneSurface
import com.assaneai.app.ui.theme.AssaneSurfaceAlt
import com.assaneai.app.ui.theme.AssaneText
import com.assaneai.app.ui.theme.SenegalGreen
import com.assaneai.app.ui.theme.SenegalRed
import com.assaneai.app.ui.theme.SenegalYellow
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { AssaneRoot(applicationContext) }
    }
}

@Composable
private fun AssaneRoot(context: Context) {
    val preferences = remember { context.getSharedPreferences("assane_session", Context.MODE_PRIVATE) }
    var backendUrl by remember { mutableStateOf(preferences.getString("backend_url", BuildConfig.ASSANE_BACKEND_URL) ?: BuildConfig.ASSANE_BACKEND_URL) }
    val client = remember(backendUrl) { BackendClient(backendUrl) }
    var selectedTheme by remember { mutableStateOf(preferences.getString("theme", "dark") ?: "dark") }
    var showBackendConfig by rememberSaveable { mutableStateOf(false) }
    var token by remember { mutableStateOf(preferences.getString("token", null)) }
    var user by remember { mutableStateOf(loadUser(preferences)) }
    var error by remember { mutableStateOf("") }

    AssaneAITheme(darkTheme = selectedTheme != "light") {
    if (token.isNullOrBlank() || user == null) {
            AuthScreen(
                client = client,
                backendUrl = backendUrl,
                error = error,
                onError = { error = it },
                onConfigureBackend = { showBackendConfig = true },
                onSession = { session ->
                token = session.token
                user = session.user
                saveSession(preferences, session)
                error = ""
            },
        )
        if (showBackendConfig) {
            BackendConfigDialog(
                currentUrl = backendUrl,
                onDismiss = { showBackendConfig = false },
                onSave = { newUrl ->
                    backendUrl = newUrl.trimEnd('/')
                    preferences.edit().putString("backend_url", backendUrl).apply()
                    showBackendConfig = false
                    error = "Adresse backend enregistrée."
                },
            )
        }
    } else {
        MainWorkspace(
            client = client,
            token = token!!,
            user = user!!,
            onLogout = {
                preferences.edit().clear().apply()
                token = null
                user = null
            },
            onPreferencesSaved = { saved ->
                selectedTheme = saved.theme
                preferences.edit().putString("theme", saved.theme).putString("background", saved.background).apply()
            },
        )
    }
    }
}

@Composable
private fun AuthScreen(
    client: BackendClient,
    backendUrl: String,
    error: String,
    onError: (String) -> Unit,
    onConfigureBackend: () -> Unit,
    onSession: (Session) -> Unit,
) {
    var registerMode by rememberSaveable { mutableStateOf(true) }
    var firstName by rememberSaveable { mutableStateOf("") }
    var lastName by rememberSaveable { mutableStateOf("") }
    var email by rememberSaveable { mutableStateOf("") }
    var phone by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var confirmPassword by rememberSaveable { mutableStateOf("") }
    var otpCode by rememberSaveable { mutableStateOf("") }
    var challenge by remember { mutableStateOf<RegistrationChallenge?>(null) }
    var loading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Box(Modifier.fillMaxSize().background(AssaneBackground)) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 42.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("Assane AI", color = AssaneText, fontSize = 30.sp, fontWeight = FontWeight.Bold)
            Text("L’ordinateur qui travaille avec toi", color = AssaneMuted, fontSize = 14.sp)
            Spacer(Modifier.height(30.dp))
            Surface(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(24.dp), color = AssaneSurface) {
                Column(Modifier.padding(22.dp)) {
                    if (challenge != null) {
                        Text("Vérifie ton numéro", color = AssaneText, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                        Text("Un code temporaire a été envoyé au ${challenge!!.maskedPhone}.", color = AssaneMuted, fontSize = 13.sp)
                        Spacer(Modifier.height(18.dp))
                        AuthField("Code SMS à 6 chiffres", otpCode, { otpCode = it.filter(Char::isDigit).take(6) })
                        Text("Ton inscription est enregistrée temporairement. Le compte sera activé après vérification du code.", color = AssaneMuted, fontSize = 11.sp)
                        if (error.isNotBlank()) {
                            Spacer(Modifier.height(10.dp))
                            Text(error, color = SenegalRed, fontSize = 13.sp)
                        }
                        Spacer(Modifier.height(16.dp))
                        Button(
                            enabled = !loading && otpCode.length == 6,
                            onClick = {
                                scope.launch {
                                    loading = true
                                    try {
                                        onSession(client.verifyRegistrationOtp(challenge!!.otpRequestId, otpCode))
                                    } catch (ex: Exception) {
                                        onError(if (ex is BackendException) ex.message.orEmpty() else "Impossible de vérifier le code")
                                    } finally { loading = false }
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(16.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen),
                        ) {
                            if (loading) CircularProgressIndicator(Modifier.size(20.dp), color = Color.White, strokeWidth = 2.dp)
                            else Text("Vérifier et activer", fontWeight = FontWeight.Bold)
                        }
                        TextButton(
                            enabled = !loading,
                            onClick = {
                                scope.launch {
                                    loading = true
                                    try {
                                        challenge = client.resendRegistrationOtp(challenge!!.pendingSignupId)
                                        otpCode = ""
                                        onError("")
                                    } catch (ex: Exception) {
                                        onError(if (ex is BackendException) ex.message.orEmpty() else "Impossible de renvoyer le code")
                                    } finally { loading = false }
                                }
                            },
                            modifier = Modifier.align(Alignment.CenterHorizontally),
                        ) { Text("Renvoyer un code", color = SenegalYellow) }
                        TextButton(onClick = { challenge = null; otpCode = "" }, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                            Text("Modifier les informations", color = AssaneMuted)
                        }
                    } else {
                        Text(if (registerMode) "Créer ton compte" else "Se connecter", color = AssaneText, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                        Text("Ton compte est sauvegardé pour tes prochaines sessions.", color = AssaneMuted, fontSize = 13.sp)
                        Spacer(Modifier.height(18.dp))
                        if (registerMode) {
                            AuthField("Prénom", firstName, { firstName = it })
                            AuthField("Nom", lastName, { lastName = it })
                            AuthField("Numéro de téléphone", phone, { phone = it })
                        }
                        AuthField("E-mail", email, { email = it })
                        AuthField("Mot de passe", password, { password = it }, password = true)
                        if (registerMode) {
                            AuthField("Confirmer le mot de passe", confirmPassword, { confirmPassword = it }, password = true)
                        }
                        if (error.isNotBlank()) {
                            Spacer(Modifier.height(10.dp))
                            Text(error, color = SenegalRed, fontSize = 13.sp)
                        }
                        Spacer(Modifier.height(16.dp))
                        Button(
                            enabled = !loading,
                            onClick = {
                                if (registerMode && password != confirmPassword) {
                                    onError("Les deux mots de passe ne correspondent pas.")
                                } else if (registerMode && (firstName.isBlank() || lastName.isBlank() || email.isBlank() || phone.isBlank())) {
                                    onError("Remplis tous les champs obligatoires avant de continuer.")
                                } else {
                                    scope.launch {
                                        loading = true
                                        try {
                                            if (registerMode) {
                                                challenge = client.startRegistration(firstName, lastName, email, phone, password)
                                            } else {
                                                onSession(client.login(email, password))
                                            }
                                        } catch (ex: Exception) {
                                            onError(if (ex is BackendException) ex.message.orEmpty() else "Impossible de joindre le backend Assane AI")
                                        } finally { loading = false }
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(16.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen),
                        ) {
                            if (loading) CircularProgressIndicator(Modifier.size(20.dp), color = Color.White, strokeWidth = 2.dp)
                            else Text(if (registerMode) "Enregistrer et recevoir le code" else "Se connecter", fontWeight = FontWeight.Bold)
                        }
                        TextButton(onClick = { registerMode = !registerMode; onError("") }, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                            Text(if (registerMode) "J’ai déjà un compte" else "Créer un nouveau compte", color = SenegalYellow)
                        }
                    }
                }
            }
            Spacer(Modifier.height(20.dp))
            Text("Aucun compte Google n’est nécessaire.", color = AssaneMuted, fontSize = 12.sp)
            TextButton(onClick = onConfigureBackend) { Text("Configurer l’adresse du backend", color = AssaneBlue, fontSize = 12.sp) }
        }
    }
}

@Composable
private fun BackendConfigDialog(currentUrl: String, onDismiss: () -> Unit, onSave: (String) -> Unit) {
    var value by rememberSaveable(currentUrl) { mutableStateOf(currentUrl) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Adresse du backend") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Si tu utilises un téléphone, 127.0.0.1 désigne le téléphone. Utilise l’adresse IPv4 de ton PC sur le même Wi‑Fi.", color = AssaneMuted, fontSize = 12.sp)
                OutlinedTextField(
                    value = value,
                    onValueChange = { value = it },
                    label = { Text("URL Assane AI Core") },
                    placeholder = { Text("http://192.168.1.20:8000") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Annuler") } },
        confirmButton = {
            Button(
                enabled = value.trim().startsWith("http://") || value.trim().startsWith("https://"),
                onClick = { onSave(value.trim()) },
            ) { Text("Enregistrer") }
        },
    )
}

@Composable
private fun AuthField(label: String, value: String, onValueChange: (String) -> Unit, password: Boolean = false) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp),
        singleLine = true,
        visualTransformation = if (password) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MainWorkspace(client: BackendClient, token: String, user: AssaneUser, onLogout: () -> Unit, onPreferencesSaved: (AssanePreferences) -> Unit) {
    var prompt by rememberSaveable { mutableStateOf("") }
    var activeTask by remember { mutableStateOf<AssaneTask?>(null) }
    var deployment by remember { mutableStateOf<AssaneDeployment?>(null) }
    var selectedEvent by remember { mutableStateOf<AssaneEvent?>(null) }
    var showSettings by remember { mutableStateOf(false) }
    var showProfile by remember { mutableStateOf(false) }
    var showTiers by remember { mutableStateOf(false) }
    var showImportMenu by remember { mutableStateOf(false) }
    var showBrowser by remember { mutableStateOf(false) }
    var showDeployment by remember { mutableStateOf(false) }
    var showPreview by remember { mutableStateOf(false) }
    var previewUrl by remember { mutableStateOf("") }
    var previewId by remember { mutableStateOf("") }
    var previewQr by remember { mutableStateOf<androidx.compose.ui.graphics.ImageBitmap?>(null) }
    var error by remember { mutableStateOf("") }
    var importMessage by remember { mutableStateOf("") }
    var sending by remember { mutableStateOf(false) }
    var generatingImage by remember { mutableStateOf(false) }
    var androidBuildStatus by remember { mutableStateOf("") }
    var androidArtifactId by remember { mutableStateOf("") }
    var androidArtifactName by remember { mutableStateOf("assane-app.apk") }
    var projectType by remember { mutableStateOf("") }
    var workspaceSection by rememberSaveable { mutableStateOf("home") }
    var historyTasks by remember { mutableStateOf<List<AssaneTask>>(emptyList()) }
    var historyLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val logoutAndClear: () -> Unit = {
        scope.launch {
            runCatching { client.logout(token) }
            onLogout()
        }
    }
    val downloadLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/vnd.android.package-archive")) { uri ->
        if (uri != null && androidArtifactId.isNotBlank()) {
            scope.launch {
                try {
                    val bytes = client.downloadArtifact(token, androidArtifactId)
                    context.contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                    androidBuildStatus = "Artefact enregistré sur le téléphone."
                } catch (ex: Exception) {
                    androidBuildStatus = "Téléchargement impossible : ${ex.message ?: "erreur inconnue"}"
                }
            }
        }
    }
    val importLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            scope.launch {
                try {
                    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                        ?: throw IllegalStateException("Fichier illisible")
                    val name = uri.lastPathSegment?.substringAfterLast('/') ?: "import.bin"
                    val mime = context.contentResolver.getType(uri) ?: "application/octet-stream"
                    client.uploadFile(token, name, mime, bytes, activeTask?.id ?: "general")
                    importMessage = "Fichier importé dans le workspace Assane AI."
                } catch (ex: Exception) {
                    importMessage = "Import impossible : ${ex.message ?: "erreur inconnue"}"
                }
            }
        }
    }

    LaunchedEffect(activeTask?.id) {
        val id = activeTask?.id ?: return@LaunchedEffect
        projectType = runCatching { client.detectProject(token, id).optString("type") }.getOrDefault("")
        while (activeTask?.status in setOf("queued", "planning", "running")) {
            delay(2500)
            try {
                activeTask = client.getTask(token, id)
            } catch (ex: Exception) {
                error = ex.message ?: "Erreur de suivi de tâche"
                break
            }
        }
    }

    LaunchedEffect(workspaceSection, token) {
        if (workspaceSection == "history") {
            historyLoading = true
            historyTasks = runCatching { client.listTasks(token) }.getOrElse {
                error = it.message ?: "Impossible de charger l’historique"
                emptyList()
            }
            historyLoading = false
        }
    }

    Scaffold(
        containerColor = AssaneBackground,
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        AssaneLogo(size = 34)
                        Spacer(Modifier.width(10.dp))
                        Column {
                            Text("Ordinateur d’Assane", color = AssaneText, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                            Text("Espace de travail sécurisé", color = AssaneMuted, fontSize = 11.sp)
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { showBrowser = true }) {
                        Icon(Icons.Default.Memory, "Ouvrir l’Ordinateur Assane", tint = SenegalYellow)
                    }
                    TextButton(onClick = { showProfile = true }) {
                        Box(Modifier.size(30.dp).clip(CircleShape).background(SenegalGreen), contentAlignment = Alignment.Center) {
                            Text(user.firstName.take(1).uppercase(), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        }
                        Spacer(Modifier.width(5.dp))
                        Text("Profil", color = AssaneText, fontSize = 12.sp)
                    }
                    IconButton(onClick = logoutAndClear) { Icon(Icons.Default.Logout, "Se déconnecter", tint = AssaneMuted) }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = AssaneBackground),
            )
        },
        bottomBar = {
            WorkspaceBottomNavigation(
                selected = workspaceSection,
                onSelect = { section ->
                    if (section == "settings") showSettings = true else workspaceSection = section
                },
            )
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding).padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item {
                WorkspaceNavigation(
                    selected = workspaceSection,
                    onSelect = { workspaceSection = it },
                )
            }
            if (workspaceSection == "history") {
                item {
                    HistoryPanel(
                        tasks = historyTasks,
                        loading = historyLoading,
                        onOpenTask = { task ->
                            scope.launch {
                                activeTask = runCatching { client.getTask(token, task.id) }.getOrDefault(task)
                                workspaceSection = "computer"
                            }
                        },
                    )
                }
            } else if (workspaceSection == "computer") {
                item {
                    ComputerWorkspaceSummary(
                        task = activeTask,
                        projectType = projectType,
                        onOpenBrowser = { showBrowser = true },
                        onImport = { showImportMenu = true },
                        onPreview = { showPreview = true },
                        onPublish = { showDeployment = true },
                    )
                }
            } else if (workspaceSection == "artifacts") {
                item {
                    ArtifactsSummary(
                        artifactId = androidArtifactId,
                        artifactName = androidArtifactName,
                        buildStatus = androidBuildStatus,
                        onDownload = { if (androidArtifactId.isNotBlank()) downloadLauncher.launch(androidArtifactName) },
                    )
                }
            } else {
            item {
                Spacer(Modifier.height(4.dp))
                WelcomeCard(user)
            }
            item {
                DashboardOverviewCard(
                    task = activeTask,
                    projectType = projectType,
                    onOpenComputer = { showBrowser = true },
                    onOpenBrowser = { showBrowser = true },
                    onImport = { showImportMenu = true },
                    onGenerateImage = {
                        if (prompt.isNotBlank()) {
                            scope.launch {
                                generatingImage = true
                                importMessage = ""
                                try {
                                    val result = client.generateImage(token, prompt.trim())
                                    importMessage = if (result.optBoolean("ok", false)) "Image générée et préparée comme artefact." else "La génération d’image a échoué."
                                } catch (ex: Exception) {
                                    importMessage = "Génération impossible : ${ex.message ?: "erreur inconnue"}"
                                } finally {
                                    generatingImage = false
                                }
                            }
                        } else {
                            importMessage = "Écris d’abord une demande pour générer une image."
                        }
                    },
                )
            }
            item {
                PromptCard(
                    prompt = prompt,
                    onPromptChange = { prompt = it },
                    sending = sending,
                    onImport = { showImportMenu = true },
                    onBrowser = { showBrowser = true },
                    onGenerateImage = {
                        if (prompt.isNotBlank()) {
                            scope.launch {
                                generatingImage = true
                                importMessage = ""
                                try {
                                    val result = client.generateImage(token, prompt.trim())
                                    importMessage = if (result.optBoolean("ok", false)) "Image générée et préparée comme artefact." else "La génération d’image a échoué."
                                } catch (ex: Exception) {
                                    importMessage = "Génération impossible : ${ex.message ?: "erreur inconnue"}"
                                } finally {
                                    generatingImage = false
                                }
                            }
                        }
                    },
                    generatingImage = generatingImage,
                    onSend = {
                        if (prompt.isBlank()) return@PromptCard
                        scope.launch {
                            sending = true
                            error = ""
                            try {
                                activeTask = client.createTask(token, prompt.trim())
                                prompt = ""
                            } catch (ex: Exception) {
                                error = ex.message ?: "Le backend Assane AI ne répond pas"
                            } finally {
                                sending = false
                            }
                        }
                    },
                )
            }
            if (error.isNotBlank()) {
                item { ErrorCard(error) }
            }
            if (importMessage.isNotBlank()) {
                item { StatusCard(importMessage) }
            }
            activeTask?.let { task ->
                item {
                    ComputerCard(
                        task = task,
                        onOpenComputer = { showBrowser = true },
                        onStop = {
                            scope.launch {
                                try {
                                    activeTask = client.stopTask(token, task.id)
                                } catch (ex: Exception) {
                                    error = ex.message ?: "Impossible d’arrêter la tâche"
                                }
                            }
                        },
                        onContinue = {
                            scope.launch {
                                try {
                                    activeTask = client.continueTask(token, task.id)
                                } catch (ex: Exception) {
                                    error = ex.message ?: "Impossible de reprendre la tâche"
                                }
                            }
                        },
                    )
                }
                if (task.status == "succeeded") {
                    item {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(onClick = {
                                scope.launch {
                                    try {
                                        val response = client.createPreview(token, task.id)
                                        previewUrl = response.optString("url")
                                        previewId = response.optJSONObject("preview")?.optString("id").orEmpty()
                                        val qrData = response.optJSONObject("preview")?.optString("qr_data_url", "") ?: ""
                                        previewQr = if (qrData.contains(",")) {
                                            val bytes = Base64.decode(qrData.substringAfter(","), Base64.DEFAULT)
                                            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
                                        } else null
                                        showPreview = previewUrl.isNotBlank()
                                    } catch (ex: Exception) {
                                        error = ex.message ?: "Impossible de préparer l’aperçu"
                                    }
                                }
                            }, modifier = Modifier.weight(1f)) {
                                Icon(Icons.Default.Visibility, "Aperçu")
                                Spacer(Modifier.width(6.dp))
                                Text("Aperçu")
                            }
                            OutlinedButton(onClick = { showDeployment = true }, modifier = Modifier.weight(1f)) {
                                Icon(Icons.Default.Cloud, "Publication")
                                Spacer(Modifier.width(6.dp))
                                Text("Publier")
                            }
                        }
                        if (androidBuildStatus.isNotBlank()) {
                            Spacer(Modifier.height(8.dp))
                            Text(androidBuildStatus, color = AssaneMuted, fontSize = 12.sp)
                        }
                        if (androidArtifactId.isNotBlank()) {
                            OutlinedButton(onClick = { downloadLauncher.launch(androidArtifactName) }, modifier = Modifier.fillMaxWidth()) {
                                Icon(Icons.Default.Download, "Télécharger l’artefact")
                                Spacer(Modifier.width(6.dp))
                                Text("Télécharger ${androidArtifactName.substringAfterLast('.', "artefact").uppercase()}")
                            }
                        }
                        if (projectType == "android") {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                TextButton(onClick = {
                                    scope.launch {
                                        androidBuildStatus = "Construction de l’APK…"
                                    try {
                                        val response = client.buildAndroid(token, task.id, "apk", "debug")
                                        val artifact = response.optJSONObject("result")?.optJSONObject("artifact")
                                        androidArtifactId = artifact?.optString("id").orEmpty()
                                        androidArtifactName = artifact?.optString("filename", "assane-app.apk") ?: "assane-app.apk"
                                        androidBuildStatus = if (response.optBoolean("ok", false)) "APK de test prêt dans les artefacts Assane AI." else "APK non produit : ${response.optJSONObject("result")?.optString("error", "échec du build") }"
                                    } catch (ex: Exception) {
                                        androidBuildStatus = "APK indisponible : ${ex.message ?: "SDK Android ou runner manquant"}"
                                    }
                                    }
                                }) { Text("Construire APK") }
                                TextButton(onClick = {
                                scope.launch {
                                    androidBuildStatus = "Construction de l’AAB release…"
                                    try {
                                        val response = client.buildAndroid(token, task.id, "aab", "release")
                                        val artifact = response.optJSONObject("result")?.optJSONObject("artifact")
                                        androidArtifactId = artifact?.optString("id").orEmpty()
                                        androidArtifactName = artifact?.optString("filename", "assane-app.aab") ?: "assane-app.aab"
                                        androidBuildStatus = if (response.optBoolean("ok", false)) "AAB prêt. La publication Play Store exige encore une confirmation et un compte configuré." else "AAB non produit : ${response.optJSONObject("result")?.optString("error", "échec du build") }"
                                    } catch (ex: Exception) {
                                        androidBuildStatus = "AAB indisponible : ${ex.message ?: "SDK Android, signature ou runner manquant"}"
                                    }
                                }
                                }) { Text("Construire AAB") }
                            }
                        }
                    }
                }
                item { EventTimeline(task.events, onLongPress = { selectedEvent = it }) }
            }
            }
            item { Spacer(Modifier.height(28.dp)) }
        }
    }
    selectedEvent?.let { event ->
        ResponseActionDialog(
            event = event,
            onDismiss = { selectedEvent = null },
        )
    }
    if (showBrowser) {
        ComputerDialog(
            client = client,
            token = token,
            task = activeTask,
            onDismiss = { showBrowser = false },
            onResult = { importMessage = it },
            onImport = { showImportMenu = true },
            onPreview = {
                activeTask?.let { current ->
                    scope.launch {
                        try {
                            val response = client.createPreview(token, current.id)
                            previewUrl = response.optString("url")
                            previewId = response.optJSONObject("preview")?.optString("id").orEmpty()
                            showPreview = previewUrl.isNotBlank()
                        } catch (ex: Exception) {
                            error = ex.message ?: "Impossible de préparer l’aperçu"
                        }
                    }
                } ?: run { importMessage = "L’aperçu nécessite une tâche active." }
            },
            onBuild = { format, variant ->
                activeTask?.let { current ->
                    scope.launch {
                        androidBuildStatus = "Construction ${format.uppercase()}…"
                        try {
                            val response = client.buildAndroid(token, current.id, format, variant)
                            val artifact = response.optJSONObject("result")?.optJSONObject("artifact")
                            androidArtifactId = artifact?.optString("id").orEmpty()
                            androidArtifactName = artifact?.optString("filename", "assane-app.$format") ?: "assane-app.$format"
                            androidBuildStatus = if (response.optBoolean("ok", false)) "${format.uppercase()} prêt dans les artefacts Assane AI." else "${format.uppercase()} non produit."
                        } catch (ex: Exception) {
                            androidBuildStatus = "Build indisponible : ${ex.message ?: "runner ou SDK manquant"}"
                        }
                    }
                } ?: run { importMessage = "Le build nécessite une tâche active." }
            },
            onPublish = { showDeployment = true },
        )
    }
    if (showPreview) {
        PreviewDialog(
            url = previewUrl,
            qr = previewQr,
            onDismiss = { showPreview = false },
            onRevoke = {
                scope.launch {
                    try {
                        if (previewId.isNotBlank()) client.revokePreview(token, previewId)
                        showPreview = false
                        importMessage = "Aperçu révoqué."
                    } catch (ex: Exception) {
                        error = ex.message ?: "Impossible de révoquer l’aperçu"
                    }
                }
            },
        )
    }
    if (showDeployment) {
        activeTask?.let { task ->
            DeploymentDialog(
                client = client,
                token = token,
                task = task,
                deployment = deployment,
                onDismiss = { showDeployment = false },
                onUpdated = { deployment = it },
                onError = { error = it },
            )
        }
    }
    if (showImportMenu) {
        ImportMenuDialog(
            onDismiss = { showImportMenu = false },
            onPickFiles = {
                showImportMenu = false
                importLauncher.launch(arrayOf("*/*"))
            },
        )
    }
    if (showProfile) {
        ProfileScreen(
            user = user,
            onDismiss = { showProfile = false },
            onOpenBrowser = { showProfile = false; showBrowser = true },
            onOpenAppearance = { showProfile = false; showSettings = true },
            onOpenTiers = { showProfile = false; showTiers = true },
            onInfo = { importMessage = it },
            onLogout = logoutAndClear,
        )
    }
    if (showTiers) {
        TierSelectionDialog(
            client = client,
            token = token,
            onDismiss = { showTiers = false },
            onInfo = { importMessage = it },
        )
    }
    if (showSettings) {
        ProfileSettingsDialog(
            client = client,
            token = token,
            onDismiss = { showSettings = false },
            onSaved = onPreferencesSaved,
        )
    }
}

@Composable
private fun WorkspaceBottomNavigation(selected: String, onSelect: (String) -> Unit) {
    Surface(color = AssaneSurfaceAlt, shadowElevation = 8.dp) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 6.dp, vertical = 5.dp), horizontalArrangement = Arrangement.SpaceEvenly) {
            listOf(
                "home" to (Icons.Default.Memory to "Accueil"),
                "history" to (Icons.Default.Terminal to "Historique"),
                "computer" to (Icons.Default.Code to "Espace Work"),
                "artifacts" to (Icons.Default.Download to "Artefacts"),
                "settings" to (Icons.Default.Settings to "Paramètres"),
            ).forEach { (key, item) ->
                val active = selected == key || (key == "settings" && selected != "settings" && false)
                TextButton(
                    onClick = { onSelect(key) },
                    modifier = Modifier.weight(1f),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 2.dp, vertical = 3.dp),
                    colors = ButtonDefaults.textButtonColors(contentColor = if (active) SenegalGreen else AssaneMuted),
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(item.first, item.second, modifier = Modifier.size(19.dp))
                        Text(item.second, fontSize = 9.sp, maxLines = 1)
                    }
                }
            }
        }
    }
}

@Composable
private fun WorkspaceNavigation(selected: String, onSelect: (String) -> Unit) {
    Surface(shape = RoundedCornerShape(18.dp), color = AssaneSurfaceAlt) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(5.dp),
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            listOf("home" to "Accueil", "history" to "Historique", "computer" to "Ordinateur").forEach { (key, label) ->
                val active = selected == key
                TextButton(
                    onClick = { onSelect(key) },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.textButtonColors(
                        containerColor = if (active) AssaneSurface else Color.Transparent,
                        contentColor = if (active) SenegalYellow else AssaneMuted,
                    ),
                ) { Text(label, fontSize = 12.sp, fontWeight = if (active) FontWeight.Bold else FontWeight.Normal) }
            }
        }
    }
}

@Composable
private fun ArtifactsSummary(artifactId: String, artifactName: String, buildStatus: String, onDownload: () -> Unit) {
    Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
        Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Download, "Artefacts", tint = SenegalYellow)
                Spacer(Modifier.width(8.dp))
                Column {
                    Text("Artefacts Assane AI", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                    Text("Fichiers réellement générés par les tâches", color = AssaneMuted, fontSize = 12.sp)
                }
            }
            if (buildStatus.isNotBlank()) Text(buildStatus, color = AssaneMuted, fontSize = 12.sp)
            if (artifactId.isBlank()) {
                Text("Aucun artefact disponible pour la tâche active.", color = AssaneMuted, fontSize = 13.sp)
            } else {
                Surface(shape = RoundedCornerShape(14.dp), color = AssaneSurfaceAlt) {
                    Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Code, "Artefact", tint = SenegalGreen)
                        Spacer(Modifier.width(9.dp))
                        Column(Modifier.weight(1f)) {
                            Text(artifactName, color = AssaneText, fontSize = 13.sp)
                            Text("Identifiant : $artifactId", color = AssaneMuted, fontSize = 10.sp)
                        }
                        TextButton(onClick = onDownload) { Text("Télécharger", color = SenegalYellow, fontSize = 11.sp) }
                    }
                }
            }
        }
    }
}

@Composable
private fun HistoryPanel(tasks: List<AssaneTask>, loading: Boolean, onOpenTask: (AssaneTask) -> Unit) {
    Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
        Column(Modifier.fillMaxWidth().padding(16.dp)) {
            Text("Historique", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
            Text("Tâches réellement enregistrées dans ton compte", color = AssaneMuted, fontSize = 12.sp)
            Spacer(Modifier.height(12.dp))
            when {
                loading -> Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(Modifier.size(18.dp), color = SenegalGreen, strokeWidth = 2.dp)
                    Spacer(Modifier.width(8.dp))
                    Text("Chargement de l’historique…", color = AssaneMuted, fontSize = 13.sp)
                }
                tasks.isEmpty() -> Text("Aucune tâche enregistrée pour le moment.", color = AssaneMuted, fontSize = 13.sp)
                else -> tasks.forEach { task ->
                    Surface(
                        modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
                        shape = RoundedCornerShape(14.dp),
                        color = AssaneSurfaceAlt,
                    ) {
                        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(task.prompt.take(100), color = AssaneText, fontSize = 13.sp, maxLines = 2)
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    "${task.status} · ${task.eventCount} événement(s)" + (task.lastEventMessage?.let { " · $it" } ?: ""),
                                    color = AssaneMuted,
                                    fontSize = 11.sp,
                                    maxLines = 2,
                                )
                            }
                            TextButton(onClick = { onOpenTask(task) }) { Text("Ouvrir", color = SenegalYellow, fontSize = 12.sp) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ComputerWorkspaceSummary(
    task: AssaneTask?,
    projectType: String,
    onOpenBrowser: () -> Unit,
    onImport: () -> Unit,
    onPreview: () -> Unit,
    onPublish: () -> Unit,
) {
    Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
        Column(Modifier.fillMaxWidth().padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Memory, "Ordinateur d’Assane", tint = SenegalYellow)
                Spacer(Modifier.width(8.dp))
                Column(Modifier.weight(1f)) {
                    Text("Ordinateur d’Assane", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                    Text("Workspace réel · ${projectType.ifBlank { "projet non détecté" }}", color = AssaneMuted, fontSize = 12.sp)
                }
                Box(Modifier.size(9.dp).clip(CircleShape).background(SenegalGreen))
            }
            Spacer(Modifier.height(12.dp))
            Surface(shape = RoundedCornerShape(14.dp), color = AssaneSurfaceAlt) {
                Column(Modifier.fillMaxWidth().padding(12.dp)) {
                    Text(
                        task?.let { "${it.status} · ${it.currentStep}" } ?: "Aucune tâche active",
                        color = AssaneText,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                    )
                    Text(
                        task?.lastEventMessage ?: "Lance une tâche pour remplir l’ordinateur d’Assane.",
                        color = AssaneMuted,
                        fontSize = 12.sp,
                        maxLines = 2,
                    )
                }
            }
            Spacer(Modifier.height(12.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                WorkspaceToolButton(Icons.Default.Visibility, "Navigateur", onOpenBrowser, Modifier.weight(1f))
                WorkspaceToolButton(Icons.Default.AttachFile, "Fichiers", onImport, Modifier.weight(1f))
                WorkspaceToolButton(Icons.Default.Visibility, "Aperçu", onPreview, Modifier.weight(1f))
                WorkspaceToolButton(Icons.Default.Cloud, "Publier", onPublish, Modifier.weight(1f))
            }
            Spacer(Modifier.height(8.dp))
            Text("Éditeur · Terminal · Inspection · Artefacts · Build", color = AssaneMuted, fontSize = 11.sp)
        }
    }
}

@Composable
private fun WorkspaceToolButton(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, onClick: () -> Unit, modifier: Modifier = Modifier) {
    OutlinedButton(onClick = onClick, modifier = modifier, contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 4.dp, vertical = 8.dp)) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(icon, label, modifier = Modifier.size(17.dp), tint = SenegalYellow)
            Text(label, fontSize = 10.sp, maxLines = 1)
        }
    }
}

@Composable
private fun WelcomeCard(user: AssaneUser) {
    Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
        Row(Modifier.fillMaxWidth().padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(48.dp).clip(CircleShape).background(SenegalGreen), contentAlignment = Alignment.Center) {
                Text(user.firstName.take(1).uppercase(), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 20.sp)
            }
            Spacer(Modifier.width(13.dp))
            Column(Modifier.weight(1f)) {
                Text("Bonjour ${user.firstName}", color = AssaneText, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Text("Que veux-tu qu’Assane fasse pour toi ?", color = AssaneMuted, fontSize = 13.sp)
            }
            Icon(Icons.Default.Cloud, "Backend connecté", tint = SenegalGreen)
        }
    }
}

@Composable
private fun PromptCard(prompt: String, onPromptChange: (String) -> Unit, sending: Boolean, onImport: () -> Unit, onBrowser: () -> Unit, onGenerateImage: () -> Unit, generatingImage: Boolean, onSend: () -> Unit) {
    Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
        Column(Modifier.padding(16.dp)) {
            Text("Nouvelle tâche", color = AssaneText, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            Spacer(Modifier.height(10.dp))
            OutlinedTextField(
                value = prompt,
                onValueChange = onPromptChange,
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
                placeholder = { Text("Exemple : analyse ce projet et prépare un APK…", color = AssaneMuted) },
            )
            Spacer(Modifier.height(8.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                TextButton(onClick = onImport) {
                    Icon(Icons.Default.AttachFile, "Importer")
                    Spacer(Modifier.width(4.dp))
                    Text("Importer")
                }
                TextButton(onClick = onBrowser) {
                    Icon(Icons.Default.Folder, "Navigateur")
                    Spacer(Modifier.width(4.dp))
                    Text("Navigateur")
                }
                TextButton(onClick = onGenerateImage, enabled = prompt.isNotBlank() && !generatingImage) {
                    Icon(Icons.Default.ImageIcon, "Générer une image")
                    Spacer(Modifier.width(4.dp))
                    Text(if (generatingImage) "Génération…" else "Image")
                }
                Spacer(Modifier.weight(1f))
                Text("Les clés restent sur le backend", color = AssaneMuted, fontSize = 11.sp)
                Spacer(Modifier.width(12.dp))
                Button(onClick = onSend, enabled = !sending && prompt.isNotBlank(), shape = RoundedCornerShape(14.dp), colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen)) {
                    if (sending) CircularProgressIndicator(Modifier.size(18.dp), color = Color.White, strokeWidth = 2.dp)
                    else Icon(Icons.Default.Send, "Envoyer")
                    Spacer(Modifier.width(6.dp))
                    Text("Lancer")
                }
            }
        }
    }
}

@Composable
private fun StatusCard(message: String) {
    Surface(shape = RoundedCornerShape(18.dp), color = AssaneSurfaceAlt) {
        Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.CheckCircle, "Information", tint = SenegalGreen)
            Spacer(Modifier.width(10.dp))
            Text(message, color = AssaneText, fontSize = 13.sp)
        }
    }
}


@Composable
private fun DeploymentDialog(
    client: BackendClient,
    token: String,
    task: AssaneTask,
    deployment: AssaneDeployment?,
    onDismiss: () -> Unit,
    onUpdated: (AssaneDeployment) -> Unit,
    onError: (String) -> Unit,
) {
    var projectName by rememberSaveable { mutableStateOf("assane-projet") }
    var target by rememberSaveable { mutableStateOf("vercel") }
    var loading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(deployment?.id, deployment?.status) {
        val id = deployment?.id ?: return@LaunchedEffect
        while (deployment?.status == "deploying") {
            delay(3000)
            try {
                onUpdated(client.getDeployment(token, id))
            } catch (ex: Exception) {
                onError(ex.message ?: "Impossible de suivre la publication")
                break
            }
        }
    }

    AlertDialog(
        onDismissRequest = { if (!loading) onDismiss() },
        title = { Text(if (deployment == null) "Préparer la publication" else "Publication Assane AI") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                if (deployment == null) {
                    Text("Assane va analyser le workspace, vérifier les limites puis attendre ta confirmation.", color = AssaneMuted)
                    Text("Choisir la destination", color = AssaneText, fontWeight = FontWeight.Bold)
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        listOf("vercel" to "Site web", "github" to "Dépôt de code", "cloudflare_pages" to "Pages web", "google_play" to "Play Store").forEach { (value, label) ->
                            OutlinedButton(
                                onClick = { target = value },
                                colors = ButtonDefaults.outlinedButtonColors(
                                    containerColor = if (target == value) SenegalGreen.copy(alpha = 0.18f) else Color.Transparent,
                                ),
                            ) { Text(label, fontSize = 11.sp) }
                        }
                    }
                    OutlinedTextField(
                        value = projectName,
                        onValueChange = { projectName = it },
                        label = { Text(if (target == "github") "Dépôt : propriétaire/nom" else if (target == "google_play") "Nom du paquet Android" else "Nom du projet") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                } else {
                    Text("Projet : ${deployment.projectName}", color = AssaneText, fontWeight = FontWeight.Bold)
                    Text("Fichiers préparés : ${deployment.fileCount}", color = AssaneMuted)
                    when (deployment.status) {
                        "awaiting_confirmation" -> Text("Aucune publication ne sera lancée sans ton accord explicite.", color = SenegalYellow)
                        "deploying" -> Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(Modifier.size(18.dp), color = SenegalYellow, strokeWidth = 2.dp)
                            Spacer(Modifier.width(8.dp))
                            Text("Assane vérifie la publication…", color = AssaneMuted)
                        }
                        "succeeded" -> Text("Publication vérifiée et accessible.", color = SenegalGreen)
                        else -> Text(deployment.error ?: "La publication n’a pas été vérifiée.", color = SenegalRed)
                    }
                    deployment.url?.let { Text(it, color = AssaneBlue, fontSize = 12.sp) }
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !loading) { Text("Fermer") }
        },
        confirmButton = {
            when {
                deployment == null -> Button(
                    enabled = !loading && projectName.isNotBlank(),
                    onClick = {
                        scope.launch {
                            loading = true
                            try {
                                onUpdated(client.requestDeployment(token, task.id, projectName.trim(), target))
                            } catch (ex: Exception) {
                                onError(ex.message ?: "Impossible de préparer la publication")
                            } finally {
                                loading = false
                            }
                        }
                    },
                ) { Text(if (loading) "Préparation…" else "Préparer") }
                deployment.status == "awaiting_confirmation" -> Button(
                    onClick = {
                        scope.launch {
                            loading = true
                            try {
                                onUpdated(client.confirmDeployment(token, deployment.id))
                            } catch (ex: Exception) {
                                onError(ex.message ?: "Impossible de confirmer la publication")
                            } finally {
                                loading = false
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen),
                ) { Text("Confirmer") }
                else -> TextButton(onClick = onDismiss) { Text("Terminé") }
            }
        },
    )
}

@Composable
private fun ComputerCard(task: AssaneTask, onOpenComputer: () -> Unit, onStop: () -> Unit, onContinue: () -> Unit) {
    val working = task.status in setOf("queued", "planning", "running")
    val interrupted = task.status in setOf("stopped", "connection_lost", "paused")
    Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurfaceAlt) {
        Column(Modifier.padding(18.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(42.dp).clip(RoundedCornerShape(12.dp)).background(Color(0xFF242B3A)), contentAlignment = Alignment.Center) {
                    Icon(Icons.Default.Memory, "Ordinateur Assane", tint = SenegalYellow)
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text("Ordinateur d’Assane", color = AssaneText, fontWeight = FontWeight.Bold)
                    Text(if (working) "Assane réfléchit…" else task.status, color = if (working) SenegalYellow else SenegalGreen, fontSize = 12.sp)
                }
                if (working) CircularProgressIndicator(Modifier.size(22.dp), color = SenegalYellow, strokeWidth = 2.dp)
                else Icon(Icons.Default.CheckCircle, "Terminé", tint = SenegalGreen)
            }
            Spacer(Modifier.height(14.dp))
            Text(task.prompt, color = AssaneText, fontSize = 14.sp)
            Spacer(Modifier.height(12.dp))
            LinearProgressIndicator(
                progress = { if (working) 0.55f else if (task.status == "succeeded") 1f else 0.1f },
                modifier = Modifier.fillMaxWidth().height(6.dp).clip(CircleShape),
                color = SenegalGreen,
                trackColor = Color(0xFF303747),
            )
            Spacer(Modifier.height(8.dp))
                            Text(
                    when (task.status) {
                        "connection_lost" -> "Connexion perdue. Envoyez un message pour continuer."
                        "stopped", "paused" -> "Assane est arrêté. Envoyez un message pour continuer."
                        else -> "Étape : ${task.currentStep}"
                    },
                    color = if (task.status == "connection_lost") SenegalRed else AssaneMuted,
                    fontSize = 12.sp,
                )
                Spacer(Modifier.height(10.dp))
                OutlinedButton(onClick = onOpenComputer, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Memory, "Ouvrir l’Ordinateur Assane")
                    Spacer(Modifier.width(7.dp))
                    Text("Ouvrir l’Ordinateur Assane")
                }
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (working) {
                        OutlinedButton(onClick = onStop) { Text("Arrêter") }
                    }
                    if (interrupted) {
                        Button(onClick = onContinue, colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen)) {
                            Text("Continuer")
                        }
                    }
                }

        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun EventTimeline(events: List<AssaneEvent>, onLongPress: (AssaneEvent) -> Unit) {
    val context = LocalContext.current
    Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
        Column(Modifier.padding(18.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Terminal, "Journal", tint = AssaneBlue)
                Spacer(Modifier.width(8.dp))
                Text("Journal de travail", color = AssaneText, fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.height(12.dp))
            if (events.isEmpty()) Text("En attente des événements du backend…", color = AssaneMuted, fontSize = 13.sp)
            events.forEachIndexed { index, event ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(vertical = 6.dp)
                        .combinedClickable(onClick = {}, onLongClick = { onLongPress(event) }),
                    verticalAlignment = Alignment.Top,
                ) {
                    Box(Modifier.size(9.dp).clip(CircleShape).background(if (event.kind == "error") SenegalRed else SenegalGreen))
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f)) {
                        Text(event.message, color = AssaneText, fontSize = 13.sp)
                        if (index < events.lastIndex) Spacer(Modifier.height(2.dp))
                    }
                    TextButton(onClick = {
                        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                        clipboard.setPrimaryClip(ClipData.newPlainText("Réponse Assane AI", event.message))
                    }) {
                        Icon(Icons.Default.ContentCopy, "Copier", tint = AssaneMuted, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("Copier", color = AssaneMuted, fontSize = 11.sp)
                    }
                }
            }
        }
    }
}

@Composable
private fun ErrorCard(error: String) {
    Surface(shape = RoundedCornerShape(18.dp), color = Color(0xFF351E24)) {
        Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Warning, "Erreur", tint = SenegalRed)
            Spacer(Modifier.width(10.dp))
            Text(error, color = Color(0xFFFFC4C4), fontSize = 13.sp)
        }
    }
}

@Composable
private fun AssaneLogo(size: Int) {
    Box(Modifier.size(size.dp).clip(RoundedCornerShape((size / 4).dp)).background(SenegalGreen), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Box(Modifier.size((size / 3).dp).clip(CircleShape).background(SenegalYellow))
            Box(Modifier.size((size / 7).dp).clip(CircleShape).background(SenegalRed))
        }
    }
}

@Composable
private fun ResponseActionDialog(event: AssaneEvent, onDismiss: () -> Unit) {
    val context = LocalContext.current
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Actions sur la réponse") },
        text = {
            Column {
                TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) {
                    Text("Demander à Assane", modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                    Icon(Icons.Default.ArrowForward, "Demander")
                }
                TextButton(onClick = {
                    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    clipboard.setPrimaryClip(ClipData.newPlainText("Réponse Assane AI", event.message))
                    onDismiss()
                }, modifier = Modifier.fillMaxWidth()) {
                    Text("Copier", modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                    Icon(Icons.Default.ContentCopy, "Copier")
                }
                TextButton(onClick = {
                    val send = Intent(Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(Intent.EXTRA_TEXT, event.message)
                    }
                    context.startActivity(Intent.createChooser(send, "Partager la réponse"))
                    onDismiss()
                }, modifier = Modifier.fillMaxWidth()) {
                    Text("Partager", modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                    Icon(Icons.Default.ArrowForward, "Partager")
                }
                TextButton(onClick = {
                    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    clipboard.setPrimaryClip(ClipData.newPlainText("Texte sélectionné", event.message))
                    onDismiss()
                }, modifier = Modifier.fillMaxWidth()) {
                    Text("Sélectionner le texte", modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                    Icon(Icons.Default.ContentCopy, "Sélectionner")
                }
                TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) {
                    Text("Signaler", modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                    Icon(Icons.Default.Warning, "Signaler")
                }
            }
        },
        confirmButton = {},
    )
}

@Composable
private fun PreviewDialog(url: String, qr: androidx.compose.ui.graphics.ImageBitmap?, onDismiss: () -> Unit, onRevoke: () -> Unit) {
    val context = LocalContext.current
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Aperçu Assane AI") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Voici un lien temporaire pour voir le résultat. Il expire automatiquement et peut être révoqué.", color = AssaneMuted, fontSize = 12.sp)
                OutlinedTextField(value = url, onValueChange = {}, readOnly = true, modifier = Modifier.fillMaxWidth(), singleLine = true)
                qr?.let { bitmap ->
                    Image(bitmap = bitmap, contentDescription = "QR code de l’aperçu", modifier = Modifier.size(180.dp).align(Alignment.CenterHorizontally))
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = {
                        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                        clipboard.setPrimaryClip(ClipData.newPlainText("Aperçu Assane AI", url))
                    }) {
                        Icon(Icons.Default.ContentCopy, "Copier le lien")
                        Spacer(Modifier.width(5.dp))
                        Text("Copier")
                    }
                    TextButton(onClick = onRevoke) { Text("Révoquer", color = SenegalRed) }
                }
            }
        },
        confirmButton = { Button(onClick = onDismiss) { Text("Fermer") } },
    )
}

@Composable
private fun ComputerDialog(
    client: BackendClient,
    token: String,
    task: AssaneTask?,
    onDismiss: () -> Unit,
    onResult: (String) -> Unit,
    onImport: () -> Unit = {},
    onPreview: () -> Unit = {},
    onBuild: (format: String, variant: String) -> Unit = { _, _ -> },
    onPublish: () -> Unit = {},
) {
    var selectedApp by rememberSaveable { mutableStateOf("Navigateur") }
    var appMenu by remember { mutableStateOf(false) }
    var url by rememberSaveable { mutableStateOf("https://") }
    var loading by remember { mutableStateOf(false) }
    var resultTitle by remember { mutableStateOf("") }
    var resultText by remember { mutableStateOf("") }
    var previews by remember { mutableStateOf<List<androidx.compose.ui.graphics.ImageBitmap>>(emptyList()) }
    var savedImages by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false)) {
        Surface(Modifier.fillMaxSize(), color = AssaneBackground) {
            Column(Modifier.fillMaxSize().padding(horizontal = 18.dp, vertical = 18.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onDismiss) { Icon(Icons.Default.Close, "Fermer", tint = AssaneText) }
                    Column(Modifier.weight(1f)) {
                        Text("Ordinateur d’Assane", color = AssaneText, fontSize = 21.sp, fontWeight = FontWeight.Bold)
                        Text("Espace isolé · ${task?.currentStep ?: "prêt"}", color = AssaneMuted, fontSize = 12.sp)
                    }
                    Box {
                        OutlinedButton(onClick = { appMenu = !appMenu }) {
                            Icon(
                                when (selectedApp) {
                                    "Navigateur", "Fichiers" -> Icons.Default.Folder
                                    "Éditeur" -> Icons.Default.Code
                                    "Aperçu" -> Icons.Default.Visibility
                                    "Publication" -> Icons.Default.Cloud
                                    else -> Icons.Default.Terminal
                                },
                                "Application active",
                            )
                            Spacer(Modifier.width(6.dp))
                            Text(selectedApp)
                        }
                        if (appMenu) {
                            Surface(
                                modifier = Modifier.width(210.dp).align(Alignment.TopEnd).padding(top = 52.dp),
                                shape = RoundedCornerShape(14.dp),
                                color = AssaneSurface,
                                shadowElevation = 8.dp,
                            ) {
                                Column(Modifier.padding(8.dp)) {
                                    Text("Sélectionnez une application", color = AssaneMuted, fontSize = 12.sp, modifier = Modifier.padding(8.dp))
                                    listOf("Navigateur", "Fichiers", "Éditeur", "Terminal", "Aperçu", "Build", "Publication").forEach { app ->
                                        TextButton(onClick = { selectedApp = app; appMenu = false }, modifier = Modifier.fillMaxWidth()) {
                                            Text(app, color = if (selectedApp == app) SenegalYellow else AssaneText, modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                Spacer(Modifier.height(12.dp))
                Surface(Modifier.fillMaxWidth().weight(1f), shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
                    when (selectedApp) {
                        "Navigateur" -> Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Folder, "Navigateur Assane", tint = AssaneBlue)
                                Spacer(Modifier.width(8.dp))
                                Column {
                                    Text("Navigateur Assane", color = AssaneText, fontWeight = FontWeight.Bold)
                                    Text("Inspection de sites publics, liens, images et documents autorisés", color = AssaneMuted, fontSize = 12.sp)
                                }
                            }
                            OutlinedTextField(value = url, onValueChange = { url = it }, label = { Text("Adresse à inspecter") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                            Button(
                                enabled = !loading && url.startsWith("http"),
                                onClick = {
                                    scope.launch {
                                        loading = true
                                        errorMessage = ""
                                        resultTitle = ""
                                        resultText = ""
                                        previews = emptyList()
                                        savedImages = false
                                        try {
                                            val inspected = client.openBrowser(token, url.trim())
                                            val extracted = client.extractImages(token, url.trim(), taskId = task?.id ?: "general", limit = 8, save = false)
                                            resultTitle = inspected.optString("title").ifBlank { inspected.optString("url", url) }
                                            resultText = inspected.optString("text").take(1200)
                                            val decoded = buildList {
                                                val images = extracted.optJSONArray("images") ?: return@buildList
                                                for (index in 0 until images.length()) {
                                                    val encoded = images.optJSONObject(index)?.optString("preview_data_url", "") ?: ""
                                                    if (encoded.startsWith("data:image/") && encoded.contains(",")) {
                                                        val bytes = Base64.decode(encoded.substringAfter(","), Base64.DEFAULT)
                                                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.let { add(it.asImageBitmap()) }
                                                    }
                                                }
                                            }
                                            previews = decoded
                                            onResult("Navigateur : ${resultTitle.ifBlank { url }} inspecté ; ${decoded.size} image(s) affichée(s).")
                                        } catch (ex: Exception) {
                                            errorMessage = ex.message ?: "Inspection impossible"
                                            onResult("Navigateur indisponible : $errorMessage")
                                        } finally {
                                            loading = false
                                        }
                                    }
                                },
                                shape = RoundedCornerShape(14.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen),
                            ) { if (loading) CircularProgressIndicator(Modifier.size(18.dp), color = Color.White, strokeWidth = 2.dp) else Text("Inspecter avec Assane") }
                            if (resultTitle.isNotBlank()) Text(resultTitle, color = AssaneText, fontWeight = FontWeight.Bold)
                            if (resultText.isNotBlank()) Text(resultText, color = AssaneMuted, fontSize = 12.sp)
                            if (previews.isNotEmpty()) {
                                Text("Images publiques trouvées : ${previews.size}", color = AssaneMuted, fontSize = 12.sp)
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    previews.take(6).forEachIndexed { index, bitmap ->
                                        Image(bitmap = bitmap, contentDescription = "Image publique ${index + 1}", modifier = Modifier.size(76.dp).clip(RoundedCornerShape(10.dp)))
                                    }
                                }
                                if (savedImages) {
                                    Text("Images conservées dans les artefacts Assane AI.", color = SenegalGreen, fontSize = 12.sp)
                                } else {
                                    TextButton(enabled = !loading, onClick = {
                                        scope.launch {
                                            loading = true
                                            try {
                                                val stored = client.extractImages(token, url.trim(), taskId = task?.id ?: "general", limit = 8, save = true)
                                                savedImages = stored.optBoolean("persisted", false)
                                                onResult(if (savedImages) "Les images inspectées ont été conservées dans les artefacts." else "Les images n’ont pas été conservées.")
                                            } catch (ex: Exception) {
                                                errorMessage = ex.message ?: "Conservation impossible"
                                            } finally {
                                                loading = false
                                            }
                                        }
                                    }) { Text("Conserver les images") }
                                }
                            }
                            if (errorMessage.isNotBlank()) Text(errorMessage, color = SenegalRed, fontSize = 12.sp)
                            Spacer(Modifier.weight(1f))
                            Text("Les secrets et clés restent sur le backend. Les URLs privées ou dangereuses sont refusées.", color = AssaneMuted, fontSize = 11.sp)
                        }
                        "Fichiers" -> Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Default.Folder, "Fichiers Assane", tint = SenegalYellow, modifier = Modifier.size(34.dp))
                            Text("Fichiers du workspace", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                            Text("Importe des documents, images, APK ou autres fichiers dans l’espace de la tâche.", color = AssaneMuted)
                            Surface(Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp), color = AssaneSurfaceAlt) {
                                Column(Modifier.padding(14.dp)) {
                                    Text("Workspace actif", color = AssaneText, fontWeight = FontWeight.Bold)
                                    Text(task?.id ?: "Aucune tâche active", color = AssaneMuted, fontSize = 12.sp)
                                    Text("Les fichiers importés restent liés à ton compte.", color = AssaneMuted, fontSize = 12.sp)
                                }
                            }
                            Button(onClick = onImport, colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen)) {
                                Icon(Icons.Default.AttachFile, "Importer")
                                Spacer(Modifier.width(7.dp))
                                Text("Importer dans le workspace")
                            }
                        }
                        "Aperçu" -> Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Default.Visibility, "Aperçu Assane", tint = SenegalYellow, modifier = Modifier.size(34.dp))
                            Text("Aperçu du résultat", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                            Text("Assane prépare un lien temporaire et un QR code lorsque le workspace contient un résultat compatible.", color = AssaneMuted)
                            Button(enabled = task != null, onClick = onPreview, colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen)) {
                                Icon(Icons.Default.Visibility, "Préparer l’aperçu")
                                Spacer(Modifier.width(7.dp))
                                Text("Préparer l’aperçu")
                            }
                            if (task == null) Text("Une tâche active est nécessaire.", color = AssaneMuted, fontSize = 12.sp)
                        }
                        "Build" -> Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Default.Code, "Build Assane", tint = SenegalYellow, modifier = Modifier.size(34.dp))
                            Text("Build et artefacts", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                            Text("Les boutons lancent un build réel côté backend. La disponibilité dépend du runner et du SDK configurés.", color = AssaneMuted)
                            OutlinedButton(enabled = task != null, onClick = { onBuild("apk", "debug") }, modifier = Modifier.fillMaxWidth()) { Text("Construire APK debug") }
                            OutlinedButton(enabled = task != null, onClick = { onBuild("aab", "release") }, modifier = Modifier.fillMaxWidth()) { Text("Construire AAB release") }
                            if (task == null) Text("Une tâche active est nécessaire.", color = AssaneMuted, fontSize = 12.sp)
                        }
                        "Publication" -> Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Default.Cloud, "Publication Assane", tint = SenegalYellow, modifier = Modifier.size(34.dp))
                            Text("Publication", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                            Text("Assane prépare la publication, puis demande une confirmation avant toute action sensible.", color = AssaneMuted)
                            Button(enabled = task != null, onClick = onPublish, colors = ButtonDefaults.buttonColors(containerColor = SenegalGreen)) {
                                Icon(Icons.Default.Cloud, "Préparer la publication")
                                Spacer(Modifier.width(7.dp))
                                Text("Préparer une publication")
                            }
                            if (task == null) Text("Une tâche active est nécessaire.", color = AssaneMuted, fontSize = 12.sp)
                        }
                        "Éditeur" -> Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Default.Code, "Éditeur Assane", tint = SenegalYellow, modifier = Modifier.size(34.dp))
                            Text("Éditeur Assane", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                            Text("Le workspace de la tâche est la zone de travail isolée d’Assane. Les fichiers créés ou importés apparaissent ensuite comme artefacts.", color = AssaneMuted)
                            Surface(Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp), color = AssaneSurfaceAlt) {
                                Column(Modifier.padding(14.dp)) {
                                    Text("Workspace actif", color = AssaneText, fontWeight = FontWeight.Bold)
                                    Text(task?.id ?: "Aucune tâche active", color = AssaneMuted, fontSize = 12.sp)
                                    Text("Étape : ${task?.currentStep ?: "en attente"}", color = AssaneMuted, fontSize = 12.sp)
                                }
                            }
                            Text("L’édition et l’exécution suivent les permissions du backend et du runner configuré.", color = AssaneMuted, fontSize = 12.sp)
                        }
                        else -> Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Default.Terminal, "Terminal Assane", tint = SenegalYellow, modifier = Modifier.size(34.dp))
                            Text("Terminal Assane", color = AssaneText, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                            Text("Journal des actions exécutées dans le workspace. Assane n’exécute pas de commande directement depuis l’application Android.", color = AssaneMuted)
                            task?.events?.takeLast(8)?.forEach { event ->
                                Text("${event.kind}  ·  ${event.message}", color = AssaneText, fontSize = 12.sp)
                            } ?: Text("Aucune tâche active.", color = AssaneMuted, fontSize = 12.sp)
                        }
                    }
                }
                Spacer(Modifier.height(10.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                    TextButton(onClick = onDismiss) { Text("Fermer") }
                }
            }
        }
    }
}

@Composable
private fun BrowserDialog(client: BackendClient, token: String, onDismiss: () -> Unit, onResult: (String) -> Unit) {
    var url by rememberSaveable { mutableStateOf("https://") }
    var loading by remember { mutableStateOf(false) }
    var siteTitle by remember { mutableStateOf("") }
    var errorMessage by remember { mutableStateOf("") }
    var previews by remember { mutableStateOf<List<androidx.compose.ui.graphics.ImageBitmap>>(emptyList()) }
    var savedImages by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Navigateur Assane") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Assane inspecte les sites publics et peut afficher les images accessibles.", color = AssaneMuted, fontSize = 12.sp)
                OutlinedTextField(value = url, onValueChange = { url = it }, label = { Text("Adresse du site") }, singleLine = true)
                if (siteTitle.isNotBlank()) Text(siteTitle, color = AssaneText, fontWeight = FontWeight.Bold)
                if (previews.isNotEmpty()) {
                    Text("Images publiques trouvées : ${previews.size}", color = AssaneMuted, fontSize = 12.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        previews.take(4).forEachIndexed { index, bitmap ->
                            Image(bitmap = bitmap, contentDescription = "Image publique ${index + 1}", modifier = Modifier.size(76.dp).clip(RoundedCornerShape(10.dp)))
                        }
                    }
                    if (!savedImages) {
                        TextButton(
                            onClick = {
                                scope.launch {
                                    loading = true
                                    try {
                                        val stored = client.extractImages(token, url.trim(), limit = 8, save = true)
                                        savedImages = stored.optBoolean("persisted", false)
                                        onResult(if (savedImages) "Les images ont été conservées dans tes artefacts." else "Les images n’ont pas été conservées.")
                                    } catch (ex: Exception) {
                                        errorMessage = ex.message ?: "conservation impossible"
                                    } finally {
                                        loading = false
                                    }
                                }
                            },
                            enabled = !loading,
                        ) { Text("Conserver les images") }
                    } else {
                        Text("Images conservées dans les artefacts Assane AI.", color = SenegalGreen, fontSize = 12.sp)
                    }
                }
                if (errorMessage.isNotBlank()) Text(errorMessage, color = SenegalRed, fontSize = 12.sp)
                if (loading) Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(Modifier.size(18.dp), color = SenegalYellow, strokeWidth = 2.dp)
                    Spacer(Modifier.width(8.dp))
                    Text("Assane inspecte la page…", color = AssaneMuted, fontSize = 12.sp)
                }
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Fermer") } },
        confirmButton = {
            Button(enabled = !loading && url.startsWith("http"), onClick = {
                if (siteTitle.isNotBlank() || previews.isNotEmpty()) {
                    onDismiss()
                } else {
                    scope.launch {
                        loading = true
                        errorMessage = ""
                        try {
                            val inspected = client.openBrowser(token, url.trim())
                            val extracted = client.extractImages(token, url.trim(), limit = 8, save = false)
                            siteTitle = inspected.optString("title", inspected.optString("url"))
                            val decoded = buildList {
                                val items = extracted.optJSONArray("images") ?: return@buildList
                                for (index in 0 until items.length()) {
                                    val encoded = items.optJSONObject(index)?.optString("preview_data_url", "") ?: ""
                                    if (encoded.startsWith("data:image/") && encoded.contains(",")) {
                                        val bytes = Base64.decode(encoded.substringAfter(","), Base64.DEFAULT)
                                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.let { add(it.asImageBitmap()) }
                                    }
                                }
                            }
                            previews = decoded
                            savedImages = false
                            onResult(if (inspected.optBoolean("ok", false)) "Site inspecté : ${siteTitle.ifBlank { url }} ; ${decoded.size} image(s) affichée(s)." else "Inspection du site impossible.")
                        } catch (ex: Exception) {
                            errorMessage = ex.message ?: "erreur inconnue"
                            onResult("Navigateur indisponible : $errorMessage")
                        } finally {
                            loading = false
                        }
                    }
                }
            }) { Text(if (loading) "Inspection…" else if (siteTitle.isNotBlank() || previews.isNotEmpty()) "Terminé" else "Inspecter") }
        },
    )
}

@Composable
private fun ImportMenuDialog(onDismiss: () -> Unit, onPickFiles: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Ajouter à la conversation") },
        text = {
            Column {
                TextButton(onClick = onPickFiles, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.AttachFile, "Fichiers locaux")
                    Spacer(Modifier.width(10.dp))
                    Text("Ajouter des fichiers locaux")
                }
                TextButton(onClick = onPickFiles, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.ImageIcon, "Photos")
                    Spacer(Modifier.width(10.dp))
                    Text("Photos et images")
                }
                TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Folder, "Fichiers récents")
                    Spacer(Modifier.width(10.dp))
                    Text("Fichiers récents")
                }
                TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Terminal, "Tâches récentes")
                    Spacer(Modifier.width(10.dp))
                    Text("Tâches récentes")
                }
                TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Settings, "Compétences")
                    Spacer(Modifier.width(10.dp))
                    Text("Compétences")
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Fermer") } },
    )
}

@Composable
private fun ProfileScreen(
    user: AssaneUser,
    onDismiss: () -> Unit,
    onOpenBrowser: () -> Unit,
    onOpenAppearance: () -> Unit,
    onOpenTiers: () -> Unit,
    onInfo: (String) -> Unit,
    onLogout: () -> Unit,
) {
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false)) {
        Surface(Modifier.fillMaxSize(), color = AssaneBackground) {
            Column(Modifier.fillMaxSize().padding(horizontal = 18.dp, vertical = 20.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onDismiss) { Icon(Icons.Default.ArrowBack, "Retour", tint = AssaneText) }
                    Text("Profil Assane AI", color = AssaneText, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.height(16.dp))
                Surface(shape = RoundedCornerShape(22.dp), color = AssaneSurface) {
                    Row(Modifier.fillMaxWidth().padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(58.dp).clip(CircleShape).background(SenegalGreen), contentAlignment = Alignment.Center) {
                            Text(user.firstName.take(1).uppercase(), color = Color.White, fontSize = 24.sp, fontWeight = FontWeight.Bold)
                        }
                        Spacer(Modifier.width(14.dp))
                        Column {
                            Text("${user.firstName} ${user.lastName}".trim(), color = AssaneText, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                            Text(user.email, color = AssaneMuted, fontSize = 13.sp)
                            if (user.phone.isNotBlank()) Text(user.phone, color = AssaneMuted, fontSize = 12.sp)
                        }
                    }
                }
                Spacer(Modifier.height(18.dp))
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
                    item { ProfileSectionLabel("Ton espace") }
                    item { ProfileRow(Icons.Default.Terminal, "Tâches planifiées", "Gérer les tâches à venir") { onInfo("Les tâches planifiées seront disponibles lorsque le planificateur serveur sera activé.") } }
                    item { ProfileRow(Icons.Default.Folder, "Connaissance", "Sources et fichiers de ton workspace") { onInfo("La connaissance reste limitée aux sources et artefacts autorisés dans ton espace.") } }
                    item { ProfileRow(Icons.Default.Folder, "Navigateur Assane", "Inspecter des sites et images publics", onOpenBrowser) }
                    item { ProfileRow(Icons.Default.Code, "Compétences", "Skills disponibles pour les tâches") { onInfo("Les Skills actifs sont chargés par le backend Assane AI.") } }
                    item { ProfileSectionLabel("Capacités Assane") }
                    item { ProfileRow(Icons.Default.Memory, "Niveau Assane", "Moyen, Fiable ou Élevé selon ton besoin", onOpenTiers) }
                    item { ProfileSectionLabel("Connexions") }
                    item { ProfileRow(Icons.Default.Cloud, "Connecteurs", "Services autorisés côté serveur") { onInfo("Les clés restent sur le backend ; aucun secret n’est affiché ici.") } }
                    item { ProfileRow(Icons.Default.Cloud, "Intégrations", "Publication et outils externes") { onInfo("Les intégrations dépendent de la configuration du serveur et de ta confirmation.") } }
                    item { ProfileSectionLabel("Préférences") }
                    item { ProfileRow(Icons.Default.Settings, "Langue", "Français — autres langues selon disponibilité") { onInfo("La langue principale actuelle est le français.") } }
                    item { ProfileRow(Icons.Default.Settings, "Apparence", "Thème, fond et instructions personnalisées", onOpenAppearance) }
                    item { ProfileRow(Icons.Default.Close, "Cache", "Effacer les données locales de cette session") { onInfo("Pour effacer la session locale, utilise Se déconnecter.") } }
                }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(onClick = onLogout, modifier = Modifier.fillMaxWidth(), colors = ButtonDefaults.outlinedButtonColors(contentColor = SenegalRed)) {
                    Icon(Icons.Default.Logout, "Se déconnecter")
                    Spacer(Modifier.width(8.dp))
                    Text("Se déconnecter")
                }
            }
        }
    }
}

@Composable
private fun ProfileSectionLabel(label: String) {
    Text(label.uppercase(), color = SenegalYellow, fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 8.dp, bottom = 2.dp))
}

@Composable
private fun ProfileRow(icon: androidx.compose.ui.graphics.vector.ImageVector, title: String, subtitle: String, onClick: () -> Unit) {
    TextButton(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Icon(icon, title, tint = AssaneBlue)
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f), horizontalAlignment = Alignment.Start) {
            Text(title, color = AssaneText, fontSize = 15.sp)
            Text(subtitle, color = AssaneMuted, fontSize = 11.sp)
        }
        Icon(Icons.Default.ArrowForward, "Ouvrir", tint = AssaneMuted, modifier = Modifier.size(18.dp))
    }
}

@Composable
private fun ProfileSettingsDialog(client: BackendClient, token: String, onDismiss: () -> Unit, onSaved: (AssanePreferences) -> Unit) {
    var preferences by remember { mutableStateOf(AssanePreferences()) }
    var loaded by remember { mutableStateOf(false) }
    var saving by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        try {
            preferences = client.getPreferences(token)
        } catch (_: Exception) {
            // Les valeurs par défaut restent utilisables si le backend est momentanément indisponible.
        } finally {
            loaded = true
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Profil personnalisé") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                if (!loaded) {
                    CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp)
                } else {
                    Text("Thème", color = AssaneMuted, fontSize = 12.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("dark", "light").forEach { value ->
                            OutlinedButton(onClick = { preferences = preferences.copy(theme = value) }) {
                                Text(if (value == "dark") "Sombre" else "Clair")
                            }
                        }
                    }
                    Text("Fond", color = AssaneMuted, fontSize = 12.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("default", "green", "night").forEach { value ->
                            OutlinedButton(onClick = { preferences = preferences.copy(background = value) }) {
                                Text(value.replaceFirstChar { it.uppercase() })
                            }
                        }
                    }
                    OutlinedTextField(
                        value = preferences.customInstructions,
                        onValueChange = { preferences = preferences.copy(customInstructions = it) },
                        label = { Text("Ajouter une instruction à Assane") },
                        placeholder = { Text("Exemple : réponds de façon concise…") },
                        minLines = 4,
                    )
                }
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Annuler") } },
        confirmButton = {
            Button(
                enabled = loaded && !saving,
                onClick = {
                    scope.launch {
                        saving = true
                        try {
                            val saved = client.updatePreferences(token, preferences)
                            onSaved(saved)
                        } finally {
                            saving = false
                        }
                        onDismiss()
                    }
                },
            ) { Text(if (saving) "Enregistrement…" else "Enregistrer") }
        },
    )
}

private fun saveSession(preferences: android.content.SharedPreferences, session: Session) {
    preferences.edit()
        .putString("token", session.token)
        .putString("user_id", session.user.id)
        .putString("first_name", session.user.firstName)
        .putString("last_name", session.user.lastName)
        .putString("email", session.user.email)
        .putString("phone", session.user.phone)
        .apply()
}

private fun loadUser(preferences: android.content.SharedPreferences): AssaneUser? {
    val id = preferences.getString("user_id", null) ?: return null
    return AssaneUser(
        id = id,
        firstName = preferences.getString("first_name", "") ?: "",
        lastName = preferences.getString("last_name", "") ?: "",
        email = preferences.getString("email", "") ?: "",
        phone = preferences.getString("phone", "") ?: "",
    )
}


@Composable
private fun TierSelectionDialog(
    client: BackendClient,
    token: String,
    onDismiss: () -> Unit,
    onInfo: (String) -> Unit,
) {
    var current by remember { mutableStateOf<AssaneTier?>(null) }
    var tiers by remember { mutableStateOf<List<AssaneTier>>(emptyList()) }
    var loaded by remember { mutableStateOf(false) }
    var selecting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        try {
            val response = client.getTiers(token)
            current = response.first
            tiers = response.second
        } catch (ex: Exception) {
            onInfo("Les niveaux Assane sont momentanément indisponibles : ${ex.message ?: "erreur inconnue"}")
        } finally {
            loaded = true
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Niveau Assane AI") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Choisis le niveau qui correspond à ton usage. Il contrôle les limites du workspace et des outils côté serveur.", color = AssaneMuted, fontSize = 12.sp)
                if (!loaded) {
                    CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp)
                } else {
                    LazyColumn(
                        modifier = Modifier.height(360.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        items(tiers, key = { it.id }) { tier ->
                            val selected = current?.id == tier.id
                            TextButton(
                                onClick = {
                                    scope.launch {
                                        selecting = true
                                        try {
                                            current = client.selectTier(token, tier.id)
                                            onInfo("Niveau ${tier.name} sélectionné pour ton compte.")
                                        } catch (ex: Exception) {
                                            onInfo("Impossible de sélectionner ce niveau : ${ex.message ?: "erreur inconnue"}")
                                        } finally {
                                            selecting = false
                                        }
                                    }
                                },
                                enabled = !selecting,
                                modifier = Modifier.fillMaxWidth().padding(0.dp),
                            ) {
                                Surface(
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(18.dp),
                                    color = if (selected) AssaneSurfaceAlt else AssaneSurface,
                                ) {
                                    Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Text(tier.name, color = AssaneText, fontWeight = FontWeight.Bold, fontSize = 15.sp, modifier = Modifier.weight(1f))
                                            if (selected) Icon(Icons.Default.CheckCircle, "Niveau actif", tint = SenegalGreen, modifier = Modifier.size(20.dp))
                                        }
                                        Text(tier.description, color = AssaneMuted, fontSize = 11.sp)
                                        Text(
                                            "${tier.maxIterations} étapes · ${tier.maxConcurrentTasks} tâche(s) · ${tier.deploymentTargets.size} cible(s) · " +
                                                buildList {
                                                    if (tier.webSearch) add("recherche")
                                                    if (tier.imageGeneration) add("images")
                                                    if (tier.androidRelease) add("Android release")
                                                }.ifEmpty { listOf("outils essentiels") }.joinToString(" · "),
                                            color = AssaneBlue,
                                            fontSize = 11.sp,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Fermer") } },
    )
}


@Composable
private fun DashboardOverviewCard(
    task: AssaneTask?,
    projectType: String,
    onOpenComputer: () -> Unit,
    onOpenBrowser: () -> Unit,
    onImport: () -> Unit,
    onGenerateImage: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(22.dp),
        color = AssaneSurface,
    ) {
        Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(38.dp).clip(CircleShape).background(SenegalGreen), contentAlignment = Alignment.Center) {
                    Icon(Icons.Default.Memory, "Ordinateur d’Assane", tint = Color.White, modifier = Modifier.size(21.dp))
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text("Ordinateur d’Assane", color = AssaneText, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                    Text("Crée, inspecte, teste et prépare tes projets", color = AssaneMuted, fontSize = 11.sp)
                }
                TextButton(onClick = onOpenComputer) { Text("Ouvrir", color = SenegalGreen, fontSize = 12.sp) }
            }

            StageStrip(status = task?.status ?: "idle")

            if (task == null) {
                Text("Aucune tâche en cours. Décris ton idée ci-dessous et Assane s’occupe du plan de travail.", color = AssaneMuted, fontSize = 12.sp)
            } else {
                Surface(shape = RoundedCornerShape(16.dp), color = AssaneSurfaceAlt) {
                    Column(Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                when (task.status) {
                                    "succeeded" -> "Tâche terminée"
                                    "stopped", "cancelled" -> "Tâche arrêtée"
                                    "connection_lost" -> "Connexion perdue"
                                    else -> "Assane travaille…"
                                },
                                color = if (task.status == "succeeded") SenegalGreen else SenegalYellow,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.weight(1f),
                            )
                            Text("${taskProgress(task)}%", color = AssaneMuted, fontSize = 12.sp)
                        }
                        LinearProgressIndicator(
                            progress = { taskProgress(task) / 100f },
                            modifier = Modifier.fillMaxWidth().height(6.dp).clip(CircleShape),
                            color = SenegalGreen,
                            trackColor = Color.DarkGray,
                        )
                        Text("Étape : ${task.currentStep.ifBlank { "préparation" }} · ${task.iteration} passage(s)", color = AssaneMuted, fontSize = 11.sp)
                    }
                }
            }

            Text("Outils puissants", color = AssaneText, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                DashboardToolButton(Icons.Default.Visibility, "Navigateur", "Inspecter", onOpenBrowser, Modifier.weight(1f))
                DashboardToolButton(Icons.Default.AttachFile, "Importer", "Fichier", onImport, Modifier.weight(1f))
                DashboardToolButton(Icons.Default.ImageIcon, "Image", "Générer", onGenerateImage, Modifier.weight(1f))
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                DashboardToolButton(Icons.Default.Code, "Éditeur", "Modifier", onOpenComputer, Modifier.weight(1f))
                DashboardToolButton(Icons.Default.Terminal, "Terminal", "Exécuter", onOpenComputer, Modifier.weight(1f))
                DashboardToolButton(Icons.Default.Cloud, "Aperçu", if (projectType == "android") "Android" else "Web", onOpenComputer, Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun DashboardToolButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    OutlinedButton(
        onClick = onClick,
        modifier = modifier,
        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 6.dp, vertical = 8.dp),
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(icon, title, tint = AssaneBlue, modifier = Modifier.size(19.dp))
            Text(title, color = AssaneText, fontSize = 10.sp, maxLines = 1)
            Text(subtitle, color = AssaneMuted, fontSize = 9.sp, maxLines = 1)
        }
    }
}

@Composable
private fun StageStrip(status: String) {
    val stages = listOf("Analyse", "Plan", "Création", "Tests", "Finalisation")
    val activeIndex = when (status) {
        "queued", "planning" -> 0
        "running" -> 2
        "succeeded" -> 4
        "failed", "cancelled", "stopped", "connection_lost" -> 2
        else -> -1
    }
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        stages.forEachIndexed { index, label ->
            Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.weight(1f)) {
                Box(
                    Modifier.size(22.dp).clip(CircleShape).background(
                        when {
                            index < activeIndex -> SenegalGreen
                            index == activeIndex -> SenegalYellow
                            else -> AssaneSurfaceAlt
                        },
                    ),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(if (index < activeIndex) "✓" else "${index + 1}", color = Color.White, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
                Text(label, color = if (index <= activeIndex) AssaneText else AssaneMuted, fontSize = 9.sp, maxLines = 1)
            }
        }
    }
}

private fun taskProgress(task: AssaneTask): Int {
    if (task.status == "succeeded") return 100
    if (task.status in setOf("failed", "cancelled", "stopped", "connection_lost")) return 0
    return (20 + task.iteration * 10).coerceIn(20, 95)
}
