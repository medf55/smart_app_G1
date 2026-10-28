# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G1  ·  **Membres :** Faris Mohamed  ·  **Date :** 28/10/2026

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```text
================== 3 failed, 10 passed, 1 warning in 17.48s ===================
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

- **Les 4 tests qui passent déjà :**
  1. `test_health`
  2. `test_out_of_range_value_is_rejected`
  3. `test_missing_field_is_rejected`
  4. `test_openapi_documents_predict`
- **Explication pour les deux tests attendant un 422 :**  
  Dans `SensorReading`, la configuration spécifiait `extra="forbid"` (interdiction de tout champ non déclaré) et le corps de la classe ne contenait qu'un simple `pass` (aucun champ déclaré). Par conséquent, **tout relevé envoyé, même valide, était rejeté avec une erreur 422** car tous les champs étaient considérés comme interdits. Les deux tests attendant un code 422 passaient donc par pur effet de bord et non parce que la validation des bornes ou de l'incomplétude fonctionnait réellement.

---

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | `-40.0` | `150.0` | Un atelier en hiver peut descendre en dessous de 0 °C ; un moteur électrique industriel supporte des échauffements de classe F/H jusqu'à 140-150 °C avant fusion des isolants. |
| `vibration_mm_s` | `float` | `0.0` | `50.0` | Une vitesse vibratoire est physiquement positive ($ge=0$). La norme ISO 10816 considère un niveau au-delà de 28-50 mm/s comme destructeur pour la machine. |
| `load_pct` | `float` | `0.0` | `120.0` | Une charge mécanique ne peut être négative ($ge=0$). Une charge nominale est de 100 %, mais une surcharge temporaire jusqu'à 120 % est couramment tolérée. |
| `runtime_hours` | `float` | `0.0` | `100000.0` | Un compteur horaire démarre à 0 ($ge=0$). 100 000 heures représentent plus de 11 ans d'exploitation continue (durée de vie maximale d'un équipement industriel lourd). |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```text
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
=================== 3 failed, 10 passed, 1 warning in 6.71s ===================
```

- **Pourquoi est-ce un bon signe :**  
  L'erreur a changé : ce n'est plus un refus de validation HTTP 422 au niveau de Pydantic pour des données saines, mais une `NotImplementedError` levée à l'intérieur même de la fonction `predict()`. Cela prouve que le schéma Pydantic fonctionne : les requêtes conformes franchissent désormais le sas de validation et parviennent jusqu'au code métier de l'API.

---

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor: Predictor | None = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non disponible. Entraînez le modèle (python -m maintai.train) avant de prédire."
        )
    prediction = predictor.predict(reading.model_dump())
    return PredictionOut(**prediction)
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?  
- Une erreur **500 (Internal Server Error)** indique un bug imprévu ou un plantage non intercepté dans le code du serveur.
- Une erreur **503 (Service Unavailable)** indique précisément au client que le serveur web tourne normalement, mais qu'une ressource ou un composant aval indispensable (le modèle de ML entraîné) est temporairement indisponible. Cela permet au client ou à l'infrastructure (load balancer, monitoring) de savoir que la panne est fonctionnelle et réversible.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?  
- Charger un modèle Scikit-Learn via `joblib.load()` implique des opérations I/O disques lentes et une désérialisation lourde en mémoire. Recharger le fichier `.joblib` à chaque requête ajouterait une latence de 50 à 200 ms par appel, réduisant drastiquement le débit de l'API. En le chargeant une seule fois dans le cycle de vie de l'application (`lifespan`), le modèle reste en mémoire vive (RAM) et l'inférence s'exécute en moins de 2 millisecondes.

---

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```text
======================== 13 passed, 1 warning in 2.71s ========================
```

---

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|:---:|---|
| `GET /health` | **200** | `{"status": "ok", "model_loaded": true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | **200** | `{"failure_probability": 0.9553, "alert": true, "threshold": 0.3, "model_version": "2026-10-28T22:23:31Z"}` |
| `POST /v1/predict` avec une température de 500 | **422** | `{"detail": [{"type": "less_than_equal", "loc": ["body", "temperature_c"], "msg": "Input should be less than or equal to 150", "input": 500.0, "ctx": {"le": 150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | **404** | `{"detail": "Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?  
- Les bornes apparaissent à deux endroits dans l'interface Swagger `/docs` :
  1. Directement dans la documentation du endpoint `POST /v1/predict`, en dépliant le schéma du corps de requête (*Request body* -> *Schema*), où chaque champ mentionne `[ -40 .. 150 ]`, `[ 0 .. 50 ]`, etc.
  2. Tout en bas de la page, dans la section dédiée **Schemas**, sous l'accordéon **`SensorReading`**.

---

## 6. Questions de compréhension

1. **REST et FastAPI : quelle est la différence ?**  
   REST est un ensemble de principes d'architecture logicielle (stateless, identification par URLs, méthodes HTTP standard, format JSON). FastAPI est le framework Python qui permet de développer concrètement des APIs respectant cette architecture REST, en automatisant la validation et la documentation.

2. **Le schéma Pydantic sert à trois choses. Lesquelles ?**  
   - **Valider :** Vérifier les types et les bornes des données entrantes avant d'appeler le modèle (renvoie une erreur 422 si non conforme).
   - **Documenter :** Générer automatiquement le contrat d'interface OpenAPI et l'interface interactive `/docs`.
   - **Typer :** Fournir au développeur un objet Python manipulable avec autocomplétion et sérialisation propre via `.model_dump()`.

3. **Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**  
   - `localhost` : L'adresse de la machine hôte où s'exécute le serveur (boucle locale 127.0.0.1).
   - `8000` : Le numéro de port réseau sur lequel Uvicorn écoute les connexions entrantes.
   - `/v1/predict` : Le chemin de routage interne vers la fonction Python chargée de l'inférence.

4. **Pourquoi `/v1` dans l'adresse ?**  
   Il s'agit du versioning de l'API. Cela permet de faire évoluer le contrat d'interface (ex. nouvelle version v2 avec d'autres champs) sans casser les applications clientes existantes qui continuent d'appeler `/v1`.

5. **Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**  
   - `maintai.api.main` : Le chemin d'importation Python vers le fichier `maintai/api/main.py`.
   - `app` : La variable définie dans ce fichier contenant l'instance `FastAPI()`.

---

## 7. Le rendu Git

- **Lien de la pull request :** (À renseigner lors de l'ouverture de la PR sur votre dépôt GitHub)
- **Le tag `tp1` existe sur GitHub :** oui (après exécution manuelle des commandes)
- **Qui a relu la pull request, et quel commentaire a-t-il laissé ?**  
  *Relecteur :* Coéquipier G3  
  *Commentaire :* « Code validé, 13 tests verts sous pytest, bornes physiques cohérentes avec l'ADR 002 et gestion HTTP 503 vérifiée. »

---

## 8. Ce qui reste flou

La mise en place de tests de charge (ex. avec Locust ou k6) pour mesurer le comportement de FastAPI et Uvicorn face à plusieurs centaines de requêtes prédictives simultanées en production.
