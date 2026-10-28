# ADR 002 : Validation des entrées de l'API et gestion du modèle absent

**Date :** 28/10/2026 · **Auteurs :** Faris Mohamed (Groupe G1)

---

## Contexte
L'API de prédiction de pannes MaintAI expose le modèle d'apprentissage supervisé à des clients distants (tableaux de bord, automates d'atelier, applications mobiles). Pour garantir la robustesse et la fiabilité du service, deux problématiques majeures se posent :
1. Comment valider les données de capteurs en entrée pour empêcher l'envoi de valeurs aberrantes ou corrompues au modèle Scikit-Learn sans bloquer de légitimes variations physiques ?
2. Quel comportement adopter lorsque l'API démarre mais que le fichier d'artefact du modèle (`models/model.joblib`) n'est pas encore présent sur le disque ?

---

## Décision 1 : Bornes physiques des capteurs

### Options étudiées
1. **Option A (Copier les min/max du jeu de données synthétique) :**
   - *Avantages :* Simple à extraire automatiquement depuis `sensors.csv`.
   - *Inconvénients :* Dangereux en production. Si une machine réelle en été monte à 95 °C alors que le dataset d'entraînement s'arrêtait à 93 °C, la requête serait rejetée à tort (faux rejet), privant l'équipe d'une alerte critique.
2. **Option B (Définir des bornes physiques admissibles réalistes) :**
   - *Avantages :* Cohérent avec les tolérances électromécaniques réelles des moteurs industriels, protège le modèle contre les valeurs extravagantes (ex. 500 °C ou vibrations négatives) tout en tolérant les dérives en conditions extrêmes.
   - *Inconvénients :* Nécessite une compréhension des grandeurs physiques manipulées.

### Décision retenue
Nous retenons l'**Option B**. Les bornes physiques configurées dans `SensorReading` sont :
- `temperature_c` (de **-40.0 °C à 150.0 °C**) : Un atelier non chauffé en hiver peut descendre en dessous de 0 °C ; un moteur électrique industriel supporte des échauffements de classe F/H jusqu'à 140-150 °C avant fusion d'isolant.
- `vibration_mm_s` (de **0.0 mm/s à 50.0 mm/s**) : Une vitesse vibratoire quadratique ne peut physiquement pas être négative ($ge=0$). La norme ISO 10816 classe une machine en état destructif bien avant 50 mm/s.
- `load_pct` (de **0.0 % à 120.0 %**) : La charge ne peut être négative ($ge=0$). Une charge nominale est de 100 %, mais une surcharge temporaire industrielle jusqu'à 120 % est courante et admise.
- `runtime_hours` (de **0.0 h à 100 000.0 h**) : Un compteur horaire démarre à 0 et ne peut être négatif. 100 000 heures représentent plus de 11 ans de fonctionnement continu (durée de vie limite d'un équipement lourd).

---

## Décision 2 : Comportement en cas de modèle absent au démarrage

### Options étudiées
1. **Option A (Refuser de démarrer / Crash au boot avec `raise FileNotFoundError`) :**
   - *Ce qu'elle fait perdre :* Perte totale de visibilité et d'observabilité. L'orchestrateur (Docker, Kubernetes) tente de redémarrer le conteneur en boucle (*CrashLoopBackOff*). La route `/health` devient inaccessible, empêchant les outils de monitoring de savoir *pourquoi* le conteneur est tombé.
2. **Option B (Démarrer en mode dégradé et répondre HTTP 503 sur `/predict`) :**
   - *Ce qu'elle fait perdre :* La fonction de prédiction n'est pas opérationnelle immédiatement.
   - *Ce qu'elle apporte :* Le serveur HTTP est en ligne, la documentation Swagger `/docs` reste explorable, et la route `GET /health` répond avec succès (`status: ok, model_loaded: false`), alertant précisément les équipes d'administration système sur la cause exacte (artefact manquant). Dès qu'un entraînement est déposé, l'API peut le recharger.

### Décision retenue
Nous retenons l'**Option B** : démarrer le serveur FastAPI même si le modèle est absent, signaler l'état dans `/health`, et renvoyer une erreur explicite **HTTP 503 Service Unavailable** sur `POST /v1/predict` indiquant clairement la procédure de remédiation (`python -m maintai.train`).

---

## Conséquences
- **Ce que cela facilite :** Intégration DevOps fluide avec les sondes de disponibilité (*readiness/liveness probes*), documentation interactive autonome, diagnostic instantané des pannes logicielles.
- **Ce qu'il faudra surveiller :** Prévoir un mécanisme de rechargement à chaud (*hot-reload*) du modèle sans avoir à redémarrer le serveur HTTP lorsque le fichier `.joblib` est mis à jour par un pipeline de réentraînement continu.
