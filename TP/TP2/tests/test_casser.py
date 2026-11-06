import pytest

HEADERS = {"X-API-Key": "test-key"}
VALID = {
    "temperature_c": 60.0,
    "vibration_mm_s": 2.0,
    "load_pct": 50.0,
    "runtime_hours": 5000.0,
}

CAS_REFUSES = [
    (
        "champ manquant",
        "/v1/predict",
        {k: v for k, v in VALID.items() if k != "load_pct"},
        422,
    ),
    ("valeur absurde", "/v1/predict", {**VALID, "load_pct": 250.0}, 422),
    (
        "texte au lieu d'un nombre",
        "/v1/predict",
        {**VALID, "temperature_c": "chaud"},
        422,
    ),
    ("champ en trop", "/v1/predict", {**VALID, "extra_field": 999}, 422),
    ("mauvaise route", "/v1/inconnue", VALID, 404),
]


@pytest.mark.parametrize("description, url, corps, attendu", CAS_REFUSES)
def test_requete_refusee(client, description, url, corps, attendu):
    assert client.post(url, json=corps, headers=HEADERS).status_code == attendu
