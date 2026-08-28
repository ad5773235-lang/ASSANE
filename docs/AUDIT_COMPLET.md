# Audit complet d’Assane AI

Date : 22 août 2026.

## Réponse directe

**Assane AI ne peut pas encore déployer n’importe quel projet.** Le projet contient une base réelle pour recevoir des demandes, authentifier des utilisateurs, conserver des tâches, sélectionner des Skills, appeler des fournisseurs configurés, manipuler un workspace et préparer des artefacts. Des pipelines serveur Vercel, GitHub, Cloudflare Pages et Cloudflare Workers sont maintenant implémentés sous conditions. Les backends génériques et les autres cibles ne possèdent pas encore d’adaptateur de publication complet.

Le pipeline Vercel est accessible via une demande préparée depuis une tâche, une confirmation unique et une exécution côté serveur. Il calcule les hashes, téléverse les fichiers, crée le deployment, suit `READY` ou `ERROR`, puis vérifie l’URL par HTTP. L’ancienne opération générique `deploy` reste explicitement marquée `implemented: false` pour les cibles non reliées, afin d’empêcher une fausse réussite.

## Classement des composants

| Composant | État | Preuve observée | Décision |
|---|---|---|---|
| Client Android Compose | Présent | Sources Kotlin, manifest, thèmes, client HTTP et écrans de profil | Fonctionnel comme base de client |
| Comptes | Présent | Inscription prénom/nom/e-mail/téléphone/mot de passe et connexion | Fonctionne localement |
| Sessions | Présent | Jeton signé avec expiration et vérification côté API | À renforcer avec rotation/révocation en production |
| Isolation des utilisateurs | Présente | Requêtes de tâches et artefacts filtrées par `user_id` | Vérifiée par test API de base |
| Préférences et profil | Présents | Endpoints de préférences et écran Android | Fonctionne comme base |
| Persistance | Incomplète pour la production | SQLite local dans `storage/db.py`, aucun PostgreSQL ni migration de production | À migrer avant multi-utilisateur sérieux |
| Orchestrateur | Présent mais incomplet | Boucle d’itérations, événements, checkpoints et états | À compléter avec file durable, reprise exacte et annulation réelle |
| Sélection des Skills | Présente mais rudimentaire | Manifests JSON et correspondance par mots déclencheurs | À compléter avec scoring, dépendances et permissions effectives |
| Registre d’outils | Présent mais partiellement appliqué | `ToolSpec` contient permissions et effets de bord | L’orchestrateur doit vérifier ces permissions avant dispatch |
| Runner local | Présent | Allowlist et exécution dans un workspace | Développement contrôlé uniquement |
| Runner Docker | Présent mais non autonome | Limites réseau, CPU, mémoire, PID et capacités dans `manager.py` | Nécessite une infrastructure Docker correctement raccordée |
| Navigateur | Présent | Playwright/Chromium et blocage des URL privées | Dépend de Chromium et d’un environnement sécurisé |
| Inspection | Présente | Inspection URL/fichiers/APK | À compléter par quotas et validation de types plus stricte |
| Importation et artefacts | Présents | Upload, hash SHA-256, stockage propriétaire et téléchargement | À migrer vers un stockage objet durable |
| Génération d’image | Présente mais dépendante | Adaptateurs OpenAI/Stability | Nécessite des clés et une gestion complète des réponses/artefacts |
| GitHub | Présent sous conditions | Adaptateur serveur avec blobs, tree, commit atomique, mise à jour et relecture de branche | Nécessite `GITHUB_TOKEN`, un dépôt explicite et Contents: write |
| Vercel | Présent sous conditions | Adaptateur serveur avec upload, création, suivi et vérification HTTP | Nécessite `VERCEL_TOKEN` et un workspace frontend/statique compatible |
| Cloudflare Pages/Workers | Présent sous conditions | Adaptateurs Pages multipart et Workers module avec vérification HTTP | Nécessite compte, projet/script autorisé et permissions adaptées |
| Confirmation | Présente pour les cibles enregistrées | Demande expirante, revendication atomique et route `/deployments/{id}/confirm` à usage unique | Les cibles sans adaptateur restent bloquées |
| Compilation Android | Présente mais non validée | Wrapper Gradle et tâches `assembleDebug`/tests | SDK Android/JDK/runner requis ; aucune APK ne doit être annoncée ici |
| Déploiement universel | Manquant | Les adaptateurs Vercel, GitHub et Cloudflare couvrent certaines cibles ; les backends génériques et tous les runtimes ne sont pas couverts | Impossible de promettre “n’importe quel projet” |

## Vérification spécifique du déploiement

