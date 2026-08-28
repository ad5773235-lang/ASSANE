# Authentification OTP SMS Assane AI

## Principe

L’inscription Assane AI est maintenant en deux étapes. Le frontend envoie les informations de compte au backend. Le backend crée une inscription temporaire, génère un code aléatoire à six chiffres, stocke uniquement son hash, associe le code à une demande unique et demande au fournisseur SMS de transporter le message. Le compte `users` n’est créé et activé qu’après vérification correcte du code.

Le fournisseur SMS ne décide pas si le code est valide. Il ne reçoit que la destination et le message à transporter. La génération, l’expiration, les tentatives, l’invalidation d’un ancien code et l’activation sont contrôlées par Assane AI.

## Routes

| Route | Rôle |
|---|---|
| `POST /auth/register` | Crée une inscription temporaire et demande l’envoi d’un code |
| `POST /auth/register/verify` | Vérifie le code et active le compte |
| `POST /auth/register/resend` | Invalide le code précédent et en demande un nouveau |
| `POST /auth/login` | Connexion ultérieure avec e-mail et mot de passe |
| `POST /auth/logout` | Révocation de la session serveur |

La réponse d’inscription ne contient jamais le code OTP. Elle contient uniquement un identifiant de demande, un identifiant d’inscription temporaire, un numéro masqué et l’expiration. L’application Android affiche ensuite l’écran « Vérifie ton numéro ».

## Sécurité

Les codes sont générés avec une source aléatoire cryptographique, hachés avec le contexte de la demande et invalidés lorsqu’un nouveau code est demandé. Une demande est limitée à cinq tentatives par défaut, expire après cinq minutes et est soumise à une limite de demandes par heure. Ces valeurs sont configurables côté serveur. Le code est à usage unique et les demandes utilisées, expirées, échouées ou remplacées ne peuvent plus être acceptées.

Les inscriptions temporaires conservent le hash du mot de passe, jamais le mot de passe en clair. Elles sont supprimées après activation. La table `users` contient `phone_verified`, et le profil public peut indiquer cet état sans exposer de données sensibles.

## Fournisseur SMS

`backend/app/auth/sms_provider.py` définit `SmsProvider`. En développement, `DevelopmentSmsProvider` ne contacte aucun réseau réel. Le code n’est écrit dans les logs que si `ASSANE_SMS_LOG_OTP=true`, ce qui doit rester réservé au développement local. En production, `ASSANE_SMS_PROVIDER=development` et `ASSANE_SMS_LOG_OTP=true` sont refusés par la validation de configuration.

Le fournisseur réel doit être implémenté côté serveur derrière cette interface, à partir des identifiants fournis par l’opérateur. Il ne faut jamais placer son token dans l’APK, dans un fichier partagé, dans le chat ou dans une archive livrée.

## Test local

Pour tester le parcours sans envoyer de SMS réel, utilise le mode `development` et un fournisseur de test injecté dans la suite pytest. Les tests ne doivent pas transformer un code fixe en mécanisme de production. Le mode développement ne doit pas être déployé publiquement.
