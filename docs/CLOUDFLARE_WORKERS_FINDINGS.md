# Vérification Cloudflare Workers API

Source officielle consultée le 22 août 2026 :

- https://developers.cloudflare.com/api/resources/workers/subresources/scripts/methods/update/

L’API historique permet d’envoyer un module Worker avec `PUT /accounts/{account_id}/workers/scripts/{script_name}`. Le jeton doit avoir au minimum la permission `Workers Scripts Write`. Le nom du script est un paramètre explicite. L’adaptateur doit refuser les fichiers arbitraires, choisir un point d’entrée Worker détecté, publier uniquement après confirmation et vérifier l’URL publique configurée.
