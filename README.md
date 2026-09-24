# TODO TUI — Gestionnaire de listes de tâches

Interface en mode texte (curses) pour gérer des listes de tâches. Le fichier de liste est au format JSON.

## Installation

Aucune dépendance externe. Il suffit de disposer de Python 3.

```bash
chmod +x todo.py
```

## Utilisation

```bash
python3 todo.py <liste>.list
```

Le fichier de liste est créé automatiquement s'il n'existe pas. Les répertoires parents sont également créés si nécessaire.

Navigation et actions :

- **Flèches haut/bas** : déplacer la sélection
- **Entrée** : ouvrir les détails ou modifier la tâche sélectionnée
- **n** : créer une tâche
- **d** : marquer comme DONE
- **u** : marquer comme TODO
- **Tab** : basculer entre TODO et DONE
- **i** : trier par ID (inverser en appuyant de nouveau)
- **p** : trier par priorité (inverser en appuyant de nouveau)
- **e** : trier par échéance (inverser en appuyant de nouveau)
- **r** : trier par date de réalisation (inverser en appuyant de nouveau)
- **c** : filtrer les catégories par occurrence saisie
- **/** : rechercher dans les descriptions par occurrence saisie
- **q** : quitter

Les filtres de catégorie et de description peuvent être combinés. Le critère de tri et les filtres actifs s'affichent dans l'en-tête.

## Format d'un fichier de liste

Le fichier est au format JSON, une liste d'objets (un par tâche) :

```json
[
  {
    "id": "1",
    "created": "2026-09-23T09:00:00",
    "modified": "2026-09-23T09:00:00",
    "priority": 3,
    "status": "TODO",
    "done_at": "",
    "category": "courses",
    "due_date": "2026-09-25",
    "task": "Acheter du pain"
  }
]
```

- `id` : identifiant unique et auto-incrémenté
- `created` / `modified` : dates au format ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)
- `priority` : entier (plus élevé = plus prioritaire)
- `status` : `TODO` ou `DONE`
- `done_at` : date de traitement (vide si la tâche n'est pas encore traitée)
- `category` : catégorie (vide si aucune catégorie)
- `task` : description de la tâche
