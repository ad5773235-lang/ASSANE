# Interface observée dans les visuels disponibles

## Capture principale

`assane_ai_clean_interface_preview.png` montre une interface sombre de conversation Assane AI avec barre supérieure, actions de partage et copie, état « Tâche terminée » et zone de saisie avec pièces jointes, microphone et envoi. Cette capture inclut le clavier Android ; elle ne permet pas de confirmer tous les panneaux du nouveau dashboard.

## Capture Ordinateur d’Assane

`assane_ai_working_preview.png` montre un écran Android intitulé « Ordinateur d’Assane », un profil utilisateur, une zone de demande avec trombone et bouton « Lancer », puis une carte de travail avec « Assane réfléchit… », progression à 55 %, étape `decision` et un journal de travail. Le journal affiche l’analyse, la réflexion, l’exécution de `build_apk` et un résultat de runner en attente.

Ces visuels sont des previews du projet et non une capture live réalisée sur l’APK fourni le 24 août 2026. L’APK fourni a été inspecté par métadonnées : il n’avait pas d’icône déclarée. L’APK corrigé possède maintenant `res/drawable/ic_assane_ai.xml`; aucun appareil ou émulateur n’était connecté pour faire des captures runtime.

## Visuels complémentaires

`previews/assane_ai_app_icon.png` montre une proposition visuelle d’icône Assane AI inspirée des couleurs du Sénégal et d’un assistant. Elle sert de référence de design ; l’icône réellement embarquée dans l’APK corrigé est le vectoriel `res/drawable/ic_assane_ai.xml`.

`previews/assane_ai_execution_computer.png` montre une proposition desktop de l’Ordinateur d’Assane avec explorateur, éditeur, terminal, build, inspection de fichiers, tests et artefacts. Elle représente la structure fonctionnelle visée ; elle n’est pas une capture live prise depuis l’APK Android fourni.
