"""
Status Window — Daily Quest Log
A Kivy (pure Python) rewrite of the daily schedule app.

Run it with:
    pip install kivy
    python main.py

Everything about how the app behaves lives in this file, in plain
Python. The visual layout/styling lives in statuswindow.kv (Kivy's
layout language — it's mostly declarative, similar in spirit to how
you'd describe a UI in a dict/config, not a separate "language" to
learn deeply).
"""

import json
import os
import uuid
from datetime import datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window

Window.clearcolor = (0.02, 0.03, 0.06, 1)

# ---------------------------------------------------------------------------
# Colors — same palette as the web version, expressed as 0-1 RGBA tuples
# ---------------------------------------------------------------------------
COL_BG = (0.02, 0.03, 0.06, 1)
COL_PANEL = (0.04, 0.07, 0.13, 1)
COL_PANEL_RAISED = (0.06, 0.10, 0.19, 1)
COL_LINE = (0.12, 0.23, 0.42, 1)
COL_BLUE = (0.31, 0.76, 1, 1)
COL_PURPLE = (0.65, 0.55, 0.98, 1)
COL_GOLD = (1, 0.78, 0.34, 1)
COL_RED = (1, 0.27, 0.33, 1)
COL_TEXT = (0.9, 0.95, 1, 1)
COL_MUTED = (0.42, 0.48, 0.6, 1)

# ---------------------------------------------------------------------------
# Persistence — a single JSON file on disk, right next to the app's data
# folder. This is the Python equivalent of the localStorage/window.storage
# calls in the web version.
# ---------------------------------------------------------------------------

def default_state():
    return {
        "start_time": "09:30",
        "auto_reschedule": False,
        "completed_days": [],
        "history": {},          # date string -> {"start_time":..., "tasks":[...]}
        "scheduled_next": [],   # tasks queued for tomorrow
        "active_timer": None,   # {"task_id":..., "started_at": iso str, "paused": bool, "remaining_sec": float}
        "last_date": None,
        "tasks": [
            {"id": "mindfulness", "name": "Jimquick mindfulness", "duration": 30, "enabled": True, "completed": False, "notes": ""},
            {"id": "workout", "name": "Workout", "duration": 60, "enabled": True, "completed": False, "notes": ""},
            {"id": "hyperion", "name": "Hyperion dev review", "duration": 60, "enabled": True, "completed": False, "notes": ""},
            {"id": "codingapp", "name": "Coding language app", "duration": 120, "enabled": True, "completed": False, "notes": ""},
            {"id": "jobsearch", "name": "Job search", "duration": 60, "enabled": True, "completed": False, "notes": ""},
            {"id": "lunch", "name": "Lunch / buffer", "duration": 60, "enabled": True, "completed": False, "notes": ""},
            {"id": "myganet", "name": "Myganet website", "duration": 60, "enabled": True, "completed": False, "notes": ""},
            {"id": "barber", "name": "Barber shop app", "duration": 60, "enabled": True, "completed": False, "notes": ""},
            {"id": "trading", "name": "Trading app/website", "duration": 60, "enabled": True, "completed": False, "notes": ""},
            {"id": "shower", "name": "Shower", "duration": 30, "enabled": True, "completed": False, "notes": ""},
            {"id": "cook", "name": "Cook dinner", "duration": 45, "enabled": True, "completed": False, "notes": ""},
            {"id": "eat", "name": "Eat dinner", "duration": 30, "enabled": True, "completed": False, "notes": ""},
            {"id": "clean", "name": "Clean up", "duration": 30, "enabled": True, "completed": False, "notes": ""},
        ],
    }


def today_key():
    return datetime.now().strftime("%Y-%m-%d")


def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            # merge in any new default keys an older save file might be missing
            for k, v in default_state().items():
                state.setdefault(k, v)
            return state
        except (json.JSONDecodeError, OSError):
            pass
    return default_state()


def save_state(path, state):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_path, path)  # atomic-ish write, avoids half-written files


