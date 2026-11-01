# track — notes for agents and other newcomers

Automatic time tracker for X11 desktops. A background server samples the
active window once per second and stores one JSON file per day; a PyQt5 UI
shows today's timeline and lets you edit category rules and a daily note.
Nothing leaves the machine.

## Layout

```
track/cli.py            console script `track` (the only entry point)
track/core/             Qt-free: data model, sampling, persistence
  common.py             Category, AppInfo, Minute, rule matching, time helpers,
                        log file naming, shared argparse options
  active_applications.py  ActiveApplications: one day of {minute -> Minute}
  time_tracker.py       TimeTracker: sampling loop body, JSON persistence,
                        the lock that guards the model (see Threads)
  desktop_usage_info/   active window + idle time; backend_name() picks one
                        from the environment, TRACK_BACKEND=x11|gnome|windows
                        overrides
    backend_x11/        xprop subprocess + psutil, libXss via ctypes
    backend_gnome/      GNOME Shell on Wayland: `gdbus` calls to Mutter's idle
                        monitor and to the Window Calls Extended extension
    backend_windows/    unmaintained, win32gui is not a declared dependency
  util.py               logging setup, log(), catch()
track/server/           TrackServer: zmq REP loop + sampler thread
track/track-server      script stub the UI spawns when no server answers
track/ui/               PyQt5 client; mainwindow.ui is a Qt Designer file
                        with custom widgets QSpoiler and EvaluationWidget
test/                   pytest; markers `unit` and `system` (see Checks)
dev/                    private git submodule with generic check scripts
```

`track.core` must stay importable without PyQt5 — the server runs headless.

## Processes and protocol

- Server: `track serve`. Binds `tcp://127.0.0.1:<port>` (default 3456), no
  authentication. Samples every second on a daemon thread, autosaves every
  120 s and on shutdown (SIGINT/SIGTERM or the `quit` command).
- UI: `track` or `track ui`. zmq REQ client; if the server does not answer
  it starts `track/track-server` itself and retries once.
- CLI: `track list`, `track show track-YYYYMMDD.json`, `track server CMD`.
- Request: `{"cmd": <name>, "data": {...}}`. Reply: `{"data": {...}}`,
  `{"type": "ok"}` or `{"type": "error", "what": "...",
  ["error_type": "request_malformed"]}`.
- Commands: `version`, `apps`, `current`, `rules`, `set_rules {rules}`,
  `note`, `set_note {note}`, `clip_from {index}`, `clip_to {index}`,
  `save`, `quit`. Dispatch table: `TrackServer.handle_request`.

## Data

All files live in `--data-dir` (default `~/.track`):

- `track-YYYYMMDD.json`: `{"tracker_data": {"apps": [[title, category,
  seconds, cmdline], ...], "minutes": {"<minute of day>": [[app_index,
  seconds], ...]}}, "daily_note": str}`. `ActiveApplications.__data__()` /
  `from_dict()` are the two sides of it.
- `category_rules.json`: `[[regex, category], ...]`, matched case-insensitively
  against the window title, first hit wins.
- A file that fails to parse is moved to `*.corrupt` instead of being
  overwritten.
- Categories are plain ints: 0 idle, 1 unassigned, 2 work, 3 private, 4 break
  (`common.Category`). Rules loaded from JSON carry ints, not enum members.

## Threads

`TimeTracker.update()` runs on the sampler thread, the request handlers on the
main thread. Every mutation or serialization of the application store goes
through `TimeTracker._lock`; the server calls `applications_data()`,
`clip_from()`, `clip_to()`, `set_rules()`, `persist()` — never the model
directly. Keep it that way.

## Run and check

```
uv sync                       # creates .venv (Python >= 3.12)
uv run track                  # UI + server
uv run pytest -m unit         # no display needed
uv run pytest -m system       # needs X11 (xprop, a focused window); the
                              # server/timegraph tests also pass with
                              # QT_QPA_PLATFORM=offscreen
uv run ruff check             # select = ALL, ~500 findings left
uv run mypy track             # strict, ~450 findings left
uv run pre-commit run --all-files
```

Pre-commit hooks are installed and `fail_fast`; until the ruff/mypy backlog
is cleared, commits need `--no-verify`. The lint backlog is deliberate
technical debt, not something to "fix" en passant in an unrelated change.

## Conventions

- Lint/type config lives in `pyproject.toml`. Line length 100.
- Qt virtual methods and signals are camelCase because the API says so;
  everything else is snake_case.
- Logging via `log()` from `track.core.util`; no `print()` in library code.
- Version: `track.core.version_info`, keep in sync with `pyproject.toml`.
  The UI compares it with the server's and only warns on mismatch.

## Known gaps

- Wayland works only with GNOME Shell and only with the
  `window-calls-extended@hseliger.eu` extension enabled; there is no portable
  "focused window" API. Other compositors fall back to the x11 backend, which
  sees nothing but XWayland clients.
- `backend_windows` is untested for years.
- `track.wpr` is a Wing IDE project file pointing at a removed script.
- `dev/` is a private submodule; `dev/check-shellscripts` is referenced by
  pre-commit.
