User guide
==========

This guide is for people using **MyBudget Desk** in the browser: recording money in and out,
staying inside budgets, and using optional **voice** shortcuts.

.. contents::
   :local:
   :depth: 2

Getting started
---------------

After you sign in, the **Dashboard** shows your balance, income and expenses for the current
month, budgets, goals, and recent activity. Use **Add transaction** (or the links in empty
states) whenever you need a full form with every field visible.

Transactions
------------

* **Expenses** reduce your balance and can be tied to a **category** so budgets update.
* **Income** increases your balance; say or type phrases that include words like *salary*,
  *received*, or *income* so the app treats the line as income.
* Always check the **amount**, **date**, and **category** before saving—especially after voice
  input, which is a helper, not a replacement for your review.

Speak to add (voice)
--------------------

Voice uses your browser’s **Web Speech API** (dictation). It works best in **Google Chrome**
or **Microsoft Edge** on a desktop or laptop.

Where it appears
~~~~~~~~~~~~~~~~

* **Dashboard** — **Speak transaction** fills a hidden form and **submits** when the phrase
  is complete enough (amount + category for expenses; income only needs amount and income
  wording).
* **Add / edit transaction** — **Talk to fill form** only fills visible fields; you press
  **Save** yourself.

What to say
~~~~~~~~~~~

Use clear numbers and plain words. **Expenses** need an amount and a **category** that matches
one of yours (the parser also maps common synonyms to categories where configured). **Income**
needs an amount and wording that signals income (for example *received*, *salary*, *pay*).

You can add optional **timing** such as *yesterday*, *today*, or *last week* so the saved date
matches what you mean (approximate for *last week*).

Your **category names** are matched when you say them; synonym lists in the app map everyday
words to those categories when helpful.

Microphone and “not allowed” errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Browsers only allow the microphone on a **secure** page. That usually means:

* **HTTPS**, or
* **http://127.0.0.1:**\ port (or ``localhost``) for local development.

Plain **http://** on a **LAN IP** (for example ``192.168.x.x``) often blocks the mic. If you
see a **not-allowed** or permission error:

#. Click the **lock** or **tune** icon in the address bar → **Site settings** → set
   **Microphone** to **Allow**, then reload.
#. On **Windows**: **Settings → Privacy & security → Microphone** — allow your browser.
#. Open the app at **http://127.0.0.1:PORT** (replace PORT with your server port) or deploy
   behind **HTTPS**.

If recognition starts but nothing is saved, the status line explains what was missing (for
example category name on an expense).

Budgets and alerts
------------------

When you log an **expense** in a **category** that has an active **budget**, the spent total
updates. If you configure **alert** thresholds, you may see notifications when you approach
or exceed a limit.

Savings goals and reports
-------------------------

**Goals** track targets over time; **reports** help you see patterns. Exact layouts may vary
by release—use the on-screen labels and the **developer** docs if you need field-level
details.

Where to go next
----------------

* :doc:`developer_guide` — how the voice feature is wired in code.
* :doc:`maintenance` — for admins: docs build, deployment notes.
