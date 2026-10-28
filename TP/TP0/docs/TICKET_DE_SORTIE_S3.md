# Ticket de sortie — Séance 3

**Nom :** Faris Mohamed · **Groupe :** G1 · **Date :** 28/10/2026

---

### 1. Quelle est la baseline de votre projet, et son score ?
* **Sur MaintAI (classification) :** Prédire systématiquement la classe majoritaire (« pas de panne ») via `DummyClassifier(strategy="most_frequent")`.
  - **Score :** Accuracy = 0,824 (82,4 %), mais **Rappel = 0,000 (0 %)**.
* **Sur CantineAI (régression) :** Prédire systématiquement la moyenne historique via `DummyRegressor(strategy="mean")`.
  - **Score :** MAE = **70,27 repas**.

---

### 2. Pourquoi évaluer tous les modèles sur le même jeu de test ?
Pour garantir une comparaison juste et rigoureuse (*fair comparison*). Si chaque modèle était évalué sur des échantillons différents ou avec des graines aléatoires distinctes, les variations de scores refléteraient le hasard du découpage (ex. un sous-ensemble plus facile ou plus difficile) plutôt que la qualité intrinsèque des algorithmes et de leurs représentations.

---

### 3. Dans quel cas l'accuracy peut-elle tromper ?
L'accuracy est profondément trompeuse en présence de **classes fortement déséquilibrées**. Dans MaintAI, 82,4 % des machines ne tombent jamais en panne : un modèle trivial qui prédit toujours « 0 » affiche une accuracy de 82,4 % tout en ignorant 100 % des pannes réelles (rappel nul). Dans ce contexte critique où une panne manquée arrête l'usine, seule une métrique asymétrique comme le **rappel (recall)** est pertinente.

---

### 4. Qu'est-ce qui reste flou pour vous ?
L'arbitrage fin entre le rééquilibrage des classes (`class_weight="balanced"`) et l'ajustement direct du seuil de probabilité lors de l'inférence opérationnelle (sujet qui fait le lien direct avec l'API développée en Séance 4).
