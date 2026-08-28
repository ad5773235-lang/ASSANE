# Inspection de l’APK Assane AI — 24 août 2026

## Résultat principal

L’APK fourni par l’utilisateur (`/home/ubuntu/upload/app-debug.apk`) a été inspecté directement. Il contient le package `com.assaneai.app`, la version `1.0` et le libellé `Assane AI`, mais sa métadonnée d’application ne déclare aucune icône : `application: label='Assane AI' icon=''`. Aucune ressource d’icône Assane spécifique n’était visible dans l’archive.

Son empreinte SHA-256 est `420a820959aed0ada6a8e051570e70dc57a89076f76b8b0a171363f77110e174`.

## Corrections appliquées au projet

Le manifeste Android déclare maintenant `@drawable/ic_assane_ai` pour `android:icon` et `android:roundIcon`. La ressource vectorielle `app/src/main/res/drawable/ic_assane_ai.xml` fournit une icône Assane AI visible dans le lanceur, avec fond sombre, symbole vert et accents jaune/rouge.

L’inscription Android possède maintenant un bouton explicite **Enregistrer et recevoir le code**. Le parcours affiche ensuite **Vérifie ton numéro**, explique que l’inscription est temporairement enregistrée, puis propose **Vérifier et activer**, **Renvoyer un code** et **Modifier les informations**. Le backend conserve l’inscription temporaire et ne crée le compte actif qu’après vérification OTP.

## Validation de la correction

L’APK corrigé a été compilé avec `assembleDebug` et contrôlé comme archive. Son empreinte SHA-256 est `fd1dbcdd4541268f7213151b699af51c01e6915dff8c524f36cb887bed740a6b`.

Les métadonnées de l’APK corrigé déclarent :

```text
application: label='Assane AI' icon='res/drawable/ic_assane_ai.xml'
application-icon-160:'res/drawable/ic_assane_ai.xml'
application-icon-240:'res/drawable/ic_assane_ai.xml'
application-icon-320:'res/drawable/ic_assane_ai.xml'
```

L’AAB release de validation a également été recompilé et son empreinte est `7796dfe7432b75e788d48e4b0c5a3aaf67cd877068192de70012fbda07bc93c9`.

## Limite de la vérification

Aucun appareil ou émulateur Android n’était connecté au moment du contrôle (`adb devices` ne listait aucun appareil). La présence de l’icône dans le manifeste et l’archive est donc vérifiée directement, tandis que l’apparence complète de l’écran sur un téléphone devra être confirmée par installation de l’APK corrigé sur ton appareil.
