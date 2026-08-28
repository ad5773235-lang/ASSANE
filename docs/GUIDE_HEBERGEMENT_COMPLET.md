# Installer et héberger Assane AI

## 1. Architecture recommandée

Assane AI est composé de plusieurs éléments qui ne doivent pas nécessairement être installés sur le même ordinateur.

| Composant | Rôle | Hébergement recommandé |
|---|---|---|
| Client Android | Interface utilisateur, compte, tâches, aperçu et téléchargement | Téléphone ou émulateur Android |
| Backend FastAPI | Authentification, orchestrateur, API, intégrations et événements | VPS Linux, serveur personnel ou machine locale toujours allumée |
| Base de données | Comptes, tâches, événements et préférences | SQLite pour développement ; PostgreSQL recommandé avant une utilisation sérieuse |
| Stockage d’artefacts | APK, AAB, images, fichiers et résultats | Volume persistant local au départ ; stockage objet en production |
| Runner | Exécution isolée, commandes et build Android | Service Docker séparé, avec quotas et réseau contrôlé |
| Navigateur | Inspection de sites publics et extraction d’images | Backend ou service navigateur séparé avec Chromium |
| Fournisseurs externes | Modèle, images, voix, publication et services associés | Backend uniquement ; jamais dans l’APK |

Le chemin le plus simple pour commencer est d’utiliser un serveur Ubuntu toujours allumé. Tu peux utiliser ton propre ordinateur, mais il devra rester connecté à Internet lorsque tu veux utiliser Assane depuis le téléphone. Pour un service indépendant de ton ordinateur, utilise un VPS ou un serveur dédié. Le client Android ne doit jamais contenir les clés des fournisseurs.

> Important : le fichier `docker-compose.yml` actuel démarre le backend et ses volumes, mais il ne crée pas automatiquement PostgreSQL ni un runner Docker séparé. Le runner local convient au développement contrôlé. Pour un environnement de production, il faut ajouter un service runner isolé ou une machine d’exécution séparée.

## 2. Préparer le serveur

Sur un serveur Ubuntu récent, installe Git, Docker et le plugin Compose :

```bash
sudo apt update
sudo apt install -y git curl ca-certificates docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Après l’ajout au groupe Docker, ouvre une nouvelle session SSH ou exécute `newgrp docker`. Vérifie ensuite :

```bash
docker --version
docker compose version
```

Clone ensuite le projet dans un répertoire non public :

```bash
sudo mkdir -p /opt/assane-ai
sudo chown -R "$USER":"$USER" /opt/assane-ai
git clone URL_DU_DEPOT /opt/assane-ai
cd /opt/assane-ai
```

Si tu as seulement le ZIP, transfère-le sur le serveur puis décompresse-le :

```bash
mkdir -p /opt/assane-ai
unzip "Assane AI Aperçu Publication.zip" -d /opt/assane-ai
cd /opt/assane-ai/AssaneAI
```

## 3. Configurer l’environnement serveur

Ne crée pas l’APK avec les clés secrètes. Sur le serveur uniquement :

```bash
cd /opt/assane-ai/AssaneAI
cp .env.example .env
chmod 600 .env
nano .env
```

Les variables principales sont les suivantes :

| Variable | Valeur à fournir |
|---|---|
| `ASSANE_ENV` | `production` sur un serveur réel |
| `ASSANE_JWT_SECRET` | Une chaîne aléatoire longue, différente de la valeur d’exemple |
| `ASSANE_PUBLIC_BASE_URL` | URL HTTPS publique du backend, par exemple `https://api.ton-domaine.com` |
| `ASSANE_CORS_ORIGINS` | Origines autorisées, pas `*` en production si tu peux les limiter |
| `ASSANE_RUNNER_MODE` | `local` pour démarrer simplement ; `docker` seulement lorsque le runner est réellement raccordé |
| `ASSANE_DOCKER_IMAGE` | Image builder disponible sur le serveur si le mode Docker est actif |
| `OPENAI_API_KEY`, `MISTRAL_API_KEY` ou autre modèle | Clés ajoutées uniquement sur le serveur si tu les utilises |
| `VERCEL_TOKEN` | Uniquement si tu veux publier vers Vercel |
| `GITHUB_TOKEN` | Uniquement si tu veux publier vers un dépôt autorisé |
| `CLOUDFLARE_API_TOKEN` | Uniquement si tu veux publier vers Cloudflare |
| `GOOGLE_PLAY_PACKAGE_NAME` | Nom du paquet Android, par exemple `com.exemple.assane` |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` | Chemin serveur vers le JSON Play Store, jamais dans le ZIP |
| `GOOGLE_PLAY_TRACK` | `internal`, `alpha`, `beta` ou `production` |

Génère un secret JWT au lieu d’utiliser `change-me` :

```bash
openssl rand -hex 48
```

Le fichier `.env` ne doit jamais être envoyé dans le chat, ajouté à Git ou inclus dans une archive distribuée. Seul `.env.example` doit être partagé.

## 4. Lancer le backend avec Docker Compose

Le lancement initial est :

```bash
cd /opt/assane-ai/AssaneAI
docker compose build
docker compose up -d
```

Consulte les journaux :

```bash
docker compose ps
docker compose logs -f assane-backend
```

Teste l’API depuis le serveur :

```bash
curl http://127.0.0.1:8000/health
```

La réponse attendue doit contenir un état `ok: true`. Si le backend redémarre en boucle, lis les journaux avant de modifier l’APK : une clé absente, une dépendance Python, Playwright/Chromium ou un mauvais chemin de données peuvent être en cause.

Pour arrêter ou redémarrer le service :

```bash
docker compose down
docker compose up -d
```

Les volumes `assane_data` et `assane_artifacts` doivent être conservés. Ne lance pas `docker compose down -v` sauf si tu acceptes de supprimer les données locales du projet.

## 5. Navigateur et inspection des sites

Le backend utilise Playwright/Chromium pour ouvrir des sites publics. L’image backend du projet prévoit l’installation de Chromium. Après la construction, vérifie les journaux et teste une inspection avec une URL publique.

Le navigateur refuse les adresses privées, loopback et réservées. L’extraction d’images applique également une limite de nombre et de taille. Avec `save=false`, les images sont seulement renvoyées pour aperçu ; avec `save=true`, elles sont conservées dans les artefacts du compte authentifié.

Une URL publique de preview ne fonctionnera pas avec `ASSANE_PUBLIC_BASE_URL=http://localhost:8000` depuis un téléphone distant. Il faut une adresse DNS ou IP accessible et idéalement HTTPS.

