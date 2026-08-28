# Assane AI

Assane AI est un projet composé d’un **client Android compilable en APK** et d’un **noyau backend agentique**. Le backend contient l’orchestrateur, les Skills, le registre d’outils, la persistance des comptes et des tâches, le runner de workspace et les adaptateurs vers les fournisseurs externes.

Le projet n’est pas une copie de Manus. Il reprend une logique d’assistant agentique — plan, outils, observation, progression et correction — avec une identité visuelle différente inspirée du Sénégal.

## Important : l’APK et le backend

Les clés Manus, GitHub, Mistral, Vercel, Cloudflare, OpenAI, Stability et Deepgram ne doivent jamais être intégrées dans l’APK. L’APK appelle le backend Assane AI, et le backend appelle les fournisseurs avec les clés conservées dans `.env`.

Un APK seul peut afficher l’interface, mais il ne peut pas sécuriser correctement des clés privées. Pour un fonctionnement réel, il faut donc lancer le backend sur un ordinateur ou un serveur accessible par l’APK.

## Démarrer le backend

Copie `.env.example` vers `.env` et renseigne uniquement les clés que tu possèdes réellement :

```bash
cp .env.example .env
```

Installe ensuite les dépendances et lance le serveur :

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Ou avec Docker Compose depuis la racine :

```bash
docker compose up --build
```

L’API sera disponible sur `http://localhost:8000`. La documentation interactive sera disponible sur `http://localhost:8000/docs`.

## Compiler l’APK

Ouvre le dossier racine dans Android Studio avec un JDK 17 ou supérieur compatible avec ton installation Gradle. Le module Android se trouve dans `app/`.

Pour l’émulateur Android, l’URL debug par défaut est `http://10.0.2.2:8000`, car cette adresse redirige vers le localhost de l’ordinateur hôte. Pour un téléphone réel, remplace l’URL dans `app/build.gradle.kts` par l’adresse IP locale ou HTTPS de ton backend.

Lance ensuite :

```bash
./gradlew assembleDebug
```

L’APK debug sera produit dans :

```text
app/build/outputs/apk/debug/app-debug.apk
```

Le projet inclut une inscription avec prénom, nom, e-mail, numéro de téléphone et mot de passe. Le backend crée d’abord une inscription temporaire, génère un OTP SMS aléatoire et n’active le compte qu’après vérification du code. Le code est haché, temporaire, limité en tentatives et à usage unique. Les informations de session sont conservées côté Android pour permettre la reconnexion. Chaque compte possède aussi ses préférences propres : thème, fond et instructions personnalisées.

Un appui long d’environ deux secondes sur un événement de réponse ouvre le menu d’actions avec « Demander à Assane », « Copier », « Partager », « Sélectionner le texte » et « Signaler ». Le bouton Profil/Personnaliser ouvre l’écran où l’utilisateur choisit le thème, le fond et écrit une instruction personnelle. Cette instruction est sauvegardée via `PUT /preferences` et injectée dans le contexte du modèle uniquement pour le compte concerné.

## Contrôle d’une tâche et navigateur Assane

Pendant une tâche, l’application interroge régulièrement le backend. L’utilisateur peut arrêter la tâche avec le bouton « Arrêter ». Le backend passe alors la tâche à l’état `stopped`, conserve le dernier checkpoint et ajoute l’événement « Assane est arrêté. Envoyez un message pour continuer. ». Le bouton « Continuer » appelle `POST /tasks/{id}/continue` et relance l’orchestrateur. Si un fournisseur ne répond plus, l’état `connection_lost` affiche « Connexion perdue. Vérifiez le réseau puis envoyez un message pour continuer. ».

Le navigateur headless d’Assane est disponible via `POST /browser/open`. Il doit être installé dans le backend avec `playwright install chromium`, ou automatiquement dans l’image Docker. Il ouvre uniquement des URL publiques, extrait le titre et le texte de la page et peut enregistrer une capture dans le workspace. Les sites nécessitant une connexion, les réseaux privés et les opérations sensibles doivent rester soumis à des règles et confirmations supplémentaires.