def apply_daily_rollover(state):
    """If the calendar day has changed since we last saved, archive
    yesterday into history, reset today's completed/notes, and pull in
    anything queued for 'tomorrow'."""
    today = today_key()
    if state["last_date"] and state["last_date"] != today:
        state["history"][state["last_date"]] = {
            "start_time": state["start_time"],
            "tasks": json.loads(json.dumps(state["tasks"])),  # deep copy
        }
        reset_tasks = []
        for t in state["tasks"]:
            if t.get("custom"):
                continue  # one-off tasks don't carry over
            t = dict(t)
            t["completed"] = False
            t["notes"] = ""
            t["_alerted"] = False
            reset_tasks.append(t)
        for item in state.get("scheduled_next", []):
            reset_tasks.append({
                "id": "custom-" + uuid.uuid4().hex[:8],
                "name": item["name"],
                "duration": item["duration"],
                "enabled": True,
                "completed": False,
                "notes": "",
                "custom": True,
            })
        state["tasks"] = reset_tasks
        state["scheduled_next"] = []
        state["auto_reschedule"] = False
        state["active_timer"] = None
    state["last_date"] = today
    return state


def compute_streak(state):
    days = set(state.get("completed_days", []))
    streak = 0
    cursor = datetime.now().date()
    while cursor.strftime("%Y-%m-%d") in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def parse_hhmm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def format_hhmm(total_minutes):
    total_minutes = int(total_minutes) % (24 * 60)
    h, m = divmod(total_minutes, 60)
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{m:02d} {ampm}"


def duration_label(minutes):
    if minutes < 60:
        return f"{minutes}m"
    h, m = divmod(minutes, 60)
    return f"{h}h" if m == 0 else f"{h}h {m}m"


def compute_schedule(state):
    """Returns a list of dicts: one per task, each with computed
    start_minute/end_minute (only meaningful if the task is enabled),
    honoring the 'reschedule from now' anchor if it's turned on."""
    cursor = parse_hhmm(state["start_time"])
    now_minutes = datetime.now().hour * 60 + datetime.now().minute
    anchored = False
    rows = []
    for task in state["tasks"]:
        if task["enabled"] and state.get("auto_reschedule") and not task["completed"] and not anchored:
            if now_minutes > cursor:
                cursor = now_minutes
            anchored = True
        start = cursor
        if task["enabled"]:
            cursor += task["duration"]
        rows.append({"task": task, "start": start, "end": cursor if task["enabled"] else start})
    return rows, cursor


# ---------------------------------------------------------------------------
# UI widgets
# ---------------------------------------------------------------------------

