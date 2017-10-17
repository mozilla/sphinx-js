=========
sphinx-js
=========

Why
===

When you write a JavaScript library, how do you explain it to people? If it's a small project in a domain your users are familiar with, JSDoc's alphabetical list of routines might suffice. But in a larger project, it is useful to intersperse prose with your API docs without having to copy and paste things.

sphinx-js lets you use the industry-leading `Sphinx <http://sphinx-doc.org/>`_ documentation tool with JS projects. It provides a handful of directives, patterned after the Python-centric `autodoc <www.sphinx-doc.org/en/latest/ext/autodoc.html>`_ ones, for pulling JSDoc-formatted documentation into reStructuredText pages. And, because you can keep using JSDoc in your code, you remain compatible with the rest of your JS tooling, like Google's Closure Compiler.

Setup
=====

1. Install JSDoc using npm. ``jsdoc`` must be on your ``$PATH``, so you might want to install it globally::

        npm install -g jsdoc

   We work with jsdoc 3.4.3, 3.5.4, and quite possibly other versions.
2. Install sphinx-js, which will pull in Sphinx itself as a dependency::

        pip install sphinx-js

3. Make a documentation folder in your project by running ``sphinx-quickstart`` and answering its questions::

        cd my-project
        sphinx-quickstart

          > Root path for the documentation [.]: docs
          > Separate source and build directories (y/n) [n]:
          > Name prefix for templates and static dir [_]:
          > Project name: My Project
          > Author name(s): Fred Fredson
          > Project version []: 1.0
          > Project release [1.0]:
          > Project language [en]:
          > Source file suffix [.rst]:
          > Name of your master document (without suffix) [index]:
          > Do you want to use the epub builder (y/n) [n]:
          > autodoc: automatically insert docstrings from modules (y/n) [n]:
          > doctest: automatically test code snippets in doctest blocks (y/n) [n]:
          > intersphinx: link between Sphinx documentation of different projects (y/n) [n]:
          > todo: write "todo" entries that can be shown or hidden on build (y/n) [n]:
          > coverage: checks for documentation coverage (y/n) [n]:
          > imgmath: include math, rendered as PNG or SVG images (y/n) [n]:
          > mathjax: include math, rendered in the browser by MathJax (y/n) [n]:
          > ifconfig: conditional inclusion of content based on config values (y/n) [n]:
          > viewcode: include links to the source code of documented Python objects (y/n) [n]:
          > githubpages: create .nojekyll file to publish the document on GitHub pages (y/n) [n]:
          > Create Makefile? (y/n) [y]:
          > Create Windows command file? (y/n) [y]:

4. In the generated Sphinx conf.py file, turn on ``sphinx_js`` by adding it to ``extensions``::

        extensions = ['sphinx_js']

5. If your JS source code is anywhere but at the root of your project, add ``js_source_path = '../somewhere/else'`` on a line by itself in conf.py. The root of your JS source tree should be where that setting points, relative to the conf.py file. (The default, ``../``, works well when there is a ``docs`` folder at the root of your project and your source code lives directly inside the root.)
6. If you have special jsdoc configuration, add ``jsdoc_config_path = '../conf.json'`` (for example) to conf.py as well.
7. If you're documenting only JS and no other languages, you can set your "primary domain" to JS in conf.py::

        primary_domain = 'js'

   Then you can omit all the "js:" prefixes in the directives below.

Use
===

In short, write a folder full of reStructuredText files, use the following directives to pull in your JSDoc documentation, then tell Sphinx to render it all by running ``make html`` in your docs directory. If you have never used Sphinx or written reStructuredText before, here is `where we left off in its tutorial <http://www.sphinx-doc.org/en/stable/tutorial.html#defining-document-structure>`_. For a quick start, just add things to index.rst for now.

autofunction
------------

First, document your JS code using standard JSDoc formatting::

    /**
     * Return the ratio of the inline text length of the links in an element to
     * the inline text length of the entire element.
     *
     * @param {Node} node - Types or not: either works.
     * @throws {PartyError|Hearty} Multiple types work fine.
     * @returns {Number} Types and descriptions are both supported.
     */
    function linkDensity(node) {
        const length = node.flavors.get('paragraphish').inlineLength;
        const lengthWithoutLinks = inlineTextLength(node.element,
                                                    element => element.tagName !== 'A');
        return (length - lengthWithoutLinks) / length;
    }

Then, reference your documentation using sphinx-js directives. Our directives work much like Sphinx's standard autodoc ones. You can specify just a function's name... ::

    .. js:autofunction:: someFunction

...and a nicely formatted block of documentation will show up in your docs.

You can also throw in your own explicit parameter list, if you want to note
optional parameters::

    .. js:autofunction:: someFunction(foo, bar[, baz])

