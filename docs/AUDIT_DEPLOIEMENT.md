# Audit du déploiement d’Assane AI

Date de l’audit : 22 août 2026.

## Conclusion directe

**Non, la version actuelle d’Assane AI ne peut pas encore déployer n’importe quel projet.** Elle possède maintenant un premier adaptateur de publication réel pour Vercel, ainsi qu’une base agentique, un runner et des adaptateurs HTTP. GitHub, Cloudflare et les autres cibles ne disposent pas encore d’un adaptateur de publication complet.

Le code ne doit donc pas annoncer une publication réussie lorsqu’elle n’a pas été exécutée et observée. Dans la version actuelle, une demande Vercel est préparée avec un manifeste de fichiers, attend une confirmation unique, puis lance l’adaptateur Vercel côté serveur. Celui-ci téléverse les fichiers, crée le déploiement, suit son état et vérifie l’URL finale. Les cibles sans adaptateur restent bloquées et ne sont pas présentées comme publiées.

## Résultats vérifiés

| Domaine | État | Vérification | Conséquence |
|---|---|---|---|
| Authentification et comptes | Fonctionne comme base | Inscription, connexion, session signée et isolation par `user_id` testées localement | Base utilisable pour un prototype contrôlé |
| Persistance | Présente mais non production-ready | `storage/db.py` utilise SQLite ; aucun PostgreSQL, migration ou pool de connexions n’est fourni | À renforcer avant hébergement multi-utilisateur |
| Runner local | Présent | Allowlist de programmes et workspace par tâche | Réservé au développement contrôlé ; pas d’isolation forte |
| Runner Docker | Présent mais dépendant de l’infrastructure | Conteneur avec réseau désactivé, capacités supprimées, limites CPU/mémoire/PID et workspace monté | Doit être installé séparément et correctement raccordé |
| Modèle agentique | Présent mais incomplet | Orchestrateur, événements, checkpoints et sélection de Skills présents | La reprise, les files durables et le contrôle d’annulation doivent être durcis |
| Adaptateur Vercel | Opérationnel sous conditions | Routes de demande/confirmation, upload de fichiers, suivi `READY/ERROR` et vérification HTTP | Nécessite `VERCEL_TOKEN`, workspace frontend/statique compatible |
| Adaptateur GitHub | Opérationnel sous conditions | Blobs, tree, commit atomique, mise à jour de branche et relecture du SHA | Nécessite `GITHUB_TOKEN`, dépôt explicite et permission Contents: write |
| Adaptateur Cloudflare Pages | Opérationnel sous conditions | Multipart Pages, suivi du stage et vérification HTTP | Nécessite compte, projet Pages autorisé et permission Pages Write |
| Adaptateur Cloudflare Workers | Opérationnel sous conditions | Upload du module Worker détecté et vérification de l’URL configurée | Nécessite permission Workers Scripts Write et URL publique de contrôle |
| Confirmation de publication | Présente pour toutes les cibles enregistrées | `POST /deployments/{deployment_id}/confirm` consomme une demande expirante et atomiquement revendiquée | Les cibles sans adaptateur restent refusées |
| Android | Client présent | Gradle expose les tâches Android ; `tasks` réussit | La compilation complète exige un SDK Android configuré |
| APK release | Non validé | L’URL release est `https://your-assane-backend.example.com` | À remplacer par une vraie URL HTTPS avant distribution |

## Ce qui est nécessaire pour un vrai déploiement

Pour publier un projet web statique ou frontend, il faut d’abord détecter le framework et construire le projet dans un runner isolé. Il faut ensuite créer ou sélectionner le projet distant, transférer les fichiers ou l’artefact de build, suivre le résultat, enregistrer l’URL et conserver les journaux. L’adaptateur doit vérifier que le projet appartient à l’utilisateur et ne doit agir qu’après confirmation explicite.

Pour un backend, il faut une cible d’hébergement compatible avec le runtime et la persistance nécessaires. Un projet Android exige un environnement Android SDK/JDK/Gradle, puis un stockage sécurisé de l’APK ou de l’AAB. Un projet nécessitant une base de données, des secrets, un GPU, Docker ou des services privés ne peut pas être considéré comme déployable simplement parce qu’il a été compilé.

Le terme **n’importe quel projet** doit donc être remplacé par une matrice de cibles et de runtimes supportés. Chaque nouvelle cible doit posséder un adaptateur réel, une validation de prérequis, un suivi de déploiement, une stratégie de rollback et un test d’intégration avec des identifiants non sensibles.

## Priorités recommandées

1. Implémenter un contrat de déploiement explicite avec une cible, un type de projet, un artefact, les prérequis, l’état, les journaux et l’URL de résultat.
2. Séparer la demande de déploiement, la confirmation et l’exécution. La confirmation doit reprendre uniquement l’action affichée à l’utilisateur et empêcher la réutilisation d’une ancienne demande.
3. Tester en conditions réelles Vercel, GitHub et Cloudflare avec des comptes de déploiement dédiés et des projets sans secret. Les tests simulés ne remplacent pas ce test opérateur.
4. Remplacer SQLite par PostgreSQL et ajouter un stockage d’artefacts durable avant un usage multi-utilisateur sérieux.
5. Exécuter le runner non fiable dans un service séparé, sans secrets du backend, avec limites de ressources, réseau contrôlé et nettoyage du workspace.
6. Ajouter des tests de bout en bout : création, compilation, déploiement de test, suivi, échec, reprise, rollback et vérification d’isolation entre deux comptes.

## Formulation honnête pour l’interface

Assane AI peut **préparer** un projet, modifier ses fichiers, l’exécuter dans un runner configuré, le compiler lorsque l’environnement est disponible et préparer une demande de publication. La **publication réelle** dépend d’un adaptateur configuré pour la cible choisie, de clés valides côté serveur, d’un runner adapté, d’un stockage persistant et de la confirmation de l’utilisateur. Elle n’est pas universelle dans la version actuelle.

## Aperçu, APK/AAB et Play Store

L’espace de résultat inclut maintenant un aperçu web temporaire lié à une tâche et à un utilisateur, avec expiration, révocation et QR code. Il ne constitue pas un déploiement public permanent tant que `ASSANE_PUBLIC_BASE_URL` n’est pas une URL HTTPS accessible et que le health check n’est pas validé.

Le parcours Android distingue l’APK debug, téléchargeable comme artefact de test, et l’AAB release, destiné à une piste Play Store après signature et configuration. L’adaptateur `google_play` existe côté serveur, mais aucune publication réelle n’a été effectuée dans l’environnement d’audit : le compte de service, les permissions Play Console et un AAB signé doivent être fournis par l’opérateur.
