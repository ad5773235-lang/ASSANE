# Google Play Developer API — exigences vérifiées

Source officielle consultée le 22 août 2026 : [Getting Started — Google Play Developer API](https://developers.google.com/android-publisher/getting_started).

La documentation indique que l’accès doit être configuré avec OAuth ou un compte de service. Pour un backend, le compte de service est généralement approprié ; ses identifiants doivent rester dans un environnement serveur sécurisé. Le compte de service doit être ajouté dans Google Play Console via **Users & Permissions** avec les droits nécessaires.

Le téléversement d’un AAB appartient au flux d’édition Play Developer API : un AAB doit d’abord être construit et signé correctement, puis téléversé dans une édition avant une mise en production ou une piste de test. Assane AI doit donc séparer les états `aab_built`, `upload_ready`, `uploaded_to_draft`, `awaiting_release_confirmation` et `released`.

Le ZIP ne doit jamais contenir la clé JSON du compte de service. Cette clé reste sur le backend, et le client Android ne reçoit qu’un état générique, un identifiant de piste non sensible ou un résultat vérifié. L’existence d’un AAB ne signifie pas que l’application est publiée sur Play Store.
