# Contrat d’aperçu et de publication Assane AI

## Principe général

Assane AI ne doit jamais confondre un fichier construit, un aperçu local, un lien de test temporaire et une publication publique. Chaque résultat porte un état explicite, une date d’expiration éventuelle, une vérification et une action autorisée.

| Type de projet | Aperçu | Résultat de test | Livraison | Publication externe |
|---|---|---|---|---|
| Site statique ou frontend | Serveur d’aperçu temporaire ou URL de déploiement vérifiée | Lien HTTP et contrôle de disponibilité | URL publique, partage et QR code | Vercel ou Pages selon adaptateur configuré |
| Application Android | Résumé du build et, si disponible, page d’artefact | APK installable uniquement après build validé | Téléchargement APK ; AAB pour distribution | Play Store seulement après configuration développeur et confirmation distincte |
| Backend Python/Node | Aperçu uniquement si un hôte de test est configuré | Health check et journaux | URL ou image selon la cible | Adaptateur d’hébergement spécialisé requis |
| Docker | Aucun aperçu générique sans hôte | Image construite et test de démarrage | Image ou artefact | Registry + hôte explicitement configurés |

## États obligatoires

Le backend doit utiliser des états distincts : `draft`, `building`, `built`, `preview_ready`, `awaiting_confirmation`, `publishing`, `verifying`, `succeeded`, `failed`, `expired` et `cancelled`. Un état `succeeded` est autorisé seulement si l’artefact ou l’URL a été vérifié par le mécanisme correspondant.

## Aperçu et lien temporaire

Un aperçu web doit être isolé dans un workspace ou un conteneur, exposé par un service de preview contrôlé et limité dans le temps. Le lien doit être aléatoire, révocable et associé à l’utilisateur et à la tâche. Le QR code ne contient que ce lien temporaire ; il ne donne pas accès aux fichiers du backend ni aux secrets.

## Android et Play Store

`assembleDebug` produit éventuellement un APK de test. `bundleRelease` produit éventuellement un AAB, mais cela ne signifie pas qu’il est signé pour la distribution. La signature release, la clé privée et le compte développeur restent des prérequis séparés. Le bouton Play Store doit donc ouvrir une publication confirmée uniquement lorsqu’un compte développeur et un adaptateur de livraison sont configurés ; Assane ne doit pas promettre une publication simplement parce que l’AAB existe.

## Confirmation

La confirmation affiche le type de résultat, le nom du projet, les fichiers ou l’URL cible, la durée de validité et les risques. Une confirmation de publication web ne vaut pas confirmation d’envoi sur Play Store. Les secrets ne sont jamais affichés dans l’APK ni dans les messages utilisateur.