## 6. Runner local ou runner Docker

Pour une première installation, tu peux garder :

```env
ASSANE_RUNNER_MODE=local
```

Ce mode est adapté au développement contrôlé sur une machine de confiance. Il ne constitue pas une isolation forte pour du code utilisateur non fiable.

Pour le mode Docker, construis d’abord l’image Android :

```bash
docker build -f docker/android-builder.Dockerfile -t assane/android-builder:2026-08 .
```

Puis configure :

```env
ASSANE_RUNNER_MODE=docker
ASSANE_DOCKER_IMAGE=assane/android-builder:2026-08
```

Le backend doit pouvoir appeler Docker. Dans un déploiement naïf, le conteneur backend ne possède pas automatiquement le client Docker ni l’accès au daemon de l’hôte. La solution la plus sûre est un **service runner séparé** qui reçoit des demandes authentifiées et possède uniquement les permissions nécessaires. Le montage direct du socket `/var/run/docker.sock` dans le backend est pratique pour un laboratoire, mais augmente fortement l’impact d’une compromission ; ne l’utilise pas sans comprendre cette conséquence.

Le runner doit appliquer un workspace par tâche, des limites CPU/mémoire/PID, un réseau désactivé par défaut, un utilisateur non privilégié, un délai maximal et un nettoyage après exécution. Les secrets du backend ne doivent jamais être montés dans le workspace de compilation.

## 7. Build Android, APK et AAB

Pour un build Android réel, le runner doit avoir un JDK, le SDK Android, les plateformes et les build-tools correspondant au projet. L’image `android-builder.Dockerfile` sert de base, mais elle doit être construite et testée sur une machine où Docker fonctionne réellement.

Les deux parcours sont distincts :

| Sortie | Commande | Usage |
|---|---|---|
| APK debug | `./gradlew assembleDebug` | Test local ou téléchargement sur un téléphone |
| APK release | `./gradlew assembleRelease` | Distribution contrôlée après signature |
| AAB release | `./gradlew bundleRelease` | Téléversement vers une piste Play Store après signature |
| Tests unitaires | `./gradlew test` | Vérification sans émulateur |
| Tests connectés | `./gradlew connectedDebugAndroidTest` | Nécessite un émulateur ou appareil attaché |

Assane enregistre un APK ou un AAB trouvé dans le workspace comme artefact propriétaire. Le téléchargement Android doit être déclenché par l’utilisateur via le sélecteur de fichiers du téléphone.

