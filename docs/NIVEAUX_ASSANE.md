# Niveaux Assane AI

## Principe

Les niveaux **Assane Moyen**, **Assane Fiable** et **Assane Élevé** sont des politiques de capacité du backend. Ils ne représentent pas trois modèles d’intelligence artificielle distincts et ne fournissent aucune clé externe. Le modèle IA réellement utilisé dépend de la configuration serveur, tandis que le niveau détermine les limites et les fonctions autorisées.

## Application des politiques

Chaque compte reçoit `assane_moyen` à son inscription. Le niveau est enregistré dans la table `account_tiers`, liée à l’identifiant utilisateur interne. Les routes `GET /tiers`, `GET /tier`, `GET /tier/limitations` et `PUT /tier` exigent une session Bearer valide. Le client Android ne transmet pas un identifiant de compte arbitraire pour sélectionner un niveau.

Le niveau est appliqué aux tâches simultanées, au nombre maximal d’itérations de l’orchestrateur, à la génération d’images, au build Android release et aux cibles de publication autorisées. Les contrôles du navigateur, de l’inspection, du runner et des artefacts du backend principal continuent de s’appliquer à tous les niveaux.

## Interface utilisateur

Le profil Android comporte une section **Capacités Assane** et une entrée **Niveau Assane**. Le dialogue présente les trois niveaux sous forme de cartes avec leur description, le nombre d’étapes, les tâches simultanées, les cibles et les fonctions disponibles. Aucun crédit, tarif, fournisseur ou secret n’est affiché.

## Limites

Le changement de niveau n’installe pas PostgreSQL, Docker, un modèle local, un navigateur ou une clé fournisseur. Pour une utilisation réelle, les prérequis du backend doivent être installés et configurés. La publication Google Play exige toujours un AAB signé, un compte développeur et une confirmation explicite.
