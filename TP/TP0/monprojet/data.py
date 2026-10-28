"""Chargement et découpage des données.

À vous d'écrire load_data() et split(). Les tests de tests/test_data.py disent ce qui est attendu.
"""
import pandas as pd
from sklearn.model_selection import train_test_split  # noqa: F401  (utile pour split)

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    """Lit le fichier CSV et renvoie un DataFrame.

    Attendu :
    - lire config.DATA_PATH (ou `path` s'il est donné) ;
    - si la colonne config.TARGET n'existe pas, lever une ValueError avec un message clair ;
    - retirer les lignes où la cible est manquante.

    Pistes : pd.read_csv, df.columns, df.dropna(subset=[...]).
    """
    filepath = path if path is not None else config.DATA_PATH
    df = pd.read_csv(filepath)
    if config.TARGET not in df.columns:
        raise ValueError(f"La colonne cible '{config.TARGET}' est absente du fichier {filepath}")
    df = df.dropna(subset=[config.TARGET])
    return df


def feature_columns(df: pd.DataFrame) -> list:
    """Les colonnes d'entrée : celles de config.FEATURES, ou toutes sauf la cible et la date. (Fournie.)"""
    if config.FEATURES is not None:
        return list(config.FEATURES)
    excluded = {config.TARGET, config.TIME_COLUMN}
    return [c for c in df.columns if c not in excluded]


def split(df: pd.DataFrame):
    """Renvoie X_train, X_test, y_train, y_test.

    Attendu :
    - X = les colonnes de feature_columns(df) ; y = la colonne cible ;
    - si config.SPLIT == "random" : un découpage aléatoire de taille config.TEST_SIZE,
      avec la graine config.SEED, et stratifié sur y pour une classification ;
    - si config.SPLIT == "chronologique" : trier selon config.TIME_COLUMN et garder
      les lignes les plus récentes pour le test (le modèle apprend le passé, il est testé sur le futur).

    Pistes : train_test_split(..., test_size=..., random_state=..., stratify=...) ;
    pd.to_datetime(...).argsort() ; X.iloc[...].
    """
    features = feature_columns(df)
    X = df[features]
    y = df[config.TARGET]

    if config.SPLIT == "chronologique":
        if config.TIME_COLUMN not in df.columns:
            raise ValueError(f"La colonne temporelle '{config.TIME_COLUMN}' est absente.")
        order = pd.to_datetime(df[config.TIME_COLUMN]).argsort()
        X_sorted = X.iloc[order]
        y_sorted = y.iloc[order]
        n_test = int(round(len(df) * config.TEST_SIZE))
        n_train = len(df) - n_test
        X_train, X_test = X_sorted.iloc[:n_train], X_sorted.iloc[n_train:]
        y_train, y_test = y_sorted.iloc[:n_train], y_sorted.iloc[n_train:]
        return X_train, X_test, y_train, y_test
    else:
        stratify = y if config.TASK == "classification" else None
        return train_test_split(
            X, y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=stratify
        )
