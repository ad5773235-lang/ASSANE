# Confidentialité réseau et comportement Android

## Appels réseau

L’APK communique uniquement avec l’API backend Assane AI. Les clés de Manus, Mistral, OpenAI, Vercel, GitHub, Cloudflare, Stability et Deepgram restent dans l’environnement du serveur. Elles ne sont ni compilées dans l’APK, ni envoyées au client, ni affichées dans l’interface utilisateur.

L’interface parle de services Assane AI, d’un workspace, d’une publication ou d’une vérification. Elle ne doit pas prétendre qu’aucun service réseau n’est utilisé : le backend et les fournisseurs configurés sont des composants techniques nécessaires à certaines fonctions.

## Ouvertures d’applications

Le manifeste Android ne déclare pas d’intent-filter pour les fichiers, les liens web, l’installation de paquets ou les APK. Assane AI n’ouvre donc pas automatiquement une autre application et n’accepte pas implicitement qu’un fichier ou un APK externe soit lancé dans l’application.

L’activité principale reste exportée uniquement parce qu’Android exige ce comportement pour une activité lancée depuis l’icône. Le partage de réponse est une action séparée, déclenchée exclusivement après un appui explicite sur « Partager » ; il ouvre le sélecteur Android normal. Les actions d’importation utilisent le sélecteur de fichiers Android pour que l’utilisateur choisisse volontairement un fichier.

La configuration `android:allowBackup="false"` est utilisée pour réduire l’exposition automatique des données locales de session. Les APK importés sont inspectés comme fichiers et ne sont pas exécutés par Assane AI.