Un AAB non signé ou signé avec une clé de test ne doit pas être présenté comme prêt pour le Play Store. La clé de signature release doit être gérée séparément, avec sauvegardes et permissions strictes.

## 8. Publication web et aperçu

Pour un projet web compatible, le cycle est :

```text
analyse → build → manifeste → aperçu temporaire → vérification → confirmation → publication → vérification HTTP
```

Le bouton Aperçu crée un lien temporaire et un QR code. Le lien expire et peut être révoqué. Pour une URL publique permanente, il faut utiliser un adaptateur configuré comme Vercel, GitHub/Pages ou Cloudflare. Assane ne doit pas afficher « publié » si l’URL finale n’a pas répondu correctement au contrôle prévu.

Vercel reste la cible la plus complètement bouclée dans le projet. GitHub et Cloudflare exigent des tokens et permissions corrects. Un backend Python, Node ou Docker doit encore disposer d’un hébergeur compatible et d’un adaptateur spécialisé ; le simple fait de réussir un build local ne suffit pas.

## 9. Publication Play Store

Le parcours Play Store exige un compte développeur, un nom de paquet existant, un AAB release signé et un compte de service autorisé dans Google Play Console. Le compte de service doit rester côté serveur.

La séquence est :

```text
AAB signé → création d’une édition → upload du bundle → association à une piste → confirmation → commit → contrôle du résultat
```

Une publication vers `production` doit avoir une confirmation distincte d’une publication vers `internal`, `alpha` ou `beta`. L’adaptateur présent dans Assane prépare ce flux, mais il ne peut être testé réellement qu’avec tes propres identifiants et un paquet Play Console configuré.

## 10. Connecter l’application Android

Dans le projet Android, l’URL release ne doit pas rester une valeur d’exemple. Compile avec une URL HTTPS réelle :

```bash
./gradlew assembleRelease -PassaneBackendUrl=https://api.ton-domaine.com
```

Selon la configuration du projet, tu peux aussi utiliser :

```bash
ASSANE_RELEASE_BACKEND_URL=https://api.ton-domaine.com ./gradlew assembleRelease
```

L’application envoie les demandes au backend. Elle ne doit contenir aucune clé Vercel, GitHub, Cloudflare, Google Play ou de modèle IA. Si le serveur change d’URL, il faut reconstruire l’APK ou prévoir un mécanisme de configuration public maîtrisé.

## 11. Tests dans l’ordre conseillé

Teste d’abord `/health`, puis l’inscription, la connexion et `/auth/me`. Continue avec la création d’une tâche, les événements, l’arrêt/reprise, l’importation, l’inspection d’URL, le navigateur, l’extraction d’images, la génération d’image, le téléchargement d’artefact et enfin le preview.

Après cela, teste sur un petit projet web sans secret. Vérifie que l’aperçu est accessible, que le QR code encode la bonne URL, que la révocation bloque le lien et que le statut ne devient pas `succeeded` sans vérification. Pour Android, valide d’abord un APK debug, puis un AAB release dans un environnement de build réel. Le test Play Store doit être effectué sur une piste interne avant toute production.

## 12. Ce qui n’est pas encore automatique

Cette procédure ne transforme pas Assane AI en plateforme universelle en une seule commande. Le backend prend maintenant en charge un mode PostgreSQL configuré par `ASSANE_DATABASE_URL`, une file de jobs persistante mono-processus, la récupération après redémarrage, la révocation de sessions et des quotas d’artefacts. SQLite reste le défaut du développement local ; le stockage objet, les sauvegardes, le worker distribué et le rollback restent à ajouter pour une exploitation à haute disponibilité.

L’APK debug a été compilé et vérifié dans l’environnement de développement de cette version. Cela ne prouve pas qu’un APK ou un AAB peut être produit dans n’importe quel serveur : le SDK, les licences, les dépendances Gradle, la signature, l’émulateur et les ressources matérielles doivent être réellement disponibles. Consulte `docs/REMEDIATION_2026-08.md` pour la matrice des vérifications réalisées.

## Références

[1]: https://docs.docker.com/engine/install/ubuntu/ — Installer Docker Engine sur Ubuntu.
[2]: https://docs.docker.com/compose/ — Docker Compose.
[3]: https://playwright.dev/python/docs/intro — Playwright Python.
[4]: https://developers.google.com/android-publisher/getting_started — Google Play Developer API, configuration du compte de service.
[5]: https://developers.google.com/android-publisher/api-ref/rest/v3/edits/bundles/upload — Google Play Developer API, upload d’un bundle.
