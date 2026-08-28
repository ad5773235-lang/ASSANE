# Déployer Assane AI sur Render

Ce guide utilise le backend existant. Il ne remplace pas l’application Android et ne supprime pas l’Ordinateur d’Assane, l’OTP, l’historique, les tâches, les artefacts ou les fonctions déjà présentes.

## Architecture Render

```text
APK Assane AI
      │ HTTPS
      ▼
Render Web Service — assane-ai-api
      ├── FastAPI
      ├── PostgreSQL Render
      ├── disque persistant /app/data
      ├── worker intégré au processus backend actuel
      ├── OTP Unimatrix
      └── fournisseurs IA configurés
```

Le fichier `render.yaml` à la racine décrit le Web Service Docker, PostgreSQL, le disque persistant et le health check `/health`. Render documente les Blueprints, les services Docker et les références `fromDatabase` dans son [Blueprint YAML Reference][1].

## Création

Il faut d’abord pousser le projet dans un dépôt GitHub privé ou public contrôlé par le propriétaire. Dans Render, choisir **New > Blueprint**, connecter le dépôt et sélectionner `render.yaml`. Render crée le service Web et la base PostgreSQL selon le Blueprint. Le service Docker utilise `docker/backend.Dockerfile`.

Après création, renseigner obligatoirement les variables marquées `sync: false` dans le Dashboard Render :

| Variable | Valeur à fournir |
| --- | --- |
| `ASSANE_PUBLIC_BASE_URL` | URL Render HTTPS réellement créée, ou domaine personnalisé |
| `ASSANE_CORS_ORIGINS` | Origines autorisées réelles, pas `*` en production |
| `UNIMATRIX_ACCESS_KEY_ID` | Identifiant fourni par Unimatrix |
| `UNIMATRIX_ACCESS_KEY_SECRET` | Secret uniquement si le mode HMAC est utilisé |
| `MANUS_API_KEY`, `MISTRAL_API_KEY`, `OPENAI_API_KEY`, etc. | Seulement les fournisseurs réellement utilisés |
| `GITHUB_TOKEN`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN` | Seulement les cibles réellement autorisées |

Les valeurs doivent être ajoutées dans Render **Environment**, jamais dans GitHub, le ZIP ou l’APK. Le Blueprint génère le secret JWT et relie `ASSANE_DATABASE_URL` à PostgreSQL.

## Vérification

Après le déploiement, vérifier d’abord :

```text
https://URL-RENDER/health
https://URL-RENDER/docs
```

Tester ensuite l’inscription, la demande OTP, la vérification, la connexion, la création d’une tâche, l’historique, l’importation et les fonctions de l’Ordinateur d’Assane. Avec `ASSANE_SMS_PROVIDER=unimatrix`, un SMS réel exige un compte Unimatrix autorisé et des identifiants valides.

Le backend lit maintenant la variable `PORT` fournie par Render et conserve `8000` comme valeur de développement local. Render fournit automatiquement TLS pour l’URL publique du Web Service ; un domaine personnalisé peut être ajouté ensuite.

## Stockage et limites importantes

Le disque Render est nécessaire pour conserver les workspaces et artefacts locaux, car le système de fichiers d’un service Render est éphémère par défaut. Render précise qu’un disque persistant est attaché à un seul service et empêche le scale horizontal de ce service [2]. Pour plusieurs instances, il faudra migrer les artefacts vers un stockage objet partagé.

PostgreSQL Render est utilisé pour les utilisateurs, sessions, tâches, événements, OTP et déploiements. Render fournit les mécanismes de sauvegarde et de restauration PostgreSQL dans son service géré [3].

Le projet actuel possède un runner Docker durci prévu pour une machine disposant d’un moteur Docker. Un Web Service Render construit depuis un Dockerfile ne fournit pas automatiquement un démon Docker utilisable pour lancer des conteneurs frères. Ainsi, l’API et le worker peuvent être déployés sur Render, mais les builds Android et l’exécution isolée complète doivent être validés avec un runner distant séparé ou une architecture Render compatible. Il ne faut pas annoncer ces builds comme disponibles avant un test réel.

## Build de l’APK release

Une fois l’URL HTTPS publique réellement disponible, construire l’APK/AAB depuis un environnement de build Android avec :

```powershell
.\gradlew.bat bundleRelease -PassaneBackendUrl=https://URL-RENDER
```

Le projet bloque volontairement un build release si l’URL est vide, en HTTP, locale ou liée à un émulateur. Cette protection évite de livrer une application qui dépendrait par erreur de l’ordinateur personnel.

[1]: https://render.com/docs/blueprint-spec "Render Blueprint YAML Reference"
[2]: https://render.com/docs/disks "Render Persistent Disks"
[3]: https://render.com/docs/postgresql "Render Postgres"
