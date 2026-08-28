package com.assaneai.app.data

import com.assaneai.app.BuildConfig
import com.assaneai.app.model.AssaneDeployment
import com.assaneai.app.model.AssaneEvent
import com.assaneai.app.model.AssanePreferences
import com.assaneai.app.model.AssaneTask
import com.assaneai.app.model.AssaneTier
import com.assaneai.app.model.AssaneUser
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.URLEncoder
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class BackendException(message: String) : Exception(message)

data class RegistrationChallenge(
    val pendingSignupId: String,
    val otpRequestId: String,
    val maskedPhone: String,
    val expiresAt: String,
)

class BackendClient(baseUrlOverride: String? = null) {
    private val baseUrl = (baseUrlOverride?.trim()?.ifBlank { null } ?: BuildConfig.ASSANE_BACKEND_URL).trimEnd('/')

    suspend fun startRegistration(firstName: String, lastName: String, email: String, phone: String, password: String): RegistrationChallenge {
        val body = JSONObject()
            .put("first_name", firstName)
            .put("last_name", lastName)
            .put("email", email)
            .put("phone", phone)
            .put("password", password)
        val json = post("/auth/register", body, null)
        return RegistrationChallenge(
            pendingSignupId = json.getString("pending_signup_id"),
            otpRequestId = json.getString("otp_request_id"),
            maskedPhone = json.optString("phone", "ton numéro"),
            expiresAt = json.optString("expires_at", ""),
        )
    }

    suspend fun resendRegistrationOtp(pendingSignupId: String): RegistrationChallenge {
        val json = post("/auth/register/resend", JSONObject().put("pending_signup_id", pendingSignupId), null)
        return RegistrationChallenge(
            pendingSignupId = json.getString("pending_signup_id"),
            otpRequestId = json.getString("otp_request_id"),
            maskedPhone = json.optString("phone", "ton numéro"),
            expiresAt = json.optString("expires_at", ""),
        )
    }

    suspend fun verifyRegistrationOtp(otpRequestId: String, code: String): Session {
        return sessionFrom(post("/auth/register/verify", JSONObject().put("otp_request_id", otpRequestId).put("code", code), null))
    }

    suspend fun login(email: String, password: String): Session {
        val body = JSONObject().put("email", email).put("password", password)
        return sessionFrom(post("/auth/login", body, null))
    }

    suspend fun logout(token: String): JSONObject = post("/auth/logout", JSONObject(), token)

    suspend fun getTiers(token: String): Pair<AssaneTier, List<AssaneTier>> {
        val json = get("/tiers", token)
        val all = buildList {
            val array = json.optJSONArray("tiers") ?: JSONArray()
            for (index in 0 until array.length()) add(tierFrom(array.getJSONObject(index)))
        }
        val current = tierFrom(json.getJSONObject("current"))
        return current to all
    }

    suspend fun selectTier(token: String, tierId: String): AssaneTier {
        val response = put("/tier", JSONObject().put("tier_id", tierId), token)
        return tierFrom(response.getJSONObject("tier"))
    }

    suspend fun getPreferences(token: String): AssanePreferences {
        val preferences = get("/preferences", token).getJSONObject("preferences")
        return AssanePreferences(
            theme = preferences.optString("theme", "dark"),
            background = preferences.optString("background", "default"),
            customInstructions = preferences.optString("custom_instructions", ""),
        )
    }

    suspend fun updatePreferences(token: String, preferences: AssanePreferences): AssanePreferences {
        val body = JSONObject()
            .put("theme", preferences.theme)
            .put("background", preferences.background)
            .put("custom_instructions", preferences.customInstructions)
        val result = post("/preferences", body, token)
        val json = result.getJSONObject("preferences")
        return AssanePreferences(
            theme = json.optString("theme", "dark"),
            background = json.optString("background", "default"),
            customInstructions = json.optString("custom_instructions", ""),
        )
    }

