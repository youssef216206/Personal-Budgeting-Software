Developer guide
===============

Overview for contributors: Django project layout, main apps, and the **browser voice**
pipeline (``voice.js`` + templates + forms).

.. contents::
   :local:
   :depth: 2

Stack and layout
----------------

* **Framework:** Django (see ``Personal_Budgeting_Software/settings.py``).
* **Primary app:** ``budgeting`` — models, views, forms, templates, static assets.
* **API documentation:** Sphinx autodoc from ``docs/api/`` (module docstrings are the source
  of truth for Python symbols).

Run the development server from the project root (with your virtualenv activated)::

   python manage.py runserver

Static assets for the budgeting UI live under ``budgeting/static/budgeting/`` (for example
``css/master.css``, ``js/voice.js``).

Voice: data flow
----------------

End-to-end path:

#. **Template** exposes element IDs and JSON the script expects.
#. **``voice.js``** (IIFE) parses the transcript, fills DOM fields, and optionally submits
   a form.
#. **``TransactionForm``** / **``transaction_form_voice_hidden``** validate the POST like any
   other transaction.

Dashboard (auto-submit)
~~~~~~~~~~~~~~~~~~~~~~~

``budgeting/templates/budgeting/dashboard.html``:

* **Button:** ``dash-voice-mic-btn``
* **Status:** ``dash-voice-status``
* **Categories JSON:** ``<script type="application/json" id="dash-voice-categories-data">``
* **Form:** ``dash-voice-form`` — POSTs to transaction create; hidden inputs rendered from
  ``voice_quick_form`` (all widgets are ``HiddenInput``).

The dashboard view (see ``budgeting.views``) passes ``voice_categories_json`` and
``voice_quick_form`` into the template context.

Transaction form (fill only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``budgeting/templates/budgeting/transaction_form.html``:

* **Button:** ``voice-mic-btn``
* **Status:** ``voice-mic-status``
* **JSON:** ``voice-categories-data``
* **``autoSubmit``** is ``false`` in ``voice.js`` for this attachment — user saves manually.

Hidden voice form helper
~~~~~~~~~~~~~~~~~~~~~~~~

``transaction_form_voice_hidden`` in ``budgeting/forms.py`` clones ``TransactionForm`` for
the given user and forces **every field** to ``HiddenInput``. That keeps a single validation
path: the same ``clean`` / ``save`` logic as the normal transaction UI.

JavaScript parsing rules
~~~~~~~~~~~~~~~~~~~~~~~~

Implementation: ``budgeting/static/budgeting/js/voice.js``.

* **Income** if the lowercase phrase matches ``received``, ``earned``, ``salary``, or
  ``income``.
* **Amount** — first plausible number (comma or dot as decimal).
* **Category** — substring match against user/system category **names**, then synonym tables
  (Food, Transport, Entertainment, Bills, Healthcare, Salary).
* **Date** — ``yesterday``, ``today``, ``last week`` adjust a base ``Date``; time is set to a
  noon placeholder for ``datetime-local``.

Before starting recognition, the script may call ``getUserMedia`` to trigger a clear
permission prompt, and it refuses to run on non–secure contexts (see ``isSecureContext``).

Extending behaviour
~~~~~~~~~~~~~~~~~~~

* Add synonyms in ``parseTranscript`` → ``synonyms`` array in ``voice.js``.
* Ensure new **form field names** stay aligned with ``fillTransactionForm`` selectors
  (``name="kind"``, ``amount``, ``category``, ``description``, ``occurred_at``).
* If you add a new voice entry point, call ``attachMic`` with a unique button/status/data id
  triple; reuse the same JSON shape as the dashboard.

Templates and context
---------------------

Views that render transaction or dashboard screens should continue to pass
``voice_categories_json`` when they include ``voice.js``, so the client-side category list
matches the server’s queryset (user + global categories).

Tests
-----

Add or extend tests in ``budgeting/tests`` for view/form behaviour. Voice itself is
**browser-only**; automated tests normally cover POST validation and redirects rather than
speech APIs.

Further reading
---------------

* :doc:`user_guide` — end-user phrasing and troubleshooting.
* :doc:`maintenance` — doc builds and release hygiene.
* :doc:`api/modules` — full Python API reference.