| Type de projet | Peut-il être préparé ? | Peut-il être réellement publié par cette version ? | Manque principal |
|---|---:|---:|---|
| Frontend statique | Oui, si les fichiers sont fournis | Non | Adaptateur de build/upload vers une cible réelle |
| Application React/Vite ou autre frontend | Partiellement | Non | Détection du framework, build reproductible et adaptateur de publication |
| Backend Python/Node | Partiellement | Non | Cible d’hébergement, variables secrètes, migrations, logs et health checks |
| Projet Android | Partiellement | Non | SDK/JDK/Gradle configurés, tests, stockage APK/AAB et distribution |
| Projet Docker | Partiellement | Non | Registry, contrôle d’image, déploiement d’un service et rollback |
| GitHub | Oui pour préparer des fichiers | Non | Opérations GitHub d’écriture et confirmation liée au dépôt |
| Vercel | Oui | Oui sous conditions, avec l’adaptateur serveur et une clé valide | Le compte, le runtime et les limites de fichiers doivent être compatibles |
| Cloudflare Pages/Workers | Oui pour préparer un workspace | Non | Adaptateurs d’upload/build et suivi de déploiement |
| Projet nécessitant GPU, base privée ou matériel spécialisé | Non garanti | Non | Infrastructure compatible et politique de secrets/ressources |
| Projet arbitraire | Non garanti | Non | Contrat d’exécution, adaptateur et tests propres à chaque runtime |

## Tests effectués

Le script de syntaxe Python termine avec succès pour tous les modules backend. Des tests de fumée isolés ont validé la création de compte, le hachage de mot de passe, la session, la tâche, les préférences, l’artefact, la lecture/écriture de workspace, le runner local et l’isolation API. Un test de l’adaptateur Vercel avec transport réseau contrôlé a validé le séquencement upload, création, état `READY` et vérification HTTP sans publier réellement. Un test API a validé la préparation Vercel, la confirmation unique et le refus d’une seconde confirmation.

La commande `./gradlew tasks --no-daemon` termine avec succès. La compilation `./gradlew assembleDebug --no-daemon` n’a pas pu terminer, car aucun emplacement de SDK Android n’est configuré dans cet environnement. Il serait incorrect d’annoncer qu’un APK compilé a été produit.

## Corrections appliquées pour cette version

Le fichier `.env` réel a été retiré du projet destiné à l’archive ; seul `.env.example` doit être distribué. Les bases SQLite et fichiers d’exécution de test ont été supprimés avant le packaging. L’URL release Android est désormais configurable avec `-PassaneBackendUrl=...` ou `ASSANE_RELEASE_BACKEND_URL=...`, et la documentation précise qu’une valeur d’exemple interdit toute distribution. Le comportement générique de déploiement reste marqué comme non implémenté pour les cibles sans adaptateur, tandis que Vercel, GitHub et Cloudflare disposent de pipelines dédiés sous conditions. Enfin, ce rapport et `AUDIT_DEPLOIEMENT.md` sont inclus dans `docs/`.

## Plan de passage à un vrai déploiement

La prochaine étape réaliste n’est pas de promettre toutes les plateformes à la fois. Les contrats Vercel, GitHub et Cloudflare existent désormais, mais ils doivent encore être testés en conditions réelles sur des comptes dédiés et avec des projets sans secret. Après cette validation réelle, il faudra encore renforcer les pipelines GitHub/Cloudflare, ajouter les adaptateurs d’hébergement backend et industrialiser la distribution Android. En parallèle, il faudra remplacer SQLite par PostgreSQL, externaliser les artefacts, séparer le worker et le runner, et ajouter des tests d’intégration.

## Inspection de sites et images publiques

Le navigateur backend ouvre les URL publiques dans un workspace dédié par utilisateur. La nouvelle route `POST /browser/extract-images` utilise `extract_images` pour récupérer les images `img` et les images Open Graph publiques, contrôler les redirections, limiter le nombre et la taille, générer un aperçu et retourner les données au client Android. Le client affiche les aperçus dans le dialogue Navigateur Assane.

La conservation n’est pas automatique. Elle exige l’action explicite « Conserver les images » ; le backend vérifie l’utilisateur authentifié et écrit ensuite les fichiers dans ses artefacts propriétaires. Les tests locaux couvrent les URL privées, les schémas interdits, les PNG transparents, la limite d’aperçu, l’absence d’identité pour une conservation et le flux d’extraction simulé. Un test réel avec un site public reste à effectuer après installation de Playwright/Chromium et avec une cible dont les droits de récupération sont respectés.

## Espace d’aperçu et publication Android

Une première couche d’aperçu temporaire est maintenant présente. Une tâche web avec `index.html` peut créer un lien associé à l’utilisateur et à la tâche, limité dans le temps, révocable et servi par le backend. La réponse contient un QR code PNG qui encode uniquement le lien public configuré. La résolution des ressources respecte le sous-répertoire `dist` ou `build` lorsque le frontend possède une sortie compilée.

Le client Android affiche ce lien et le QR code, permet de copier le lien et expose une révocation explicite. Pour Android, `build_android_artifact` distingue `assembleDebug`/APK et `bundleRelease`/AAB, recherche le fichier généré et l’enregistre comme artefact propriétaire. La route Android propose le téléchargement authentifié sur le téléphone. La cible `google_play` prépare et, lorsque les identifiants serveur et les permissions sont valides, téléverse un AAB vers une édition et une piste configurées ; elle ne doit jamais être considérée comme publiée sans confirmation et commit réussi.

Ces fonctions restent conditionnelles : un preview public exige une URL HTTPS réellement accessible, un projet web avec point d’entrée, un runner adapté pour le build et un serveur persistant. Un APK/AAB exige le SDK Android, JDK, Gradle, et pour l’AAB distribué une signature appropriée. Play Store exige un compte développeur, un compte de service sécurisé côté serveur et les droits Play Console. Aucun de ces prérequis n’est simulé dans l’archive.
