# Assane AI — signature release et publication Google Play

## 1. Comprendre les deux clés

Pour une application publiée avec **Play App Signing**, il faut distinguer la clé d’upload et la clé de signature de l’application. La clé d’upload reste chez le développeur et sert à signer l’AAB envoyé à Play Console. Google protège la clé de signature de l’application et l’utilise ensuite pour signer les APK distribués aux appareils [1] [2].

> La clé d’upload doit rester secrète. Son certificat public peut être partagé avec les services qui demandent une empreinte, mais jamais le fichier `.jks`, le mot de passe ou la clé privée.

Dans le cas d’une nouvelle application, il est recommandé de laisser Google gérer la clé de signature de l’application et de conserver localement uniquement une clé d’upload. La perte ou la compromission de la clé d’upload peut être traitée par une demande de réinitialisation ; la perte d’une clé de signature gérée soi-même est beaucoup plus grave [2].

## 2. Préparer le projet Assane AI

Dans le projet, l’identifiant Android est actuellement `com.assaneai.app`, le nom affiché est `Assane AI` et le `versionCode` initial est `1`. L’identifiant `applicationId` doit rester identique entre les versions publiées. Pour chaque nouvelle version, augmente `versionCode` et adapte `versionName`.

L’AAB doit aussi contenir l’URL HTTPS réelle du backend Assane AI. Le projet accepte la propriété Gradle `assaneBackendUrl` ou la variable `ASSANE_RELEASE_BACKEND_URL`. Ne mets pas une URL d’exemple dans un AAB destiné aux utilisateurs.

Avant la compilation release, vérifie depuis un navigateur ou `curl` que l’URL répond réellement :

```bash
curl -fsS https://api.ton-domaine.example/health
```

La réponse attendue doit venir de ton backend Assane AI. Si le backend utilise des aperçus publics, `ASSANE_PUBLIC_BASE_URL` doit également être cette base HTTPS publique, sans clé d’API dans l’APK.

## 3. Créer la clé d’upload

Fais cette opération sur ton ordinateur ou un serveur de confiance, jamais dans un dépôt public. Crée un dossier privé et génère une clé RSA d’au moins 2 048 bits, conformément aux prérequis indiqués par Google Play [2] :

```bash
mkdir -p "$HOME/.assane-ai-keys"
chmod 700 "$HOME/.assane-ai-keys"

keytool -genkeypair -v \
  -keystore "$HOME/.assane-ai-keys/assaneai-upload.jks" \
  -alias assaneai-upload \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -storetype JKS
```

`keytool` demandera le mot de passe du keystore et celui de la clé. Choisis un mot de passe long, unique et conservé dans un gestionnaire de mots de passe. Ne l’écris pas dans ce guide, dans Git, dans l’APK ou dans une conversation.

Vérifie le certificat public sans divulguer la clé privée :

```bash
keytool -list -v \
  -keystore "$HOME/.assane-ai-keys/assaneai-upload.jks" \
  -alias assaneai-upload

keytool -exportcert -rfc \
  -keystore "$HOME/.assane-ai-keys/assaneai-upload.jks" \
  -alias assaneai-upload \
  -file "$HOME/.assane-ai-keys/assaneai-upload-cert.pem"
```

Sauvegarde le fichier `.jks` dans au moins un emplacement chiffré séparé. Ne mets jamais la sauvegarde dans le même dépôt que le code. Le certificat `.pem` est public ; le `.jks` ne l’est pas.

## 4. Configurer Gradle sans mettre la clé dans le projet

À la racine du projet, crée localement un fichier `keystore.properties` qui ne sera jamais inclus dans le ZIP ou Git :

```properties
storeFile=/chemin/absolu/vers/.assane-ai-keys/assaneai-upload.jks
storePassword=TON_MOT_DE_PASSE_LOCAL
keyAlias=assaneai-upload
keyPassword=TON_MOT_DE_PASSE_LOCAL
```

