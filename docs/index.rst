Personal Budgeting Software
============================

Django web application for personal budgeting: transactions, budgets, subscriptions, savings
goals, reports, and notifications—including optional **voice** entry on supported browsers.

Each **API module** page (for example ``budgeting.models`` or ``budgeting.views``) lists classes
and functions with descriptions taken from Python **docstrings**. The **module index**
(``py-modindex.html``) is link-only; use the pages under **API reference** for prose.

.. rst-class:: docs-guide-list-title

**Guides**

.. rst-class:: docs-guide-list

- **:doc:`User guide <user_guide>`** — Day-to-day use: transactions, voice phrases, mic
  troubleshooting, budgets and goals.
- **:doc:`Developer guide <developer_guide>`** — Project layout, ``voice.js`` pipeline,
  templates, and how to extend parsing safely.
- **:doc:`Maintenance <maintenance>`** — Building this documentation, static assets, releases,
  and voice support boundaries.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   user_guide
   developer_guide
   maintenance

.. toctree::
   :maxdepth: 2
   :caption: API reference

   api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
