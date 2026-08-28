# Nouvelle interface Assane AI

## Direction visuelle

La nouvelle interface reprend les références fournies par l’utilisateur comme inspiration de structure : une identité Assane AI visible, une navigation latérale ou un profil, une zone de création, l’état détaillé de la tâche, un aperçu, un espace de code, un terminal, des outils rapides, l’importation et la publication. Les couleurs vert, jaune et rouge restent propres à Assane AI. Les images fournies sont conservées dans `docs/ui_references/` comme références de conception et ne sont pas présentées comme des captures d’exécution réelle.

## Tableau de bord Android

L’accueil affiche maintenant une carte **Ordinateur d’Assane** avec un accès direct au navigateur et aux outils. Une bande d’étapes présente Analyse, Plan, Création, Tests et Finalisation. Lorsqu’une tâche est active, la carte affiche son état, sa progression calculée depuis l’état backend, son étape courante et le nombre de passages.

La grille **Outils puissants** donne accès au Navigateur pour inspecter une page publique, à Importer pour envoyer un fichier au workspace, à Image pour lancer la génération configurée, à Éditeur et Terminal via l’Ordinateur d’Assane, ainsi qu’à l’accès Aperçu. Les actions utilisent les callbacks déjà reliés au backend ; elles ne simulent pas une réussite locale.

## Fonctions conservées

L’écran de tâche garde le journal de travail, l’état « Assane travaille… », les boutons Arrêter et Continuer, l’aperçu temporaire avec QR code, le téléchargement d’artefacts, la construction APK/AAB conditionnée à la détection Android, la publication avec confirmation, l’appui long sur les événements de réponse et le profil complet.

Le dialogue Ordinateur d’Assane conserve le sélecteur Navigateur, Éditeur et Terminal. Le navigateur appelle l’inspection backend, bloque les URL privées selon les contrôles serveur et peut afficher les images publiques détectées. L’importation est envoyée au workspace de l’utilisateur authentifié. Les clés de fournisseurs restent dans le backend et ne sont jamais affichées dans l’APK.

## Validation

L’APK debug et l’AAB release ont été recompilés après l’ajout du tableau de bord. La compilation a réussi avec les avertissements de dépréciation d’icônes Android existants. Les tests backend précédents de l’intégration des niveaux et des routes authentifiées ont réussi avec 7 tests passés.
