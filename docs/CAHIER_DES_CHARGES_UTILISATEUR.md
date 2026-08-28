Oui. J’ai inspecté le ZIP Assane_AI_Online_Config_2026-08-24.zip, notamment l’APK source, le backend, Docker, l’authentification OTP, les configurations et les tests.
🔴 Verdict : ce n’est pas encore l’infrastructure que tu veux
Le projet est beaucoup plus avancé que ce que je pensais, mais Manus a laissé plusieurs éléments de développement/local qui empêchent de dire « ASSANE AI est prêt comme un service indépendant de mon PC ».
❌ 1. L’APK debug dépend encore du PC
Dans app/build.gradle.kts, le build debug utilise :
http://10.0.2.2:8000
10.0.2.2 sert à faire communiquer un émulateur Android avec le PC hôte. Ce n'est donc pas une adresse d'infrastructure publique.
Encore plus important : l'interface contient même un champ avec :
http://192.168.1.20:8000
et explique à l'utilisateur d'utiliser l'adresse IPv4 du PC.
➡️ Ça ne correspond pas à ton objectif final.
🟠 2. Le release est prévu pour une URL distante
Bonne nouvelle : le projet contient déjà un mécanisme beaucoup plus correct.
Le release récupère :
assaneBackendUrl
ASSANE_API_URL
ASSANE_RELEASE_BACKEND_URL
Donc Manus a prévu que tu puisses construire l'APK avec une véritable URL :
https://api.assane-ai.com
C'est la bonne direction.
Mais actuellement aucune vraie URL d'infrastructure n'est intégrée.
🟢 3. Le backend est réellement présent
Il y a un vrai backend FastAPI avec notamment :
/auth/register
/auth/register/resend
/auth/register/verify
/auth/login
/auth/me
/auth/logout
/tasks
/uploads
/media/generate-image
/health
Il y a également un orchestrateur IA, gestion des tâches, fichiers, artefacts, déploiement, etc.
Donc ce n'est pas juste une maquette frontend.
🟢 4. L'OTP est déjà bien commencé
J'ai vérifié le code OTP.
Il possède :
génération aléatoire du code ;
code à 6 chiffres ;
expiration ;
hash du code ;
vérification sécurisée ;
nombre maximal de tentatives ;
invalidation après utilisation ;
limitation des demandes ;
renvoi du code ;
abstraction du fournisseur SMS.
Il existe même un adaptateur Unimatrix.
Donc cette partie est déjà assez bien structurée.
Mais le ZIP est configuré par défaut avec :
ASSANE_SMS_PROVIDER=development
Donc actuellement il n'envoie pas réellement les SMS tant que tu n'as pas configuré un fournisseur SMS.
🟢 5. Les tests backend passent
J'ai exécuté les tests présents dans le projet :
12 tests réussis, 0 échec.
Il reste seulement des avertissements FastAPI concernant l'ancienne méthode on_event, mais ce n'est pas ce qui bloque ton architecture.
🟠 6. Docker est présent, mais ce n'est pas encore une infrastructure complète
Le projet possède :
docker-compose.yml
PostgreSQL
backend
volumes persistants
restart: unless-stopped
C'est une bonne base.
Mais il manque encore des éléments importants pour une vraie infrastructure de production :
                    INTERNET
                       │
                       ▼
                 HTTPS / Proxy
                       │
                       ▼
                 ASSANE API
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Backend   PostgreSQL  Redis
             │
             ▼
        AI Orchestrator
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
      IA    IA    IA
Le ZIP ne fournit pas encore toute cette infrastructure haute disponibilité.
🔥 Le problème principal
Manus a essentiellement créé :
un backend capable d'être hébergé
mais pas encore :
une infrastructure ASSANE AI réellement hébergée et indépendante de ton ordinateur.
C'est une différence importante.
Le ZIP est donc une bonne base logicielle, mais il faut maintenant passer à l'étape :
serveur réel → domaine → HTTPS → backend → base de données → SMS → APK release.
Et il y a une chose que je demanderais absolument à Manus de corriger
Il faut lui dire de supprimer la dépendance au PC pour le mode final, notamment :
10.0.2.2:8000
192.168.x.x:8000
localhost:8000
127.0.0.1
Les adresses locales peuvent rester dans une configuration de développement uniquement, mais elles ne doivent jamais être utilisées par l'APK de production.
Conclusion
Élément
État
APK
🟢 Présent
Backend FastAPI
🟢 Présent
Orchestrateur IA
🟢 Présent
Authentification
🟢 Présente
OTP
🟢 Bien commencé
Fournisseur SMS réel
🟠 À configurer
PostgreSQL
🟢 Prévu
Docker
🟢 Présent
URL publique réelle
🔴 Pas configurée
HTTPS production
🔴 Pas configuré
APK release connecté à ton infrastructure
🔴 Pas encore
Infrastructure indépendante du PC
🟠 Pas encore
Tests backend
🟢 12/12 réussis
Donc ne demande pas à Manus de refaire tout ASSANE AI depuis zéro. Il a déjà construit une base assez importante. Il faut plutôt lui demander de corriger cette base et de la transformer réellement en infrastructure en ligne indépendante du PC, puis nous pourrons vérifier le nouveau ZIP