# TODO List — Gestionnaire de listes de tâches (Python)

Gestionnaire de listes de tâches en ligne de commande. Chaque liste est un fichier
CSV simple, ouvrable avec le programme ou manuellement.

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

Chaque ligne (en dehors de l'en-tête) représente une tâche au format CSV :

```
id,created,modified,priority,status,done_at,task
```

- `id` : identifiant unique et auto-incrémenté
- `created` / `modified` : dates au format ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)
- `priority` : entier (plus élevé = plus prioritaire)
- `status` : `TODO` ou `DONE`
- `done_at` : date de traitement (vide si la tâche n'est pas encore traitée)
- `task` : description de la tâche

## Installation

Aucune dépendance externe. Il suffit de disposer de Python 3.

```bash
chmod +x todo.py
```

## Utilisation

### Ajouter une tâche

```bash
python3 todo.py <liste>.list add "Description de la tâche" [-p PRIORITÉ]
```

- `Description de la tâche` : texte de la tâche (entre guillemets si il contient des espaces)
- `-p PRIORITÉ` ou `--priority PRIORITÉ` : priorité entière (défaut `0`)

Exemple :

```bash
python3 todo.py ma_liste.list add "Acheter du pain" -p 3
python3 todo.py todo.list add "Répondre aux emails"
```

### Afficher la liste

```bash
python3 todo.py <liste>.list list [--status TODO|DONE] [--sort CRITÈRE]
```

- `--status` : filtrer par statut (`TODO` ou `DONE`). Par défaut, les deux statuts sont affichés.
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
python3 todo.py <liste>.list edit ID [-t NOUVELLE_DESCRIPTION] [-p NOUVELLE_PRIORITÉ]
```

- `ID` : identifiant de la tâche (entier)
- `-t NOUVELLE_DESCRIPTION` ou `--task NOUVELLE_DESCRIPTION` : nouvelle description de la tâche
- `-p NOUVELLE_PRIORITÉ` ou `--priority NOUVELLE_PRIORITÉ` : nouvelle priorité entière

Si une option n'est pas fournie, le programme vous demande de la saisir
interactivement (la valeur actuelle est proposée par défaut).

Cette commande :

1. Modifie la description et/ou la priorité de la tâche
2. Met à jour sa `modified`

Exemples :

```bash
# Modification complète via les options
python3 todo.py ma_liste.list edit 2 -t "Répondre aux emails importants" -p 5

# Mode interactif (on propose la valeur actuelle)
python3 todo.py ma_liste.list edit 4
```

## Résumé des commandes

| Commande | Description |
|----------|-------------|
| `add "tâche" [-p N]` | Ajouter une tâche (priorité N, défaut 0) |
| `list [--status S] [--sort C]` | Afficher la liste filtrée et triée |
| `done ID` | Marquer la tâche ID comme traitée |
| `edit ID [-t T] [-p P]` | Modifier la description et/ou la priorité de la tâche ID |

## Notes

- Les tâches `DONE` sont toujours affichées à la fin de la liste, après les `TODO`.
- Les IDs sont auto-incréments et uniques par fichier de liste.
- Aucune configuration externe n'est nécessaire : chaque liste est un fichier autonome.