# Status Window — Python (Kivy) version

A pure-Python rewrite of the quest-log app using
[Kivy](https://kivy.org/) — a real cross-platform app framework
(desktop, Android, iOS) that's just Python underneath.

## Important — please read before relying on this

I wrote and syntax-checked this code, but **I could not actually run
it** in the environment I built it in (no internet access there to
install Kivy, and no display to test the UI). The Python is valid and
the logic mirrors the JavaScript version closely, but there's a real
chance of small runtime issues in the `.kv` layout file the first time
you run it — mismatched widget IDs, a binding typo, that sort of
thing. Treat this as a strong first draft to run and debug on your
machine, not a guaranteed-working drop-in. If you hit an error, paste
me the traceback and I'll fix it — that's normal for a first run of
UI code like this.

## Two files that matter

- **`main.py`** — all the actual logic: task data, the timer, streaks,
  daily rollover, saving/loading. This is the file you'd read and
  edit to change how the app *behaves*.
- **`statuswindow.kv`** — describes what's on screen and how it's
  styled (colors, layout, spacing). Kivy's `.kv` format is
  declarative — closer to a structured config file than "real" code —
  but it does use Python expressions inline (e.g. `app.streak_text`),
  so it's not entirely code-free.

## Running it on your computer (Mac, Windows, or Linux — no Mac needed for this part)

```
pip install -r requirements.txt
python main.py
```

A window should open with the quest log. Your data saves to a JSON
file automatically (see "Where your data lives" below) — close and
reopen the app and it'll still be there.

## Where your data lives

`main.py` saves everything to a single JSON file in Kivy's standard
per-app data folder — you can open `schedule_data.json` in a text
editor any time to see exactly what's stored, since it's plain,
readable JSON (not a database).

## Getting this onto your iPhone

This is the same situation as before, just with a different toolchain:

- Kivy has an iOS path called **kivy-ios** (and the `buildozer` tool
  for Android). Like Capacitor, **it still requires a Mac with
  Xcode** — there's no way around that; Apple only allows iOS builds
  from macOS.
- Kivy's iOS pipeline is honestly less mature and more fiddly to set
  up than Capacitor's — expect more troubleshooting if you go this
  route. I'd recommend getting the app running well on your desktop
  first, then tackling kivy-ios as a separate step once the Python
  logic is solid — happy to walk through that when you're ready.

## What's different from the JavaScript/web version

To keep this a manageable first version, I left a few things out
rather than guess at Python equivalents you didn't ask for:

- **Week/month calendar views** — not included yet.
- **Calendar (.ics) export** — not included yet.
- **In-page "starts in 10 minutes" alerts** — not included yet (the
  on-screen quest-cleared popup and the countdown timer are both in).

Everything else — the task list, per-task timer with pause/resume,
notes, streaks, day-clear, daily reset/rollover, reschedule-from-now,
and the "queue something for tomorrow" board — is implemented. Let me
know if you want any of the left-out pieces added back in Python.
