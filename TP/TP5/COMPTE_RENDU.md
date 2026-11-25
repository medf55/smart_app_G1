# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** 5IIR · G1  ·  **Membres :** Salah Eddine El Assassi, …  ·  **Date :** 25/11/2026

> Les valeurs entre crochets `[...]` (identifiants de run, md5, commits) dépendent de votre machine :
> remplacez-les par celles de votre terminal et de `mlflow ui`.

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
5 failed, 27 passed
```

Quels tests échouent, et pourquoi ?

Les 5 tests de `tests/test_tracking.py`. `log_run` n'est pas encore écrite : elle renvoie `""` sans rien
enregistrer, donc MLflow ne contient aucun run, ni paramètres, ni `data_md5`, ni modèle à recharger.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant : vers le dossier `TP/TP4` (installation éditable faite au TP4, on réutilise son environnement).
Après : vers `TP/TP5`. C'est pour cela que `test_installed_version_matches_the_code` échoue si on oublie
`pip install -e .` : la version installée (celle du TP4) ne correspond pas au code du TP5.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)  # toutes les runs de MaintAI dans la même expérience
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))  # la version des données, comme dans le .dvc
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
    return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --model forest --threshold 0.2` | 0.831 | 0.479 | 0.854 |

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Le run `--threshold 0.2` (régression logistique, C=1.0) : il a le meilleur recall (0.838), donc il manque le moins
de pannes. On paie ce choix par plus de fausses alertes (precision 0.543 au lieu de 0.622), ce qui est acceptable
puisqu'une fausse alerte coûte moins cher qu'une panne. La forêt aléatoire n'est pas meilleure : à seuil égal, elle a
un recall et une precision plus faibles que la régression logistique (0.728 / 0.562 contre 0.750 / 0.622 au seuil 0.3,
et 0.831 / 0.479 contre 0.838 / 0.543 au seuil 0.2), tout en étant plus lourde. Le réglage du seuil compte plus que le
choix du modèle. Diminuer C (régularisation plus forte) fait au contraire baisser le recall.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

`scikit-learn==1.8.0` (avec aussi `mlflow==3.18.0`, `numpy==2.4.4`, `pandas==3.0.2`, `skops==0.16.0`…).
Au TP4, le modèle `.joblib` ne pouvait être rechargé de façon fiable qu'avec la même version de scikit-learn que
celle de l'entraînement, et cette version n'était notée qu'à la main (`sklearn_version` dans `model_info.json`,
versions figées dans `requirements.txt`). MLflow enregistre automatiquement, avec chaque modèle, les versions exactes
de ses dépendances : on sait toujours quel environnement recréer pour le recharger.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans le dossier où on lance l'entraînement (`TP/TP5`) : `mlflow.db` (base SQLite avec les paramètres et
métriques) et `mlruns/` (les artefacts : le modèle, son `MLmodel`, son `requirements.txt`…). Ils ne vont pas dans Git
(ils sont dans le `.gitignore`) : ce sont des fichiers générés, binaires, qui grossissent à chaque run, et qui
contiennent les modèles ; Git sert à versionner le code, pas les résultats d'expériences.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: [md5 v1]
  size: [taille]
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

Ce sont exactement les mêmes valeurs : `file_md5` calcule la même empreinte que DVC. À partir d'un run MLflow, on
peut donc retrouver le reçu `.dvc` (et le commit Git) qui correspond aux données utilisées, puis les récupérer avec
`dvc checkout` ou `dvc pull`. C'est le lien entre le modèle et ses données.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Un fichier de données peut être gros, et Git garderait chaque version pour toujours dans l'historique. DVC le garde
hors de Git (dans son cache, puis dans le stockage) et Git ne versionne qu'un petit reçu de quelques lignes (md5 et
taille). Ce reçu suffit à identifier et récupérer la bonne version du fichier.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data/sensors.csv.dvc:
	changed outs:
		modified:           data/sensors.csv
```

DVC voit que le fichier ne correspond plus au reçu : c'est une nouvelle version, pas encore enregistrée.

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | [commit « Données v1 »] | [md5 v1] | 5000 |
| v2 | [commit « Données v2 »] | [md5 v2] | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

5000 lignes. `git checkout` remet l'ancien reçu, puis `dvc checkout` remet le fichier qui correspond à ce reçu, depuis
le cache. Retour à la v2 avec `git checkout HEAD -- data/sensors.csv.dvc` puis `dvc checkout` : 8000 lignes.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

```
1 file fetched and 1 file added
```

DVC lit le reçu, ne trouve le fichier ni dans l'espace de travail ni dans le cache, et le télécharge depuis le
stockage (`dvc-stockage`). `data/sensors.csv` revient, avec ses 8000 lignes : c'est ce que ferait un coéquipier qui
vient de cloner le dépôt.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | [md5 v1] | 4000 | 0.750 | 0.622 |
| v2 | [md5 v2] | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non. Le recall est même un peu plus bas (0.741 contre 0.750) et la precision un peu plus haute, mais surtout les deux
runs ne sont pas mesurés sur le même jeu de test : le test de la v2 est tiré des données v2 (autre graine, 1600
relevés, taux de panne 12.8 % au lieu de 13.6 %). Les écarts peuvent venir des données de test et non du modèle. Pour
comparer deux modèles, il faut les évaluer sur les mêmes données de test ; le `data_md5` de chaque run permet justement
de voir que les deux runs ne portent pas sur les mêmes données.

## 5. Décision : l'ADR 004

Voir `docs/adr/004-choix-du-modele.md` : régression logistique, C=1.0, seuil 0.2.
Run : `[run_id]` · `data_md5` : `[md5 v1]`.

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   Git versionne le code (et les reçus `.dvc`). DVC versionne les fichiers de données, gardés dans un cache et un
   stockage hors de Git. MLflow garde la trace de chaque entraînement : paramètres, `data_md5`, métriques, et le modèle
   avec les versions exactes de ses dépendances.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le stockage est un dossier de notre PC (`%USERPROFILE%\dvc-stockage`) : ce chemin n'a de sens que sur notre machine,
   donc il va dans `.dvc/config.local`, ignoré par Git. Pour partager, il faudrait un stockage accessible par tous
   (S3, Google Drive, un serveur SSH…), ajouté sans `--local` pour que sa configuration soit commitée dans `.dvc/config`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Le code : dans Git (et le wheel du TP4). Les données : dans DVC (le reçu dans Git, le fichier dans le stockage).
   Le modèle avec ses versions exactes : dans MLflow (un run, son identifiant, le `requirements.txt` du modèle).

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : oui / non
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? non
  (le `.gitignore` de `TP5` exclut `mlflow.db`, `mlruns/`, `data/*.csv` ; DVC ignore lui-même `.dvc/cache` et
  `.dvc/config.local`).

## 8. Ce qui reste flou

…
