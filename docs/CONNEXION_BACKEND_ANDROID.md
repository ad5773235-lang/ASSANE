# Connexion de l’APK Android au backend Assane AI

## Cause la plus fréquente pendant l’inscription

Dans un APK installé sur un téléphone, `127.0.0.1` et `localhost` désignent le téléphone lui-même. Ils ne désignent pas le PC qui exécute Assane AI Core. L’émulateur Android utilise généralement `10.0.2.2` pour atteindre le PC hôte, mais cette adresse ne convient pas à un téléphone physique.

## Téléphone et PC sur le même Wi-Fi

Dans PowerShell sur le PC Windows, lancer le backend en écoutant sur le réseau local :

```powershell
py backend/run.py
```

Le projet utilise par défaut `ASSANE_HOST=0.0.0.0` et le port `8000`. Il faut ensuite connaître l’adresse IPv4 du PC :

```powershell
ipconfig
```

Repérer l’adresse IPv4 de la carte Wi-Fi, par exemple `192.168.1.20`. Tester depuis le navigateur du téléphone :

```text
http://192.168.1.20:8000/docs
```

Si cette page ne s’ouvre pas, autoriser le port 8000 dans le pare-feu Windows sur le réseau privé et vérifier que les deux appareils sont sur le même réseau.

Dans l’application Assane AI, avant de créer le compte, toucher **Configurer l’adresse du backend**, saisir l’adresse IPv4 réelle du PC, puis enregistrer :

```text
http://192.168.1.20:8000
```

Ne pas saisir `127.0.0.1` depuis le téléphone. L’APK debug autorise le HTTP local uniquement pour ce scénario de développement. Pour la production, utiliser une vraie URL HTTPS avec un certificat valide.

## Émulateur Android

Avec un émulateur Android standard, l’adresse par défaut `http://10.0.2.2:8000` peut atteindre le PC hôte. Avec un appareil physique, il faut l’adresse IPv4 du PC comme expliqué ci-dessus.

## Ce qui ne change pas

L’inscription appelle toujours `/auth/register`, puis le backend génère et envoie l’OTP. Le code OTP n’est pas généré dans l’APK. L’icône principale Android, les deux références visuelles et les fonctions de l’Ordinateur d’Assane ne sont pas concernés par ce correctif réseau.
