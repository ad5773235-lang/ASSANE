plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

val releaseBackendUrl = providers.gradleProperty("assaneBackendUrl")
    .orElse(providers.environmentVariable("ASSANE_API_URL"))
    .orElse(providers.environmentVariable("ASSANE_RELEASE_BACKEND_URL"))
    .orElse("")
    .get()

val releaseUrlIsLocal = releaseBackendUrl.isBlank() ||
    !releaseBackendUrl.startsWith("https://", ignoreCase = true) ||
    releaseBackendUrl.contains("localhost", ignoreCase = true) ||
    releaseBackendUrl.contains("127.0.0.1") ||
    releaseBackendUrl.contains("10.0.2.2") ||
    Regex("192\\.168\\.").containsMatchIn(releaseBackendUrl)

if (gradle.startParameter.taskNames.any { it.contains("release", ignoreCase = true) } && releaseUrlIsLocal) {
    throw GradleException("Build release bloqué : fournissez une URL HTTPS publique avec -PassaneBackendUrl ou ASSANE_API_URL")
}

android {
    namespace = "com.assaneai.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.assaneai.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }

    kotlinOptions {
        jvmTarget = "21"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    buildTypes {
        getByName("debug") {
            buildConfigField("String", "ASSANE_BACKEND_URL", "\"http://10.0.2.2:8000\"")
        }
        getByName("release") {
            buildConfigField("String", "ASSANE_BACKEND_URL", "\"$releaseBackendUrl\"")
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2025.01.00")
    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.8.5")
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")

    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
}