You can even add additional content. If you do, it will appear just below any extracted documentation::

    .. js:autofunction:: someFunction

        Here are some things that will appear...

        * Below
        * The
        * Extracted
        * Docs

        Enjoy!

``js:autofunction`` has one option, ``:short-name:``, which comes in handy for chained APIs whose implementation details you want to keep out of sight. When you use it on a class method, the containing class won't be mentioned in the docs, the function will appear under its short name in indices, and cross references must use the short name as well (``:func:`someFunction```)::

    .. js:autofunction:: someClass#someFunction
       :short-name:

``autofunction`` can also be used on callbacks defined with the `@callback tag <http://usejsdoc.org/tags-callback.html>`_.

There is experimental support for abusing ``autofunction`` to document `@typedef tags <http://usejsdoc.org/tags-typedef.html>`_ as well, though the result will be styled as a function, and ``@property`` tags will fall misleadingly under an "Arguments" heading. Still, it's better than nothing until we can do it properly.

autoclass
---------

We provide a ``js:autoclass`` directive which documents a class with the concatenation of its class comment and its constructor comment. It shares all the features of ``js:autofunction`` and even takes the same ``:short-name:`` flag, which can come in handy for inner classes. The easiest way to use it is to invoke its ``:members:`` option, which automatically documents all your class's public methods and attributes::

    .. js:autoclass:: SomeEs6Class(constructor, args, if, you[, wish])
       :members:

You can add private members by saying... ::

    .. js:autoclass:: SomeEs6Class
       :members:
       :private-members:

Privacy is determined by JSDoc ``@private`` tags.

Exclude certain members by name with ``:exclude-members:``::

    .. js:autoclass:: SomeEs6Class
       :members:
       :exclude-members: Foo, bar, baz

Or explicitly list the members you want. We will respect your ordering. ::

    .. js:autoclass:: SomeEs6Class
       :members: Qux, qum

When explicitly listing members, you can include ``*`` to include all unmentioned members. This is useful to have control over ordering of some elements, without having to include an exhaustive list. ::

    .. js:autoclass:: SomeEs6Class
       :members: importMethod, *, uncommonlyUsedMethod

Finally, if you want full control, pull your class members in one at a time by embedding ``js:autofunction`` or ``js:autoattribute``::

    .. js:autoclass:: SomeEs6Class

       .. js:autofunction:: SomeEs6Class#someMethod

       Additional content can go here and appears below the in-code comments,
       allowing you to intersperse long prose passages and examples that you
       don't want in your code.

autoattribute
-------------

This is useful for documenting public properties::

    class Fnode {
        constructor(element) {
            /**
             * The raw DOM element this wrapper describes
             */
            this.element = element;
        }
    }

And then, in the docs... ::

    .. autoclass:: Fnode

       .. autoattribute:: Fnode#element

This is also the way to document ES6-style getters and setters, as it omits the trailing ``()`` of a function. The assumed practice is the usual JSDoc one: document only one of your getter/setter pair::

    class Bing {
        /** The bong of the bing */
        get bong() {
            return this._bong;
        }

        set bong(newBong) {
            this._bong = newBong * 2;
        }
    }

And then, in the docs... ::

   .. autoattribute:: Bing#bong

Dodging Ambiguity With Pathnames
--------------------------------

If you have same-named objects in different files, use pathnames to disambiguate them. Here's a particularly long example::

    .. js:autofunction:: ./some/dir/some/file.SomeClass#someInstanceMethod.staticMethod~innerMember

You may recognize the separators ``#.~`` from `JSDoc namepaths <http://usejsdoc.org/about-namepaths.html>`_; they work the same here.

For conciseness, you can use any unique suffix, as long as it consists of complete path segments. These would all be equivalent to the above, assuming they are unique within your source tree::

    innerMember
    staticMethod~innerMember
    SomeClass#someInstanceMethod.staticMethod~innerMember
    some/file.SomeClass#someInstanceMethod.staticMethod~innerMember

Things to note:

* We use simple file paths rather than JSDoc's ``module:`` prefix.
* We use simple backslash escaping exclusively rather than switching escaping schemes halfway through the path; JSDoc itself `is headed that way as well <https://github.com/jsdoc3/jsdoc/issues/876>`_. The characters that need to be escaped are ``#.~(/``, though you do not need to escape the dots in a leading ``./`` or ``../``. A really horrible path might be... ::

    some/path\ with\ spaces/file.topLevelObject#instanceMember.staticMember\(with\(parens
* Relative paths are relative to the ``js_source_path`` specified in the config. Absolute paths are not allowed.

Behind the scenes, sphinx-js will change all separators to dots so that...

* Sphinx's "shortening" syntax works: ``:func:`~InwardRhs.atMost``` prints as merely ``atMost()``. (For now, you should always use dots rather than other namepath separators: ``#~``.)
* Sphinx indexes more informatively, saying methods belong to their classes.

