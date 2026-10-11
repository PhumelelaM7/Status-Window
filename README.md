# Status Window

A gamified daily quest and schedule app built with **Django**. You reflect first, commit to your day, work through quests on a computed timeline, and track progress toward longer-term goals, all inside a dark "System Window" interface.

> **Status:** active development on the `django-rewrite` branch. The long-term aim is a polished multi-user product for the web, and eventually Android and iOS.

---

## Philosophy

Status Window is built on ideas from Miyamoto Musashi's *Book of Five Rings* and the *Dokkodo*. They sit underneath the app as design principles, not as theming. The interface stays modern and does not lecture.

| Ring | Idea | How it shows up in the app | Status |
|------|------|----------------------------|--------|
| **Earth** | See reality without excuses | Goals require a *why it matters* and a *success definition*. Quests are split into Essential / Flexible / Optional. | Built (category grouping awaiting full test) |
| **Water** | Adapt without abandoning direction | Per-quest reschedule with a pinned time, plus a live overdue prompt instead of silent failure. | Built |
| **Fire** | Function when pressure becomes real | Goal deadline countdown, and a distraction-free **focus mode** with a pausable timer. | Built |
| **Wind** | Study other paths | Review and experiment view to compare scheduling approaches week over week. | Planned |
| **Void** | Act without unnecessary thought | A minimal "one thing right now" mode where scaffolding fades as habits form. | Planned |

Design guardrails: a streak is a measurement, not the objective. A missed quest means "adjust the plan," not "you failed." Completing a goal starts a maintenance phase (periodic reflection check-ins), not an ending.

---

## Features

### Daily schedule
- **Reflect, then commit.** Before pressing **Start My Day**, only the day notes (a diary) and a way to schedule future quests are available. Pressing it records the real start time and unlocks the day.
- **Computed timeline.** Quest start and end times are calculated from the day's start time plus each quest's duration, in order. Disabled quests are skipped.
- **Pinned times.** Rescheduling a quest to a specific time pins it there (`anchor_time`), and later quests cascade from it.
- **Essential / Flexible / Optional** sections, each with its own mini-timeline.
- Per-quest controls: mark complete, reorder (up/down), enable/disable, reschedule (date and time), notes, and **Focus**.
- **Progress bar** of completed versus scheduled minutes.
- **Streak** of consecutive cleared days. **Clear Day** only works when every enabled quest is complete.
- **Date navigation** to any past or future day.
- **Day notes** (diary) for every date.

### Failed quests and live overdue detection
- A small script checks every 60 seconds. When an incomplete quest's end time passes, a themed modal offers **Reschedule** or **Mark Failed**.
- Failed quests stay visible but greyed out, with no complete or reschedule actions, and are excluded from progress.

### Focus mode (Fire)
- A standalone full-screen page showing only the current objective and a countdown.
- Pause and resume. When time runs out, choose **+10 minutes** or **Mark Complete**.

### Goals
- Short-term and long-term goals with *why it matters*, *success definition*, and an optional **end date**.
- **Fire-ring countdown** (days remaining, deadline today, or days overdue).
- Goal detail page lists linked quests, with an **Unlink** button (the quest stays on its day).
- **Mark Goal Complete** (also sets the goal inactive).
- Quests work on their own *or* as steps toward a goal. The link is optional.

### Accounts and multi-user
- Sign up, log in, log out (Django auth).
- A `Profile` per user (display name and points) is created automatically by a signal.
- Every `Goal`, `Quest`, and `DaySchedule` belongs to a user. All views are login-protected and filtered by `request.user`, so accounts never see each other's data. Isolation was tested with two accounts.

---

## Tech stack

- **Python 3.12**, **Django 6.1**
- **MariaDB 12.3** via the `mysqlclient` connector
- Server-rendered Django templates, plain CSS, and a little vanilla JavaScript (overdue watcher, focus timer)
- Fonts: Orbitron and Rajdhani (Google Fonts)

---

## Project structure

```
status-window-python/
├── manage.py
├── config/                  # Django project settings and root URLs
├── accounts/                # Profile model, signup, backfill command
│   └── management/commands/backfill_profiles.py
├── goals/                   # Goal model, views, deadline countdown logic
│   └── deadlines.py         # compute_countdown()
├── quests/                  # Quest + DaySchedule models, schedule views
│   ├── scheduling.py        # compute_schedule / compute_streak / compute_progress
│   └── templates/quests/    # today.html, _quest_row.html, focus.html, ...
├── templates/               # base.html, registration/login.html
├── static/
│   ├── css/style.css        # main System Window theme
│   ├── css/focus.css        # focus-mode page only
│   └── js/                  # quest-watcher.js, focus.js
├── main.py, statuswindow.kv # legacy Kivy version (kept on master; can be removed here)
└── README.md
```

Business logic that does not need Django lives in plain functions (`scheduling.py`, `deadlines.py`) so it stays easy to read and test.

---

## Data model

