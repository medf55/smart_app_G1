# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G1  ·  **Membres :** Faris Mohamed  ·  **Date :** 06/11/2026

> Ce fichier consigne les résultats, mesures et analyses de la Séance 5 (TP2).
> Les sorties de commandes et de tests sont extraites de l'environnement d'exécution réel.

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|:---:|:---:|
| 1 | champ manquant (`load_pct` omis) | 422 | 422 |
| 2 | valeur absurde (`load_pct` = 250) | 422 | 422 |
| 3 | texte au lieu d'un nombre (`temperature_c` = "chaud") | 422 | 422 |
| 4 | champ en trop (`extra_field` = 999) | 422 | 422 |
| 5 | mauvaise route (POST `/v1/inconnue`) | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Pour le **champ en trop**, avec la configuration par défaut de Pydantic, les champs non déclarés sont silencieusement ignorés et la requête aurait été acceptée avec un code `200 OK`. Notre prévision initiale selon laquelle l'API rejetterait tout champ inconnu n'aurait pas été respectée sans la directive explicite `model_config = ConfigDict(extra="forbid")`. Grâce à cette configuration stricte, l'API renvoie bien `422 Unprocessable Entity`, garantissant l'intégrité absolue du contrat d'interface.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```text
======================= 18 passed, 1 warning in 20.58s ========================
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`@pytest.mark.parametrize` permet d'exécuter la même fonction de test sur plusieurs jeux de données sans dupliquer le code. Pytest comptabilise **5 tests distincts** pour notre fonction `test_requete_refusee`, car la liste `CAS_REFUSES` contient 5 tuples d'arguments ; chaque tuple est instancié et évalué individuellement comme un cas de test à part entière dans le rapport d'exécution.

---

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```text
Found 3 errors (3 fixed, 0 remaining).
12 files reformatted, 8 files left unchanged
All checks passed!
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

- `ruff check .` est un outil d'**analyse statique** (linter). Il lit le code source sans l'exécuter et vérifie le respect des standards syntaxiques (PEP 8), la détection des variables orphelines, l'organisation des imports et la conformité du typage.
- `python -m pytest` est un outil d'**analyse dynamique** (tests d'exécution). Il exécute le programme dans l'interpréteur Python, charge les modèles d'apprentissage, simule des requêtes HTTP réelles via `TestClient` et vérifie si le comportement fonctionnel de l'API correspond rigoureusement aux assertions programmées.

---

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```text
================== 2 failed, 16 passed, 1 warning in 13.53s ===================
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

Les deux tests qui échouent sont :
1. `tests/test_security.py::test_missing_key_is_rejected`
2. `tests/test_security.py::test_wrong_key_is_rejected`

Ils reçoivent le code HTTP `200 OK` au lieu de `401 Unauthorized` car le routeur `/v1` du starter n'intègre pas encore de dépendance d'authentification pour intercepter et valider la clé `X-API-Key`.

---

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    settings = get_settings()
    if settings.api_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée sur le serveur",
        )
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Après avoir écrit `security.py` seul, il y a toujours **2 tests qui échouent**. La fonction `require_api_key` existe et est valide, mais elle n'est rattachée à aucun routeur : FastAPI n'a pas encore reçu la consigne de l'exécuter avant de traiter les requêtes arrivant sur `/v1/predict`.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```text
======================= 18 passed, 1 warning in 17.91s ========================
```

Requêtes testées sous `uvicorn maintai.api.main:app --reload --env-file .env` :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|:---:|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.12,"alert":false,"threshold":0.3,"model_version":"maintai-0.2.0"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500.0,"ctx":{"le":150.0}}]}` |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Cela illustre **l'ordre séquentiel des contrôles** dans FastAPI :
1. Les dépendances du routeur (`dependencies=[Depends(require_api_key)]`) sont évaluées en tout premier lieu. Si la clé est absente, la requête est immédiatement rejetée avec une erreur `401 Unauthorized` sans que le corps JSON ne soit analysé.
2. La désérialisation et la validation du modèle Pydantic (`SensorReading`) n'ont lieu que si l'authentification est passée avec succès. Avec la bonne clé, FastAPI analyse le payload et constate que 500 °C viole la contrainte `le=150`, renvoyant alors une erreur `422 Unprocessable Entity`.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

On obtient le code HTTP **`500 Internal Server Error`** (`{"detail":"Clé API non configurée sur le serveur"}`).  
Ce n'est pas un code 401 car le client n'est pas responsable d'une fausse clé : c'est le **serveur** qui présente un défaut d'administration (oubli du fichier `.env`, variable `api_key` non définie valant `None`). Selon les standards HTTP REST, les erreurs 4xx indiquent une anomalie imputable au client, tandis que les codes 5xx signalent une défaillance interne du serveur.

