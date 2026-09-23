#!/usr/bin/env python3
"""Gestionnaire de listes de tâches (TODO / DONE).

Chaque liste est un fichier texte. Une tâche est représentée par une ligne
au format CSV avec les colonnes :
    id,created,modified,priority,status,task

- created / modified : dates ISO 8601 (YYYY-MM-DDTHH:MM:SS)
- priority : entier (plus il est élevé, plus la tâche est prioritaire)
- status : TODO ou DONE
- done_at : date de traitement (vide si TODO)
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

HEADER = ["id", "created", "modified", "priority", "status", "done_at", "task"]
STATUS_TODO = "TODO"
STATUS_DONE = "DONE"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def next_id(rows: list[dict]) -> int:
    ids = [int(r["id"]) for r in rows if r["id"].isdigit()]
    return max(ids) + 1 if ids else 1


def read_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            # Normalise les clés manquantes
            row = {k: r.get(k, "") for k in HEADER}
            row["priority"] = int(row["priority"]) if row["priority"].isdigit() else 0
            rows.append(row)
        return rows


def write_list(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in HEADER})


def find_row(rows: list[dict], task_id: int) -> int:
    for i, r in enumerate(rows):
        if int(r["id"]) == task_id:
            return i
    return -1


def add_task(path: Path, task: str, priority: int) -> None:
    rows = read_list(path)
    ts = now_iso()
    rows.append({
        "id": str(next_id(rows)),
        "created": ts,
        "modified": ts,
        "priority": priority,
        "status": STATUS_TODO,
        "done_at": "",
        "task": task,
    })
    write_list(path, rows)
    print(f"Ajouté : [{rows[-1]['id']}] {task} (priorité {priority})")


def mark_done(path: Path, task_id: int) -> None:
    rows = read_list(path)
    idx = find_row(rows, task_id)
    if idx < 0:
        print(f"ID {task_id} introuvable.", file=sys.stderr)
        sys.exit(1)
    rows[idx]["status"] = STATUS_DONE
    rows[idx]["done_at"] = now_iso()
    rows[idx]["modified"] = now_iso()
    write_list(path, rows)
    print(f"Traité : [{rows[idx]['id']}] {rows[idx]['task']}")


def edit_task(path: Path, task_id: int, task: str | None, priority: int | None) -> None:
    rows = read_list(path)
    idx = find_row(rows, task_id)
    if idx < 0:
        print(f"ID {task_id} introuvable.", file=sys.stderr)
        sys.exit(1)

    if task is None:
        task = input(f"Nouvelle description [{rows[idx]['task']}]: ").strip() or rows[idx]["task"]
    if priority is None:
        prio_str = input(f"Nouvelle priorité [{rows[idx]['priority']}]: ").strip()
        if prio_str:
            try:
                priority = int(prio_str)
            except ValueError:
                print("Priorité doit être un entier.", file=sys.stderr)
                sys.exit(1)

    rows[idx]["task"] = task
    if priority is not None:
        rows[idx]["priority"] = priority
    rows[idx]["modified"] = now_iso()
    write_list(path, rows)
    print(f"Modifié : [{rows[idx]['id']}] {rows[idx]['task']} (priorité {rows[idx]['priority']})")


def move_to_done_section(rows: list[dict]) -> list[dict]:
    """Réorganise la liste : TODO d'abord, DONE à la fin (ordre interne préservé)."""
    return [r for r in rows if r["status"] == STATUS_TODO] + \
           [r for r in rows if r["status"] == STATUS_DONE]


def sort_rows(rows: list[dict], sort_by: str, status: str) -> list[dict]:
    """Tri selon le critère, en fonction du statut."""
    if sort_by == "created":
        key = lambda r: r["created"]
    elif sort_by == "modified":
        key = lambda r: r["modified"]
    elif sort_by == "priority":
        key = lambda r: -r["priority"]  # décroissant : prioritaire en premier
    elif sort_by == "done_at":
        key = lambda r: r["done_at"]
    else:
        print(f"Critère de tri inconnu : {sort_by}", file=sys.stderr)
        sys.exit(1)
    return sorted(rows, key=key)


def list_tasks(path: Path, status: str | None, sort_by: str) -> None:
    rows = read_list(path)
    if status:
        rows = [r for r in rows if r["status"] == status.upper()]
    rows = sort_rows(rows, sort_by, status)
    rows = move_to_done_section(rows)

    if not rows:
        print("(vide)")
        return

    print(f"{'ID':<5}{'STATUT':<7}{'CRÉÉ':<20}{'MODIF':<20}{'DONE_AT':<20}{'PRIO':<5}TÂCHE")
    for r in rows:
        print(f"{r['id']:<5}{r['status']:<7}{r['created']:<20}{r['modified']:<20}"
              f"{r['done_at']:<20}{r['priority']:<5}{r['task']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestionnaire de listes TODO")
    parser.add_argument("list", help="Chemin du fichier de liste")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Ajouter une tâche")
    p_add.add_argument("task", help="Description de la tâche")
    p_add.add_argument("-p", "--priority", type=int, default=0, help="Priorité (entier)")

    p_done = sub.add_parser("done", help="Marquer une tâche comme traitée")
    p_done.add_argument("id", type=int, help="ID de la tâche")

    p_edit = sub.add_parser("edit", help="Modifier une tâche")
    p_edit.add_argument("id", type=int, help="ID de la tâche")
    p_edit.add_argument("-t", "--task", default=None, help="Nouvelle description")
    p_edit.add_argument("-p", "--priority", type=int, default=None, help="Nouvelle priorité")

    p_list = sub.add_parser("list", help="Afficher la liste")
    p_list.add_argument("--status", choices=["TODO", "DONE"], default=None,
                        help="Filtrer par statut")
    p_list.add_argument("--sort", choices=["created", "modified", "priority", "done_at"],
                        default="created", help="Critère de tri")

    args = parser.parse_args()
    path = Path(args.list)

    if args.command == "add":
        add_task(path, args.task, args.priority)
    elif args.command == "done":
        mark_done(path, args.id)
    elif args.command == "edit":
        edit_task(path, args.id, args.task, args.priority)
    elif args.command == "list":
        list_tasks(path, args.status, args.sort)


if __name__ == "__main__":
    main()