#!/usr/bin/env python3
"""Gestionnaire de listes de tâches (TODO / DONE).

Chaque liste est un fichier JSON. Une tâche est un dictionnaire avec les clés :
    id, created, modified, priority, status, done_at, category, due_date, task

- created / modified : dates ISO 8601 (YYYY-MM-DDTHH:MM:SS)
- priority : entier (plus il est élevé, plus la tâche est prioritaire)
- status : TODO ou DONE
- done_at : date de traitement (vide si TODO)
- category : catégorie (vide si aucune)
- due_date : échéance (vide si aucune). Format accepté :
    - "YYYY-MM-DD" (date seule)
    - "YYYY-MM-DDTHH:MM:SS" (date + heure)
    - "YYYY-MM-DD HH:MM:SS" (date + heure avec espace)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

STATUS_TODO = "TODO"
STATUS_DONE = "DONE"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_due_date(value: str) -> str | None:
    """Normalise une échéance en date ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS).
    Retourne None si la chaîne est vide ou non reconnue."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    # Déjà au bon format ?
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            return None
    # Date + heure avec 'T'
    if len(value) == 19 and value[10] == "T":
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            return value
        except ValueError:
            return None
    # Date + heure avec espace
    if len(value) == 19 and value[10] == " ":
        try:
            datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return value.replace(" ", "T")
        except ValueError:
            return None
    print(f"Format d'échéance non reconnu : {value!r}. Utilisez YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS.",
          file=sys.stderr)
    return None


def read_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    rows = data if isinstance(data, list) else []
    # Normalisation : s'assurer que chaque tâche a les clés par défaut
    for r in rows:
        r.setdefault("category", "")
        r.setdefault("due_date", "")
    return rows


