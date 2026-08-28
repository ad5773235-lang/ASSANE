# Vérification GitHub Git Database API

Sources officielles consultées le 22 août 2026 :

- https://docs.github.com/en/rest/git/trees
- https://docs.github.com/en/rest/git/refs

Un commit multi-fichiers peut être construit avec des blobs, un tree basé sur le tree courant, un commit, puis une mise à jour de la référence de branche. L’API des trees demande la permission fine-grained `Contents: write`. Pour ne pas supprimer les fichiers existants, le nouveau tree doit utiliser le `base_tree` du commit courant.

Une branche est une référence Git qui pointe vers un commit. L’adaptateur doit donc lire la référence de branche, conserver son SHA attendu, créer les objets Git, puis mettre à jour la référence. Un conflit au moment de la mise à jour doit être traité comme un échec, jamais comme une publication réussie.