| Model | Key fields |
|-------|-----------|
| `Goal` | `user`, `title`, `why_it_matters`, `success_definition`, `term` (short/long), `end_date`, `is_active`, `is_completed` |
| `Quest` | `user`, `title`, `goal` (optional), `category`, `scheduled_date`, `order`, `duration_minutes`, `start_time`, `anchor_time`, `is_enabled`, `is_completed`, `completed_at`, `is_failed`, `notes` |
| `DaySchedule` | `user`, `date` (unique per user), `start_time`, `day_started`, `is_cleared`, `notes` |
| `Profile` | `user` (one-to-one), `display_name`, `points` |

---

## Getting started (Windows / PowerShell)

### 1. Clone and create a virtual environment
```powershell
git clone https://github.com/PhumelelaM7/Status-Window.git
cd Status-Window
git checkout django-rewrite
python -m venv venv
venv\Scripts\activate
```
> The project folder is nested: the folder containing `manage.py` is the one that holds `venv`. If `venv\Scripts\activate` says the module can't be loaded, you are one folder too high.

### 2. Install dependencies
```powershell
pip install django mysqlclient
```

### 3. Set up MariaDB
Install MariaDB, then in the MariaDB prompt:
```sql
CREATE DATABASE status_window CHARACTER SET utf8mb4;
CREATE USER 'status_window_user'@'localhost' IDENTIFIED BY 'your-own-password';
GRANT ALL PRIVILEGES ON status_window.* TO 'status_window_user'@'localhost';
FLUSH PRIVILEGES;
```
Then put the same values in the `DATABASES` section of `config/settings.py` (`NAME`, `USER`, `PASSWORD`, host `localhost`, port `3306`, `charset: utf8mb4`).

### 4. Migrate, create an admin, run
```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py backfill_profiles    # only needed for users created before the Profile signal
python manage.py runserver
```
Open `http://127.0.0.1:8000/`. Sign up at `/accounts/signup/` or log in at `/accounts/login/`. The admin is at `/admin/`.

---

## Main URLs

| Path | Purpose |
|------|---------|
| `/` and `/<year>/<month>/<day>/` | Daily schedule |
| `/add/` | Add a quest |
| `/start-my-day/`, `/clear-day/` | Commit to the day, clear the day |
| `/quest/<id>/focus/` | Focus mode |
| `/quest/<id>/reschedule/` | Reschedule date and time |
| `/goals/`, `/goals/add/`, `/goals/<id>/` | Goal list, create, detail |
| `/accounts/login/`, `/accounts/signup/` | Authentication |

Quest actions (complete, move, enable, notes, mark failed, unlink) are POST-only endpoints under `/quest/<id>/...`.

---

## Development conventions

- Python follows **PEP 8**, with **docstrings** on every function and class and `#` comments explaining the *why*.
- HTML templates use `<!-- -->` comments to mark sections.
- State-changing views accept **POST only** and redirect afterward (post/redirect/get).
- Every query touching user data filters by `request.user`.
- Work happens one feature at a time, with a git commit per working milestone.

---

## Roadmap

**Next up**
- Verify the Essential / Flexible / Optional grouped view end to end, then commit.
- User profile page: quests completed, goals completed, highest streak, display name, points.
- Goals depth: parity with quests (progress from linked quests, notes, add-quest-from-goal).
- Auto-complete linked quests when a goal is completed (scope to be decided).
- Completed goals in their own list section, and a "Skill" designation for completed goals.

**Philosophy features**
- Wind: review and experiment view (compare scheduling methods week over week).
- Void: minimal mode.
- Goal maintenance mode (periodic reflection check-ins after completion).
- Goal to "Path" redesign (onboarding, committed daily practice, consistency percentage).
- Dokkodo reflection layer (non-punitive prompts, "moved this 4 times" nudges).
- Optional "Daily Duel" (one most-important task per day) and a nightly review.

**Polish and product**
- Visual pass to match the original design (Day/Week/Month tabs, in-page alerts, `.ics` export, queued-for-tomorrow panel).
- Tests for the scheduling and countdown logic.
- Packaging for the App Store and Google Play.

---

## Known issues and technical debt

- **Secrets in settings.** The database password is hardcoded in `config/settings.py`. Move it to environment variables or a git-ignored `.env` before sharing the repo.
- **`requirements.txt` is stale.** It only lists Django's early dependencies and is saved as UTF-16 (PowerShell's `>` redirect does that). Regenerate it in UTF-8 with `pip freeze | Out-File -Encoding utf8 requirements.txt`.
- **Project lives inside OneDrive.** Syncing can delay or lock file writes during development. Moving the project to a plain local folder (for example `C:\Dev\`) is recommended. It is already backed up via git.
- **Legacy files.** `main.py`, `statuswindow.kv`, and `db.sqlite3` are leftovers from the earlier Kivy/SQLite versions and can be deleted from this branch.
- **Unused view.** `set_start_time` and its URL remain from an earlier design. The Start My Day flow replaced the preset-time buttons.

---

## History

1. Web artifact (HTML/JS) schedule tool
2. "System Window" reskin, PWA, and a Capacitor iOS wrapper
3. Kivy (Python) rewrite
4. **Django rewrite** (current): accounts, goals, quests, MariaDB, focus mode, categories
