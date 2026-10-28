# Activité 2 : Créer l'environnement et lancer le squelette

**Document de référence :** `S3_polycopie_etudiant.pdf` (Page 3)  
**Dossier de travail :** `projet_a_completer/`

---

## 1. Création de l'environnement et vérification initiale

1. **Création du `.venv` et installation des dépendances :**
   - Environnement virtuel initialisé avec Python 3.13 (`python -m venv .venv`).
   - Dépendances installées via `pip install -r requirements.txt` (numpy 2.4.4, pandas 3.0.2, scikit-learn 1.8.0, joblib 1.5.3, pytest 9.1.1).

2. **Lancement initial de `python -m pytest` :**
   ```text
   collected 8 items

   tests\test_data.py FF.                                                   [ 37%]
   tests\test_models.py FF                                                  [ 62%]
   tests\test_train.py FFF                                                  [100%]

   =================== 7 failed, 1 passed in 106.61s ===================
   ```
   *Constat :* Résultat strictement conforme à l'attendu du polycopié (**7 failed, 1 passed**).  
   Le seul test passant est `test_split_chronologique_teste_sur_le_futur` car dans `config.py`, le réglage initial est `SPLIT = "random"` (le test chronologique fait un simple `return` précoce).

---

## 2. Réponse à la question 6

### Question : Que se passe-t-il lors de la commande `python monprojet/train.py`, et pourquoi ?

* **Ce qui se produit :**
  L'exécution échoue avec l'erreur :
  ```text
  Traceback (most recent call last):
    File "...\monprojet\train.py", line 18, in <module>
      from monprojet import config
  ModuleNotFoundError: No module named 'monprojet'
  ```
* **Pourquoi :**
  Quand on lance directement un fichier via `python dossier/script.py`, Python place le répertoire du script (`monprojet/`) en tête de `sys.path`, et **non** la racine du projet. Par conséquent, Python cherche un sous-paquet nommé `monprojet` à l'intérieur de `monprojet/`, ce qui échoue.
* **La solution :**
  Il faut toujours exécuter depuis la racine du projet en utilisant l'option module `-m` :
  ```bash
  python -m monprojet.train
  ```
  *(À ce stade, lancer avec `-m` déclenche ensuite un `NotImplementedError: main() n'est pas encore écrite`, car les fonctions métier restent à implémenter).*

---

## 3. Quelles fonctions devrez-vous écrire, et dans quels fichiers ?

| Fichier cible | Fonctions à implémenter | Rôle attendu | Tests validés après écriture |
| :--- | :--- | :--- | :--- |
| **`monprojet/data.py`** | `load_data(path=None)` | Lit le CSV (`DATA_PATH`), vérifie la présence de `TARGET` (lève `ValueError` si absent), supprime les lignes où la cible est manquante. | **3 passed** |
| | `split(df)` | Extrait $X$ et $y$, applique un découpage aléatoire stratifié (`random`) ou chronologique trié par date (`chronologique`). | |
| **`monprojet/models.py`** | `candidates()` | Renvoie un dictionnaire de modèles non entraînés. Le **premier** modèle doit obligatoirement être la baseline (`DummyClassifier` ou `DummyRegressor`), suivi d'au moins 3 modèles ML avec graine fixe (`SEED`). | **5 passed** |
| **`monprojet/train.py`** | `evaluate(model, X_test, y_test)` | Prédit sur le jeu de test et renvoie un dictionnaire de métriques (`accuracy`, `recall`, `precision`, `f1` ou `mae`, `rmse`, `r2`) arrondies à 3 décimales (float). | **6 passed** |
| | `main()` | Orchestre le flux : charge les données, découpe, entraîne chaque modèle dans un `Pipeline` avec preprocessing, évalue, affiche le tableau trié selon `MAIN_METRIC`, trouve le meilleur modèle et sauvegarde `model.joblib` et `metrics.json` dans `models/`. | **8 passed** |
