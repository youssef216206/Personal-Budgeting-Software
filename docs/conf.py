# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "Personal_Budgeting_Software.settings",
)

import django  # noqa: E402

django.setup()

project = "Personal Budgeting Software"
copyright = "2026"
author = "Project team"
release = "1.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Document everyone meaningful; keep Django ORM noise out so docstrings stay visible.
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    # Only these underscore names ( Sphinx expects a comma-separated string here).
    "private-members": "_matching_budgets, _subscription_save_message",
    "show-inheritance": True,
    # Class description, then fields and methods in source order (easier to read).
    "member-order": "bysource",
}
# Merge class docstring with __init__ when present (clearer for forms/views).
autoclass_content = "both"


def _skip_django_model_noise(app, what, name, obj, skip, options):
    """Hide Django-generated members that usually have no project docstring."""
    if not name:
        return skip
    if what == "class":
        if name in (
            "DoesNotExist",
            "MultipleObjectsReturned",
            "NotUpdated",
            "_meta",
            "_base_manager",
            "_default_manager",
        ):
            return True
        if name.startswith("get_next_by_") or name.startswith("get_previous_by_"):
            return True
        # get_foo_display is auto for choices; keep if custom docstring—usually empty.
        if name.startswith("get_") and name.endswith("_display"):
            return True
    return skip


def setup(app):
    app.connect("autodoc-skip-member", _skip_django_model_noise)

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "titles_only": False,
    "includehidden": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", "https://docs.djangoproject.com/en/stable/_objects/"),
}
