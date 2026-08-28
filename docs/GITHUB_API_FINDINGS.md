# Résultats de vérification de l’API GitHub

Sources officielles consultées le 22 août 2026 :

- https://docs.github.com/en/rest/repos/contents
- https://docs.github.com/en/rest/repos/repos

L’API GitHub permet de créer, modifier et supprimer du contenu Base64 dans un dépôt. Pour remplacer un fichier existant, le champ `sha` du blob courant est requis. Les jetons fine-grained doivent disposer au minimum de la permission `Contents: write` pour créer ou mettre à jour des fichiers.

La création d’un dépôt d’organisation se fait via l’API des dépôts et nécessite des permissions adaptées, avec un traitement différent entre dépôt personnel et dépôt d’organisation. L’adaptateur Assane AI doit donc limiter le périmètre au dépôt explicitement choisi, exclure les secrets et fichiers générés, préparer une liste de fichiers, demander confirmation, puis écrire et vérifier le commit. Il ne doit jamais créer ou pousser dans un dépôt arbitraire sans cible et confirmation liées à la demande.
