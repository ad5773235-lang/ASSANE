# Cycle agentique complet d’Assane AI

Assane AI n’est pas limité à une réponse textuelle. Le backend contient un orchestrateur qui reçoit la demande, sélectionne les Skills, expose seulement les outils autorisés au modèle, exécute les actions dans le workspace de la tâche et enregistre les observations.

## Cycle principal

```text
Demande utilisateur
  → réflexion et plan
  → sélection des Skills
  → choix d’un outil
  → éditeur ou ordinateur isolé
  → résultat réel
  → observation et événement
  → correction ou prochaine action
  → test
  → artefact
  → confirmation si nécessaire
  → téléchargement, partage ou déploiement
```

## Capacités incluses dans la structure

Le registre prévoit la lecture et l’écriture de fichiers, l’exécution de commandes autorisées, la compilation et les tests Android, l’inspection de liens publics, l’inspection de documents, d’images et d’APK, la génération d’images avec un fournisseur configuré, la persistance du workspace, le téléchargement et le partage d’artefacts, ainsi que la demande de déploiement.

Une action irréversible ou externe doit renvoyer `requires_confirmation` au lieu d’être exécutée directement. La publication sur GitHub, Vercel ou Cloudflare doit donc être complétée par un adaptateur et une confirmation explicite avant l’envoi final.

## Ordinateur et éditeur

Le workspace appartient à la tâche et à l’utilisateur. Le runner local est destiné au développement. Le runner Docker durci utilise un réseau désactivé, un système de fichiers en lecture seule sauf le workspace, la suppression des capabilities Linux, `no-new-privileges`, des limites de processus, de mémoire et de CPU, puis détruit le conteneur à la fin de la commande.

Pour un APK inconnu, Assane AI doit d’abord inspecter l’archive et ses métadonnées. Il ne doit pas installer automatiquement un APK téléchargé ni l’exécuter sur le serveur principal.

## Images et fichiers

Une image générée ou importée devient un artefact. Le backend conserve son hash SHA-256 et son chemin privé. L’APK Android peut ensuite demander le téléchargement de l’artefact ou l’afficher après authentification. Les clés des fournisseurs restent côté backend.

## Connaissance du Sénégal

Les instructions globales indiquent qu’Assane AI doit être utile sur le Sénégal. Cette règle ne signifie pas qu’il connaît automatiquement chaque événement. Pour une information récente, il doit utiliser une source connectée et mentionner l’origine de l’information lorsqu’elle est disponible.

## Profils

Chaque compte utilisateur est séparé par son identifiant. Le compte contient le prénom, le nom, l’e-mail, le téléphone, le mot de passe haché, les tâches, les événements et les artefacts. Assane AI ne doit jamais donner à un utilisateur les fichiers ou l’historique d’un autre compte.

Le propriétaire global configuré est Assane Moussa Goudiaby. Cette information est une instruction d’identité de l’assistant et ne remplace pas le profil de l’utilisateur connecté. Si une personne demande qui est le propriétaire, Assane AI peut donner le nom configuré.
