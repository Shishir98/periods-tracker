# luna — period tracker

A minimal, private period tracker built with Django.
All data stays on your machine (SQLite). No accounts, no cloud, no ads.

---

## setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Start the server
python manage.py runserver
```

Then open http://127.0.0.1:8000 in your browser.

---

## features

- **Dashboard** — cycle status orb, key stats, mini calendar, recent log
- **Log** — record period days, flow intensity, mood, symptoms, notes
- **Calendar** — click any day to add or edit an entry
- **History** — full log with cycle stats
- **Predictions** — next period estimate based on your average cycle length

## data

Uses SQLite by default (`db.sqlite3` in the project root).
To use PostgreSQL, update `DATABASES` in `period_tracker/settings.py`.

## structure

```
period_tracker/
├── manage.py
├── requirements.txt
├── period_tracker/       # Django project config
│   ├── settings.py
│   └── urls.py
└── tracker/              # Main app
    ├── models.py         # CycleEntry model
    ├── views.py          # dashboard, log_entry, history
    ├── forms.py          # CycleEntryForm
    ├── urls.py
    ├── migrations/
    ├── templates/tracker/
    │   ├── base.html
    │   ├── dashboard.html
    │   ├── log_entry.html
    │   └── history.html
    └── static/tracker/
        ├── css/style.css
        └── js/main.js
```
