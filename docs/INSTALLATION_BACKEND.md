# Installation et hébergement du backend Assane AI

## Architecture

L’application Android est le client. Le backend est l’API privée qui reçoit les tâches, authentifie les comptes, conserve l’état, appelle le modèle, sélectionne les Skills et contrôle le runner. Le runner exécute les commandes et les compilations dans un workspace isolé. Le navigateur headless ouvre les URL publiques depuis le backend ou un conteneur dédié.

```text
APK Android → API Assane AI → Orchestrateur → Modèle configuré
                                      ↓
                              Runner Docker
                              Éditeur / terminal
                              Android SDK / Gradle
                              Navigateur headless
```

## Installation locale

Installe Python 3.11 ou plus récent, Docker Desktop, Git, un JDK compatible et Android Studio si la compilation APK est nécessaire. Depuis la racine du projet, crée le fichier d’environnement :

```bash
cp .env.example .env
```

Renseigne dans `.env` les clés que tu possèdes. Ne copie jamais `.env` dans l’APK et ne le publie pas dans Git.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python run.py
```

Sous Windows PowerShell :

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
python run.py
```

Vérifie ensuite :

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## Docker

Pour lancer le backend avec son image :

```bash
docker compose up --build
```

L’image installe Chromium pour le navigateur headless. Le runner d’exécution doit être configuré en mode Docker lorsque des fichiers ou commandes non fiables sont utilisés. Le mode local est réservé au développement contrôlé. Construis d’abord l’image Android dédiée :

```bash
docker build -f docker/android-builder.Dockerfile -t assane/android-builder:2026-08 .
```

Puis configure le runner :

```env
ASSANE_RUNNER_MODE=docker
ASSANE_DOCKER_IMAGE=assane/android-builder:2026-08
```

Si le backend tourne lui-même dans un conteneur, il ne doit pas recevoir automatiquement le socket Docker de l’hôte. Utilise de préférence un worker/runner séparé autorisé à exécuter les jobs ; une connexion au daemon Docker ne doit être ajoutée qu’après évaluation de ce risque.

En production, sépare si possible le service API, le worker agentique, le runner Android et le navigateur. Le runner ne doit pas avoir accès aux secrets du backend et doit avoir des limites CPU, mémoire, processus, disque et durée. L’image `android-builder.Dockerfile` fournit la base SDK/JDK, mais sa construction et la disponibilité du daemon Docker doivent être vérifiées sur la machine d’hébergement.

## Modèle et clés

Les clés de Manus, Mistral, OpenAI, GitHub, Vercel, Cloudflare, Stability et Deepgram restent sur le serveur. L’APK ne reçoit qu’une URL HTTPS vers l’API Assane AI et un jeton de session utilisateur.

Si aucun modèle n’est configuré, le backend doit retourner une erreur explicite plutôt que simuler une réponse. La publication est exécutée côté serveur uniquement pour la première cible Vercel. Le flux est : `POST /tasks/{id}/deploy/request`, affichage du résumé à l’utilisateur, puis `POST /deployments/{id}/confirm`. Le backend téléverse les fichiers, crée le deployment, suit son état et vérifie l’URL HTTP avant d’enregistrer `succeeded`. GitHub, Cloudflare et les autres cibles restent bloqués tant que leurs adaptateurs ne sont pas ajoutés. L’APK affiche des libellés Assane AI et ne contient pas les clés fournisseurs.

## Connexion de l’APK

Dans `app/build.gradle.kts`, utilise `http://10.0.2.2:8000` pour un émulateur Android lorsque le backend tourne sur le même ordinateur. Pour un téléphone réel sur le même Wi-Fi, utilise l’adresse LAN de l’ordinateur, par exemple `http://192.168.1.25:8000`. Pour un accès distant, utilise une URL HTTPS telle que `https://api.assane-ai.example`.

Compile l’APK de développement avec :

```bash
./gradlew assembleDebug
```

Pour une release, fournis obligatoirement l’URL HTTPS réelle du backend au moment de la compilation. La valeur peut être passée par une propriété Gradle ou une variable d’environnement :

```bash
./gradlew assembleRelease -PassaneBackendUrl=https://api.example.tld
# ou
ASSANE_RELEASE_BACKEND_URL=https://api.example.tld ./gradlew assembleRelease
```

Si la valeur d’exemple est conservée, l’APK release ne doit pas être distribué. Le résultat se trouve dans `app/build/outputs/apk/debug/app-debug.apk` ou `app/build/outputs/apk/release/app-release.apk`.

## Hébergement permanent

Pour que l’application fonctionne lorsque ton ordinateur personnel est éteint, le backend et le runner doivent être installés sur une machine qui reste allumée : serveur dédié, VPS puissant ou machine GPU. Un service Render classique peut héberger l’API légère, mais il ne doit pas être considéré comme un hébergement GPU Ollama ou comme un runner Android complet sans vérifier les ressources disponibles.

Configure un domaine HTTPS, un reverse proxy, une sauvegarde du stockage, une base de données persistante, un stockage d’artefacts et une surveillance. N’expose jamais le port de développement directement à Internet.

## Navigateur Assane

Le navigateur utilise Playwright et Chromium. Il peut ouvrir une URL publique, récupérer le titre et le texte de la page et enregistrer une capture dans le workspace. Les URL privées, les adresses locales et les réseaux internes sont bloqués par défaut. Les connexions à des comptes, les téléchargements sensibles, la publication et les actions destructives doivent demander une confirmation explicite.

