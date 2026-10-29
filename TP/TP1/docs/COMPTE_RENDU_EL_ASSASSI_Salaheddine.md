# Choix du modèle — Cantine : prévision des repas servis

Date : 28/10/2026 · Groupe : G3 · Auteur : Salaheddine El Assassi

**Axe de ce rapport : comparaison des modèles et choix du modèle retenu.**

## Contexte
Le gestionnaire de la cantine doit décider chaque veille combien de repas préparer. Trop peu, des élèves restent sans repas ; trop, la nourriture est jetée. On prédit donc `repas_servis` (régression). Métrique principale : la **MAE** (erreur absolue moyenne), exprimée directement en **nombre de repas**, donc lisible par le gestionnaire. Une erreur de 20 repas en trop ou en moins a le même coût : la MAE pénalise les deux sens de la même façon.

## Données et découpage
- Fichier : `data/cantine_repas.csv`, **340 jours de service** (09/09/2024 → 19/06/2026), 11 colonnes, aucune valeur manquante dans la cible.
- Cible : `repas_servis` (moyenne 499, de 248 à 695 repas).
- Variables utilisées (toutes sauf la cible et la date) : `jour`, `inscrits`, `menu`, `temperature_c`, `pluie_mm`, `examens`, `sortie_scolaire`, `veille_vacances`, `repas_semaine_precedente`.
- `repas_semaine_precedente` est vide pour 60 jours (première semaine après chaque vacances) : imputée par la médiane dans `build_preprocessing()`.
- **Découpage chronologique** (série temporelle) : entraînement sur les 272 premiers jours (09/09/2024 → 24/02/2026), **test sur les 68 derniers jours** (25/02/2026 → 19/06/2026). Le modèle apprend le passé et il est évalué sur le futur.

Réglages de `config.py` : `DATA_PATH = ROOT / "data" / "cantine_repas.csv"`, `TARGET = "repas_servis"`, `TASK = "regression"`, `MAIN_METRIC = "mae"`, `SPLIT = "chronologique"`, `TIME_COLUMN = "date"`. **Aucune autre ligne de code n'a été modifiée** : les 8 tests passent tels quels.

## Résultats sur le jeu de test

| Modèle | MAE (repas, principale) | RMSE (repas) | R² |
|---|---|---|---|
| Baseline (moyenne d'entraînement, `DummyRegressor`) | 70,3 | 88,4 | −0,15 |
| **Régression linéaire** | **22,2** | **28,2** | **0,88** |
| Random Forest (200 arbres) | 31,8 | 41,6 | 0,75 |
| KNN (k = 15) | 38,4 | 48,2 | 0,66 |
| HistGradientBoosting | 39,0 | 51,0 | 0,62 |

## Décision
Modèle retenu : **la régression linéaire**, qui obtient la plus petite MAE (22,2 repas). Elle se trompe en moyenne de 22 repas sur environ 525 servis par jour pendant la période de test, soit environ **4 %**.

Elle bat largement la baseline : **−48 repas de MAE, soit 68 % d'erreur en moins** (70,3 → 22,2). Le R² négatif de la baseline montre qu'elle fait moins bien qu'une moyenne calculée sur la période de test : les effectifs augmentent (moyenne de 493 repas en entraînement, 525 en test).

Critère d'acceptation : MAE ≤ 30 repas sur le jeu de test chronologique **et** au moins 50 % sous la baseline → **atteint** (22,2 repas, −68 %).

Pourquoi la régression linéaire bat les modèles d'arbres : avec 272 jours d'entraînement, les effets sont surtout additifs (jour de la semaine, menu, examens, veille de vacances) et une droite les capte bien. Les arbres ne savent pas non plus extrapoler au-delà des valeurs vues : la hausse des inscrits (de 620 à 697) les pénalise. C'est aussi le modèle le plus simple à expliquer au gestionnaire.

## Limites
- **Jeu de test court** : 68 jours seulement, dont 10 jours d'examens, 4 sorties scolaires et 2 veilles de vacances ; l'erreur sur ces cas rares reste peu fiable.
- **Choix fait sur le test** : le modèle est choisi sur le même jeu qui sert à mesurer, donc sa MAE est légèrement optimiste ; une validation croisée temporelle serait plus rigoureuse.
- **Les cas rares restent difficiles** : la plus grosse erreur atteint 69 repas (vendredi 01/05/2026, 695 servis, 626 prédits).
- **Une seule cantine, deux années scolaires** : le modèle ne se transpose pas tel quel à un autre établissement.
- **Coûts symétriques supposés** : si un repas manquant coûte plus cher qu'un repas jeté, il faudrait viser une prévision légèrement au-dessus (quantile), plutôt que la MAE seule.
