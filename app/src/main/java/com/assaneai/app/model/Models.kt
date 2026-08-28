package com.assaneai.app.model

data class AssaneTier(
    val id: String,
    val name: String,
    val description: String,
    val maxIterations: Int,
    val maxConcurrentTasks: Int,
    val runnerMode: String,
    val persistence: String,
    val deploymentTargets: List<String>,
    val androidRelease: Boolean,
    val googlePlay: Boolean,
    val webSearch: Boolean,
    val imageGeneration: Boolean,
)

data class AssaneUser(
    val id: String,
    val firstName: String,
    val lastName: String,
    val email: String,
    val phone: String,
)

data class AssaneEvent(
    val kind: String,
    val message: String,
)

data class AssaneTask(
    val id: String,
    val prompt: String,
    val status: String,
    val currentStep: String,
    val iteration: Int = 0,
    val updatedAt: String? = null,
    val eventCount: Int = 0,
    val lastEventMessage: String? = null,
    val events: List<AssaneEvent> = emptyList(),
)

data class AssaneArtifact(
    val id: String,
    val filename: String,
    val mimeType: String,
    val sizeBytes: Long = 0,
)

data class AssaneDeployment(
    val id: String,
    val taskId: String,
    val target: String,
    val projectName: String,
    val status: String,
    val url: String? = null,
    val verified: Boolean = false,
    val fileCount: Int = 0,
    val totalBytes: Long = 0,
    val error: String? = null,
)
