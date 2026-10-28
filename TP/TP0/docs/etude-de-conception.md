# Étude de conception — MaintAI

**Groupe :** G1 · **Auteur :** Faris Mohamed · **Version :** Finale (Séance 3) · **Date :** 28/10/2026

---

## 1. Contexte et utilisateurs
- **Utilisateur principal :** Technicien ou responsable de l'équipe de maintenance de l'usine.

---

## 2. Problème et décision
- **Décision prise avec le système :** Sélectionner chaque matin la liste prioritaire des machines nécessitant une inspection préventive sur site.
- **Fréquence :** Quotidienne (chaque matin à la prise de poste).
- **Coût d'une erreur :**
  - *Faux Négatif (panne non détectée) :* Arrêt complet d'une ligne de production pendant une journée entière (coût de production très lourd pour l'usine).
  - *Faux Positif (fausse alerte) :* Une heure de temps technicien consacrée à une vérification non nécessaire.

---

## 3. Approche par sous-problème

| Sous-problème | Approche | Pourquoi pas une approche plus simple |
| :--- | :--- | :--- |
| Détection du risque de panne machine | Machine Learning supervisé (Classification binaire tabulaire) | Un système à base de règles statiques (seuils if/else rigides) ne capte pas les interactions combinées et non linéaires entre température, vibration, charge moteur et heures de vol. |

---

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
| :--- | :--- | :--- | :--- |
| `data/exemple_pannes.csv` | Relevés télémétriques de capteurs industriels (données de synthèse du cours) | 5 000 relevés, 4 variables continues, 1 cible binaire | Non (télémétrie machine exclusivement industrielle, RGPD non applicable) |

---

## 5. Métriques, baseline et critères d'acceptation
- **Baseline et son score :** Modèle prédisant systématiquement la classe majoritaire « pas de panne » (`DummyClassifier(strategy="most_frequent")`). Score : **Accuracy = 0,824**, mais **Rappel = 0,000** (incapable de stopper une panne).
- **Métrique principale et pourquoi :** Le **Rappel (Recall)**. Rater une panne coûte une journée d'arrêt d'usine, alors qu'une fausse alerte ne coûte qu'une heure d'inspection.
- **Critères d'acceptation quantifiés :**
  - **Métrique :** Rappel $\ge 0,75$ et Précision $\ge 0,50$.
  - **Jeu de données :** Jeu de test tenu strictement à l'écart (20 %, soit 1 000 relevés).
  - **Condition :** Doit battre significativement la baseline sur le rappel sans dégrader la précision en dessous de 50 %.

---

## 6. Architecture prévue
Pipeline modulaire Python orchestré par Scikit-Learn :
- `data.py` : ingestion et découpage stratifié.
- `train.py` : prétraitement (`StandardScaler`, `ColumnTransformer`) et entraînement comparatif automatisé.
- Sérialisation des artefacts dans `models/model.joblib` et `models/metrics.json`.

---

## 7. Choix technologiques
- Langage : Python 3.13
- Bibliothèques de modélisation : `scikit-learn`, `pandas`, `numpy`, `joblib`
- Framework de tests : `pytest`

---

## 8. Risques, éthique, confidentialité
- Risque d'usure anormale ou de surchauffe masquée en cas de dysfonctionnement d'un capteur.
- Aucune donnée nominative ou sensible stockée.

---

## 9. Limites et hors périmètre
- Le modèle fournit une prédiction instantanée et n'intègre pas encore de calcul de durée résiduelle avant défaillance (RUL - Remaining Useful Life).
- Déploiement en temps réel / streaming non prévu en séance 3 (abordé via API REST en séance 4).
