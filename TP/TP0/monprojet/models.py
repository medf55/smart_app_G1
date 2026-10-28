"""Les modèles à comparer.

À vous d'écrire candidates(). Les tests de tests/test_models.py disent ce qui est attendu.
"""
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.linear_model import LinearRegression, LogisticRegression

from monprojet import config


def candidates() -> dict:
    """Renvoie un dictionnaire {nom: modèle scikit-learn non entraîné}.

    Attendu :
    - le PREMIER modèle est la baseline : le modèle le plus simple possible
      (DummyClassifier pour une classification, DummyRegressor pour une régression) ;
    - au moins trois vrais modèles ensuite, adaptés à config.TASK ;
    - random_state=config.SEED pour les modèles qui ont du hasard.

    Pistes : sklearn.dummy, sklearn.linear_model, sklearn.ensemble, sklearn.neighbors, sklearn.tree.
    """
    if config.TASK == "classification":
        return {
            "baseline": DummyClassifier(strategy="most_frequent"),
            "régression logistique": LogisticRegression(random_state=config.SEED, max_iter=1000),
            "forêt aléatoire": RandomForestClassifier(random_state=config.SEED, n_estimators=100),
            "gradient boosting": HistGradientBoostingClassifier(random_state=config.SEED),
            "régression logistique (balanced)": LogisticRegression(random_state=config.SEED, max_iter=1000, class_weight="balanced"),
        }
    else:
        return {
            "baseline": DummyRegressor(strategy="mean"),
            "régression linéaire": LinearRegression(),
            "forêt aléatoire": RandomForestRegressor(random_state=config.SEED, n_estimators=100),
            "gradient boosting": HistGradientBoostingRegressor(random_state=config.SEED),
        }
