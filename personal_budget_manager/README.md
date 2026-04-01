# Gestionnaire de Budget Personnel

Programme qui lit un fichier CSV bancaire, analyse les dépenses et génère un rapport PDF.

---

## Installation

### 1. Installer les bibliothèques Python
Exécuter cette commande **une seule fois** dans le terminal :

```bash
pip install -r requirements.txt
```

### 2. Extensions VS Code
En ouvrant ce projet dans VS Code, une notification s'affiche automatiquement pour installer les extensions recommandées.
Liste des extensions :
- **Python** — indispensable pour le développement Python
- **Pylance** — autocomplétion Python
- **Rainbow CSV** — affiche les fichiers CSV avec des couleurs
- **vscode-pdf** — ouvre les PDF directement dans VS Code
---

## Lancement du programme
```bash
cd personal_budget_manager
python main.py
```

Le fichier `rapport_budget.pdf` sera généré automatiquement.

---

## Structure du projet
```
personal_budget_manager/
├── main.py              ← Point d'entrée du programme (à exécuter)
├── lecteur_csv.py       ← Lecture des fichiers CSV/Excel
├── analyseur.py         ← Analyse des dépenses
├── visualiseur.py       ← Génération des graphiques
├── generateur.py        ← Génération du rapport PDF
├── transactions.csv     ← Fichier des transactions bancaires
├── requirements.txt     ← Liste des bibliothèques Python requises
└── .vscode/
    └── extensions.json  ← Extensions VS Code recommandées
```

---

## Modifier les paramètres
Les paramètres se trouvent en haut du fichier `main.py` :
```python
CHEMIN_CSV = "transactions.csv"   # Nom du fichier CSV bancaire

MES_BUDGETS = {                   # Budget mensuel par catégorie (€)
    'Transport':          150,
    'Alimentation':       250,
    'Logement':           750,
    'Shopping':            80,
    'Loisirs':             60,
    'Remboursement prêt': 200,
}

OBJECTIF_EPARGNE = 1500.0         # Objectif d'épargne (€)
```
