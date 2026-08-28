# Cibles de déploiement Assane AI

Assane AI utilise un registre explicite d’adaptateurs. Une cible n’est considérée comme disponible que si l’adaptateur correspondant est enregistré et si son exécution termine par une vérification positive.

| Cible | État | Fonctionnement |
|---|---|---|
| Vercel | Disponible sous conditions | Upload de fichiers, création, suivi et vérification HTTP |
| GitHub | Disponible sous conditions | Création de blobs, tree basé sur la branche, commit atomique, mise à jour de référence et relecture du SHA |
| Cloudflare Pages | Disponible sous conditions | Déploiement multipart Pages, suivi du stage puis vérification HTTP |
| Cloudflare Workers | Disponible sous conditions | Upload d’un module Worker explicitement détecté puis vérification de l’URL publique |
| Backend Python/Node | Préparation seulement | Détection du runtime et prérequis ; aucun hébergeur générique n’est supposé |
| Docker | Préparation seulement | Détection et runner ; registry, hôte et rollback restent à configurer |
| Android | Artefact seulement | Build/test avec SDK et JDK dans l’image Android dédiée ; distribution non automatisée |

Les noms des fournisseurs restent côté backend. L’APK envoie une demande générique à l’API Assane AI et reçoit uniquement l’état, l’URL ou l’artefact. Cette séparation n’élimine pas la dépendance réseau : elle empêche seulement les clés et les détails d’intégration de se retrouver dans l’application.

Une publication doit suivre le cycle `analyse → prérequis → build → manifeste → confirmation → exécution → suivi → vérification`. L’API ne doit jamais renvoyer `succeeded` parce qu’un upload ou une commande locale a simplement réussi.

## Espace de résultat

Pour les sites statiques et frontends, Assane AI peut maintenant créer un aperçu temporaire dans le workspace avec URL configurable et QR code. Le lien est révocable et l’accessibilité doit être vérifiée sur un serveur réellement exposé.

Pour Android, la sortie est séparée en APK debug téléchargeable pour test et AAB release destiné à une piste de distribution. Le bouton Play Store ne constitue une publication que si un compte de service serveur, les permissions Play Console, la signature et la confirmation de release sont configurés.

| Résultat | État |
|---|---|
| Aperçu web temporaire | Disponible sous conditions, avec expiration et révocation |
| QR code d’aperçu | Disponible si la dépendance QR est installée |
| APK debug | Route de build et artefact propriétaire ; SDK/runner requis |
| AAB release | Route de build et artefact propriétaire ; signature/SDK requis |
| Play Store | Adaptateur serveur sous conditions ; jamais de clé dans l’APK |