def write_list(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")


def next_id(rows: list[dict]) -> int:
    ids = [int(r["id"]) for r in rows if str(r["id"]).isdigit()]
    return max(ids) + 1 if ids else 1


def find_row(rows: list[dict], task_id: int) -> int:
    for i, r in enumerate(rows):
        if int(r["id"]) == task_id:
            return i
    return -1


def read_multiline(prompt: str, default: str = "") -> str:
    """Lit plusieurs lignes depuis l'entrée standard, jusqu'à une ligne vide."""
    print(prompt)
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    text = "\n".join(lines)
    return text if text else default


def add_task(path: Path, task: str | None, priority: int, category: str | None, due_date: str | None,
             silent: bool = False) -> None:
    rows = read_list(path)
    ts = now_iso()
    if task is None:
        task = read_multiline("Saisir la tâche (ligne vide pour terminer) :")
        if not task:
            print("Aucune tâche saisie.", file=sys.stderr)
            sys.exit(1)
    due = parse_due_date(due_date) if due_date else ""
    rows.append({
        "id": str(next_id(rows)),
        "created": ts,
        "modified": ts,
        "priority": priority,
        "status": STATUS_TODO,
        "done_at": "",
        "category": category or "",
        "due_date": due or "",
        "task": task,
    })
    write_list(path, rows)
    if not silent:
        print(f"Ajouté : [{rows[-1]['id']}] {task.splitlines()[0]} (priorité {priority})")


def mark_done(path: Path, task_id: int, silent: bool = False) -> None:
    rows = read_list(path)
    idx = find_row(rows, task_id)
    if idx < 0:
        print(f"ID {task_id} introuvable.", file=sys.stderr)
        sys.exit(1)
    rows[idx]["status"] = STATUS_DONE
    rows[idx]["done_at"] = now_iso()
    rows[idx]["modified"] = now_iso()
    write_list(path, rows)
    if not silent:
        print(f"Traité : [{rows[idx]['id']}] {rows[idx]['task'].splitlines()[0]}")


def unmark_done(path: Path, task_id: int, silent: bool = False) -> None:
    rows = read_list(path)
    idx = find_row(rows, task_id)
    if idx < 0:
        print(f"ID {task_id} introuvable.", file=sys.stderr)
        sys.exit(1)
    rows[idx]["status"] = STATUS_TODO
    rows[idx]["done_at"] = ""
    rows[idx]["modified"] = now_iso()
    write_list(path, rows)
    if not silent:
        print(f"Non traité : [{rows[idx]['id']}] {rows[idx]['task'].splitlines()[0]}")


def edit_task(path: Path, task_id: int, task: str | None, priority: int | None, category: str | None, due_date: str | None) -> None:
    rows = read_list(path)
    idx = find_row(rows, task_id)
    if idx < 0:
        print(f"ID {task_id} introuvable.", file=sys.stderr)
        sys.exit(1)

    if task is None:
        task = read_multiline(
            f"Nouvelle description [{rows[idx]['task'].splitlines()[0] if rows[idx]['task'] else ''}] :",
            default=rows[idx]["task"],
        )
    if priority is None:
        prio_str = input(f"Nouvelle priorité [{rows[idx]['priority']}]: ").strip()
        if prio_str:
            try:
                priority = int(prio_str)
            except ValueError:
                print("Priorité doit être un entier.", file=sys.stderr)
                sys.exit(1)
    if category is None:
        cat_str = input(f"Nouvelle catégorie [{rows[idx].get('category', '')}]: ").strip()
        category = cat_str if cat_str else rows[idx].get("category", "")
    if due_date is None:
        due_str = input(f"Nouvelle échéance [{rows[idx].get('due_date', '')}]: ").strip()
        if due_str:
            due_date = parse_due_date(due_str)
            if due_date is None:
                sys.exit(1)
        else:
            due_date = rows[idx].get("due_date", "")

    rows[idx]["task"] = task
    if priority is not None:
        rows[idx]["priority"] = priority
    rows[idx]["category"] = category or ""
    rows[idx]["due_date"] = due_date or ""
    rows[idx]["modified"] = now_iso()
    write_list(path, rows)
    print(f"Modifié : [{rows[idx]['id']}] {rows[idx]['task'].splitlines()[0]} (priorité {rows[idx]['priority']})")


def move_to_done_section(rows: list[dict]) -> list[dict]:
    """Réorganise la liste : TODO d'abord, DONE à la fin (ordre interne préservé)."""
    return [r for r in rows if r["status"] == STATUS_TODO] + \
           [r for r in rows if r["status"] == STATUS_DONE]


def sort_rows(rows: list[dict], sort_by: str, status: str | None) -> list[dict]:
    """Tri selon le critère, en fonction du statut."""
    if sort_by == "created":
        key = lambda r: r["created"]
    elif sort_by == "modified":
        key = lambda r: r["modified"]
    elif sort_by == "priority":
        key = lambda r: -r["priority"]  # décroissant : prioritaire en premier
    elif sort_by == "done_at":
        key = lambda r: r["done_at"]
    elif sort_by == "due_date":
        # Les tâches sans échéance viennent en dernier
        key = lambda r: r.get("due_date", "") or "9999"
    else:
        print(f"Critère de tri inconnu : {sort_by}", file=sys.stderr)
        sys.exit(1)
    return sorted(rows, key=key)


def is_overdue(row: dict) -> bool:
    """Vérifie si une tâche est en retard (échéance dépassée)."""
    due = row.get("due_date", "")
    if not due:
        return False
    try:
        if len(due) == 10:
            due_dt = datetime.strptime(due, "%Y-%m-%d")
        else:
            due_dt = datetime.strptime(due[:19].replace(" ", "T"), "%Y-%m-%dT%H:%M:%S")
        return due_dt < datetime.now()
    except ValueError:
        return False


def due_in_days(row: dict, days: int) -> bool:
    """Vérifie si l'échéance est dans les prochains `days` jours (ou dépassée)."""
    due = row.get("due_date", "")
    if not due:
        return False
    try:
        if len(due) == 10:
            due_dt = datetime.strptime(due, "%Y-%m-%d")
        else:
            due_dt = datetime.strptime(due[:19].replace(" ", "T"), "%Y-%m-%dT%H:%M:%S")
        now = datetime.now()
        delta = (due_dt - now).days
        return 0 <= delta <= days
    except ValueError:
        return False


def list_tasks(path: Path, status: str | None, sort_by: str, category: str | None,
               overdue: bool = False, due_in: int | None = None) -> None:
    rows = read_list(path)
    if status:
        rows = [r for r in rows if r["status"] == status.upper()]
    if category:
        rows = [r for r in rows if r.get("category", "").lower() == category.lower()]
    if overdue:
        rows = [r for r in rows if is_overdue(r)]
    if due_in is not None:
        rows = [r for r in rows if due_in_days(r, due_in)]
    rows = sort_rows(rows, sort_by, status)
    rows = move_to_done_section(rows)

    if not rows:
        print("(vide)")
        return

    print(f"{'ID':<5}{'STATUT':<7}{'CATÉGORIE':<15}{'ÉCHÉANCE':<20}{'CRÉÉ':<20}{'MODIF':<20}{'DONE_AT':<20}{'PRIO':<5}TÂCHE")
    for r in rows:
        task_line = r["task"].splitlines()[0] if r["task"] else ""
        cat = r.get("category", "")
        due = r.get("due_date", "")
        print(f"{r['id']:<5}{r['status']:<7}{cat:<15}{due:<20}{r['created']:<20}{r['modified']:<20}"
              f"{r['done_at']:<20}{r['priority']:<5}{task_line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestionnaire de listes TODO")
    parser.add_argument("list", help="Chemin du fichier de liste")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Ajouter une tâche")
    p_add.add_argument("task", nargs="?", default=None, help="Description de la tâche")
    p_add.add_argument("-p", "--priority", type=int, default=0, help="Priorité (entier)")
    p_add.add_argument("-c", "--category", default=None, help="Catégorie")
    p_add.add_argument("-d", "--due-date", default=None, help="Échéance (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)")

    p_done = sub.add_parser("done", help="Marquer une tâche comme traitée")
    p_done.add_argument("id", type=int, help="ID de la tâche")

    p_edit = sub.add_parser("edit", help="Modifier une tâche")
    p_edit.add_argument("id", type=int, help="ID de la tâche")
    p_edit.add_argument("-t", "--task", default=None, help="Nouvelle description")
    p_edit.add_argument("-p", "--priority", type=int, default=None, help="Nouvelle priorité")
    p_edit.add_argument("-c", "--category", default=None, help="Nouvelle catégorie")
    p_edit.add_argument("-d", "--due-date", default=None, help="Nouvelle échéance")

    p_list = sub.add_parser("list", help="Afficher la liste")
    p_list.add_argument("--status", choices=["TODO", "DONE"], default=None,
                        help="Filtrer par statut")
    p_list.add_argument("--category", default=None, help="Filtrer par catégorie")
    p_list.add_argument("--sort", choices=["created", "modified", "priority", "done_at", "due_date"],
                        default="created", help="Critère de tri")
    p_list.add_argument("--overdue", action="store_true",
                        help="Afficher uniquement les tâches en retard")
    p_list.add_argument("--due-in", type=int, default=None,
                        help="Afficher les tâches dont l'échéance est dans N jours (ou dépassée)")

    args = parser.parse_args()
    path = Path(args.list)

    if args.command == "add":
        add_task(path, args.task, args.priority, args.category, args.due_date)
    elif args.command == "done":
        mark_done(path, args.id)
    elif args.command == "edit":
        edit_task(path, args.id, args.task, args.priority, args.category, args.due_date)
    elif args.command == "list":
        list_tasks(path, args.status, args.sort, args.category,
                   overdue=args.overdue, due_in=args.due_in)


if __name__ == "__main__":
    main()