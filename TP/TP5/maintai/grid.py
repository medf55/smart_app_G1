"""Grid search : essaie toutes les combinaisons de C et de seuil, chacune devient un run MLflow.

Le choix se fait par validation croisée sur le jeu d'entraînement (pas sur le test, pour ne pas tricher).
Le meilleur réglage est ensuite mesuré une seule fois sur le jeu de test.

Usage : python -m maintai.grid
        python -m maintai.grid --min-precision 0.5
"""
import argparse
import sys

from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from maintai.config import SEED, get_settings
from maintai.data import load_data, split
from maintai.tracking import log_run
from maintai.train import build_model, evaluate

GRID_C = [0.01, 0.1, 1.0, 10.0]
GRID_THRESHOLD = [0.15, 0.2, 0.25, 0.3, 0.4, 0.5]


def cv_scores(proba, y, threshold: float) -> dict:
    pred = (proba >= threshold).astype(int)
    return {
        "cv_recall": round(float(recall_score(y, pred)), 3),
        "cv_precision": round(float(precision_score(y, pred, zero_division=0)), 3),
        "cv_accuracy": round(float(accuracy_score(y, pred)), 3),
    }


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(prog="python -m maintai.grid")
    p.add_argument("--min-precision", type=float, default=0.5,
                   help="precision minimale acceptée (sinon trop de fausses alertes)")
    args = p.parse_args(argv or [])

    settings = get_settings()
    X_train, X_test, y_train, y_test = split(load_data(settings.data_path))
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    resultats = []
    for C in GRID_C:
        # probabilités « hors pli » : chaque relevé du train est prédit par un modèle qui ne l'a pas vu
        proba = cross_val_predict(build_model("logreg", C), X_train, y_train, cv=folds,
                                  method="predict_proba")[:, 1]
        model = build_model("logreg", C).fit(X_train, y_train)
        for threshold in GRID_THRESHOLD:
            cv = cv_scores(proba, y_train, threshold)
            test = evaluate(model, X_test, y_test, threshold)
            run_id = log_run(
                params={"model": "logreg", "C": C, "threshold": threshold,
                        "n_train": len(X_train), "search": "grid"},
                metrics=cv | {k: v for k, v in test.items() if k != "threshold"},
                model=model,
                X_example=X_train.head(3),
                data_path=settings.data_path,
            )
            resultats.append({"C": C, "threshold": threshold, **cv,
                              "recall": test["recall"], "precision": test["precision"],
                              "run_id": run_id})

    print(f"{'C':>6} {'seuil':>6} {'cv_recall':>10} {'cv_prec':>8} | {'recall':>7} {'prec':>6}")
    for r in resultats:
        print(f"{r['C']:>6} {r['threshold']:>6} {r['cv_recall']:>10} {r['cv_precision']:>8} | "
              f"{r['recall']:>7} {r['precision']:>6}")

    # critère : le meilleur recall en validation croisée, avec une precision minimale
    admissibles = [r for r in resultats if r["cv_precision"] >= args.min_precision] or resultats
    best = max(admissibles, key=lambda r: (r["cv_recall"], r["cv_precision"]))
    print(f"\nMeilleur réglage (cv_precision >= {args.min_precision}) : C={best['C']}, "
          f"seuil={best['threshold']}")
    print(f"  validation croisée : recall={best['cv_recall']}, precision={best['cv_precision']}")
    print(f"  jeu de test        : recall={best['recall']}, precision={best['precision']}")
    print(f"Run MLflow : {best['run_id']}")
    return best


if __name__ == "__main__":
    main(sys.argv[1:])