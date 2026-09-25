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
import json
import sys
from datetime import datetime
from pathlib import Path


STATUS_TODO = "TODO"
STATUS_DONE = "DONE"


def safe_addnstr(screen, row: int, col: int, text: str, width: int,
                 attr: int = curses.A_NORMAL) -> None:
    if width <= 0 or row < 0 or col < 0:
        return
    try:
        max_rows, max_cols = screen.getmaxyx()
    except (AttributeError, curses.error):
        max_rows, max_cols = curses.LINES, curses.COLS
    if row >= max_rows or col >= max_cols:
        return
    width = min(width, max_cols - col)
    if row == max_rows - 1 and col + width >= max_cols:
        width = max(0, width - 1)
    if width <= 0:
        return
    try:
        screen.addnstr(row, col, text, width, attr)
    except curses.error:
        pass


def safe_move(screen, row: int, col: int) -> None:
    try:
        max_rows, max_cols = screen.getmaxyx()
    except (AttributeError, curses.error):
        max_rows, max_cols = curses.LINES, curses.COLS
    row = min(max(row, 0), max(0, max_rows - 1))
    col = min(max(col, 0), max(0, max_cols - 1))
    try:
        screen.move(row, col)
    except curses.error:
        pass


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_due_date(value: str) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            return None
    if len(value) == 19 and value[10] == "T":
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            return value
        except ValueError:
            return None
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


def add_task(path: Path, task: str | None, priority: int, category: str | None, due_date: str | None,
             silent: bool = False) -> None:
    rows = read_list(path)
    ts = now_iso()
    if task is None:
        raise ValueError("La description de la tâche est requise.")
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


def move_to_done_section(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["status"] == STATUS_TODO] + \
           [r for r in rows if r["status"] == STATUS_DONE]


def sort_rows(rows: list[dict], sort_by: str, status: str | None) -> list[dict]:
    if sort_by == "id":
        key = lambda r: int(r["id"])
    elif sort_by == "created":
        key = lambda r: r["created"]
    elif sort_by == "modified":
        key = lambda r: r["modified"]
    elif sort_by == "priority":
        key = lambda r: r["priority"]
    elif sort_by == "done_at":
        key = lambda r: r["done_at"]
    elif sort_by == "due_date":
        key = lambda r: r.get("due_date", "") or "9999"
    else:
        print(f"Critère de tri inconnu : {sort_by}", file=sys.stderr)
        sys.exit(1)
    return sorted(rows, key=key)


def draw_header(stdscr, text: str, width: int) -> None:
    safe_addnstr(stdscr, 0, 0, text, width, curses.A_BOLD | curses.A_REVERSE)


def draw_task(stdscr, row: int, task: dict, selected: bool, width: int) -> None:
    if row >= curses.LINES - 1:
        return
    attr = curses.A_REVERSE if selected else curses.A_NORMAL
    task_line = task["task"].splitlines()[0] if task["task"] else ""
    cat = task.get("category", "")
    due = task.get("due_date", "")
    prio = task.get("priority", 0)
    line = f"[{task['id']}] P{prio:>5} {task_line[:120]}"
    if cat:
        line += f" | {cat[:10]}"
    if due:
        line += f" | {due[:10]}"
    if task.get("status") == STATUS_DONE and task.get("done_at"):
        line += f" | Réalisée: {task['done_at'][:10]}"
    safe_addnstr(stdscr, row, 0, line, width, attr)


def draw_help(stdscr, width: int) -> None:
    help_text = "↑/↓: naviguer | Entrée: détails | n: nouveau | i: ID | p: priorité | e: échéance | r: réalisée | c: catégorie | /: chercher | d: done | u: undone | Tab: TODO/DONE | q: quitter"
    safe_addnstr(stdscr, curses.LINES - 1, 0, help_text, width, curses.A_REVERSE)


def matches_occurrence(value: str | None, query: str) -> bool:
    query = query.strip()
    return not query or query.casefold() in (value or "").casefold()


def category_matches(task: dict, category_filter: str) -> bool:
    return matches_occurrence(task.get("category"), category_filter)


def task_matches(task: dict, description_filter: str) -> bool:
    return matches_occurrence(task.get("task"), description_filter)


def prompt_filter(stdscr, current: str, label: str) -> str | None:
    value = current
    prompt = f"{label} (Entrée: appliquer, Échap: annuler): "
    row = curses.LINES - 2

    curses.curs_set(1)
    while True:
        safe_move(stdscr, row, 0)
        stdscr.clrtoeol()
        safe_addnstr(stdscr, row, 0, prompt + value, curses.COLS, curses.A_REVERSE)
        safe_move(stdscr, row, min(len(prompt) + len(value), curses.COLS - 1))
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


