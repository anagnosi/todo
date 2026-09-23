#!/usr/bin/env python3
"""TUI (Text User Interface) pour le gestionnaire de listes TODO.

Navigation au clavier :
- Flèches haut/bas : déplacer la sélection
- Entrée : modifier la tâche sélectionnée
- d : marquer comme DONE (depuis TODO)
- u : marquer comme TODO (depuis DONE)
- Tab : basculer entre les sections TODO et DONE
- q : quitter
- r : trier les tâches réalisées
"""

from __future__ import annotations

import curses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import todo as core


def draw_header(stdscr, text: str, width: int) -> None:
    stdscr.addnstr(0, 0, text, width, curses.A_BOLD | curses.A_REVERSE)


def draw_task(stdscr, row: int, task: dict, selected: bool, width: int) -> None:
    attr = curses.A_REVERSE if selected else curses.A_NORMAL
    task_line = task["task"].splitlines()[0] if task["task"] else ""
    cat = task.get("category", "")
    due = task.get("due_date", "")
    prio = task.get("priority", 0)
    line = f"[{task['id']}] P{prio:>5} {task_line[:50]}"
    if cat:
        line += f" | {cat[:10]}"
    if due:
        line += f" | {due[:10]}"
    if task.get("status") == core.STATUS_DONE and task.get("done_at"):
        line += f" | Réalisée: {task['done_at'][:10]}"
    stdscr.addnstr(row, 0, line, width, attr)


def draw_help(stdscr, width: int) -> None:
    help_text = "↑/↓: naviguer | Entrée: détails | n: nouveau | i: ID | p: priorité | e: échéance | r: réalisée | f: filtre catégorie | d: done | u: undone | Tab: TODO/DONE | q: quitter"
    stdscr.addnstr(curses.LINES - 1, 0, help_text, width, curses.A_REVERSE)


def category_matches(task: dict, category_filter: str) -> bool:
    pattern = category_filter.strip().strip("*")
    category = task.get("category", "")
    return not pattern or pattern.casefold() in (category or "").casefold()


def prompt_category_filter(stdscr, current: str) -> str | None:
    value = current
    prompt = "Filtre catégorie (Entrée: appliquer, Échap: annuler): "
    row = curses.LINES - 2

    curses.curs_set(1)
    while True:
        stdscr.move(row, 0)
        stdscr.clrtoeol()
        stdscr.addnstr(row, 0, prompt + value, curses.COLS, curses.A_REVERSE)
        stdscr.move(row, min(len(prompt) + len(value), curses.COLS - 1))
        stdscr.refresh()

        key = stdscr.get_wch()
        if isinstance(key, str):
            if key in ("\n", "\r"):
                curses.curs_set(0)
                return value.strip()
            if key == "\x1b":
                curses.curs_set(0)
                return None
            if key not in ("\b", "\x7f", "\t"):
                value += key
        elif key in (curses.KEY_BACKSPACE, 8, 127):
            value = value[:-1]


