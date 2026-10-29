# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 29/10/2026

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'al...
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
3 failed, 10 passed, 1 warning in 40.29s
```

Les 4 tests de `tests/test_api.py` qui passent déjà sont :

- `test_health` : `/health` est déjà codé dans `main.py`, et le modèle est entraîné par la fixture.
- `test_openapi_documents_predict` : la route `/v1/predict` est déclarée, donc elle apparaît dans `/openapi.json` même si son corps n'est pas écrit.
- `test_out_of_range_value_is_rejected` (attend 422).
- `test_missing_field_is_rejected` (attend 422).

Les deux tests 422 passent pour une mauvaise raison. `SensorReading` ne déclare encore aucun champ, et `extra="forbid"` refuse tout champ inconnu. Les quatre variables envoyées sont donc toutes des champs « en trop », et Pydantic rejette **n'importe quelle** requête avec 422. Le code 422 ne vient ni d'une borne dépassée (température à 500) ni d'un champ manquant (`load_pct`). D'ailleurs, une requête valide reçoit aussi 422 : c'est ce que montrent les échecs `assert 422 == 200` et `assert 422 == 503`.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | -40 °C : machine dans un local non chauffé en hiver. 150 °C : limite thermique courante des isolants de moteurs électriques (classe F/H) ; au-delà, la mesure est fausse ou la machine est hors service. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vitesse de vibration efficace est positive par définition. La norme ISO 10816 classe déjà « dommage » au-delà d'environ 11 mm/s ; 50 mm/s laisse une marge, mais au-delà le capteur est en défaut. |
| `load_pct` | `float` | 0 | 120 | 0 % : machine à vide. Une surcharge brève au-delà du nominal est possible, jusqu'à environ 120 % ; au-delà, les protections coupent la machine. |
| `runtime_hours` | `float` | 0 | 200 000 | Un compteur d'heures ne peut pas être négatif. 200 000 h ≈ 23 ans de fonctionnement continu, au-delà de la durée de vie d'une machine industrielle. |

Code écrit :

```python
temperature_c: float = Field(
    ge=-40, le=150,
    description="Température de la machine en °C (de -40 °C en atelier non chauffé à 150 °C, limite des isolants de moteur)",
)
vibration_mm_s: float = Field(
    ge=0, le=50,
    description="Vitesse de vibration efficace en mm/s (positive ; au-delà de 50 mm/s la machine serait déjà détruite, ISO 10816)",
)
load_pct: float = Field(
    ge=0, le=120,
    description="Charge en % de la charge nominale (0 = à vide ; surcharge brève tolérée jusqu'à 120 %)",
)
runtime_hours: float = Field(
    ge=0, le=200000,
    description="Heures de fonctionnement cumulées (positives ; 200 000 h ≈ 23 ans en continu, durée de vie maximale)",
)
```

Après avoir écrit `schemas.py` seul :

```
>       raise NotImplementedError
E       NotImplementedError
maintai\api\main.py:46: NotImplementedError
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplemente...
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed, 1 warning in 12.45s
```

Il y a toujours 3 échecs, mais l'erreur a changé : ce n'est plus `422`, c'est `NotImplementedError`. C'est bon signe : les requêtes valides passent maintenant la validation Pydantic et arrivent jusqu'à la fonction `predict()`. Le schéma fonctionne ; il ne reste qu'à écrire le corps de la route. Les deux tests 422 passent désormais pour la bonne raison (borne dépassée, champ manquant).

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non disponible : lancez d'abord python -m maintai.train",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

500 (Internal Server Error) signale un bug imprévu dans le code. Ici, rien n'a planté : le service est temporairement indisponible parce que le modèle n'a pas encore été entraîné. 503 (Service Unavailable) dit exactement cela : la requête est correcte et le serveur fonctionne, mais il ne peut pas la traiter pour l'instant. Le client sait qu'il peut réessayer plus tard. Un outil de supervision, lui, distingue une panne de code d'un déploiement incomplet.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger le modèle veut dire lire `model.joblib` sur le disque, le désérialiser et lire `model_info.json`. Cela prend beaucoup plus de temps que la prédiction elle-même. Le faire à chaque requête augmenterait la latence et la charge disque, et l'API tiendrait beaucoup moins de requêtes par seconde. Charger dans `lifespan` garde le modèle en mémoire (`state`) et le partage entre toutes les requêtes. Une erreur (modèle absent) est aussi détectée dès le démarrage et signalée par `/health`.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 12.62s
```

