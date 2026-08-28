# Résultats de vérification de l’API Vercel

Sources officielles consultées le 22 août 2026 :

- https://vercel.com/docs/rest-api/deployments/create-a-new-deployment
- https://vercel.com/docs/rest-api/deployments/upload-deployment-files

L’API de création utilise `POST https://api.vercel.com/v13/deployments`. Pour un déploiement sans Git, les fichiers doivent être téléversés auparavant ou inclus directement pour les petits contenus, puis référencés dans le corps de création. La réponse contient notamment un identifiant de déploiement et `readyState`, qui évolue vers `READY` ou `ERROR` après les états de construction.

L’upload utilise `POST https://api.vercel.com/v2/files`. Le contenu est envoyé dans le corps de la requête. Les en-têtes `Content-Length` et `x-Vercel-Digest` servent à transmettre la taille et le SHA-1 du fichier. La réponse est normalement vide pour un fichier déjà présent ou téléversé avec succès.

L’adaptateur Assane AI doit donc : calculer le SHA-1 de chaque fichier, limiter la taille et le nombre de fichiers, téléverser les fichiers, créer le déploiement avec les références SHA/size, interroger l’état par identifiant, traiter `READY` et `ERROR`, puis vérifier l’URL retournée avec une requête HTTP. Aucun état `READY` ne doit être déduit du seul succès de l’upload.