    suspend fun uploadFile(token: String, filename: String, mimeType: String, bytes: ByteArray, taskId: String = "general"): JSONObject = withContext(Dispatchers.IO) {
        val boundary = "----AssaneBoundary${UUID.randomUUID()}"
        val encodedTaskId = URLEncoder.encode(taskId, "UTF-8")
        val connection = (URL("$baseUrl/uploads?task_id=$encodedTaskId").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            connectTimeout = 15_000
            readTimeout = 120_000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Authorization", "Bearer $token")
            setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
        }
        try {
            val safeName = filename.replace("\"", "_")
            connection.outputStream.use { output ->
                output.write("--$boundary\\r\\n".toByteArray())
                output.write("Content-Disposition: form-data; name=\"file\"; filename=\"$safeName\"\\r\\n".toByteArray())
                output.write("Content-Type: $mimeType\\r\\n\\r\\n".toByteArray())
                output.write(bytes)
                output.write("\\r\\n--$boundary--\\r\\n".toByteArray())
            }
            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (status !in 200..299) throw BackendException(text.ifBlank { "Upload error $status" })
            JSONObject(text)
        } finally {
            connection.disconnect()
        }
    }

    suspend fun generateImage(token: String, prompt: String, provider: String = "openai"): JSONObject {
        return post("/media/generate-image", JSONObject().put("prompt", prompt).put("provider", provider), token)
    }

    suspend fun openBrowser(token: String, url: String): JSONObject {
        return post("/browser/open", JSONObject().put("url", url), token)
    }

    suspend fun extractImages(token: String, url: String, taskId: String = "general", limit: Int = 8, save: Boolean = false): JSONObject {
        return post(
            "/browser/extract-images",
            JSONObject().put("url", url).put("task_id", taskId).put("limit", limit).put("save", save),
            token,
        )
    }

    suspend fun createTask(token: String, prompt: String): AssaneTask {
        val response = post("/tasks", JSONObject().put("prompt", prompt), token)
        return taskFrom(response.getJSONObject("task"), emptyList())
    }

    suspend fun listTasks(token: String, limit: Int = 50): List<AssaneTask> {
        val response = get("/tasks?limit=${limit.coerceIn(1, 100)}", token)
        val tasks = response.optJSONArray("tasks") ?: JSONArray()
        return buildList {
            for (index in 0 until tasks.length()) {
                add(taskFrom(tasks.getJSONObject(index), emptyList()))
            }
        }
    }

    suspend fun stopTask(token: String, taskId: String): AssaneTask {
        val response = post("/tasks/$taskId/stop", JSONObject(), token)
        return taskFrom(response.getJSONObject("task"), emptyList())
    }

    suspend fun continueTask(token: String, taskId: String): AssaneTask {
        val response = post("/tasks/$taskId/continue", JSONObject(), token)
        return taskFrom(response.getJSONObject("task"), emptyList())
    }

    suspend fun requestDeployment(token: String, taskId: String, projectName: String, target: String = "vercel"): AssaneDeployment {
        val response = post(
            "/tasks/$taskId/deploy/request",
            JSONObject().put("target", target).put("project_name", projectName),
            token,
        )
        return deploymentFrom(response.getJSONObject("deployment"))
    }

    suspend fun confirmDeployment(token: String, deploymentId: String): AssaneDeployment {
        val response = post("/deployments/$deploymentId/confirm", JSONObject(), token)
        return deploymentFrom(response.getJSONObject("deployment"))
    }

    suspend fun getDeployment(token: String, deploymentId: String): AssaneDeployment {
        val response = get("/deployments/$deploymentId", token)
        return deploymentFrom(response.getJSONObject("deployment"))
    }

    suspend fun downloadArtifact(token: String, artifactId: String): ByteArray = withContext(Dispatchers.IO) {
        val connection = (URL("$baseUrl/artifacts/$artifactId/download").openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 15_000
            readTimeout = 120_000
            setRequestProperty("Authorization", "Bearer $token")
        }
        try {
            val status = connection.responseCode
            if (status !in 200..299) throw BackendException("Téléchargement de l’artefact impossible ($status)")
            connection.inputStream.use { it.readBytes() }
        } finally {
            connection.disconnect()
        }
    }

    suspend fun buildAndroid(token: String, taskId: String, packageFormat: String, variant: String): JSONObject {
        return post(
            "/tasks/$taskId/android/build",
            JSONObject().put("package_format", packageFormat).put("variant", variant),
            token,
        )
    }

    suspend fun createPreview(token: String, taskId: String): JSONObject {
        return post("/tasks/$taskId/preview", JSONObject(), token)
    }

    suspend fun detectProject(token: String, taskId: String): JSONObject = get("/tasks/$taskId/project", token).optJSONObject("project") ?: JSONObject()

