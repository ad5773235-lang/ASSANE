# Intégrations réelles d’Assane AI

Le backend d’Assane AI contient des adaptateurs HTTP pour Manus, Mistral, GitHub, Vercel, Cloudflare, OpenAI, Stability AI et Deepgram.

Les clés sont lues uniquement par `backend/app/core/config.py` depuis `.env`. Le client Android ne reçoit jamais ces valeurs. Il reçoit seulement une session Assane AI et l’URL du backend.

## Manus

L’adaptateur utilise `POST https://api.manus.ai/v2/task.create` avec `Authorization: Bearer $MANUS_API_KEY` et un corps `message` contenant le texte, les connecteurs, les Skills et les références de tâche. La base est configurable via `MANUS_API_BASE_URL`.

## Modèles texte

Mistral est appelé via l’API de chat avec `MISTRAL_API_KEY`, `MISTRAL_API_BASE_URL` et `MISTRAL_MODEL`. OpenAI est appelé via l’API compatible `/chat/completions` avec `OPENAI_API_KEY`, `OPENAI_API_BASE_URL` et `OPENAI_TEXT_MODEL`.

## GitHub, Vercel et Cloudflare

Le backend utilise des jetons Bearer côté serveur. GitHub expose un endpoint d’identité `/user`, Vercel un endpoint de projets `/v9/projects` et Cloudflare un endpoint de vérification de jeton `/user/tokens/verify`. Les bases URL restent configurables dans `.env`.

## Images, audio et transcription

OpenAI peut être utilisé pour la génération d’images via `/images/generations`. Stability AI utilise l’endpoint de génération d’image configuré dans `STABILITY_API_BASE_URL`. Deepgram reçoit les octets audio via `/v1/listen` avec `Authorization: Token $DEEPGRAM_API_KEY`.

## Règle de fonctionnement

Une clé vide ne produit jamais une réponse inventée. L’adaptateur renvoie une erreur de configuration, l’orchestrateur enregistre l’événement et l’interface affiche le problème. Il faut renseigner les clés réelles dans `.env`, redémarrer le backend et vérifier les permissions de chaque fournisseur.

## Sources officielles utilisées

- Manus API : https://open.manus.ai/docs/v2/introduction
- Manus task.create : https://open.manus.ai/docs/v2/task.create
- Mistral API : https://docs.mistral.ai/api/
- OpenAI API : https://platform.openai.com/docs/api-reference
- GitHub REST API : https://docs.github.com/rest
- Vercel REST API : https://vercel.com/docs/rest-api
- Cloudflare API : https://developers.cloudflare.com/api/
- Stability AI API : https://platform.stability.ai/docs/api-reference
- Deepgram API : https://developers.deepgram.com/reference/introduction
