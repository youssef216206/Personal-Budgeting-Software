# Cairo University · Faculty of Computers & Artificial Intelligence

## CS251 — Introduction to Software Engineering

**Course:** CS251 (Winter 2026)

### Instructor

**Dr. Mohamed El-Ramly**

### Teaching Assistant

**TA Basma Moukhtar**

### Team members

| Student name | ID | Email |
| --- | --- | --- |
| Youssef Mostafa Ibrahim | 20240716 | [20240716@stud.fci-cu.edu.eg](mailto:20240716@stud.fci-cu.edu.eg) |
| Sama Alaa Mohamed | 20242169 | [20242169@stud.fci-cu.edu.eg](mailto:20242169@stud.fci-cu.edu.eg) |
| Alhussien Hazem Abouelfadl | 20240087 | [20240087@stud.fci-cu.edu.eg](mailto:20240087@stud.fci-cu.edu.eg) |
| Hana Ahmed Elsayed | 20242386 | [20242386@stud.fci-cu.edu.eg](mailto:20242386@stud.fci-cu.edu.eg) |

---

## Personal Budgeting Software — MyBudget Desk

**MyBudget Desk** is a **personal budgeting** web application built with **Django**. Signed-in users manage their own finances in the browser: transactions, budgets, savings goals, subscriptions, reports, and a dashboard with charts and summaries. Staff can use Django’s built-in **admin** site after creating a superuser.

---

### Contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Run locally](#run-locally)
- [Repository layout](#repository-layout)
- [Main routes](#main-routes-url-names)
- [Documentation (Sphinx)](#optional-api-documentation-sphinx)
- [Testing](#testing)
- [Git notes](#git-notes)

---

## Features

| Area | What you can do |
| --- | --- |
| **Account** | Sign up, log in, log out |
| **Transactions** | Add, edit, and delete **income** and **expenses**, with categories and filters |
| **Budgets** | Set limits and periods; get **notifications** when spending nears or exceeds thresholds |
| **Goals** | Create **savings goals**, add contributions, track progress |
| **Subscriptions** | Manage recurring charges; middleware can record due amounts as expenses |
| **Reports** | Pick a date range, see totals, category breakdowns, charts, and short insights |
| **Dashboard** | KPI overview, voice shortcut to add transactions, Chart.js spending charts, budgets, goals, recent activity |
| **Voice input** | Optional voice capture (Web Speech API) where enabled on forms |

---

## Tech stack

- **Python 3** (compatible with **Django 6.x** — see `requirements.txt`)
- **Django** 6.x (`Django>=6.0,<7.0`)
- **SQLite** — default in `settings.py`; database files are **not** committed (see `.gitignore`)
- **Chart.js** — charts on the dashboard and reports
- **HTML / CSS** — `budgeting/static/budgeting/css/master.css`
- **JavaScript** — charts, helpers, `budgeting/static/budgeting/js/voice.js` where used

---

## Prerequisites

- **Python 3.10+** recommended ([Django 6 Python support](https://docs.djangoproject.com/en/stable/faq/install/#what-python-version-can-i-use-with-django))
- **pip**
- A terminal and a web browser

---

## Run locally

From the **`Personal-Budgeting-Software`** directory (where `manage.py` lives):

**Windows (PowerShell / CMD):**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open **http://127.0.0.1:8000/**.

Create a staff user for **http://127.0.0.1:8000/admin/**:

```bash
python manage.py createsuperuser
```

**After pulling updates:** run `python manage.py migrate` again if you see database errors. **Static assets:** with `DEBUG=True` (default here), Django serves static files for local development.

---

## Repository layout

| Path | Purpose |
| --- | --- |
| `budgeting/` | App: `models.py`, `views.py`, `forms.py`, `urls.py`, middleware |
| `budgeting/templates/budgeting/` | HTML templates |
| `budgeting/static/budgeting/` | CSS and JavaScript |
| `Personal_Budgeting_Software/` | Project settings and root URLconf |
| `docs/` | Sphinx documentation sources |
| `manage.py` | Django entrypoint |

---

## Main routes (URL names)

These are the `name=` values from `budgeting/urls.py` (for `{% url '...' %}` or `reverse()`):

| URL name | Path (typical) |
| --- | --- |
| `dashboard` | `/` |
| `signup` | `/signup/` |
| `login` | `/login/` |
| `logout` | `/logout/` |
| `transaction_list` | `/transactions/` |
| `transaction_add` | `/transactions/add/` |
| `transaction_edit` | `/transactions/<id>/edit/` |
| `transaction_delete` | `/transactions/<id>/delete/` |
| `category_list` | `/categories/` |
| `subscription_list` | `/subscriptions/` |
| `subscription_add` | `/subscriptions/add/` |
| `subscription_edit` | `/subscriptions/<id>/edit/` |
| `subscription_delete` | `/subscriptions/<id>/delete/` |
| `subscription_toggle` | `/subscriptions/<id>/toggle/` |
| `budget_list` | `/budgets/` |
| `budget_create` | `/budgets/add/` |
| `budget_edit` | `/budgets/<id>/edit/` |
| `goals_list` | `/goals/` |
| `goal_create` | `/goals/add/` |
| `goal_contribute` | `/goals/<id>/contribute/` |
| `reports` | `/reports/` |
| `notifications` | `/notifications/` |

---

## Optional API documentation (Sphinx)

```bash
pip install -r requirements-dev.txt
sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser.

---

```bash
python manage.py test
```

---

## Git notes

Example first push from the project root:

```bash
git status
git add README.md requirements.txt .gitignore
git add Personal_Budgeting_Software budgeting manage.py
git commit -m "Initial commit: MyBudget Desk Django app"

git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

Do **not** commit secrets, `.env`, or `*.sqlite3`. Treat `SECRET_KEY` in `settings.py` as **development-only** for real deployments.

---

## Acknowledgements

Course materials and SDS template: **CS251**, Cairo University, **FCAI**. Template lineage credited in the course PDF: Mostafa Saad, Mohammad El-Ramly.

---

**MyBudget Desk** · Personal Budgeting Software · CS251 course project