class TaskRow(BoxLayout):
    """One quest card. Built in Python (not pure .kv) because there's one
    of these per task and the count changes at runtime."""

    task_id = StringProperty("")
    name_text = StringProperty("")
    meta_text = StringProperty("")
    duration_text = StringProperty("")
    notes_text = StringProperty("")
    is_completed = BooleanProperty(False)
    is_timer_active = BooleanProperty(False)
    timer_text = StringProperty("")
    notes_visible = BooleanProperty(False)

    def __init__(self, app, task, start_min, end_min, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.task_id = task["id"]
        self.name_text = task["name"]
        self.duration_text = duration_label(task["duration"])
        self.is_completed = task["completed"]
        if task["completed"]:
            self.meta_text = "cleared"
        elif task["enabled"]:
            self.meta_text = f"{format_hhmm(start_min)} - {format_hhmm(end_min)}"
        else:
            self.meta_text = "skipped today"
        self.notes_text = task.get("notes", "")

    # -- callbacks wired up from statuswindow.kv --
    def on_check(self):
        self.app.toggle_task_complete(self.task_id)

    def on_minus(self):
        self.app.adjust_duration(self.task_id, -15)

    def on_plus(self):
        self.app.adjust_duration(self.task_id, 15)

    def on_toggle_enabled(self):
        self.app.toggle_task_enabled(self.task_id)

    def on_remove(self):
        self.app.remove_task(self.task_id)

    def on_notes_changed(self, text):
        self.app.set_task_notes(self.task_id, text)

    def on_start_timer(self):
        self.app.start_timer(self.task_id)

    def on_pause_resume(self):
        self.app.pause_or_resume_timer()

    def on_stop_timer(self):
        self.app.stop_timer()


class QuestPopup(Popup):
    """The 'Solo Leveling'-style quest-cleared / day-cleared flash."""
    title_text = StringProperty("")
    subtitle_text = StringProperty("")


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class StatusWindowApp(App):

    streak_text = StringProperty("STREAK x0")
    total_hours_text = StringProperty("0h")
    end_time_text = StringProperty("--")
    start_time_input = StringProperty("09:30")

    def build(self):
        self.title = "Status Window"
        self.data_path = os.path.join(self.user_data_dir, "schedule_data.json")
        self.state = load_state(self.data_path)
        self.state = apply_daily_rollover(self.state)
        self.save()

        self.root_widget = Builder.load_file("statuswindow.kv")
        self.start_time_input = self.state["start_time"]

        self.refresh_all()

        Clock.schedule_interval(self.tick_timer, 1)
        Clock.schedule_interval(lambda dt: self.refresh_all(), 60)
        return self.root_widget

    # -- persistence -----------------------------------------------------
    def save(self):
        save_state(self.data_path, self.state)

    # -- rendering ---------------------------------------------------------
    def refresh_all(self):
        rows, end_cursor = compute_schedule(self.state)
        task_list_widget = self.root_widget.ids.task_list
        task_list_widget.clear_widgets()

        total_min = 0
        completed_min = 0
        for row in rows:
            task = row["task"]
            if task["enabled"]:
                total_min += task["duration"]
                if task["completed"]:
                    completed_min += task["duration"]
            item = TaskRow(self, task, row["start"], row["end"])
            if self.state.get("active_timer") and self.state["active_timer"]["task_id"] == task["id"]:
                item.is_timer_active = True
                item.timer_text = self._format_remaining(task)
            task_list_widget.add_widget(item)

        self.total_hours_text = f"{round((total_min - completed_min) / 6) / 10}h left \u00b7 {round(total_min / 6) / 10}h"
        self.end_time_text = format_hhmm(end_cursor)
        self.streak_text = f"STREAK x{compute_streak(self.state)}"

        # progress bars: scheduled (blue) vs completed (purple), out of a 16h scale
        scale = 16 * 60
        self.root_widget.ids.bar_scheduled.value = min(100, total_min / scale * 100)
        self.root_widget.ids.bar_completed.value = min(100, completed_min / scale * 100)

        cleared_today = today_key() in self.state.get("completed_days", [])
        self.root_widget.ids.clear_day_btn.text = "\u2713 day cleared" if cleared_today else "\u2694 clear day"

        self.root_widget.ids.reschedule_btn.text = (
            "\u27f3 auto-reschedule: on" if self.state.get("auto_reschedule") else "\u27f3 reschedule from now"
        )

        self._refresh_queue()

    def _refresh_queue(self):
        queue_widget = self.root_widget.ids.queue_list
        queue_widget.clear_widgets()
        from kivy.uix.label import Label
        if not self.state.get("scheduled_next"):
            lbl = Label(text="nothing queued for tomorrow yet", color=COL_MUTED, size_hint_y=None, height=28)
            queue_widget.add_widget(lbl)

    # -- task mutation -------------------------------------------------------
    def _find_task(self, task_id):
        for t in self.state["tasks"]:
            if t["id"] == task_id:
                return t
        return None

    def toggle_task_complete(self, task_id):
        task = self._find_task(task_id)
        if not task:
            return
        was_completed = task["completed"]
        task["completed"] = not task["completed"]
        if task["completed"] and self.state.get("active_timer") and self.state["active_timer"]["task_id"] == task_id:
            self.state["active_timer"] = None
        self.save()
        self.refresh_all()
        if task["completed"] and not was_completed:
            self.show_quest_popup("QUEST CLEARED", task["name"])

    def toggle_task_enabled(self, task_id):
        task = self._find_task(task_id)
        if task:
            task["enabled"] = not task["enabled"]
            self.save()
            self.refresh_all()

    def adjust_duration(self, task_id, delta):
        task = self._find_task(task_id)
        if task:
            task["duration"] = max(15, task["duration"] + delta)
            self.save()
            self.refresh_all()

    def set_task_notes(self, task_id, text):
        task = self._find_task(task_id)
        if task:
            task["notes"] = text
            self.save()

    def remove_task(self, task_id):
        self.state["tasks"] = [t for t in self.state["tasks"] if t["id"] != task_id]
        self.save()
        self.refresh_all()

    def add_task(self):
        self.state["tasks"].append({
            "id": "custom-" + uuid.uuid4().hex[:8],
            "name": "New quest",
            "duration": 30,
            "enabled": True,
            "completed": False,
            "notes": "",
            "custom": True,
        })
        self.save()
        self.refresh_all()

    def add_queued_task(self):
        self.state.setdefault("scheduled_next", []).append({"name": "New quest", "duration": 30})
        self.save()
        self._refresh_queue()

    # -- start time ------------------------------------------------------
    def set_start_time(self, text):
        try:
            parse_hhmm(text)
        except (ValueError, IndexError):
            return  # ignore invalid input rather than crashing
        self.state["start_time"] = text
        self.save()
        self.refresh_all()

    # -- day clear / streak ------------------------------------------------
    def toggle_clear_day(self):
        key = today_key()
        days = self.state.get("completed_days", [])
        if key in days:
            self.state["completed_days"] = [d for d in days if d != key]
        else:
            self.state["completed_days"] = days + [key]
            self.show_quest_popup("DAILY QUEST COMPLETE", f"STREAK x{compute_streak(self.state)}")
        self.save()
        self.refresh_all()

    def toggle_reschedule(self):
        self.state["auto_reschedule"] = not self.state.get("auto_reschedule", False)
        self.save()
        self.refresh_all()

    # -- timer -------------------------------------------------------------
    def start_timer(self, task_id):
        self.state["active_timer"] = {
            "task_id": task_id,
            "started_at": datetime.now().isoformat(),
            "paused": False,
            "remaining_sec": None,
        }
        self.save()
        self.refresh_all()

    def pause_or_resume_timer(self):
        timer = self.state.get("active_timer")
        if not timer:
            return
        task = self._find_task(timer["task_id"])
        if not task:
            return
        if timer["paused"]:
            elapsed = task["duration"] * 60 - timer["remaining_sec"]
            timer["started_at"] = (datetime.now() - timedelta(seconds=elapsed)).isoformat()
            timer["paused"] = False
            timer["remaining_sec"] = None
        else:
            timer["remaining_sec"] = self._remaining_seconds(task, timer)
            timer["paused"] = True
        self.save()
        self.refresh_all()

    def stop_timer(self):
        self.state["active_timer"] = None
        self.save()
        self.refresh_all()

    def _remaining_seconds(self, task, timer):
        if timer["paused"]:
            return timer["remaining_sec"]
        started = datetime.fromisoformat(timer["started_at"])
        elapsed = (datetime.now() - started).total_seconds()
        return max(0, task["duration"] * 60 - elapsed)

    def _format_remaining(self, task):
        timer = self.state["active_timer"]
        remaining = self._remaining_seconds(task, timer)
        m, s = divmod(int(remaining), 60)
        return f"{m:02d}:{s:02d}"

    def tick_timer(self, dt):
        timer = self.state.get("active_timer")
        if not timer or timer["paused"]:
            return
        task = self._find_task(timer["task_id"])
        if not task:
            self.state["active_timer"] = None
            return
        remaining = self._remaining_seconds(task, timer)
        if remaining <= 0:
            self.state["active_timer"] = None
            if not task["completed"]:
                task["completed"] = True
                self.save()
                self.refresh_all()
                self.show_quest_popup("QUEST CLEARED", task["name"])
            return
        # cheap update: just find the live row widget and set its label,
        # rather than rebuilding the whole list every second
        for row in self.root_widget.ids.task_list.children:
            if isinstance(row, TaskRow) and row.task_id == timer["task_id"]:
                row.timer_text = f"{int(remaining) // 60:02d}:{int(remaining) % 60:02d}"
                break

    # -- notifications -------------------------------------------------------
    def show_quest_popup(self, title, subtitle):
        popup = QuestPopup(title_text=title, subtitle_text=subtitle)
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.8)


if __name__ == "__main__":
    StatusWindowApp().run()