def edit_task_in_window(stdscr, task: dict, path: Path, title: str = "Modification de la tâche") -> str | None:
    """Édite la tâche dans une fenêtre dédiée qui s'adapte à la taille de l'écran.
    Les flèches de direction permettent de déplacer le curseur dans le texte.
    Retourne la nouvelle valeur de la description, ou None si annulée.
    """
    value = task["task"]
    # Position du curseur dans la valeur (ligne, colonne)
    lines = value.split("\n")
    cur_line = len(lines) - 1
    cur_col = len(lines[-1]) if lines else 0
    curses.curs_set(1)

    while True:
        win_h = curses.LINES - 2
        win_w = curses.COLS - 2
        win = curses.newwin(win_h, win_w, 1, 1)
        win.box()
        win.addnstr(0, 2, f"{title} [{task['id']}]", win_w - 4, curses.A_BOLD)
        win.addnstr(win_h - 2, 2, "Entrée: saut de ligne | Tab: sauvegarder | Échap: annuler", win_w - 4, curses.A_REVERSE)
        win.refresh()

        edit_win = curses.newwin(win_h - 4, win_w - 4, 3, 2)
        edit_win.keypad(True)

        edit_win.erase()
        lines = value.split("\n")
        for i, line in enumerate(lines[:win_h - 5]):
            edit_win.addnstr(i, 0, line, win_w - 4)
        edit_win.refresh()

        edit_win.move(min(cur_line, win_h - 6), min(cur_col, win_w - 5))
        curses.curs_set(1)

        key = edit_win.get_wch()
        # Normaliser les touches de contrôle en entiers
        if isinstance(key, str):
            if key == "\t":
                key = 9
            elif key == "\n":
                key = 10
            elif key == "\r":
                key = 13
            elif key == "\x1b":
                key = 27

        if isinstance(key, int) and key >= 256:
            # Touche spéciale (flèches, backspace, etc.)
            if key == curses.KEY_BACKSPACE:
                if cur_col > 0:
                    lines = value.split("\n")
                    lines[cur_line] = lines[cur_line][:cur_col - 1] + lines[cur_line][cur_col:]
                    value = "\n".join(lines)
                    cur_col -= 1
                elif cur_line > 0:
                    lines = value.split("\n")
                    prev_len = len(lines[cur_line - 1])
                    lines[cur_line - 1] += lines[cur_line]
                    del lines[cur_line]
                    value = "\n".join(lines)
                    cur_line -= 1
                    cur_col = prev_len
            elif key == curses.KEY_LEFT:
                if cur_col > 0:
                    cur_col -= 1
                elif cur_line > 0:
                    cur_line -= 1
                    lines = value.split("\n")
                    cur_col = len(lines[cur_line])
            elif key == curses.KEY_RIGHT:
                lines = value.split("\n")
                if cur_col < len(lines[cur_line]):
                    cur_col += 1
                elif cur_line < len(lines) - 1:
                    cur_line += 1
                    cur_col = 0
            elif key == curses.KEY_UP:
                if cur_line > 0:
                    cur_line -= 1
                    lines = value.split("\n")
                    cur_col = min(cur_col, len(lines[cur_line]))
            elif key == curses.KEY_DOWN:
                lines = value.split("\n")
                if cur_line < len(lines) - 1:
                    cur_line += 1
                    cur_col = min(cur_col, len(lines[cur_line]))
            elif key == curses.KEY_HOME:  # Début
                cur_col = 0
            elif key == curses.KEY_END:  # Fin
                lines = value.split("\n")
                cur_col = len(lines[cur_line]) if cur_line < len(lines) else 0
            elif key == curses.KEY_DC:  # Suppr
                lines = value.split("\n")
                if cur_col < len(lines[cur_line]):
                    lines[cur_line] = lines[cur_line][:cur_col] + lines[cur_line][cur_col + 1:]
                elif cur_line < len(lines) - 1:
                    lines[cur_line] += lines[cur_line + 1]
                    del lines[cur_line + 1]
                value = "\n".join(lines)
        elif isinstance(key, int) and key == 27:  # Échap → annuler
            curses.curs_set(0)
            return None
        elif isinstance(key, int) and key in (10, 13):  # Entrée → insérer un saut de ligne
            lines = value.split("\n")
            lines.insert(cur_line + 1, lines[cur_line][cur_col:])
            lines[cur_line] = lines[cur_line][:cur_col]
            value = "\n".join(lines)
            cur_line += 1
            cur_col = 0
        elif isinstance(key, int) and key == 9:  # Tab → sauvegarder et quitter
            curses.curs_set(0)
            return value
        elif isinstance(key, str):
            # Caractère imprimable (chaîne str, y compris UTF-8)
            lines = value.split("\n")
            lines[cur_line] = lines[cur_line][:cur_col] + key + lines[cur_line][cur_col:]
            value = "\n".join(lines)
            cur_col += 1


