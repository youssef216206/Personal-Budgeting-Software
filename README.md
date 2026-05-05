# 🎓 Cairo University

## Faculty of Computers & Artificial Intelligence

### CS251 · Introduction to Software Engineering

---

### 📚 Instructor

**Dr. Mohamed El-Ramly**

### ✨ Teaching Assistant

**TA Basma Moukhtar**

---

# 💰 MyBudget Desk

### *Personal Budgeting Software*

*Course project — web application (Django), aligned with the Software Design Specification (SDS).*

---

## 🚀 What is this?

**MyBudget Desk** is a personal finance web app for each signed-in user: track **income** and **expenses**, set **budgets** with **notifications**, hit **savings goals**, manage **subscriptions** (recurring charges processed on requests), and explore **reports** plus a rich **dashboard** (KPIs, health score, insights, heatmap, Chart.js charts).

---

## ✨ Features

| Area | What you get |
| --- | --- |
| 🔐 **Auth** | Sign up (email as username), login, logout |
| 📊 **Dashboard** | Month KPIs (balance, income, expenses), **speak-to-add** (Web Speech API), financial **health** score, **insights**, **heatmap**, category **donut** (with “Other categories” when there are many slices), daily **line chart**, budgets, goals, alerts |
| 💸 **Transactions** | List with filters; add / edit / delete; budgets update from expenses; **voice fill** on the form |
| 📁 **Categories** | Defaults + your own categories |
| 💰 **Budgets** | Limits, date ranges, spent totals, overlap checks, threshold & over-limit alerts |
| 🎯 **Goals** | Savings targets, contributions, progress |
| 🔁 **Subscriptions** | Recurring charges; middleware can record due amounts as expenses |
| 📈 **Reports** | Date range, totals, insights, Chart.js pie + bar |
| 🔔 **Notifications** | In-app alerts and unread awareness |
| 📖 **SDS helper** | **ℹ️** on screens — SDS / user-story context (**US #1**, **#3**–**#7**, **#10**, etc.) |

---

## 🛠️ Tech stack

- **Python 3** + **Django 6.x** (see `requirements.txt`)
- **SQLite** (`db.sqlite3` — local only, **ignored** by git)
- **Chart.js**
- **HTML / CSS** (`budgeting/static/budgeting/css/master.css`)
- **JS** (`voice.js`, chart scripts)

---

## 📦 Run it locally

From the **`Personal-Budgeting-Software`** folder:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open **http://127.0.0.1:8000/**.

> 💡 Need the admin site? **`python manage.py createsuperuser`** then **http://127.0.0.1:8000/admin/**

---

## 📁 Useful paths

| Path | Why it matters |
| --- | --- |
| `budgeting/` | `models.py`, `views.py`, `forms.py`, `urls.py`, middleware, health, insights |
| `budgeting/templates/budgeting/` | Pages + layouts |
| `budgeting/static/budgeting/` | CSS, JS |
| `Personal_Budgeting_Software/` | Django settings & root URLs |

---

## 🔗 Main URL names

| Name | Typical path |
| --- | --- |
| `dashboard` | `/` |
| `signup`, `login`, `logout` | `/signup/`, `/login/`, `/logout/` |
| `transaction_*` | `/transactions/` … |
| `category_list` | `/categories/` |
| `subscription_*` | `/subscriptions/` … |
| `budget_*` | `/budgets/` … |
| `goal_*`, `goals_list` | `/goals/` … |
| `reports` | `/reports/` |
| `notifications` | `/notifications/` |

---

## 📄 SDS alignment

Maps to the **Draft SDS** (sequence diagrams / user stories): **US #1** sign-up, **US #3** transactions, **US #4** budgets, **US #5** alerts, **US #6** goals, **US #7** reports, **US #10** dashboard — use each page’s info panel for detail.

---

## 🌐 Git: commit README and push to GitHub

Run from your **repo root** (folder with `.git` / `manage.py`). Swap `YOUR_USER` / `YOUR_REPO` / branch (`main` or `master`).

```bash
git status
git add README.md requirements.txt .gitignore
git add Personal_Budgeting_Software budgeting manage.py
git status
git commit -m "Docs: refresh README with full feature list and setup; add requirements.txt"

git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
```

If `origin` exists already: `git remote -v`

```bash
git push -u origin main
```

- Do **not** commit `.env`, `db.sqlite3`, or secrets (`SECRET_KEY` in `settings.py` is dev-only).

---

## 🙏 Acknowledgements

Built for **CS251** at **Cairo University, FCAI** — course materials and SDS as in the official brief.

---

**Made with ☕, 🧮, and plenty of commits**

*MyBudget Desk · Personal Budgeting Software*