## Arrêt, reprise et connexion

`POST /tasks/{id}/stop` arrête une tâche et conserve son dernier checkpoint. L’application affiche « Assane est arrêté. Envoyez un message pour continuer. ». `POST /tasks/{id}/continue` remet la tâche en file et relance l’orchestrateur. Une erreur réseau est enregistrée avec l’état `connection_lost`, puis l’interface affiche « Connexion perdue. Vérifiez le réseau puis envoyez un message pour continuer. ».

## Vérification finale

Teste dans cet ordre : `/health`, inscription, connexion, création d’une tâche, suivi des événements, arrêt, reprise, import de fichier, inspection de fichier, ouverture d’une URL publique, génération d’image, téléchargement d’artefact, préparation Vercel, refus d’une seconde confirmation et suivi du résultat. Pour un test réel Vercel, renseigne `VERCEL_TOKEN` côté serveur et utilise un workspace sans secret. Utilise deux comptes de test pour vérifier qu’aucun workspace, artefact, déploiement ou historique n’est visible par le mauvais utilisateur.

## Cibles de publication supplémentaires

Le backend peut maintenant préparer et exécuter, sous conditions, trois familles de publication. Pour GitHub, renseigne `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPOSITORY` et `GITHUB_BRANCH`. Le dépôt et la branche doivent être explicitement choisis ; le token doit posséder `Contents: write`. Le pipeline construit un commit multi-fichiers puis relit le SHA de la branche. Un conflit de branche ou une erreur d’autorisation est enregistré comme un échec.

Pour Cloudflare Pages, renseigne `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_PAGES_PROJECT` et `CLOUDFLARE_PAGES_BRANCH`. Le projet Pages doit déjà être créé et autorisé, et le token doit disposer de `Pages Write`. Pour Cloudflare Workers, renseigne aussi `CLOUDFLARE_WORKER_NAME` et `CLOUDFLARE_WORKER_URL`. Le module `_worker.js`, `worker.js`, `src/index.js`, `src/worker.js` ou `index.js` est détecté ; l’URL configurée est ensuite vérifiée par HTTP.

Dans l’APK, ces cibles sont présentées comme des destinations Assane AI génériques. Les tokens ne sont jamais envoyés au client. Cette présentation masque les détails techniques de l’interface, mais elle ne doit pas être interprétée comme une absence de services réseau.

## Backend Python, Node et Docker

Le détecteur de projet et la route `/tasks/{task_id}/backend-plan` peuvent produire les commandes, le runtime, le chemin de santé et les avertissements nécessaires. Aucun hébergeur générique n’est supposé par défaut : un backend de production exige encore une cible explicitement autorisée, la gestion des secrets, les migrations, le stockage persistant, TLS, la supervision, le rollback et un health check. Tant qu’un adaptateur d’hébergement n’est pas installé, le plan reste `preflight_only` et ne peut pas être annoncé comme un déploiement.

## Compilation Android

Construis l’image dédiée avec `docker build -f docker/android-builder.Dockerfile -t assane/android-builder:2026-08 .`, puis configure `ASSANE_RUNNER_MODE=docker`. `ASSANE_ANDROID_CONNECTED_TESTS=false` lance les tests unitaires ; la valeur `true` ajoute les tests connectés, mais exige un émulateur réellement disponible. Un build réussi recherche l’APK dans le workspace et l’enregistre comme artefact propriétaire. La compilation doit toutefois être testée sur une machine ayant un SDK Android fonctionnel avant toute distribution.

## Inspection d’images publiques

Le backend installe désormais Pillow pour générer les aperçus d’images. La route `POST /browser/extract-images` accepte une URL publique, une limite et un indicateur `save`. Avec `save=false`, elle renvoie les métadonnées et les aperçus sans créer d’artefact permanent. Avec `save=true`, elle exige l’utilisateur authentifié et conserve les images dans son espace propriétaire. Les URL privées, les redirections vers des réseaux privés, les contenus non-image, les fichiers trop volumineux et les dépassements de quota sont refusés.

## Aperçu, QR code et publication Android

Après une tâche web réussie, `POST /tasks/{task_id}/preview` crée un lien temporaire associé au compte et à la tâche. Le lien expire automatiquement, peut être révoqué et possède un QR code PNG encodé dans la réponse. Configure `ASSANE_PUBLIC_BASE_URL` avec l’URL HTTPS réellement accessible du backend ; la valeur `localhost` ne convient qu’à un test local.

Pour un projet Android, l’interface propose `Construire APK` et `Construire AAB`. L’APK debug est un artefact de test téléchargeable. L’AAB release exige un SDK Android/JDK/Gradle fonctionnel et une configuration de signature adaptée ; l’existence du fichier ne signifie pas qu’il est prêt pour une distribution publique.

Le parcours Play Store utilise la cible `google_play`. Configure uniquement sur le serveur `GOOGLE_PLAY_PACKAGE_NAME`, `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` et `GOOGLE_PLAY_TRACK`. Le fichier JSON du compte de service ne doit jamais être ajouté au ZIP ni à l’APK. Le backend crée une édition, téléverse l’AAB, l’associe à la piste choisie et ne commit la publication qu’après la confirmation explicite. Un compte développeur Play Console et les permissions correspondantes restent indispensables.
