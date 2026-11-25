# ADR 004 : choix du modèle et du seuil d'alerte de MaintAI

Date : 25/11/2026 · Auteurs : Salah Eddine El Assassi, [coéquipiers]

## Contexte
MaintAI doit signaler les machines qui risquent de tomber en panne. Une panne manquée (faux négatif) coûte bien plus
cher qu'une fausse alerte (une inspection inutile) : le critère principal est donc le **recall**, la precision vient
ensuite. Les cinq runs ci-dessous sont dans l'expérience MLflow `maintai`, entraînés sur les mêmes données (v1, 5000 relevés).

| Run | recall | precision | accuracy |
|---|---|---|---|
| logreg, C=1.0, seuil 0.3 | 0.750 | 0.622 | 0.904 |
| logreg, C=0.01, seuil 0.3 | 0.691 | 0.653 | 0.908 |
| **logreg, C=1.0, seuil 0.2** | **0.838** | **0.543** | **0.882** |
| forest, seuil 0.3 | 0.728 | 0.562 | 0.886 |
| forest, seuil 0.2 | 0.831 | 0.479 | 0.854 |
| baseline (toujours « pas de panne ») | 0.000 | – | 0.864 |

## Options étudiées
1. **Régression logistique, C=1.0, seuil 0.3 (actuel)** : bon compromis, mais laisse passer 1 panne sur 4.
2. **Régression logistique, C=0.01** : meilleure precision, mais recall plus faible : rejeté, il manque plus de pannes.
3. **Forêt aléatoire (seuil 0.3 ou 0.2)** : plus lourde et plus lente, et moins bonne que la régression logistique
   à seuil égal, en recall comme en precision. Elle n'apporte rien sur ces données.
4. **Régression logistique, C=1.0, seuil 0.2** : le meilleur recall de tous les runs.

## Décision
On retient la **régression logistique, C=1.0, seuil d'alerte 0.2**, parce qu'elle a le meilleur recall (0.838) :
c'est elle qui manque le moins de pannes, ce qui est la contrainte principale du projet.

- Identifiant du run MLflow : `[run_id du run --threshold 0.2]`
- `data_md5` des données : `[data_md5 du run, identique au md5 de data/sensors.csv.dvc v1]`

## Conséquences
- On accepte plus de fausses alertes : la precision passe de 0.622 à 0.543, soit environ une alerte sur deux
  qui ne correspond pas à une vraie panne. Les équipes de maintenance feront plus d'inspections inutiles.
- L'accuracy baisse un peu (0.904 → 0.882) : ce n'est pas la bonne métrique ici (la baseline fait déjà 0.864).
- Le seuil 0.2 doit devenir la valeur de `MAINTAI_THRESHOLD` en production.
- À surveiller : le recall et la precision à chaque nouvelle version des données (dérive), en comparant les runs
  dans MLflow avec leur `data_md5`.