Ajoute ces exclusions à `.gitignore` :

```gitignore
keystore.properties
*.jks
*.keystore
*.p12
*.pem
```

Dans `app/build.gradle.kts`, ajoute la lecture locale des propriétés avant le bloc `android` :

```kotlin
import java.util.Properties

val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("keystore.properties")
if (keystorePropertiesFile.exists()) {
    keystorePropertiesFile.inputStream().use { keystoreProperties.load(it) }
}
```

À l’intérieur de `android { ... }`, ajoute la configuration suivante :

```kotlin
signingConfigs {
    create("release") {
        if (!keystorePropertiesFile.exists()) {
            throw GradleException("keystore.properties est requis pour un build release signé")
        }
        storeFile = file(keystoreProperties["storeFile"] as String)
        storePassword = keystoreProperties["storePassword"] as String
        keyAlias = keystoreProperties["keyAlias"] as String
        keyPassword = keystoreProperties["keyPassword"] as String
    }
}
```

Dans le build type release existant, ajoute la signature :

```kotlin
getByName("release") {
    signingConfig = signingConfigs.getByName("release")
}
```

Le projet Assane AI utilise déjà une propriété pour l’URL release. Pour compiler avec ton URL réelle, préfère :

```bash
export ASSANE_RELEASE_BACKEND_URL="https://api.ton-domaine.example"
./gradlew clean bundleRelease --no-daemon
```

ou :

```bash
./gradlew clean bundleRelease \
  -PassaneBackendUrl="https://api.ton-domaine.example" \
  --no-daemon
```

Ne construis pas une release distribuable si cette valeur est vide ou si elle contient encore un domaine d’exemple. Les avertissements de dépréciation d’icônes ne bloquent généralement pas le build, mais toute erreur Kotlin, Gradle ou de signature doit être corrigée avant l’envoi.

## 5. Vérifier l’AAB localement

L’AAB destiné à Google Play sera normalement produit ici :

```text
app/build/outputs/bundle/release/app-release.aab
```

Vérifie sa présence, son empreinte et son intégrité :

```bash
sha256sum app/build/outputs/bundle/release/app-release.aab
unzip -tq app/build/outputs/bundle/release/app-release.aab
```

Le bouton **Run** d’Android Studio n’est pas la procédure de publication : Android indique qu’il peut produire un APK `testOnly`. Pour une distribution, utilise **Generate Signed App Bundle or APK** ou la tâche Gradle `bundleRelease` avec la configuration release [3].

Si tu utilises `apksigner` sur un APK de contrôle, tu peux inspecter les certificats ainsi :

```bash
$ANDROID_HOME/build-tools/35.0.0/apksigner verify --verbose app/build/outputs/apk/release/app-release.apk
```

Pour l’AAB, l’inspection finale et la signature de distribution sont gérées dans le flux Play App Signing. Ne confonds pas un AAB local de validation avec une version effectivement publiée.

## 6. Créer l’application dans Play Console

