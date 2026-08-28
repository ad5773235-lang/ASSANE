# Résultats de vérification Cloudflare Pages

Sources officielles consultées le 22 août 2026 :

- https://developers.cloudflare.com/pages/configuration/api/
- https://developers.cloudflare.com/pages/get-started/direct-upload/

Cloudflare Pages propose une API pour gérer les projets et les déploiements. Le mode Direct Upload exige des assets déjà construits. La documentation officielle décrit un flux avec Wrangler `pages deploy` pour envoyer un dossier d’assets précompilés ; elle précise aussi qu’un projet Direct Upload ne peut pas être converti ensuite en projet Git-integrated.

L’adaptateur Assane AI doit donc distinguer création de projet et déploiement, détecter le répertoire de sortie du build, exclure les secrets, demander une confirmation avant l’action, puis suivre et vérifier le résultat. Une intégration par CLI exige que Wrangler soit présent dans un runner dédié et que le token Cloudflare ne soit jamais transmis à l’APK.
