# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'Pulse News Aggregator'
copyright = f'{datetime.now().year}, Pulse News'
author = 'Pulse News Team'
release = '1.0'

# -- General configuration ---------------------------------------------------

# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx itself (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The suffix(es) of source filenames.
source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'canonical_url': 'https://docs.pulsenews.app',
    'analytics_id': 'G-XXXXXXXXXX',  # Replace with actual Google Analytics ID if needed
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': 'edit',
    'style_nav_header_background': '#2980b9',
    # Tweak the logo and favicon
    'logo': 'https://pulsenews.app/favicon.ico',
    'favicon': 'https://pulsenews.app/favicon.ico',
    'navigation_depth': 4,
}

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents with `toctree` directives) are:
# html_sidebars = {
#     '**': [
#         'localtoc.html',
#         'relations.html',
#         'searchbox.html',
#         'donate.html',
#     ]
# }
html_sidebars = {
    '**': [
        'localtoc.html',
        'relations.html',
        'searchbox.html',
        'sourcelink.html',
    ]
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom CSS overrides
html_css_files = [
    'css/custom.css',
]

# Output file base name for HTML help builder.
htmlhelp_basename = 'PulseNewsAggregatorDoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
}

# Grouping the document tree into LaTeX files. List of tuples
# (startdocname, targetname, title, author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'PulseNewsAggregatorTex', 'Pulse News Aggregator Documentation',
     'Pulse News Team', 'manual'),
]

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': '__init__',
    'exclude-members': '_',
}

# Viewcode settings
viewcode_follow_links = True
viewcode_enable_epub = False

# Intersphinx mapping for cross-references to other projects
intersphinx_mapping = {
    'FastAPI': ('https://fastapi.tiangolo.com', None),
    'SQLModel': ('https://sqlmodel.tiangolo.com', None),
    'Next.js': ('https://nextjs.org/docs', None),
    'React': ('https://react.dev', None),
    'Tailwind CSS': ('https://tailwindcss.com', None),
    'Docker': ('https://docs.docker.com', None),
    'PostgreSQL': ('https://www.postgresql.org/docs/', None),
    'Alembic': ('https://alembic.sqlalchemy.org', None),
}

# -- Custom roles ---------------------------------------------------------

# Custom roles for defining links and formatting
rst_prolog = """
.. role:: ghissue(text, raw)
   :raw:`raw`
"""

def setup(app):
    """Override the name for a custom role.

    The role name is the role name that appears in the source.  The `raw` element
    is the processed text of the role argument.

    """