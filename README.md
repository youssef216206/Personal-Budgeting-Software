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

**Course project — web application (Django)**

---

### 👥 Team


| Name                       | ID       |
| -------------------------- | -------- |
| Youssef Mostafa Ibrahim    | 20240716 |
| Sama Alaa Mohamed          | 20242169 |
| Alhussien Hazem Abouelfadl | 20240087 |
| Hana Ahmed Elsayed         | 20242386 |


---

## 🚀 What is this?

**MyBudget Desk** is a friendly **personal finance** web app: track **income** and **expenses**, set **budgets** with **alerts**, hit **savings goals**, and explore **reports** with charts — all tied to the course **Software Design Specification (SDS)** user stories.

---

## ✨ Features (high level)


| Area                | What you get                                                                                  |
| ------------------- | --------------------------------------------------------------------------------------------- |
| 🔐 **Auth**         | Sign up, log in, log out — email-based accounts                                               |
| 💸 **Transactions** | Add income or expenses; expenses can roll into matching budgets                               |
| 📊 **Budgets**      | Limits per category & date range, overlap checks, threshold & over-limit **notifications**    |
| 🎯 **Goals**        | Savings targets, contributions, progress — success alerts when you finish                     |
| 📈 **Reports**      | Date range, totals, insights, **pie** (by category) + **bar** (income vs expenses)            |
| 🔔 **Alerts**       | Notification center + badge; budget warnings on the dashboard                                 |
| 📖 **SDS helper**   | **“i”** button on each screen → quick **user story** context (US #1, #3, #4, #5, #6, #7, #10) |


---

## 🛠️ Tech stack

- **Python 3** + **Django**
- **SQLite** (default)
- **Chart.js** (reports)
- **HTML / CSS** (custom `master.css` — light, blue–purple theme)

---

## 📦 Run it locally

```bash
cd web-part
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install django
python manage.py migrate
python manage.py runserver
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

> 💡 First time? Create a superuser if you need the admin:  
> `python manage.py createsuperuser`

---

## 📁 Useful paths


| Path                                        | Why it matters                                           |
| ------------------------------------------- | -------------------------------------------------------- |
| `budgeting/`                                | Main app: `models.py`, `views.py`, `forms.py`, `urls.py` |
| `budgeting/templates/budgeting/`            | All pages + `master.html` layout                         |
| `budgeting/static/budgeting/css/master.css` | Global styles                                            |
| `Personal_Budgeting_Software/settings.py`   | Django settings                                          |


---

## 📄 SDS alignment

Implementation maps to the **Draft SDS** sequence diagrams and class/sequence usage table (e.g. **US #1** sign-up, **US #3** transactions, **US #4** budgets, **US #5** alerts, **US #6** goals, **US #7** reports, **US #10** dashboard). Use the in-app **ℹ️** panel on each page for a short reminder.

---

## 🙏 Acknowledgements

Built for **CS251** at **Cairo University, FCAI** — course materials and SDS template credits as in the official project brief.

---

**Made with ☕, 🧮, and a lot of `git commit`**

*MyBudget Desk · Personal Budgeting Software*