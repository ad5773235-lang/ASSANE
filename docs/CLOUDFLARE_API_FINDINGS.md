# Vérification Cloudflare Pages API

Sources officielles consultées le 22 août 2026 :

- https://developers.cloudflare.com/api/resources/pages/subresources/projects/subresources/deployments/methods/create/
- https://developers.cloudflare.com/api/resources/pages/subresources/projects/subresources/deployments/methods/get/

La création utilise `POST /accounts/{account_id}/pages/projects/{project_name}/deployments` avec un token ayant au moins la permission `Pages Write`. La requête est `multipart/form-data`. Le corps peut contenir un manifeste des chemins et hashes, une branche et un répertoire de sortie de build. Le dépôt et le compte doivent avoir été autorisés dans Cloudflare Pages.

La consultation utilise `GET /accounts/{account_id}/pages/projects/{project_name}/deployments/{deployment_id}`. Le résultat expose notamment `latest_stage.status`, `latest_stage.name`, `is_skipped`, `url` et les alias. Le pipeline Assane AI doit considérer un déploiement réussi seulement après un statut de stage `success` et une vérification HTTP de l’URL retournée.
