# TP0 : MaintAI

**Nom :** Faris Mohamed · **Groupe :** G1

---

## Le problème
Prédire une panne de machine industrielle à partir de 4 relevés de capteurs (température, vitesse de vibration, taux de charge moteur et heures de fonctionnement cumulées). Une panne manquée entraîne l'arrêt complet d'une ligne de production pendant une journée, tandis qu'une fausse alerte ne mobilise un technicien que pendant une heure d'inspection préventive.

---

## Résultats sur le jeu de test

| Modèle | Accuracy | Rappel | Précision | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| **baseline** | 0.824 | 0.000 | 0.000 | 0.000 |
| **régression logistique** | 0.889 | 0.574 | 0.737 | 0.645 |
| **régression logistique (balanced)** | 0.839 | **0.847** | 0.527 | 0.649 |
| **gradient boosting** | 0.881 | 0.574 | 0.697 | 0.629 |
| **forêt aléatoire** | 0.873 | 0.545 | 0.671 | 0.602 |

---

## Mon choix, et pourquoi
J'ai retenu la **régression logistique avec rééquilibrage des classes (`class_weight="balanced"`)** (ou alternativement avec ajustement du seuil de décision à 0,3). 

**Justification :**  
Dans notre contexte industriel, le coût d'un faux négatif (panne non détectée = arrêt d'une ligne de production pendant une journée entière) est critique comparé à celui d'un faux positif (une heure d'inspection d'un technicien). La baseline majoritaire et les modèles standards privilégient l'accuracy au détriment du rappel (qui plafonne à 0,574). La régression logistique équilibrée est la seule à maximiser la détection des pannes réelles en portant le rappel à **84,7 %**, tout en conservant une précision acceptable supérieure à 50 %.

---

## Le critère (rappel >= 0,75) est-il atteint ?
- **Avec la régression logistique standard :** Le critère n'est **pas atteint** ($Rappel = 0,574 < 0,75$). C'est un résultat valable et honnête à expliciter : sans intervention sur les poids des classes ou sur le seuil de décision, l'algorithme est biaisé par la proportion dominante de machines saines (82,4 %).
- **Avec la régression logistique équilibrée (`balanced`) :** Le critère est **pleinement atteint** ($Rappel = 0,847 \ge 0,75$ et $Précision = 0,527 \ge 0,50$). Le modèle sécurise ainsi près de 85 % des pannes potentielles de l'usine.

---

## Ce qui reste flou
Comment choisir rigoureusement entre fixer une pondération à l'entraînement (`class_weight`) ou ajuster dynamiquement le seuil de probabilité (`threshold`) au moment de l'inférence via l'API REST en fonction des variations de cadence de l'usine.