    suspend fun revokePreview(token: String, previewId: String): JSONObject {
        return request("DELETE", "/previews/$previewId", null, token)
    }

    suspend fun getTask(token: String, taskId: String): AssaneTask {
        val response = get("/tasks/$taskId", token)
        val events = eventsFrom(response.optJSONArray("events") ?: JSONArray())
        return taskFrom(response.getJSONObject("task"), events)
    }

    private suspend fun post(path: String, body: JSONObject, token: String?): JSONObject = withContext(Dispatchers.IO) {
        request("POST", path, body.toString(), token)
    }

    private suspend fun get(path: String, token: String): JSONObject = withContext(Dispatchers.IO) {
        request("GET", path, null, token)
    }

    private suspend fun put(path: String, body: JSONObject, token: String): JSONObject = withContext(Dispatchers.IO) {
        request("PUT", path, body.toString(), token)
    }

    private fun request(method: String, path: String, body: String?, token: String?): JSONObject {
        val connection = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 15_000
            readTimeout = 120_000
            setRequestProperty("Accept", "application/json")
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            if (!token.isNullOrBlank()) setRequestProperty("Authorization", "Bearer $token")
        }
        try {
            if (body != null) connection.outputStream.use { it.write(body.toByteArray()) }
            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                if (status >= 500) {
                    throw BackendException("Le serveur ASSANE AI est momentanément indisponible. Veuillez réessayer.")
                }
                val message = runCatching { JSONObject(text).optString("detail") }.getOrDefault(text)
                throw BackendException(message.ifBlank { "La demande n’a pas pu être traitée." })
            }
            return JSONObject(text)
        } finally {
            connection.disconnect()
        }
    }

    private fun sessionFrom(json: JSONObject): Session {
        val user = json.getJSONObject("user")
        return Session(
            token = json.getString("token"),
            user = AssaneUser(
                id = user.getString("id"),
                firstName = user.getString("first_name"),
                lastName = user.getString("last_name"),
                email = user.getString("email"),
                phone = user.getString("phone"),
            ),
        )
    }

    private fun tierFrom(json: JSONObject) = AssaneTier(
        id = json.optString("id"),
        name = json.optString("name"),
        description = json.optString("description"),
        maxIterations = json.optInt("max_iterations", 0),
        maxConcurrentTasks = json.optInt("max_concurrent_tasks", 0),
        runnerMode = json.optString("runner_mode"),
        persistence = json.optString("persistence"),
        deploymentTargets = buildList {
            val targets = json.optJSONArray("deployment_targets") ?: JSONArray()
            for (index in 0 until targets.length()) add(targets.optString(index))
        },
        androidRelease = json.optBoolean("allow_android_release_build", false),
        googlePlay = json.optBoolean("allow_google_play_publish", false),
        webSearch = json.optBoolean("web_search_enabled", false),
        imageGeneration = json.optBoolean("image_generation_enabled", false),
    )

    private fun deploymentFrom(json: JSONObject) = AssaneDeployment(
        id = json.getString("id"),
        taskId = json.getString("task_id"),
        target = json.getString("target"),
        projectName = json.getString("project_name"),
        status = json.getString("status"),
        url = json.optString("url").takeIf { it.isNotBlank() && it != "null" },
        verified = json.optBoolean("verified", json.optString("status") == "succeeded"),
        fileCount = json.optInt("file_count", 0),
        totalBytes = json.optLong("total_bytes", 0),
        error = json.optString("error").takeIf { it.isNotBlank() && it != "null" },
    )

    private fun taskFrom(json: JSONObject, events: List<AssaneEvent>) = AssaneTask(
        id = json.getString("id"),
        prompt = json.getString("prompt"),
        status = json.getString("status"),
        currentStep = json.getString("current_step"),
        iteration = json.optInt("iteration", 0),
        updatedAt = json.optString("updated_at").takeIf { it.isNotBlank() && it != "null" },
        eventCount = json.optInt("event_count", 0),
        lastEventMessage = json.optString("last_event_message").takeIf { it.isNotBlank() && it != "null" },
        events = events,
    )

    private fun eventsFrom(array: JSONArray): List<AssaneEvent> = buildList {
        for (index in 0 until array.length()) {
            val item = array.getJSONObject(index)
            add(AssaneEvent(item.optString("kind"), item.optString("message")))
        }
    }
}

data class Session(val token: String, val user: AssaneUser)
