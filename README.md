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
- **p** : trier par priorité croissante, les numéros les plus bas étant les plus prioritaires (inverser en appuyant de nouveau)
- **e** : trier par échéance (inverser en appuyant de nouveau)
- **r** : trier par date de réalisation (inverser en appuyant de nouveau)
- **c** : filtrer les catégories par occurrence saisie
- **/** : rechercher dans les descriptions par occurrence saisie
- **q** : quitter

Les filtres de catégorie et de description peuvent être combinés. Le critère de tri et les filtres actifs s'affichent dans l'en-tête.

## Écran d'édition des tâches

Depuis l’écran principal, **Entrée** ouvre les détails de la tâche sélectionnée. Les champs disponibles sont :

- **Priorité**
- **Catégorie**
- **Échéance**
- **Description**

### Modifier une tâche

1. Utilisez **↑/↓** pour sélectionner un champ.
2. Appuyez sur **Entrée** pour modifier le champ sélectionné.
3. Pour la description, un éditeur multiligne s’ouvre :
   - **↑/↓/←/→** déplacent le curseur ;
   - **Entrée** insère un saut de ligne ;
   - **Tab** valide la description et revient aux détails ;
   - **Échap** annule la modification de la description.
   - Le texte revient automatiquement à la ligne lorsqu'il dépasse la largeur de la fenêtre.
4. Appuyez sur **x** pour enregistrer la tâche, ou **q** pour revenir sans enregistrer.

Sur une tâche **DONE**, les champs sont en lecture seule. Vous pouvez seulement naviguer, appuyer sur **u** pour la remettre en TODO, ou **q** pour revenir.

Les échéances acceptées sont `YYYY-MM-DD`, `YYYY-MM-DDTHH:MM:SS` et `YYYY-MM-DD HH:MM:SS`.

## Format d'un fichier de liste

Le fichier est au format JSON, une liste d'objets (un par tâche) :

```json
[
  {
    "id": "1",
    "created": "2026-09-23T09:00:00",
    "modified": "2026-09-23T09:00:00",
    "priority": 1,
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
- `priority` : entier (plus la valeur est basse, plus la tâche est prioritaire)
- `status` : `TODO` ou `DONE`
- `done_at` : date de traitement (vide si la tâche n'est pas encore traitée)
- `category` : catégorie (vide si aucune catégorie)
- `task` : description de la tâche