Connecte-toi à [Google Play Console](https://play.google.com/console/) avec le compte développeur qui doit posséder Assane AI. Crée une nouvelle application avec le nom `Assane AI`, la langue par défaut, la catégorie appropriée et le type d’application correct. Le package doit correspondre à `com.assaneai.app`.

Complète les informations demandées dans le tableau de bord : fiche Play Store, icône, captures d’écran, description, classification du contenu, audience cible, présence éventuelle de publicité, formulaire Data safety, politique de confidentialité et accès à l’application. Comme Assane AI utilise un compte avec e-mail, téléphone et mot de passe, la fiche Data safety doit décrire honnêtement les données collectées, transmises, conservées et supprimées. Si l’application nécessite une connexion pour être évaluée, fournis un compte de test dans la section prévue de Play Console ; ne mets jamais ses identifiants dans le code ou le ZIP.

Les libellés de menu peuvent évoluer. Cherche la section **App integrity / Intégrité de l’application**, puis configure **Play App Signing**. Pour une nouvelle application, choisis l’option qui permet à Google de gérer la clé de signature de l’application. L’AAB envoyé sera signé localement avec ta clé d’upload ; Google utilisera ensuite sa clé de signature pour les APK distribués [1] [2].

## 7. Publier d’abord en test interne

Dans Play Console, ouvre la piste **Internal testing / Test interne**, crée une nouvelle version et importe `app-release.aab`. Contrôle le nom de package, le code de version, les messages de validation et la liste des appareils compatibles. Ajoute les testeurs autorisés et publie la version sur cette piste.

Installe l’application depuis le lien de test et vérifie au minimum :

| Contrôle | Résultat attendu |
|---|---|
| Ouverture de l’application | L’écran Assane AI s’affiche sans erreur |
| Connexion backend | L’APK atteint uniquement l’URL HTTPS configurée |
| Inscription/connexion | Le compte et la session fonctionnent |
| Profil | Apparence, instructions et niveau Assane se chargent |
| Ordinateur d’Assane | Navigateur, inspection, éditeur et terminal affichent leurs états réels |
| Tâche | « Assane réfléchit », journal, arrêt et reprise répondent au backend |
| Importation | Le fichier est envoyé au workspace du bon utilisateur |
| Aperçu/QR | Le lien est HTTPS, temporaire et révocable |
| Artefact | Le téléchargement est limité au propriétaire |
| Publication | Une confirmation est requise avant toute action sensible |

Si le backend n’est pas joignable en HTTPS, ne publie pas l’application. Un AAB accepté par Play Console ne garantit pas que le service Assane AI est correctement déployé ou accessible.

## 8. Passer progressivement en production

Après le test interne, utilise une piste fermée si tu as besoin d’un groupe plus large et contrôlé, puis une piste ouverte si tu veux recueillir des retours plus larges. Lorsque les tests, la fiche et les déclarations sont prêts, crée la release de production et envoie-la en examen. Play Console peut afficher des contrôles ou exigences supplémentaires selon le type de compte, le pays, l’application et les règles en vigueur [4].

Pour chaque mise à jour, augmente `versionCode`, conserve le même `applicationId` et signe avec la même clé d’upload, sauf procédure officielle de réinitialisation. Ne change pas la clé de signature de l’application sans comprendre les conséquences sur les mises à jour existantes.

## 9. Erreurs fréquentes à éviter

| Erreur | Conséquence |
|---|---|
| Envoyer le fichier `.jks` ou `keystore.properties` dans le ZIP | Compromission de la clé d’upload |
| Utiliser l’AAB de validation fourni sans le reconstruire | URL backend absente ou configuration non adaptée à ta production |
| Garder `versionCode=1` pour une mise à jour | Rejet du bundle déjà utilisé |
| Changer `com.assaneai.app` après une publication | Play considère souvent cela comme une autre application |
| Mettre une URL HTTP ou privée dans l’APK | Connexion non adaptée aux utilisateurs et échecs hors réseau local |
| Publier directement sans test interne | Erreurs d’authentification, de preview, d’artefacts ou de configuration non détectées |
| Confondre AAB envoyé et publication terminée | L’AAB doit encore passer les contrôles et le flux Play Console |
| Mettre des clés de fournisseurs dans Android | Fuite des secrets ; les clés doivent rester dans `.env` du backend |

## Références

[1]: https://developer.android.com/studio/publish/app-signing — Android Developers, « Sign your app ».

[2]: https://support.google.com/googleplay/android-developer/answer/9842756?hl=fr — Google Play Help, « Utiliser le service Signature d’application Play ».

[3]: https://developer.android.com/build/build-for-release — Android Developers, « Build your app for release to users ».

[4]: https://support.google.com/googleplay/android-developer/answer/9859348?hl=fr — Google Play Help, « Préparer et déployer une version ».