def prompt_category_filter(stdscr, current: str) -> str | None:
    return prompt_filter(stdscr, current, "Filtre catégorie")


def prompt_task_filter(stdscr, current: str) -> str | None:
    return prompt_filter(stdscr, current, "Recherche description")


def edit_task_in_window(stdscr, task: dict, path: Path, title: str = "Modification de la tâche") -> str | None:
    """Édite la tâche dans une fenêtre dédiée qui s'adapte à la taille de l'écran.
    Les flèches de direction permettent de déplacer le curseur dans le texte.
    Retourne la nouvelle valeur de la description, ou None si annulée.
    """
    value = task.get("task") or ""
    lines = value.split("\n")
    cur_line = len(lines) - 1
    cur_col = len(lines[-1]) if lines else 0
    top_visual = 0
    curses.curs_set(1)

    def build_visual_lines(text_lines: list[str], width: int) -> tuple[list[int], list[int], list[tuple[int, int, str]]]:
        chunks_per_line = [max(1, (len(line) + width - 1) // width) for line in text_lines]
        chunks_before = []
        visual_lines = []
        visual_count = 0
        for line_index, line in enumerate(text_lines):
            chunks_before.append(visual_count)
            for chunk_index in range(chunks_per_line[line_index]):
                start = chunk_index * width
                visual_lines.append((line_index, start, line[start:start + width]))
            visual_count += chunks_per_line[line_index]
        return chunks_per_line, chunks_before, visual_lines

    def cursor_visual_position(
        text_lines: list[str],
        chunks_per_line: list[int],
        chunks_before: list[int],
        line_index: int,
        column: int,
        width: int,
    ) -> tuple[int, int]:
        line_index = min(max(line_index, 0), len(text_lines) - 1)
        column = min(max(column, 0), len(text_lines[line_index]))
        chunk_index = min(column // width, chunks_per_line[line_index] - 1)
        visual_index = chunks_before[line_index] + chunk_index
        visual_column = min(column - chunk_index * width, width - 1)
        return visual_index, visual_column

    while True:
        lines = value.split("\n")
        if not lines:
            lines = [""]
        win_h = max(5, curses.LINES - 4)
        win_w = max(5, curses.COLS)
        if curses.LINES < 9 or curses.COLS < 5:
            return value
        win = curses.newwin(win_h, win_w, 1, 0)
        help_text = f"Entrée: saut de ligne | Tab: sauvegarder | Échap: annuler | Ligne {cur_line + 1}/{len(lines)}"
        try:
            win.box()
            safe_addnstr(win, 0, 2, f"{title} [{task['id']}]", win_w - 4, curses.A_BOLD)
            safe_addnstr(win, win_h - 2, 2, help_text, win_w - 4, curses.A_REVERSE)
            win.refresh()
        except curses.error:
            pass

        edit_h = max(1, win_h - 4)
        edit_w = max(1, win_w - 2)
        edit_win = curses.newwin(edit_h, edit_w, 2, 1)
        edit_win.keypad(True)

        cur_line = min(max(cur_line, 0), len(lines) - 1)
        cur_col = min(max(cur_col, 0), len(lines[cur_line]))

        chunks_per_line, chunks_before, visual_lines = build_visual_lines(lines, edit_w)
        cur_visual, cur_visual_col = cursor_visual_position(
            lines,
            chunks_per_line,
            chunks_before,
            cur_line,
            cur_col,
            edit_w,
        )

        if cur_visual < top_visual:
            top_visual = cur_visual
        elif cur_visual >= top_visual + edit_h:
            top_visual = cur_visual - edit_h + 1
        top_visual = min(max(top_visual, 0), max(0, len(visual_lines) - edit_h))

        try:
            edit_win.erase()
            for visible_row in range(edit_h):
                source_visual = top_visual + visible_row
                if source_visual >= len(visual_lines):
                    break
                _, _, text = visual_lines[source_visual]
                safe_addnstr(edit_win, visible_row, 0, text, edit_w)
            edit_win.refresh()
            safe_move(edit_win, min(cur_visual - top_visual, edit_h - 1),
                      min(cur_visual_col, edit_w - 1))
        except curses.error:
            pass
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
                cur_visual, cur_visual_col = cursor_visual_position(
                    lines, chunks_per_line, chunks_before, cur_line, cur_col, edit_w
                )
                if cur_visual > 0:
                    cur_visual -= 1
                    target_line, target_start, _ = visual_lines[cur_visual]
                    cur_line = target_line
                    cur_col = min(target_start + cur_visual_col, len(lines[target_line]))
            elif key == curses.KEY_DOWN:
                cur_visual, cur_visual_col = cursor_visual_position(
                    lines, chunks_per_line, chunks_before, cur_line, cur_col, edit_w
                )
                if cur_visual < len(visual_lines) - 1:
                    cur_visual += 1
                    target_line, target_start, _ = visual_lines[cur_visual]
                    cur_line = target_line
                    cur_col = min(target_start + cur_visual_col, len(lines[target_line]))
            elif key == curses.KEY_PPAGE:
                cur_visual, cur_visual_col = cursor_visual_position(
                    lines, chunks_per_line, chunks_before, cur_line, cur_col, edit_w
                )
                target_visual = max(0, cur_visual - edit_h)
                target_line, target_start, _ = visual_lines[target_visual]
                cur_line = target_line
                cur_col = min(target_start + cur_visual_col, len(lines[target_line]))
            elif key == curses.KEY_NPAGE:
                cur_visual, cur_visual_col = cursor_visual_position(
                    lines, chunks_per_line, chunks_before, cur_line, cur_col, edit_w
                )
                target_visual = min(len(visual_lines) - 1, cur_visual + edit_h)
                target_line, target_start, _ = visual_lines[target_visual]
                cur_line = target_line
                cur_col = min(target_start + cur_visual_col, len(lines[target_line]))
            elif key == curses.KEY_HOME:
                cur_visual, _ = cursor_visual_position(
                    lines, chunks_per_line, chunks_before, cur_line, cur_col, edit_w
                )
                _, cur_col, _ = visual_lines[cur_visual]
            elif key == curses.KEY_END:
                cur_visual, _ = cursor_visual_position(
                    lines, chunks_per_line, chunks_before, cur_line, cur_col, edit_w
                )
                target_line, target_start, target_text = visual_lines[cur_visual]
                cur_line = target_line
                cur_col = min(target_start + len(target_text), len(lines[target_line]))
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
    desc_top = 0
    max_desc_lines = 0

    def safe_add(row: int, text: str, attr: int = curses.A_NORMAL) -> None:
        safe_addnstr(stdscr, row, 0, text, curses.COLS, attr)

    while True:
        is_done = task.get("status") == STATUS_DONE
        meta_parts = [
            f"Créée: {task['created']}",
            f"Modifiée: {task['modified']}",
            f"Statut: {task['status']}",
        ]
        if task.get("done_at"):
            meta_parts.append(f"Traité le: {task['done_at']}")

        stdscr.erase()
        title = "Nouvelle tâche" if is_new else f"Détails de la tâche [{task['id']}]"
        safe_add(0, title, curses.A_BOLD | curses.A_REVERSE)

        row = 2
        for i, (label, value) in enumerate(editable_fields):
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            prefix = "> " if i == selected else "  "
            if i == desc_index:  # Description : afficher avec label
                real_value = value.replace("\\n", "\n")
                safe_add(row, f"{prefix}{label}:", attr)
                row += 2  # saut de ligne après le label
                lines = real_value.split("\n") if real_value else [""]
                desc_start = row
                max_desc_lines = max(0, curses.LINES - 5 - desc_start)
                visible_lines = lines[desc_top:desc_top + max_desc_lines]
                for line in visible_lines:
                    safe_add(row, line)
                    row += 1
                if max_desc_lines > 0 and len(lines) > max_desc_lines:
                    hidden = len(lines) - max_desc_lines
                    safe_add(row, f"... {hidden} ligne(s) masquée(s) | Page haut/bas")
            else:  # Autres champs : une seule ligne
                display = value.replace("\n", " / ")
                safe_add(row, f"{prefix}{label}: {display}", attr)
                row += 1

        safe_add(curses.LINES - 3, " | ".join(meta_parts))

        help_text = "↑/↓: naviguer | Entrée: éditer | d: done | u: undone | x: sauvegarder | q: annuler"
        if is_done:
            help_text = "↑/↓: naviguer | u: undone | q: revenir"
        safe_add(curses.LINES - 1, help_text, curses.A_REVERSE)

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
            actual_row = min(max(actual_row, 0), max(0, curses.LINES - 4))
            col = min(max(col, 0), max(0, curses.COLS - 1))
            try:
                stdscr.move(actual_row, col)
            except curses.error:
                pass
        else:
            curses.curs_set(0)

        stdscr.refresh()

        key = stdscr.getch()

        # Raccourcis d/u fonctionnels partout
        if key == ord("d") and not is_done:
            task_id = int(task["id"])
            mark_done(path, task_id, silent=True)
            task["status"] = STATUS_DONE
            task["done_at"] = now_iso()
            task["modified"] = now_iso()
            continue
        elif key == ord("u") and is_done:
            task_id = int(task["id"])
            unmark_done(path, task_id, silent=True)
            task["status"] = STATUS_TODO
            task["done_at"] = ""
            task["modified"] = now_iso()
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
            elif key == curses.KEY_PPAGE and selected == desc_index:
                desc_top = max(0, desc_top - max_desc_lines)
            elif key == curses.KEY_NPAGE and selected == desc_index:
                desc_lines = editable_fields[desc_index][1].replace("\\n", "\n").split("\n")
                desc_top = min(max(0, len(desc_lines) - max_desc_lines), desc_top + max_desc_lines)
            elif key in (10, 13, curses.KEY_ENTER) and not is_done:  # Entrée → commencer l'édition
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
    task["modified"] = now_iso()

    if is_new:
        # Créer une nouvelle tâche
        add_task(path, task["task"], task["priority"], task["category"], task["due_date"], silent=True)
    else:
        # Modifier une tâche existante
        rows = read_list(path)
        for r in rows:
            if r["id"] == task["id"]:
                r.update(task)
                break
        write_list(path, rows)


def create_new_task(stdscr, path: Path) -> None:
    """Crée une nouvelle tâche avec un écran identique à l'édition."""
    ts = now_iso()
    new_task = {
        "id": "?",  # provisoire
        "created": ts,
        "modified": ts,
        "priority": 0,
        "status": STATUS_TODO,
        "done_at": "",
        "category": "",
        "due_date": "",
        "task": "",
    }
    show_task_details(stdscr, new_task, path, is_new=True)


def run_tui(path: Path) -> None:
    def main(stdscr):
        stdscr.keypad(True)
        curses.curs_set(0)
        curses.noecho()
        selected = 0
        show_done = False
        sort_key = "id"
        sort_reverse = False
        category_filter = ""
        description_filter = ""

        while True:
            rows = sort_rows(read_list(path), sort_key, None)
            if sort_reverse:
                rows.reverse()
            rows = move_to_done_section(rows)
            todo_rows = [
                r for r in rows
                if r["status"] == STATUS_TODO
                and category_matches(r, category_filter)
                and task_matches(r, description_filter)
            ]
            done_rows = [
                r for r in rows
                if r["status"] == STATUS_DONE
                and category_matches(r, category_filter)
                and task_matches(r, description_filter)
            ]
            current = done_rows if show_done else todo_rows

            stdscr.erase()
            title = "Tâches à traiter (TODO)" if not show_done else "Tâches traitées (DONE)"
            sort_labels = {"id": "ID", "priority": "Priorité", "due_date": "Échéance", "done_at": "Réalisée"}
            sort_directions = {
                "id": ("croissant", "décroissant"),
                "priority": ("croissant", "décroissant"),
                "due_date": ("croissant", "décroissant"),
                "done_at": ("décroissant", "croissant"),
            }
            direction = sort_directions[sort_key][sort_reverse]
            title += f" | Tri: {sort_labels[sort_key]} ({direction})"
            if category_filter:
                title += f" | Catégorie: {category_filter}"
            if description_filter:
                title += f" | Description: {description_filter}"
            draw_header(stdscr, title, curses.COLS)
            draw_help(stdscr, curses.COLS)

            if not current:
                safe_addnstr(stdscr, 2, 0, "(vide)", curses.COLS)
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
            elif key == ord("c"):
                new_filter = prompt_category_filter(stdscr, category_filter)
                if new_filter is not None:
                    category_filter = new_filter
                    selected = 0
            elif key == ord("/"):
                new_filter = prompt_task_filter(stdscr, description_filter)
                if new_filter is not None:
                    description_filter = new_filter
                    selected = 0
            elif key == ord("n"):
                create_new_task(stdscr, path)
            elif key == ord("d") and current and not show_done:
                # Marquer comme DONE
                task_id = int(current[selected]["id"])
                mark_done(path, task_id, silent=True)
                if selected >= len(current) - 1:
                    selected = max(0, selected - 1)
            elif key == ord("u") and current and show_done:
                # Marquer comme TODO et ouvrir les détails
                task_id = int(current[selected]["id"])
                unmark_done(path, task_id, silent=True)
                rows = read_list(path)
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
        print(f"Usage: python3 {Path(sys.argv[0]).name} <fichier.list>", file=sys.stderr)
        sys.exit(1)
    path = Path(sys.argv[1])
    run_tui(path)


if __name__ == "__main__":
    main()