def show_task_details(stdscr, task: dict, path: Path, is_new: bool = False) -> None:
    """Affiche les détails de la tâche en plein écran.
    Navigation avec les flèches haut/bas, Entrée pour éditer, q pour revenir.
    Les tâches DONE sont en lecture seule.
    """
    # Champs éditables (en haut)
    editable_fields = [
        ("Priorité", str(task["priority"])),
        ("Catégorie", task.get("category", "")),
        ("Échéance", task.get("due_date", "")),
        ("Description", task["task"]),
    ]

    desc_index = 3  # Description est le dernier champ éditable
    selected = 0  # Priorité par défaut
    editing = False

    while True:
        is_done = task.get("status") == core.STATUS_DONE
        meta_parts = [
            f"Créée: {task['created']}",
            f"Modifiée: {task['modified']}",
            f"Statut: {task['status']}",
        ]
        if task.get("done_at"):
            meta_parts.append(f"Traité le: {task['done_at']}")

        stdscr.erase()
        title = "Nouvelle tâche" if is_new else f"Détails de la tâche [{task['id']}]"
        stdscr.addnstr(0, 0, title, curses.COLS, curses.A_BOLD | curses.A_REVERSE)

        row = 2
        for i, (label, value) in enumerate(editable_fields):
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            prefix = "> " if i == selected else "  "
            if i == desc_index:  # Description : afficher avec label
                real_value = value.replace("\\n", "\n")
                stdscr.addnstr(row, 0, f"{prefix}{label}:", curses.COLS, attr)
                row += 2  # saut de ligne après le label
                lines = real_value.split("\n") if real_value else [""]
                for line in lines:
                    stdscr.addnstr(row, 0, line, curses.COLS, curses.A_NORMAL)
                    row += 1
            else:  # Autres champs : une seule ligne
                display = value.replace("\n", " / ")
                stdscr.addnstr(row, 0, f"{prefix}{label}: {display}", curses.COLS, attr)
                row += 1

        # Afficher les métadonnées en bas
        stdscr.addnstr(curses.LINES - 3, 0, "  " + " | ".join(meta_parts), curses.COLS, curses.A_NORMAL)

        help_text = "↑/↓: naviguer | Entrée: éditer | d: done | u: undone | x: sauvegarder | q: annuler"
        if is_done:
            help_text = "↑/↓: naviguer | u: undone | q: revenir"
        stdscr.addnstr(curses.LINES - 1, 0, help_text, curses.COLS, curses.A_REVERSE)

        if editing and not is_done:
            curses.curs_set(1)
            lines = editable_fields[selected][1].split("\n") if editable_fields[selected][1] else [""]
            last_line = lines[-1] if lines else ""
            prefix = "> " if selected == 0 else "  "
            label = editable_fields[selected][0]
            if selected == desc_index:
                col = len(prefix) + len(last_line)
            else:
                col = len(f"{prefix}{label}: ") + len(last_line)
            actual_row = 2
            for i in range(selected):
                if i == desc_index:
                    actual_row += 2 + len(editable_fields[i][1].split("\n"))
                else:
                    actual_row += 1
            if selected == desc_index:
                actual_row += 2 + len(lines) - 1
            stdscr.move(actual_row, col)
        else:
            curses.curs_set(0)

        stdscr.refresh()

        key = stdscr.getch()

        # Raccourcis d/u fonctionnels partout
        if key == ord("d") and not is_done:
            task_id = int(task["id"])
            core.mark_done(path, task_id, silent=True)
            task["status"] = core.STATUS_DONE
            task["done_at"] = core.now_iso()
            task["modified"] = core.now_iso()
            continue
        elif key == ord("u") and is_done:
            task_id = int(task["id"])
            core.unmark_done(path, task_id, silent=True)
            task["status"] = core.STATUS_TODO
            task["done_at"] = ""
            task["modified"] = core.now_iso()
            continue

        if editing and not is_done:
            if key == 27:  # Échap → annuler l'édition
                editing = False
            elif key in (10, 13):  # Entrée → valider
                editing = False
            elif key == 9:  # Tab → saut de ligne (Description)
                if selected == desc_index:
                    editable_fields[selected] = (editable_fields[selected][0], editable_fields[selected][1] + "\n")
            elif key == ord("x"):  # sauvegarder et quitter
                break
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                val = editable_fields[selected][1]
                editable_fields[selected] = (editable_fields[selected][0], val[:-1])
            elif 0 <= key <= 255 and key not in (9,):
                editable_fields[selected] = (editable_fields[selected][0], editable_fields[selected][1] + chr(key))
        else:
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(editable_fields)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(editable_fields)
            elif key == 10 and not is_done:  # Entrée → commencer l'édition
                if selected == desc_index:
                    # Pour la Description, ouvrir une fenêtre dédiée
                    new_task = edit_task_in_window(stdscr, task, path, title="Nouvelle tâche" if is_new else "Modification de la tâche")
                    if new_task is not None:
                        editable_fields[desc_index] = ("Description", new_task)
                else:
                    editing = True
            elif key == ord("x") and not is_done:  # sauvegarder et quitter
                break
            elif key == ord("q"):  # quitter sans sauvegarder
                return

    # Sauvegarde (uniquement si pas DONE)
    if is_done:
        return

    task["task"] = editable_fields[desc_index][1]
    try:
        task["priority"] = int(editable_fields[0][1])
    except ValueError:
        pass
    task["category"] = editable_fields[1][1]
    task["due_date"] = editable_fields[2][1]
    task["modified"] = core.now_iso()

    if is_new:
        # Créer une nouvelle tâche
        core.add_task(path, task["task"], task["priority"], task["category"], task["due_date"], silent=True)
    else:
        # Modifier une tâche existante
        rows = core.read_list(path)
        for r in rows:
            if r["id"] == task["id"]:
                r.update(task)
                break
        core.write_list(path, rows)


