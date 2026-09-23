# TODO List — Gestionnaire de listes de tâches (Python)

Gestionnaire de listes de tâches en ligne de commande. Chaque liste est un fichier
JSON, ouvrable avec le programme ou manuellement.

La description d'une tâche peut contenir des retours à la ligne (il suffit d'en
insérer un dans l'argument `add` ou de le saisir en mode interactif).

## Présentation

Chaque tâche est associée à :

- Une **date de création** (`created`)
- Une **date de modification** (`modified`)
- Une **priorité** entière (plus elle est élevée, plus la tâche est prioritaire)
- Un **statut** : `TODO` (à traiter) ou `DONE` (traitée)

Lorsqu'une tâche est traitée, elle est déplacée dans la section `DONE` et lui est
associée une **date de traitement** (`done_at`). Dans l'affichage, les tâches
`DONE` sont toujours positionnées à la fin de la liste, après les `TODO`.

## Format d'un fichier de liste

Le fichier est au format JSON, une liste d'objets (une par tâche) :

```json
[
  {
    "id": "1",
    "created": "2026-09-23T09:00:00",
    "modified": "2026-09-23T09:00:00",
    "priority": 3,
    "status": "TODO",
    "done_at": "",
    "task": "Acheter du pain"
  }
]
```

- `id` : identifiant unique et auto-incrémenté
- `created` / `modified` : dates au format ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)
- `priority` : entier (plus élevé = plus prioritaire)
- `status` : `TODO` ou `DONE`
- `done_at` : date de traitement (vide si la tâche n'est pas encore traitée)
- `category` : catégorie (vide si aucune)
- `task` : description de la tâche (peut contenir des retours à la ligne)

## Installation

Aucune dépendance externe. Il suffit de disposer de Python 3.

```bash
chmod +x todo.py
```

## Utilisation

### Ajouter une tâche

```bash
python3 todo.py <liste>.list add ["Description de la tâche"] [-p PRIORITÉ] [-c CATÉGORIE]
```

- `Description de la tâche` : texte de la tâche (entre guillemets si il contient des espaces).
  La description peut contenir des retours à la ligne.
- `-p PRIORITÉ` ou `--priority PRIORITÉ` : priorité entière (défaut `0`)
- `-c CATÉGORIE` ou `--category CATÉGORIE` : catégorie (optionnelle)

Si la description n'est pas fournie, le programme passe en **mode interactif** : vous pouvez
saisir plusieurs lignes, une ligne vide pour terminer.

Exemples :

```bash
# Description simple
python3 todo.py ma_liste.list add "Acheter du pain" -p 3

# Avec catégorie
python3 todo.py ma_liste.list add "Acheter du pain" -p 3 -c "courses"

# Description multi-ligne (avec retours à la ligne)
python3 todo.py ma_liste.list add "Faire le rapport :
- Section 1
- Section 2" -p 5

# Mode interactif (saisir plusieurs lignes, ligne vide pour terminer)
python3 todo.py ma_liste.list add -p 5
```

### Afficher la liste

```bash
python3 todo.py <liste>.list list [--status TODO|DONE] [--category CATÉGORIE] [--sort CRITÈRE]
```

- `--status` : filtrer par statut (`TODO` ou `DONE`). Par défaut, les deux statuts sont affichés.
- `--category` : filtrer par catégorie (optionnel)
- `--sort` : critère de tri. Par défaut `created`.

Critères de tri disponibles :

| Statut   | Critères disponibles                     |
|----------|-------------------------------------------|
| `TODO`   | `created`, `modified`, `priority`        |
| `DONE`   | `created`, `done_at`, `priority`          |

Exemples :

```bash
# Toutes les tâches, tri par date de création (défaut)
python3 todo.py ma_liste.list list

# Uniquement les TODO, triées par priorité (la plus prioritaire en premier)
python3 todo.py ma_liste.list list --status TODO --sort priority

# Uniquement les DONE, triées par date de traitement
python3 todo.py ma_liste.list list --status DONE --sort done_at

# Filtrer par catégorie
python3 todo.py ma_liste.list list --category courses

# Toutes les tâches, triées par date de modification
python3 todo.py ma_liste.list list --sort modified
```

### Marquer une tâche comme traitée

```bash
python3 todo.py <liste>.list done ID
```

- `ID` : identifiant de la tâche (entier)

Cette commande :

1. Passe le statut de la tâche à `DONE`
2. Lui associe la date et heure courantes comme `done_at`
3. Met à jour sa `modified`

Exemple :

```bash
python3 todo.py ma_liste.list done 1
```

### Modifier une tâche

```bash
python3 todo.py <liste>.list edit ID [-t NOUVELLE_DESCRIPTION] [-p NOUVELLE_PRIORITÉ] [-c NOUVELLE_CATÉGORIE]
```

- `ID` : identifiant de la tâche (entier)
- `-t NOUVELLE_DESCRIPTION` ou `--task NOUVELLE_DESCRIPTION` : nouvelle description de la tâche
- `-p NOUVELLE_PRIORITÉ` ou `--priority NOUVELLE_PRIORITÉ` : nouvelle priorité entière
- `-c NOUVELLE_CATÉGORIE` ou `--category NOUVELLE_CATÉGORIE` : nouvelle catégorie

Si une option n'est pas fournie, le programme vous demande de la saisir
interactivement. Pour la description, le mode interactif permet de saisir
plusieurs lignes (une ligne vide pour terminer). La valeur actuelle est
proposée par défaut.

Cette commande :

1. Modifie la description, la priorité et/ou la catégorie de la tâche
2. Met à jour sa `modified`

Exemples :

```bash
# Modification complète via les options
python3 todo.py ma_liste.list edit 2 -t "Répondre aux emails importants" -p 5 -c "personnel"

# Mode interactif (on propose la valeur actuelle)
python3 todo.py ma_liste.list edit 4
```

## Résumé des commandes

| Commande | Description |
|----------|-------------|
| `add ["tâche"] [-p N] [-c CAT]` | Ajouter une tâche (priorité N, défaut 0) |
| `list [--status S] [--category CAT] [--sort C]` | Afficher la liste filtrée et triée |
| `done ID` | Marquer la tâche ID comme traitée |
| `edit ID [-t T] [-p P] [-c CAT]` | Modifier la description, la priorité et/ou la catégorie de la tâche ID |

## Notes

- Les tâches `DONE` sont toujours affichées à la fin de la liste, après les `TODO`.
- Les IDs sont auto-incréments et uniques par fichier de liste.
- Aucune configuration externe n'est nécessaire : chaque liste est un fichier autonome.