# Inspection de sites et images publiques

Le parcours Android est : l’utilisateur saisit une URL, le backend vérifie qu’elle est publique, le navigateur headless récupère le titre et le contenu, puis `extract_images` collecte les images `img` et les images Open Graph accessibles publiquement. Chaque URL d’image est résolue par rapport à l’URL finale, vérifiée contre les réseaux privés, limitée en nombre et en taille, puis téléchargée côté backend.

Les réponses contiennent des métadonnées, un aperçu JPEG encodé pour l’affichage Android et l’URL source. Les téléchargements ne deviennent pas automatiquement des artefacts permanents. Le bouton « Conserver les images » relance l’action avec `save=true` ; le backend exige alors l’identité de l’utilisateur et écrit chaque fichier dans son espace d’artefacts propriétaire.

Les règles de sécurité sont les suivantes : seuls `http` et `https` sont acceptés ; les adresses loopback, privées, réservées et link-local sont refusées ; les redirections sont contrôlées ; le nombre d’images est plafonné à 12 ; chaque image est limitée à 5 MiB ; les autres types MIME sont ignorés ; une URL externe n’est jamais considérée comme un fichier local avant son téléchargement explicite.

L’extraction ne contourne pas les droits d’auteur, les contrôles d’accès ou les règles du site. Elle ne récupère que des ressources publiquement accessibles et doit respecter les conditions applicables à la conservation ou à la redistribution.