(Le seul avertissement est une `StarletteDeprecationWarning` sur `httpx`, interne à la bibliothèque de test ; il ne vient pas de notre code.)

## 5. L'API en marche

Entraînement (`python -m maintai.dataset` puis `python -m maintai.train`) :

```
5000 relevés écrits dans ...\data\sensors.csv (taux de panne : 13.6%)
{
  "model":    { "accuracy": 0.904, "recall": 0.75, "precision": 0.622, "threshold": 0.3 },
  "baseline": { "accuracy": 0.864, "recall": 0.0 },
  "n_train": 4000,
  "n_test": 1000
}
```

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-29T00:00:16Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la section **Schemas**, en bas de la page, sur le schéma `SensorReading` : chaque champ affiche son `minimum`, son `maximum` et sa `description`. On les voit aussi dans l'onglet « Schema » du corps de requête de `POST /v1/predict`. Elles viennent de `/openapi.json`, par exemple pour la température :

```json
{"type": "number", "maximum": 150.0, "minimum": -40.0, "title": "Temperature C",
 "description": "Température de la machine en °C (de -40 °C en atelier non chauffé à 150 °C, limite des isolants de moteur)"}
```

## 6. Questions de compréhension

1. **REST et FastAPI : quelle est la différence ?**
   REST est un style d'architecture, un ensemble de conventions pour concevoir une API sur HTTP : des ressources identifiées par des URL, des verbes HTTP (GET, POST…), des codes de statut et un fonctionnement sans état. FastAPI est un framework Python qui sert à implémenter une API, REST ou non. REST est la façon de concevoir ; FastAPI est l'outil qui la code.

2. **Le schéma Pydantic sert à trois choses. Lesquelles ?**
   - **Valider** les données entrantes : types, champs obligatoires, bornes, champs inconnus refusés, avec un 422 automatique.
   - **Convertir et typer** : le JSON devient un objet Python typé (`reading.temperature_c` est un `float`), et la réponse est sérialisée en JSON (`PredictionOut`).
   - **Documenter** : FastAPI en tire le schéma OpenAPI, affiché dans `/docs` avec les bornes, les descriptions et l'exemple.

3. **Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**
   `localhost` est l'hôte, c'est-à-dire la machine elle-même (adresse 127.0.0.1). `8000` est le port sur lequel uvicorn écoute. `/v1/predict` est le chemin de la ressource, la route qui exécute la fonction `predict()`.

4. **Pourquoi `/v1` dans l'adresse ?**
   C'est le numéro de version de l'API. Si le contrat change un jour (nouvelle variable, autre format de réponse), on publie `/v2/predict` sans casser les clients qui utilisent encore `/v1`. Les deux versions peuvent coexister pendant la migration.

5. **Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**
   `maintai.api.main` est le module Python à importer, c'est-à-dire le fichier `maintai/api/main.py`. `app` est le nom de la variable de ce module qui contient l'application ASGI (`app = FastAPI(...)`), que uvicorn sert.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp1` existe sur GitHub : oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 8. Ce qui reste flou

- Le choix du seuil d'alerte (0,3) : il augmente le rappel (0,75 contre 0 pour la baseline) au prix de la précision (0,622). Comment le fixer avec le métier (coût d'une panne ratée contre coût d'une fausse alerte) ?
- Les bornes du schéma sont des choix physiques génériques. Avec des machines réelles, il faudrait les valider avec les fiches techniques des capteurs.
