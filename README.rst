=========
sphinx-js
=========

Why
===

For documentation, everything is horrible except Sphinx. JS is also horrible, but there's no point making it more horrible by leaving it undocumented or, almost worse, condemning new users to reverse-engineering how to use your lib from an alphabetical list of routine names, a la JSDoc.

How
===

Install JSDoc using npm. Add ``sphinx_js`` to your Sphinx ``extensions`` in conf.py. Document your JS code using JSDoc formatting. Then call our special directive in your Sphinx docs::

    .. js-autofunction:: someFunction

Tests
=====

Run `python setup.py test`.