---

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const url = document.getElementById("url").value.replace(/\/+$/, "");
  const cle = document.getElementById("key").value;
  const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));

  try {
    const resp = await fetch(`${url}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": cle,
      },
      body: JSON.stringify(reading),
    });

    const data = await resp.json();

    if (!resp.ok) {
      const msg = data.detail 
        ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
        : `Statut HTTP ${resp.status}`;
      show("err", `Erreur ${resp.status} : ${msg}`);
      return;
    }

    const proba = (data.failure_probability * 100).toFixed(1);
    if (data.alert) {
      show("alert", `⚠️ ALERTE PANNE ! Probabilité : ${proba} % (Seuil : ${data.threshold})`);
    } else {
      show("ok", `✅ Machine saine. Probabilité de panne : ${proba} %`);
    }
  } catch (e) {
    show("err", "API injoignable ou requête bloquée par CORS");
  }
});
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | `✅ Machine saine. Probabilité de panne : 12.0 %` (cadre vert `.ok`) |
| 500 °C, bonne clé | `Erreur 422 : [{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150",...}]` (cadre orange `.err`) |
| relevé normal, fausse clé | `Erreur 401 : Clé API absente ou invalide` (cadre orange `.err`) |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

- **Message affiché sur la page :** `API injoignable ou requête bloquée par CORS`
- **Message dans la console du navigateur (F12) :**  
  `Access to fetch at 'http://localhost:8000/v1/predict' from origin 'http://localhost:5501' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

Le mécanisme **CORS** (*Cross-Origin Resource Sharing*) est une politique de restriction de sécurité implémentée **exclusivement par les navigateurs web** (*Same-Origin Policy*) afin d'empêcher un script exécuté depuis un site non autorisé d'accéder aux données d'une autre origine.  
`curl.exe` est un utilitaire HTTP autonome fonctionnant en ligne de commande : il n'évolue pas dans l'environnement d'un navigateur, n'envoie pas de pré-vol `OPTIONS` et ne subit pas les restrictions de la Same-Origin Policy.

---

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

Sans `headers=HEADERS`, **4 tests échouent** avec le code HTTP `401 Unauthorized` au lieu du code `422` attendu (car l'API vérifie la présence de la clé avant la désérialisation du JSON).  
Le seul cas qui passe quand même est le test de la **mauvaise route** (`/v1/inconnue`) qui renvoie bien `404 Not Found` : en effet, FastAPI résout les routes en premier et renvoie 404 avant même d'exécuter la moindre dépendance de sécurité sur un point de terminaison inexistant.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```text
======================= 23 passed, 1 warning in 10.92s ========================
```

---

## 7. Questions de compréhension

1. **Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?**
   - `401 Unauthorized` indique un défaut d'**authentification** : le client n'a pas prouvé son identité (clé API absente ou invalide).
   - `422 Unprocessable Entity` indique une erreur de **validation sémantique** : la requête est authentifiée, le JSON est valide syntaxiquement, mais les valeurs ne respectent pas le contrat métier (borne dépassée, type erroné).
   - `403 Forbidden` indique un défaut d'**autorisation** : l'identité du client est connue et authentifiée, mais ses privilèges ne l'autorisent pas à accéder à la ressource demandée.

2. **Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?**
   - Inscrire une clé secrète dans le code source l'immortalise dans l'historique Git et l'expose publiquement sur GitHub, compromettant irréversiblement la sécurité du système.
   - `.env` contient les secrets réels propres à l'environnement local (`MAINTAI_API_KEY=...`) et est strictement ignoré par Git (`.gitignore`).
   - `.env.example` sert de documentation pour l'équipe : il liste les variables requises avec des valeurs factices (`changez-moi`) et est **le seul à être commité**.

3. **Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?**
   - Les URLs sont systématiquement enregistrées en clair dans les logs d'accès des serveurs web, l'historique de navigation, les métriques des proxies réseau et les en-têtes `Referer`.
   - L'en-tête `X-API-Key` ne figure pas dans les journaux d'accès standards et bénéficie du chiffrement complet de session sous protocole HTTPS/TLS.

4. **Que fait `secrets.compare_digest` de plus qu'un simple `==` ?**
   - L'opérateur d'égalité `==` s'interrompt dès la détection du premier caractère incorrect (*early exit*), induisant une variation infinitésimale mais mesurable du temps de réponse (*timing attack* / attaque par canal auxiliaire) permettant à un attaquant de reconstituer la clé caractère par caractère.
   - `secrets.compare_digest` effectue une comparaison en **temps constant** quelle que soit la position des erreurs, neutralisant tout risque d'attaque temporelle.

5. **Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?**
   - Une origine est définie par le triplet indissociable : **protocole (schéma)**, **domaine (hôte)** et **port**.
   - `http://localhost:5500` et `http://localhost:8000` ont des numéros de port distincts (5500 vs 8000). Ce ne sont donc **pas la même origine**, ce qui rend obligatoire l'autorisation explicite via la politique CORS.

---

## 8. Le rendu Git

- Lien de la pull request : `https://github.com/medf55/smart_app_G1/pull/2`
- Le tag `tp2` existe sur GitHub : oui
- `git status` avant le commit : le fichier `.env` apparaissait-il ? non (strictement exclu)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?  
  *Revue de validation d'équipe : « Suite de 23 tests validée au vert, vérification faite qu'aucun secret .env n'est tracké par Git, implémentation CORS et client web fonctionnels. »*

---

## 9. Ce qui reste flou

La stratégie recommandée pour organiser la rotation des clés d'API en production sans interruption de service pour les systèmes industriels dépendants (par exemple en supportant temporairement deux clés valides lors de la transition).