Saving Keystrokes By Setting The Primary Domain
-----------------------------------------------

To save some keystrokes, you can set ``primary_domain = 'js'`` in conf.py and then say (for example) ``autofunction`` rather than ``js:autofunction``.

Configuration Reference
-----------------------

``js_source_path``
  A list of directories to scan (non-recursively) for JS files, relative to Sphinx's conf.py file. Can be a string instead if there is only one. If there is more than one, ``root_for_relative_js_paths`` must be specified as well.

``jsdoc_config_path``
  A conf.py-relative path to a jsdoc config file, which is useful if you want to specify your own jsdoc options, like recursion and custom filename matching.

``root_for_relative_js_paths``
  The directory relative to which relative pathnames are resolved. Defaults to ``js_source_path`` if it is only one item.

Example
=======

A good example using most of sphinx-js's functionality is the Fathom documentation. A particularly juicy page is https://mozilla.github.io/fathom/ruleset.html. Click the "View page source" link to see the raw directives.

Fathom also carries a Travis CI configuration and a deployment script for building docs with sphinx-js and publishing them to GitHub Pages. Feel free to borrow them. However, `ReadTheDocs <https://readthedocs.org/>`_, the canonical hosting platform for Sphinx docs, now supports sphinx-js, so that's likely your best bet.

Caveats
=======

* We don't understand the inline JSDoc constructs like ``{@link foo}``; you have to use Sphinx-style equivalents for now, like ``:js:func:`foo``` (or simply ``:func:`foo``` if you have set ``primary_domain = 'js'`` in conf.py.
* So far, we understand and convert only the JSDoc block tags ``@param``, ``@returns``, ``@throws``, and their synonyms. Other ones will go *poof* into the ether.

Tests
=====

Run ``python setup.py test``. Run ``tox`` to test across Python versions.

Version History
===============

2.2
  * Add ``autofunction`` support for ``@callback`` tags. (krassowski)
  * Add experimental ``autofunction`` support for ``@typedef`` tags. (krassowski)
  * Add a nice error message for when jsdoc can't find any JS files.
  * Pin six more tightly so ``python_2_unicode_compatible`` is sure to be around.

2.1
  * Allow multiple folders in ``js_source_path``. This is useful for gradually migrating large projects, one folder at a time, to jsdoc. Introduce ``root_for_relative_js_paths`` to keep relative paths unambiguous in the face of multiple source paths.
  * Aggregate PathTaken errors, and report them all at once. This means you don't have to run JSDoc repeatedly while cleaning up large projects.
  * Fix a bytes-vs-strings issue that crashed on versions of Python 3 before 3.6. (jhkennedy)
  * Tolerate JS files that have filename extensions other than ".js". Before, when combined with custom jsdoc configuration that ingested such files, incorrect object pathnames were generated, which led to spurious "No JSDoc documentation was found for object ..." errors.

2.0.1
  * Fix spurious syntax errors while loading large JSDoc output by writing it to a temp file first. (jhkennedy)

2.0
  * Deal with ambiguous object paths. Symbols with identical JSDoc longnames (such as two top-level things called "foo" in different files) will no longer have one shadow the other. Introduce an unambiguous path convention for referring to objects. Add a real parser to parse them rather than the dirty tricks we were using before. Backward compatibility breaks a little, because ambiguous references are now a fatal error, rather than quietly referring to the last definition JSDoc happened to encounter.
  * Index everything into a suffix tree so you can use any unique path suffix to refer to an object.
  * Other fallout of having a real parser:

    * Stop supporting "-" as a namepath separator.
    * No longer spuriously translate escaped separators in namepaths into dots.
    * Otherwise treat paths and escapes properly. For example, we can now handle symbols that contain "(".
  * Fix KeyError when trying to gather the constructor params of a plain old
    object labeled as a ``@class``.

1.5.2
  * Fix crasher while warning that a specified longname isn't found.

1.5.1
  * Sort ``:members:`` alphabetically when an order is not explicitly specified.

1.5
  * Add ``:members:`` option to ``autoclass``.
  * Add ``:private-members:`` and ``:exclude-members:`` options to go with it.
  * Significantly refactor to allow directive classes to talk to each other.

1.4
  * Add ``jsdoc_config_path`` option.

1.3.1
  * Tolerate @args and other info field lines that are wrapped in the source code.
  * Cite the file and line of the source comment in Sphinx-emitted warnings and errors.

1.3
  * Add ``autoattribute`` directive.

1.2
  * Always do full rebuilds; don't leave pages stale when JS code has changed but the RSTs have not.
  * Make Python-3-compatible.
  * Add basic ``autoclass`` directive.

1.1
  * Add ``:short-name:`` option.

1.0
  * Initial release, with just ``js:autofunction``
