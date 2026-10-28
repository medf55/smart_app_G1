# Ticket de sortie — Séance 4

**Nom :** Faris Mohamed · **Groupe :** G1 · **Date :** 28/10/2026

---

### 1. Que fait `git pull`, et quand faut-il le lancer ?
* **Ce qu'il fait :** Il récupère les nouveaux commits présents sur le dépôt distant (GitHub) et les fusionne avec la branche locale courante (`git fetch` suivi de `git merge`).
* **Quand le lancer :** Systématiquement avant de commencer à travailler, et impérativement **avant** de faire un `git push` pour intégrer le travail que des coéquipiers auraient déjà poussé et éviter le refus `rejected (fetch first)`.

---

### 2. Quel code renvoie l'API pour une température de 500 °C, et qui écrit ce contrôle ?
* **Code renvoyé :** **HTTP 422 Unprocessable Entity**.
* **Qui écrit ce contrôle :** C'est la bibliothèque **Pydantic** intégrée à **FastAPI** qui effectue automatiquement cette vérification grâce aux contraintes déclarées sur le schéma (`Field(le=150)`). Le développeur n'a pas besoin d'écrire de structure `if` manuelle dans le code du endpoint.

---

### 3. Pourquoi rendre le TP par une pull request plutôt que pousser sur main ?
Rendre par Pull Request permet :
1. D'isoler les développements sur une branche dédiée (`tp1`) sans risquer de corrompre la branche principale stable (`main`).
2. De soumettre son code à une **revue par les pairs (*peer review*)** : un coéquipier relit, commente, s'assure que les tests passent et valide la qualité avant fusion.
3. De déclencher des vérifications automatisées (CI/CD) sur la branche avant intégration finale.

---

### 4. Qu'est-ce qui reste flou pour vous ?
La gestion avancée des conflits Git complexes lors du `git pull` ou de la fusion d'une Pull Request lorsque deux personnes modifient simultanément les mêmes lignes d'un même fichier.
