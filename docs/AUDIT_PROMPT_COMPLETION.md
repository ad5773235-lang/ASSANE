# Audit et compléments d’Assane AI

**Date de contrôle : 24 août 2026**

Ce document décrit l’amélioration incrémentale réalisée à partir du projet Assane AI existant. Le projet n’a pas été reconstruit depuis zéro. Les fonctions déjà présentes ont été conservées et les compléments ont été ajoutés autour de l’interface de l’Ordinateur d’Assane.

## Références visuelles conservées

Les deux images envoyées pour la nouvelle interface sont conservées dans le projet sous les noms suivants :

| Référence | Emplacement dans le projet | Usage |
| --- | --- | --- |
| Interface de travail 01 | `docs/ui_references/reference_ordinateur_assane_01.png` | Référence principale de l’Ordinateur d’Assane |
| Interface de travail 02 | `docs/ui_references/reference_ordinateur_assane_02.png` | Référence complémentaire pour la densité et la navigation |

Elles ne sont pas supprimées par la refonte. Les anciennes images restent uniquement des archives de comparaison et ne remplacent pas ces deux nouvelles références.

## Vérification des fonctions

| Fonction demandée | État après contrôle | Complément réalisé ou limite honnête |
| --- | --- | --- |
| Création de compte prénom, nom, e-mail, téléphone et mot de passe | Présente | Le compte est activé après vérification OTP. |
| OTP SMS | Intégré côté serveur | Un adaptateur Unimatrix réel est ajouté. L’envoi réel nécessite les identifiants Unimatrix du propriétaire du serveur. |
| Connexion persistante et déconnexion | Présente | Sessions signées et révocables conservées. |
| Tâches agentiques | Présente | Les tâches, états, événements, arrêt et reprise restent branchés au backend. |
| Historique | Complété | `GET /tasks` et `BackendClient.listTasks()` chargent les tâches réellement enregistrées du compte. Aucune conversation inventée n’est affichée. |
| Isolation des comptes | Renforcée | La liste d’historique est filtrée par `user_id` et un test entre deux comptes est ajouté. |
| Ordinateur d’Assane | Amélioré | Navigation compacte avec Accueil, Historique et Ordinateur, plus sections Navigateur, Fichiers, Éditeur, Terminal, Aperçu, Build et Publication. |
| Navigateur et inspection | Conservée | Inspection d’URL publique, extraction et affichage d’images publiques, conservation en artefact lorsque l’utilisateur le demande. |
| Importation | Conservée et exposée dans l’Ordinateur | Le bouton ouvre le sélecteur Android et envoie le fichier au workspace du compte. |
| Éditeur et terminal | Conservés | L’application indique l’espace de travail et les événements réels ; l’exécution est faite par le backend et son runner, pas par le téléphone lui-même. |
| Aperçu et QR code | Conservés | Le backend prépare un lien temporaire ; l’application affiche le lien et le QR code lorsqu’il est fourni. |
| APK/AAB et téléchargement | Conservés | Les builds dépendent du SDK, du runner et de la signature disponibles sur le serveur. |
| Publication | Conservée | Une demande de confirmation est requise avant l’exécution d’une publication sensible. |
| Génération d’images | Conservée | Elle dépend d’un fournisseur d’image réellement configuré côté serveur. |
| Icône principale Android | Vérifiée | L’icône est déclarée comme `@drawable/ic_assane_ai` dans le manifeste et n’est pas affichée comme grand logo dans l’écran de connexion. |
| Profil, apparence et instructions | Conservés | Aucun écran Crédits ou Mise à niveau n’est ajouté. |

## Modifications techniques principales

Le stockage possède maintenant `list_tasks_for_user`, qui renvoie les tâches d’un utilisateur avec le nombre d’événements et le dernier message réellement enregistré. La route `GET /tasks` utilise la session authentifiée. Le client Android possède `listTasks`, et le modèle `AssaneTask` contient les résumés nécessaires à l’écran Historique.

L’Ordinateur d’Assane reste basé sur le `ComputerDialog` existant. Son sélecteur ne se limite plus au Navigateur, à l’Éditeur et au Terminal : il expose également Fichiers, Aperçu, Build et Publication. Les callbacks utilisent les fonctions existantes d’importation, de preview, de build et de déploiement au lieu d’afficher une réussite fictive.

L’adaptateur `UnimatrixSmsProvider` utilise l’API HTTP officielle Unimatrix `sms.message.send`. Le mode simple utilise l’AccessKey ID. Le mode HMAC utilise également l’AccessKey Secret et signe les paramètres de requête. Le code OTP continue d’être généré, haché et vérifié par Assane AI ; Unimatrix sert de transport SMS.

## Limites qui restent visibles

Un SMS ne peut pas être déclaré réellement envoyé tant que le serveur n’a pas reçu un AccessKey ID valide, que le compte Unimatrix n’est pas autorisé à envoyer vers le Sénégal et qu’un test réel n’a pas confirmé la réception. De même, un build, un aperçu ou une publication ne sont pas déclarés réussis si le backend ou le fournisseur correspondant n’a pas réellement retourné et vérifié le résultat.

Aucun secret n’est placé dans l’APK, dans les images de référence ou dans l’archive source. Seul `.env.example` contient les noms de variables attendus.

## Références techniques

[1]: https://www.unimtx.com/docs/api/general "Unimatrix API General Reference"
[2]: https://www.unimtx.com/docs/api/send "Unimatrix SMS Messaging API"
[3]: https://www.unimtx.com/docs/get-started "Unimatrix Get Started"
