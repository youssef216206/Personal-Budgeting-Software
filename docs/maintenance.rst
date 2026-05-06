Maintenance notes
==================

Operational and housekeeping notes for people who ship or host **Personal Budgeting Software**
and regenerate its documentation.

.. contents::
   :local:
   :depth: 2

Documentation build
-------------------

Dependencies are listed in ``requirements-dev.txt`` (Sphinx and ``sphinx-rtd-theme``).

From the repository root::

   python -m pip install -r requirements-dev.txt
   python -m sphinx -b html docs docs/_build/html

(If ``sphinx-build`` is on your ``PATH``, you can use ``sphinx-build -b html docs docs/_build/html`` instead.)

Open ``docs/_build/html/index.html`` in a browser (or serve the folder with any static file
host).

**Tip:** After changing ``docs/conf.py``, extensions, or docstrings heavily, do a clean build::

   python -m sphinx -E -a -b html docs docs/_build/html

Content map
-----------

* **Guides** — ``user_guide.rst``, ``developer_guide.rst``, ``maintenance.rst`` (this file).
* **API** — ``docs/api/*.rst`` generated around autodoc; ``docs/api/modules.rst`` is the
  entry toctree.
* **Theme/UI** — ``docs/_static/custom.css``, ``html_theme_options`` in ``conf.py``.

When you add a new ``.rst`` file, link it from ``index.rst`` (or from another guide) so it
appears in navigation.

Application dependencies
------------------------

Production libraries live in ``requirements.txt``. Keep Django and security-related pins
reviewed on a schedule you define for your team.

Before a release, typical checks include::

   python manage.py check
   python manage.py test

Voice feature: support boundaries
---------------------------------

* **Client-side only** — recognition quality and availability depend on the user’s browser,
  OS microphone permissions, and network (some environments block cloud speech endpoints).
* **Secure context** — document that HTTP on LAN IPs is unsupported for mic access; prefer
  HTTPS or ``127.0.0.1`` for demos (see :doc:`user_guide`).
* **Privacy** — remind deployers that Web Speech in Chromium-based browsers may send audio to
  vendor speech services; an internal deployment should follow organisational policy.

Static assets
-------------

User-facing CSS/JS is under ``budgeting/static/budgeting/``. After edits, run or configure
``collectstatic`` for production per your Django deployment pattern so ``voice.js`` updates
are actually served.

Database and migrations
-----------------------

Follow Django’s normal migration workflow::

   python manage.py makemigrations
   python manage.py migrate

Never edit production data directly without backups.

Backups
-------

Back up the database and user-uploaded media (if any) according to your hosting provider.
The codebase alone does not restore user transactions.

Related docs
------------

* :doc:`user_guide`
* :doc:`developer_guide`
