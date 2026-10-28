# Choix du modèle — MaintAI

**Date :** 28/10/2026 · **Groupe :** G1 · **Auteurs :** Faris Mohamed

---

## Contexte
L'usine souhaite anticiper les pannes sur ses lignes de production à partir de relevés capteurs quotidiens pour planifier les inspections ciblées. Une panne non détectée arrête la chaîne de production toute une journée, tandis qu'une fausse alerte ne mobilise le technicien que pendant une heure. La métrique principale retenue est le **rappel (recall)** afin de minimiser au maximum les pannes manquées.

---

## Données et découpage
- **Fichier :** `data/exemple_pannes.csv`
- **Volume :** 5 000 relevés de capteurs synthétiques.
- **Colonnes prédictives :** `temperature_c`, `vibration_mm_s`, `load_pct`, `runtime_hours`.
- **Cible :** `failure` (classification binaire, 17,6 % de pannes).
- **Découpage :** Aléatoire stratifié (`SPLIT = "random"`, `SEED = 42`), 80 % en entraînement (4 000 lignes) et 20 % en test tenu strictement à l'écart (1 000 lignes).

---

## Résultats sur le jeu de test

| Modèle | Rappel (métrique principale) | Accuracy | Précision | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline (most_frequent)** | 0.000 | 0.824 | 0.000 | 0.000 |
| **Forêt aléatoire** | 0.545 | 0.873 | 0.671 | 0.602 |
| **Régression logistique (standard)** | 0.574 | 0.889 | 0.737 | 0.645 |
| **Gradient boosting** | 0.574 | 0.881 | 0.697 | 0.629 |
| **Régression logistique (balanced)** | **0.847** | 0.839 | 0.527 | 0.649 |

---

## Décision
Le modèle retenu est la **régression logistique avec pondération équilibrée (`class_weight="balanced"`)** (ou alternativement le modèle avec ajustement de seuil de décision à 0,3).
- **Comparaison à la baseline :** Il bat largement la baseline qui n'identifie aucune panne (gain de +0,847 en rappel).
- **Critère d'acceptation :** Le critère d'acceptation initial exigeait un rappel $\ge 0,75$ et une précision $\ge 0,50$. Avec 84,7 % de rappel et 52,7 % de précision, ce critère est **pleinement atteint**.
- À l'inverse, la régression logistique standard sans rééquilibrage plafonnait à un rappel de 0,574 (insuffisant au vu de l'impact financier d'un arrêt de chaîne).

---

## Limites
1. **Nature synthétique des données :** Le jeu de données généré artificiellement ne reproduit pas tous les bruits, pannes intermittentes ou dérives lentes de capteurs réels.
2. **Précision modérée :** Une précision de 52,7 % signifie qu'environ 47 % des alertes envoyées aux équipes de maintenance sont de fausses alertes (ce coût reste toutefois très inférieur à l'arrêt d'une ligne de production).
3. **Absence de dimension temporelle :** Les observations sont traitées de manière indépendante sans historique séquentiel machine par machine.