def create_new_task(stdscr, path: Path) -> None:
    """Crée une nouvelle tâche avec un écran identique à l'édition."""
    ts = core.now_iso()
    new_task = {
        "id": "?",  # provisoire
        "created": ts,
        "modified": ts,
        "priority": 0,
        "status": core.STATUS_TODO,
        "done_at": "",
        "category": "",
        "due_date": "",
        "task": "",
    }
    show_task_details(stdscr, new_task, path, is_new=True)


def run_tui(path: Path) -> None:
    def main(stdscr):
        curses.curs_set(0)
        selected = 0
        show_done = False
        sort_key = "id"
        sort_reverse = False
        category_filter = ""

        while True:
            rows = core.sort_rows(core.read_list(path), sort_key, None)
            if sort_reverse:
                rows.reverse()
            rows = core.move_to_done_section(rows)
            todo_rows = [r for r in rows if r["status"] == core.STATUS_TODO and category_matches(r, category_filter)]
            done_rows = [r for r in rows if r["status"] == core.STATUS_DONE and category_matches(r, category_filter)]
            current = done_rows if show_done else todo_rows

            stdscr.erase()
            title = "Tâches à traiter (TODO)" if not show_done else "Tâches traitées (DONE)"
            sort_labels = {"id": "ID", "priority": "Priorité", "due_date": "Échéance", "done_at": "Réalisée"}
            sort_directions = {
                "id": ("croissant", "décroissant"),
                "priority": ("décroissant", "croissant"),
                "due_date": ("croissant", "décroissant"),
                "done_at": ("décroissant", "croissant"),
            }
            direction = sort_directions[sort_key][sort_reverse]
            title += f" | Tri: {sort_labels[sort_key]} ({direction})"
            if category_filter:
                title += f" | Filtre: *{category_filter}*"
            draw_header(stdscr, title, curses.COLS)
            draw_help(stdscr, curses.COLS)

            if not current:
                stdscr.addstr(2, 0, "(vide)")
            else:
                if selected >= len(current):
                    selected = 0
                for i, task in enumerate(current):
                    draw_task(stdscr, i + 2, task, i == selected, curses.COLS)

            stdscr.refresh()

            key = stdscr.getch()
            if key == ord("q"):
                break
            elif key == curses.KEY_UP:
                selected = max(0, selected - 1)
            elif key == curses.KEY_DOWN:
                selected = min(len(current) - 1, selected + 1)
            elif key == 9:
                show_done = not show_done
                selected = 0
            elif key == ord("r"):
                if sort_key == "done_at":
                    sort_reverse = not sort_reverse
                else:
                    sort_key = "done_at"
                    sort_reverse = False
                selected = 0
            elif key == ord("i"):
                if sort_key == "id":
                    sort_reverse = not sort_reverse
                else:
                    sort_key = "id"
                    sort_reverse = False
                selected = 0
            elif key == ord("p"):
                if sort_key == "priority":
                    sort_reverse = not sort_reverse
                else:
                    sort_key = "priority"
                    sort_reverse = False
                selected = 0
            elif key == ord("e"):
                if sort_key == "due_date":
                    sort_reverse = not sort_reverse
                else:
                    sort_key = "due_date"
                    sort_reverse = False
                selected = 0
            elif key == ord("f"):
                new_filter = prompt_category_filter(stdscr, category_filter)
                if new_filter is not None:
                    category_filter = new_filter
                    selected = 0
            elif key == ord("n"):
                create_new_task(stdscr, path)
            elif key == ord("d") and current and not show_done:
                # Marquer comme DONE
                task_id = int(current[selected]["id"])
                core.mark_done(path, task_id, silent=True)
                if selected >= len(current) - 1:
                    selected = max(0, selected - 1)
            elif key == ord("u") and current and show_done:
                # Marquer comme TODO et ouvrir les détails
                task_id = int(current[selected]["id"])
                core.unmark_done(path, task_id, silent=True)
                rows = core.read_list(path)
                for r in rows:
                    if r["id"] == current[selected]["id"]:
                        show_task_details(stdscr, r, path)
                        break
                selected = 0
            elif key == 10 and current:
                show_task_details(stdscr, current[selected], path)
                selected = 0

    curses.wrapper(main)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 todo_tui.py <fichier.list>", file=sys.stderr)
        sys.exit(1)
    path = Path(sys.argv[1])
    run_tui(path)


if __name__ == "__main__":
    main()