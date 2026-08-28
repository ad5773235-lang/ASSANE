# Assane AI — rapport de remédiation du 22 août 2026

## Objet

Cette version corrige plusieurs défauts signalés par l’audit précédent sans transformer des composants conditionnels en promesses de production. Assane AI reste une application Android Compose reliée à un backend agentique Python/FastAPI. Les fournisseurs, les comptes de publication et le serveur d’exécution restent des prérequis opérateur ; leurs clés ne sont jamais embarquées dans l’APK.

## Expérience Android corrigée

L’application présente maintenant un accès visible à l’**Ordinateur d’Assane** depuis la barre supérieure et depuis chaque tâche active. Le panneau plein écran dispose d’un sélecteur d’application avec trois espaces : **Navigateur Assane**, **Éditeur Assane** et **Terminal Assane**. Le navigateur envoie une URL au backend, inspecte la page publique, affiche le titre et le texte extrait, récupère les aperçus d’images accessibles, puis propose de conserver explicitement ces images dans les artefacts de la tâche. L’éditeur et le terminal indiquent clairement le workspace isolé et le journal d’actions ; l’application Android ne lance pas de commande directement sur le téléphone.

Le flux de tâche affiche l’état, l’étape courante, la progression, le journal, l’arrêt et la reprise. L’appui long sur une ligne du journal ouvre les actions copier, partager et sélectionner. Les boutons APK/AAB ne sont plus proposés sur chaque tâche réussie : ils apparaissent uniquement lorsque le backend identifie le workspace comme projet Android. L’aperçu web temporaire, son QR code, la révocation et le téléchargement d’artefacts restent disponibles selon la configuration du backend.

## Fiabilité et persistance

Une table `jobs` a été ajoutée au stockage. La création d’une tâche, la reprise d’une tâche et la confirmation d’une publication insèrent désormais un job en file. Le worker intégré réserve les jobs avec transaction, évite les doublons actifs, récupère les jobs marqués `running` après un redémarrage et applique jusqu’à trois tentatives avec délai progressif. Cette solution est **persistante dans la base mais mono-processus** : elle ne constitue pas encore une file distribuée multi-régions ni un remplacement de Redis/Celery pour une grande production.

Le bouton Arrêter demande aussi au runner de terminer le processus local ou le conteneur Docker associé. Le contrôle d’annulation intervient entre les étapes de l’orchestrateur et peut interrompre un processus en cours lorsque le runner le permet. Une tâche stoppée doit être reprise par l’action Continuer ; aucune réussite n’est déclarée uniquement parce qu’une commande de lancement a été envoyée.

## Stockage, sessions et isolation

Les sessions signées sont maintenant enregistrées côté serveur avec identifiant, expiration, empreinte et date de révocation. La nouvelle route de déconnexion invalide réellement la session ; l’effacement Android reste un complément local. Les tâches et les artefacts sont filtrés par `user_id`. Les artefacts généraux sont valides même avant la création d’une tâche, et un test a couvert l’accès croisé entre deux comptes.

Chaque artefact persiste désormais sa taille. Un quota configurable par compte empêche le dépassement de stockage, tandis que la taille maximale d’upload est configurable. Les quotas ne remplacent pas un stockage objet durable : le backend utilise encore son volume local et doit être relié à S3, MinIO ou un service équivalent pour une haute disponibilité.

## PostgreSQL

Le backend accepte maintenant `ASSANE_DATABASE_URL` avec un adaptateur PostgreSQL et un schéma PostgreSQL dédié. Le fichier `docker-compose.yml` contient un service PostgreSQL 16, un healthcheck, un volume de données et un backend dépendant de l’état sain de la base. **La compatibilité de configuration et le schéma sont présents ; une migration de données depuis une base SQLite existante et un test de bout en bout sur un serveur PostgreSQL distant restent à effectuer.** SQLite demeure le défaut hors Compose pour le développement local.

## Sécurité et configuration de production

En mode `ASSANE_ENV=production`, le backend refuse le secret de session par défaut, une URL publique non HTTPS, le CORS `*` et le runner local. Les variables de quotas, de durée maximale de tâche et d’URL de base de données sont documentées dans `.env.example`. Le fichier `.env` réel, lorsqu’il est utilisé par l’opérateur, doit rester local au serveur et ne doit pas être envoyé dans une archive.

## Validation effectuée dans cette version

| Élément | Résultat vérifié | Limite restante |
|---|---|---|
| Syntaxe Python backend | `compileall` réussi | Pas un test de charge |
| Isolation artefacts, sessions, reprise jobs | 3 tests pytest réussis | Tests locaux SQLite |
| Configuration Compose | `docker-compose config` réussi avec modèle non secret | Aucun lancement complet de stack réalisé |
| SDK Android | platform-tools, Android 35 et Build-Tools 34/35 installés | Pas d’émulateur connecté |
| APK debug | `assembleDebug` réussi ; ZIP APK intègre ; SHA-256 `a69e58e4e8d146627066a051b811888ad3329fc56c795327c26d0bcf4903a83a` | APK debug, non signé release |
| AAB release | Non annoncé comme produit | Signature et validation Play Console nécessaires |
| Navigateur et extraction d’images | Parcours backend déjà présent ; nouveau panneau Android relié | Nécessite Playwright installé et accès réseau au déploiement |
| Vercel, GitHub, Cloudflare, Play Store | Adaptateurs et préconditions conservés | Aucun compte réel ni secret utilisé pour un E2E |

## Ce que cette version ne prétend pas

Cette archive ne prétend pas déployer n’importe quel runtime sans cible ni compte, ne prétend pas publier sur Play Store, ne prétend pas fournir un stockage objet haute disponibilité, et ne prétend pas que le worker intégré est un orchestrateur distribué. Les URLs publiques et les identifiants de publication doivent être renseignés par l’opérateur dans le backend. L’interface Assane AI ne montre pas les noms de fournisseurs ni les clés ; cela masque l’implémentation côté utilisateur sans supprimer les prérequis techniques côté serveur.

## Authentification OTP SMS ajoutée

L’inscription Android est maintenant suivie d’une vérification OTP. Le backend crée une inscription temporaire, hache le code, limite les tentatives et les demandes, invalide les anciens codes et n’active le compte qu’après vérification. Le service SMS est abstrait derrière `SmsProvider`; le mode développement n’envoie pas de SMS réel et la production refuse ce mode ainsi que la journalisation du code. Les tests OTP et les tests existants totalisent 9 tests réussis au dernier contrôle.
