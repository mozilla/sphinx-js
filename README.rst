=========
sphinx-js
=========

Why
===

When you write a JavaScript library, how do you explain it to people? If it's a small project in a domain your users are familiar with, JSDoc's hierarchal list of routines might suffice. But what about for larger projects? How can you intersperse prose with your API docs without having to copy and paste things?

sphinx-js lets you use the industry-leading Sphinx documentation tool with JS projects. It provides a handful of directives, patterned after the Python-centric autodoc ones, for pulling JSDoc-formatted function and class documentation into reStructuredText pages. And, because you can keep using JSDoc in your code, you remain compatible with the rest of your JS tooling, like Google's Closure Compiler.

How
===

1. Install JSDoc using npm.
2. Install Sphinx. (TODO: Make this more explicit for non-Python people.)
3. Add ``sphinx_js`` to your Sphinx ``extensions`` in conf.py.
4. Document your JS code using JSDoc formatting.
5. Then call our special directive in your Sphinx docs::

    .. js-autofunction:: someFunction

Tests
=====

Run ``python setup.py test``.
