# ADR 003 : Sécurisation de l'API MaintAI (Clé API et politique CORS)

Date : 06/11/2026 · Auteurs : Faris Mohamed (Groupe G1)

---

## Contexte
L'API REST MaintAI expose en inférence un modèle prédictif d'arrêt machine pour l'usine. Dans un environnement industriel connecté, cette API ne doit répondre qu'aux clients autorisés (systèmes de supervision SCADA, applications web de maintenance et clients automatisés). 

Deux décisions architecturales critiques doivent être arrêtées :
1. **Le mode de transmission de la clé secrète d'authentification** entre le client et l'API.
2. **La politique d'autorisation des origines (CORS)** pour les applications web interagissant avec l'API depuis un navigateur.

---

## Décision 1 : Transmission de la clé API via l'en-tête HTTP `X-API-Key`

### Options étudiées
1. **Option A : Transmission dans l'URL (ex. `/v1/predict?api_key=...`)**
   - *Inconvénients majeurs :* L'URL complète est enregistrée en clair dans de multiples composants d'infrastructure : historiques des navigateurs, journaux d'accès des serveurs web (access logs), proxies d'entreprise, métriques d'observabilité et en-têtes HTTP `Referer`. Si la clé apparaît dans l'URL, elle est inévitablement divulguée à des tiers.
2. **Option B : Transmission dans le corps JSON de la requête (Request Body)**
   - *Inconvénients majeurs :* Cette approche est inapplicable aux requêtes sans corps (méthodes `GET` telles que les endpoints de consultation ou de santé protégés). De plus, elle mélange artificiellement les données métier du problème (`SensorReading`) avec les métadonnées de transport et de sécurité, violant le principe de séparation des responsabilités.
3. **Option C : Transmission dans l'en-tête standard `X-API-Key` (Option retenue)**
   - *Avantages :* Les en-têtes HTTP ne sont pas enregistrés dans les journaux d'accès par défaut. En production sous HTTPS/TLS, l'intégralité des en-têtes est chiffrée de bout en bout. Cette méthode s'applique uniformément à toutes les méthodes HTTP (`GET`, `POST`, `PUT`, `DELETE`) et respecte les standards de l'industrie pour les APIs REST.

### Décision retenue
Nous retenons l'**en-tête HTTP personnalisé `X-API-Key`**, validé en amont par une dépendance FastAPI (`require_api_key`) exploitant une comparaison en temps constant (`secrets.compare_digest`) afin de neutraliser toute attaque temporelle (*timing attack*).

---

## Décision 2 : Politique d'origine CORS par liste blanche restrictive configurable

### Options étudiées
1. **Option A : Origine universelle `allow_origins=["*"]` (Wildcard)**
   - *Inconvénients majeurs :* N'importe quel site web malveillant exécuté dans le navigateur d'un opérateur ou d'un ingénieur de l'usine pourrait émettre des requêtes vers l'API interne (`http://localhost:8000` ou IP locale) à son insu. Cela élimine la protection fondamentale du modèle *Same-Origin Policy* des navigateurs.
2. **Option B : Liste blanche explicite configurée via variable d'environnement (`MAINTAI_CORS_ORIGINS`) (Option retenue)**
   - *Avantages :* Seules les origines de confiance déclarées (par exemple l'interface web locale `http://localhost:5500` et `http://127.0.0.1:5500`) sont autorisées à interagir avec l'API via le navigateur. Toute autre origine (comme le port 5501 ou un domaine externe non enregistré) est immédiatement bloquée par le navigateur lors de la négociation préalable (pré-vol HTTP `OPTIONS`).

### Décision retenue
Nous configurons le middleware `CORSMiddleware` avec une **liste stricte d'origines autorisées**, chargée dynamiquement depuis la variable d'environnement `MAINTAI_CORS_ORIGINS` définie dans `.env`.

---

## Conséquences

- **Bénéfices :**
  - Confidentialité garantie : la clé n'apparaît jamais dans les logs ni dans le code source Git.
  - Résilience aux attaques par canal auxiliaire : temps de comparaison constant sur la clé secrète.
  - Cloisonnement navigateur : protection stricte contre les requêtes inter-origines non autorisées.
  - Découplage complet : les clients non-navigateurs (`curl`, microservices, scripts d'ingénierie) ne sont pas perturbés par les politiques CORS.
- **Contraintes à surveiller :**
  - Tout nouvel outil web officiel (dashboard Streamlit, front-end de production) devra avoir son origine explicitement ajoutée à `MAINTAI_CORS_ORIGINS`.
  - Le fichier local `.env` doit obligatoirement être configuré sur chaque environnement de déploiement et rester exclu des commits Git (`.gitignore`).
