# Ticket de sortie · Séance 5

**Nom :** Faris Mohamed · **Groupe :** G1  
**Date :** 06/11/2026

---

### 1. Quelle différence entre 401 et 422 ?
- **401 Unauthorized :** Erreur d'**authentification**. L'API ne sait pas qui appelle ou refuse l'accès car la clé `X-API-Key` est absente ou invalide. Le corps de la requête n'est même pas examiné.
- **422 Unprocessable Entity :** Erreur de **validation des données**. Le client est authentifié avec succès, le JSON est bien formé, mais les données soumises violent les règles du contrat Pydantic (ex. température de 500 °C supérieure au maximum physique de 150 °C, champ manquant ou champ non autorisé avec `extra="forbid"`).

---

### 2. Pourquoi la clé n’est-elle ni dans le code ni dans Git ?
La clé API est un secret cryptographique qui confère un droit d'accès privilégié à l'API. Si elle se trouve dans le code ou dans l'historique de Git, elle est stockée de manière permanente et devient immédiatement accessible à quiconque consulte le dépôt sur GitHub. Pour garantir la sécurité, elle doit résider dans un fichier d'environnement local `.env` ignoré par Git (`.gitignore`), tandis que seul `.env.example` (contenant une fausse valeur indicative) est commité pour documenter les paramètres attendus.

---

### 3. Pourquoi curl fonctionne-t-il alors que la page du port 5501 est bloquée ?
Le mécanisme **CORS** (*Cross-Origin Resource Sharing*) est une politique de sécurité implémentée **exclusivement au sein des navigateurs web** (*Same-Origin Policy*). Elle protège l'utilisateur en empêchant un script s'exécutant sur un site tiers (ici servi sur le port 5501) d'envoyer des requêtes vers l'API sans accord explicite du serveur via l'en-tête `Access-Control-Allow-Origin`.  
À l'inverse, **`curl.exe` est un utilitaire HTTP autonome en ligne de commande** : il n'exécute aucun moteur de navigateur, n'envoie pas de requête pré-vol `OPTIONS` et n'applique pas la *Same-Origin Policy*. Il dialogue directement avec le serveur sans être soumis aux restrictions CORS.

---

### 4. Qu’est-ce qui reste flou pour vous ?
Comment concevoir une procédure propre de rotation des clés d'API en environnement de production continu, de manière à permettre la transition des applications clientes vers une nouvelle clé sans provoquer d'interruption de service temporaire.
