=========
sphinx-js
=========

Why
===

When you write a JavaScript library, how do you explain it to people? If it's a small project in a domain your users are familiar with, JSDoc's hierarchal list of routines might suffice. But what about for larger projects? How can you intersperse prose with your API docs without having to copy and paste things?

sphinx-js lets you use the industry-leading Sphinx documentation tool with JS projects. It provides a handful of directives, patterned after the Python-centric autodoc ones, for pulling JSDoc-formatted function and class documentation into reStructuredText pages. And, because you can keep using JSDoc in your code, you remain compatible with the rest of your JS tooling, like Google's Closure Compiler.

Setup
=====

1. Install JSDoc using npm.
2. Install Sphinx. (TODO: Make this more explicit for non-Python people.)
3. Make a documentation folder in your project using ``sphinx-quickstart``.
4. Add ``sphinx_js`` to ``extensions`` in the generated Sphinx conf.py.

Use
===

Document your JS code using standard JSDoc formatting::

.. code-block:: js

   /**
    * Return the ratio of the inline text length of the links in an element to
    * the inline text length of the entire element.
    * @param {node} A node of some kind
    */
   function linkDensity(node) {
       const length = node.flavors.get('paragraphish').inlineLength;
       const lengthWithoutLinks = inlineTextLength(node.element,
                                                   element => element.tagName !== 'A');
       return (length - lengthWithoutLinks) / length;
   }

Our directives work much like Sphinx's standard `autodoc
<http://www.sphinx-doc.org/en/latest/ext/autodoc.html>`_ ones. You can specify
just a function or class name::

    .. js-autofunction:: someFunction

Or you can throw in your own explicit parameter list, if you want to note
optional parameters::

    .. js-autofunction:: someFunction(foo, bar[, baz])

You can even add additional content. If you do, it will appear just below any
extracted documentation::

    .. js-autofunction:: someFunction

        Here are some things that will appear...

        * Below
        * The
        * Extracted
        * Docs

        Enjoy!

Tests
=====

Run ``python setup.py test``.