## Fonctionnement réel d’une tâche

Assane AI possède aussi un bloc d’instructions globales dans `backend/app/core/instructions.py`. Il sépare les profils utilisateurs et indique que le propriétaire de l’assistant est Assane Moussa Goudiaby. Les informations récentes sur le Sénégal doivent être vérifiées avec une source connectée lorsqu’une recherche est disponible.

L’agent peut sélectionner les Skills `android-build`, `general-agent`, `media-generation`, `inspection` et `deployment`. Ces Skills exposent les outils de workspace, de terminal, d’inspection de liens, de documents, d’images et d’APK, de génération d’images, de gestion d’artefacts et de demande de déploiement.


Lorsqu’un utilisateur écrit une demande :

```text
APK Android
  → POST /tasks
  → backend crée la tâche
  → orchestrateur sélectionne les Skills
  → modèle configuré décide
  → outil autorisé s’exécute
  → événement enregistré
  → APK interroge /tasks/{id}
  → interface affiche « Assane réfléchit » et le journal
```

Si aucun fournisseur IA ou SMS n’est configuré, le backend renvoie une erreur de configuration. Il ne fabrique pas de réponse fictive. Le transport SMS est abstrait derrière `SmsProvider`; le mode développement n’envoie pas de SMS réel et ne doit pas être utilisé en production.

## Inspection et génération

Les routes authentifiées suivantes sont prévues par le backend : `POST /inspect/url` pour inspecter un lien public, `POST /inspect/file` pour inspecter un fichier du workspace et détecter notamment les métadonnées d’un APK, et `POST /media/generate-image` pour appeler OpenAI Images ou Stability AI selon la clé configurée. Une image générée ou importée doit être enregistrée comme artefact avant téléchargement ou affichage.

## Niveaux Assane

Chaque compte reçoit un niveau de capacité par défaut, puis peut consulter et modifier son niveau depuis Profil → Capacités Assane → Niveau Assane. Les routes authentifiées sont `GET /tiers`, `GET /tier`, `GET /tier/limitations` et `PUT /tier`. Les niveaux Moyen, Fiable et Élevé appliquent des limites au nombre de tâches, aux itérations de l’orchestrateur, aux builds Android release, à la génération d’images et aux cibles de publication. Ce sont des politiques de capacité, pas trois modèles IA distincts, et elles ne fournissent aucune clé fournisseur.

Un APK inconnu est inspecté comme archive avant toute exécution. Les liens vers des réseaux privés sont bloqués par défaut par l’outil d’inspection URL. Le déploiement, le partage et les actions irréversibles doivent demander une confirmation explicite.

## Intégrations prévues

Le fichier `.env.example` contient les variables pour Manus, GitHub, Mistral, Vercel, Cloudflare, OpenAI, Stability et Deepgram. Les adaptateurs se trouvent dans `backend/app/core/providers.py`.

Les endpoints et les modèles peuvent évoluer. Vérifie toujours la documentation officielle du fournisseur avant la mise en production, puis adapte la variable de base URL ou l’adaptateur si nécessaire.

## Sécurité et état de production

Cette archive est une base fonctionnelle renforcée, mais elle ne doit pas être exposée publiquement sans configuration opérateur. En mode `ASSANE_ENV=production`, le backend refuse le secret de session par défaut, HTTP pour l’URL publique, le CORS `*` et le runner local. Le compose fourni ajoute PostgreSQL et un volume de données ; hors Compose, SQLite reste le mode de développement. Le worker persistant est mono-processus et le stockage objet, les sauvegardes, le rollback et un worker distribué restent des étapes de production à prévoir.

L’APK debug et l’AAB de validation présents dans `deliverables_verified/` ont été compilés et contrôlés localement. L’AAB n’est pas une publication Play Store. Pour une distribution réelle, fournir une URL HTTPS avec `-PassaneBackendUrl=https://...`, configurer une signature release protégée et tester d’abord sur une piste interne.

Ne mets jamais `.env`, une clé API, une clé de signature Android ou un mot de passe réel dans Git ou dans l’APK.
