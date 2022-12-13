=========
sphinx-js
=========

Why
===

When you write a JavaScript library, how do you explain it to people? If it's a small project in a domain your users are familiar with, JSDoc's alphabetical list of routines might suffice. But in a larger project, it is useful to intersperse prose with your API docs without having to copy and paste things.

sphinx-js lets you use the industry-leading `Sphinx <http://sphinx-doc.org/>`_ documentation tool with JS projects. It provides a handful of directives, patterned after the Python-centric `autodoc <www.sphinx-doc.org/en/latest/ext/autodoc.html>`_ ones, for pulling JSDoc-formatted documentation into reStructuredText pages. And, because you can keep using JSDoc in your code, you remain compatible with the rest of your JS tooling, like Google's Closure Compiler.

sphinx-js also works with TypeScript, using the TypeDoc tool in place of JSDoc and emitting all the type information you would expect.

Setup
=====

1. Install JSDoc (or TypeDoc if you're writing TypeScript). The tool must be on your ``$PATH``, so you might want to install it globally::

        npm install -g jsdoc

   ...or... ::

        npm install -g typedoc

   JSDoc 3.6.3 and TypeDoc 0.15.0 are known to work.

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

5. If you want to document TypeScript, add ``js_language = 'typescript'`` to conf.py as well.
6. If your JS source code is anywhere but at the root of your project, add ``js_source_path = '../somewhere/else'`` on a line by itself in conf.py. The root of your JS source tree should be where that setting points, relative to the conf.py file. (The default, ``../``, works well when there is a ``docs`` folder at the root of your project and your source code lives directly inside the root.)
7. If you have special JSDoc or TypeDoc configuration, add ``jsdoc_config_path = '../conf.json'`` (for example) to conf.py as well.
8. If you're documenting only JS or TS and no other languages (like C), you can set your "primary domain" to JS in conf.py::

        primary_domain = 'js'

   (The domain is ``js`` even if you're writing TypeScript.) Then you can omit all the "js:" prefixes in the directives below.

Use
===

In short, in a Sphinx project, use the following directives to pull in your JSDoc documentation, then tell Sphinx to render it all by running ``make html`` in your docs directory. If you have never used Sphinx or written reStructuredText before, here is `where we left off in its tutorial <http://www.sphinx-doc.org/en/stable/tutorial.html#defining-document-structure>`_. For a quick start, just add things to index.rst until you prove things are working.

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

Parameter properties and destructuring parameters also work fine, using `standard JSDoc syntax <https://jsdoc.app/tags-param.html#parameters-with-properties>`_::

    /**
     * Export an image from the given canvas and save it to the disk.
     *
     * @param {Object} options Output options
     * @param {string} options.format The output format (``jpeg``,  ``png``, or
     *     ``webp``)
     * @param {number} options.quality The output quality when format is
     *     ``jpeg`` or ``webp`` (from ``0.00`` to ``1.00``)
     */
    function saveCanvas({ format, quality }) {
        // ...
    }

Extraction of default parameter values works as well. These act as expected, with a few caveats::

    /**
     * You must declare the params, even if you have nothing else to say, so
     * JSDoc will extract the default values.
     *
     * @param [num]
     * @param [str]
     * @param [bool]
     * @param [nil]
     */
    function defaultsDocumentedInCode(num=5, str="true", bool=true, nil=null) {}

    /**
     * JSDoc guesses types for things like "42". If you have a string-typed
     * default value that looks like a number or boolean, you'll need to
     * specify its type explicitly. Conversely, if you have a more complex
     * value like an arrow function, specify a non-string type on it so it
     * isn't interpreted as a string. Finally, if you have a disjoint type like
     * {string|Array} specify string first if you want your default to be
     * interpreted as a string.
     *
     * @param {function} [func=() => 5]
     * @param [str=some string]
     * @param {string} [strNum=42]
     * @param {string|Array} [strBool=true]
     * @param [num=5]
     * @param [nil=null]
     */
    function defaultsDocumentedInDoclet(func, strNum, strBool, num, nil) {}

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

``autofunction`` can also be used on callbacks defined with the `@callback tag <https://jsdoc.app/tags-callback.html>`_.

There is experimental support for abusing ``autofunction`` to document `@typedef tags <https://jsdoc.app/tags-typedef.html>`_ as well, though the result will be styled as a function, and ``@property`` tags will fall misleadingly under an "Arguments" heading. Still, it's better than nothing until we can do it properly.

autoclass
---------

We provide a ``js:autoclass`` directive which documents a class with the concatenation of its class comment and its constructor comment. It shares all the features of ``js:autofunction`` and even takes the same ``:short-name:`` flag, which can come in handy for inner classes. The easiest way to use it is to invoke its ``:members:`` option, which automatically documents all your class's public methods and attributes::

    .. js:autoclass:: SomeEs6Class(constructor, args, if, you[, wish])
       :members:

You can add private members by saying... ::

    .. js:autoclass:: SomeEs6Class
       :members:
       :private-members:

Privacy is determined by JSDoc ``@private`` tags or TypeScript's ``private`` keyword.

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

You may recognize the separators ``#.~`` from `JSDoc namepaths <https://jsdoc.app/about-namepaths.html>`_; they work the same here.

For conciseness, you can use any unique suffix, as long as it consists of complete path segments. These would all be equivalent to the above, assuming they are unique within your source tree::

    innerMember
    staticMethod~innerMember
    SomeClass#someInstanceMethod.staticMethod~innerMember
    some/file.SomeClass#someInstanceMethod.staticMethod~innerMember

Things to note:

* We use simple file paths rather than JSDoc's ``module:`` prefix or TypeDoc's ``external:`` or ``module:`` ones.
* We use simple backslash escaping exclusively rather than switching escaping schemes halfway through the path; JSDoc itself `is headed that way as well <https://github.com/jsdoc3/jsdoc/issues/876>`_. The characters that need to be escaped are ``#.~(/``, though you do not need to escape the dots in a leading ``./`` or ``../``. A really horrible path might be... ::

    some/path\ with\ spaces/file.topLevelObject#instanceMember.staticMember\(with\(parens
* Relative paths are relative to the ``js_source_path`` specified in the config. Absolute paths are not allowed.

Behind the scenes, sphinx-js will change all separators to dots so that...

* Sphinx's "shortening" syntax works: ``:func:`~InwardRhs.atMost``` prints as merely ``atMost()``. (For now, you should always use dots rather than other namepath separators: ``#~``.)
* Sphinx indexes more informatively, saying methods belong to their classes.

Saving Keystrokes By Setting The Primary Domain
-----------------------------------------------

To save some keystrokes, you can set ``primary_domain = 'js'`` in conf.py and then say (for example) ``autofunction`` rather than ``js:autofunction``.

TypeScript: Getting Superclass and Interface Links To Work
----------------------------------------------------------

To have a class link to its superclasses and implemented interfaces, you'll need to document the superclass (or interface) somewhere using ``js:autoclass`` or ``js:class`` and use the class's full (but dotted) path when you do::

    .. js:autoclass:: someFile.SomeClass

Unfortunately, Sphinx's ``~`` syntax doesn't work in these spots, so users will see the full paths in the documentation.

Configuration Reference
-----------------------

``js_language``
  Use 'javascript' or 'typescript' depending on the language you use. The default is 'javascript'.

``js_source_path``
  A list of directories to scan (non-recursively) for JS or TS source files, relative to Sphinx's conf.py file. Can be a string instead if there is only one. If there is more than one, ``root_for_relative_js_paths`` must be specified as well. Defaults to '../'.

``jsdoc_config_path``
  A conf.py-relative path to a JSDoc config file, which is useful if you want to specify your own JSDoc options, like recursion and custom filename matching. If using TypeDoc, you can also point to a ``tsconfig.json`` file.

``root_for_relative_js_paths``
  Relative JS entity paths are resolved relative to this path. Defaults to ``js_source_path`` if it is only one item.

``jsdoc_cache``
  Path to a file where JSDoc output will be cached. If omitted, JSDoc will be run every time Sphinx is. If you have a large number of source files, it may help to configure this value. But be careful: the cache is not automatically flushed if your source code changes; you must delete it manually.

Example
=======

A good example using most of sphinx-js's functionality is the Fathom documentation. A particularly juicy page is https://mozilla.github.io/fathom/ruleset.html. Click the "View page source" link to see the raw directives.

`ReadTheDocs <https://readthedocs.org/>`_ is the canonical hosting platform for Sphinx docs and now supports sphinx-js as an opt-in beta. Put this in the ``.readthedocs.yml`` file at the root of your repo::

    requirements_file: docs/requirements.txt
    build:
      image: latest

Then put the version of sphinx-js you want in ``docs/requirements.txt``. For example... ::

    sphinx-js==3.1.2

Or, if you prefer, the Fathom repo carries a `Travis CI configuration <https://github.com/mozilla/fathom/blob/92304b8ad4768e90c167c3d93f9865771f5a6d80/.travis.yml#L41>`_ and a `deployment script <https://github.com/mozilla/fathom/blob/92304b8ad4768e90c167c3d93f9865771f5a6d80/tooling/travis-deploy-docs>`_ for building docs with sphinx-js and publishing them to GitHub Pages. Feel free to borrow them.

Caveats
=======

* We don't understand the inline JSDoc constructs like ``{@link foo}``; you have to use Sphinx-style equivalents for now, like ``:js:func:`foo``` (or simply ``:func:`foo``` if you have set ``primary_domain = 'js'`` in conf.py.
* So far, we understand and convert the JSDoc block tags ``@param``, ``@returns``, ``@throws``, ``@example`` (without the optional ``<caption>``), ``@deprecated``, ``@see``, and their synonyms. Other ones will go *poof* into the ether.

Tests
=====

Run the tests using tox, which will also install JSDoc and TypeDoc at pinned versions::

    pip install tox
    tox

Version History
===============

3.2.0: (December 13th, 2022)
  * Add "static" in front of static methods.
  * Pin Jinja2 and markupsafe versions. (#190)
  * Track dependencies; do not read all documents. This improves speed of incremental updates. (#194)
  * Support Python 3.10 and 3.11. (#186)
  * Support Sphinx >= 4.1.0. (#209)
  * Fix types warning for ``js_source_path`` configuration item. (#182)

  Thank you Stefan 'hr' Berder, David Huggins-Daines, Nick Alexander, mariusschenzle, Erik Rose, lonnen, and Will Kahn-Greene!

3.1.2: (April 15th, 2021)
  * Remove our declared dependency on ``docutils`` to work around the way pip's greedy dependency resolver reacts to the latest version of Sphinx. pip fails when pip-installing sphinx-js because pip sees our "any version of docutils" declaration first (which resolves greedily to the latest version, 0.17) but later encounters Sphinx's apparently new ``<0.17`` constraint and gives up. We can revert this when pip's ``--use-feature=2020-resolver`` becomes the default.

3.1.1: (March 23rd, 2021)
  * Rewrite large parts of the suffix tree that powers path lookup. This fixes several crashers.

3.1: (September 10th, 2020)
  * Re-architect language analysis. There is now a well-documented intermediate representation between JSDoc- and TypeDoc-emitted JSON and the renderers. This should make it much faster to merge PRs.
  * Rewrite much of the TypeScript analysis engine so it feeds into the new IR.

    * TypeScript analysis used to crash if your codebase contained any overloaded functions. This no longer happens; we now arbitrarily use only the first function signature of each overloaded function.
    * Add support for static properties on TS classes.
    * Support variadic args in TS.
    * Support intersection types (``foo & bar``) in TS.
    * Remove the "exported from" module links from classes and interfaces. Functions never had them. Let's see if we miss them.
    * Pathnames for TypeScript objects no longer spuriously use ``~`` after the filename path segment; now they use ``.`` as in JS.
    * More generally, TS pathnames are now just like JS ones. There is no more ``external:`` prefix in front of filenames or ``module:`` in front of namespace names.
    * TS analyzer no longer cares with the current working directory is.
    * Tests now assert only what they care about rather than being brittle to the point of prohibiting any change.
  * No longer show args in the arg list that are utterly uninformative, lacking both description and type info.
  * Class attributes are now listed before methods unless manally ordered with ``:members:``.

3.0.1: (August 10th, 2020)
  * Don't crash when encountering a ``../`` prefix on an object path. This can happen behind the scenes when ``root_for_relative_js_paths`` is set inward of the JS code.

3.0: (July 14th, 2020)
  * Make compatible with Sphinx 3, which requires Python 3.
  * Drop support for Python 2.
  * Make sphinx-js not care what the current working directory is, except for the TypeScript analyzer, which needs further work.
  * Properly RST-escape return types.

2.8: (September 16th, 2019)
  * Display generic TypeScript types properly. Make fields come before methods. (Paul Grau)
  * Combine constructor and class documentation at the top TypeScript classes. (Sebastian Weigand)
  * Switch to pytest as the testrunner. (Sebastian Weigand)
  * Add optional caching of JSDoc output, for large codebases. (Patrick Browne)
  * Fix the display of union types in TypeScript. (Sebastian Weigand)
  * Fix parsing breakage that began in typedoc 0.14.0. (Paul Grau)
  * Fix a data-intake crash with TypeScript. (Cristiano Santos)

2.7.1: (November 16th, 2018)
  * Fix a crash that would happen sometimes with UTF-8 on Windows. #67.
  * Always use conf.py's dir for JSDoc's working dir. #78. (Thomas Khyn)

2.7: (August 2nd, 2018))
  * Add experimental TypeScript support. (Wim Yedema)

2.6: (July 26th, 2018)
  * Add support for ``@deprecated`` and ``@see``. (David Li)
  * Notice and document JS variadic params nicely. (David Li)
  * Add linter to codebase.

2.5: (April 20th, 2018)
  * Use documented ``@params`` to help fill out the formal param list for a
    function. This keeps us from missing params that use destructuring. (flozz)
  * Improve error reporting when JSDoc is missing.
  * Add extracted default values to generated formal param lists. (flozz and erikrose)

2.4: (March 21, 2018)
  * Support the ``@example`` tag. (lidavidm)
  * Work under Windows. Before, we could hardly find any documentation. (flozz)
  * Properly unwrap multiple-line JSDoc tags, even if they have Windows line endings. (Wim Yedema)
  * Drop support for Python 3.3, since Sphinx has also done so.
  * Fix build-time crash when using recommonmark (for Markdown support) under Sphinx >=1.7.1. (jamrizzi)

2.3.1: (January 11th, 2018)
  * Find the ``jsdoc`` command on Windows, where it has a different name. Then
    patch up process communication so it doesn't hang.

2.3: (November 1st, 2017)
  * Add the ability to say "*" within the ``autoclass :members:`` option, meaning "and all the members that I didn't explicitly list".

2.2: (October 10th, 2017)
  * Add ``autofunction`` support for ``@callback`` tags. (krassowski)
  * Add experimental ``autofunction`` support for ``@typedef`` tags. (krassowski)
  * Add a nice error message for when JSDoc can't find any JS files.
  * Pin six more tightly so ``python_2_unicode_compatible`` is sure to be around.

2.1: (August 30th, 2017)
  * Allow multiple folders in ``js_source_path``. This is useful for gradually migrating large projects, one folder at a time, to JSDoc. Introduce ``root_for_relative_js_paths`` to keep relative paths unambiguous in the face of multiple source paths.
  * Aggregate PathTaken errors, and report them all at once. This means you don't have to run JSDoc repeatedly while cleaning up large projects.
  * Fix a bytes-vs-strings issue that crashed on versions of Python 3 before 3.6. (jhkennedy)
  * Tolerate JS files that have filename extensions other than ".js". Before, when combined with custom JSDoc configuration that ingested such files, incorrect object pathnames were generated, which led to spurious "No JSDoc documentation was found for object ..." errors.

2.0.1: (July 13th, 2017)
  * Fix spurious syntax errors while loading large JSDoc output by writing it to a temp file first. (jhkennedy)

2.0: (May 4th, 2017)
  * Deal with ambiguous object paths. Symbols with identical JSDoc longnames (such as two top-level things called "foo" in different files) will no longer have one shadow the other. Introduce an unambiguous path convention for referring to objects. Add a real parser to parse them rather than the dirty tricks we were using before. Backward compatibility breaks a little, because ambiguous references are now a fatal error, rather than quietly referring to the last definition JSDoc happened to encounter.
  * Index everything into a suffix tree so you can use any unique path suffix to refer to an object.
  * Other fallout of having a real parser:

    * Stop supporting "-" as a namepath separator.
    * No longer spuriously translate escaped separators in namepaths into dots.
    * Otherwise treat paths and escapes properly. For example, we can now handle symbols that contain "(".
  * Fix KeyError when trying to gather the constructor params of a plain old
    object labeled as a ``@class``.

1.5.2: (March 22th, 2017)
  * Fix crasher while warning that a specified longname isn't found.

1.5.1: (March 20th, 2017)
  * Sort ``:members:`` alphabetically when an order is not explicitly specified.

1.5: (March 17th, 2017)
  * Add ``:members:`` option to ``autoclass``.
  * Add ``:private-members:`` and ``:exclude-members:`` options to go with it.
  * Significantly refactor to allow directive classes to talk to each other.

1.4: (March 10th, 2017)
  * Add ``jsdoc_config_path`` option.

1.3.1: (March 6th, 2017)
  * Tolerate @args and other info field lines that are wrapped in the source code.
  * Cite the file and line of the source comment in Sphinx-emitted warnings and errors.

1.3: (February 21st, 2017)
  * Add ``autoattribute`` directive.

1.2: (February 14th, 2017)
  * Always do full rebuilds; don't leave pages stale when JS code has changed but the RSTs have not.
  * Make Python-3-compatible.
  * Add basic ``autoclass`` directive.

1.1: (February 13th, 2017)
  * Add ``:short-name:`` option.

1.0: (February 7th, 2017)
  * Initial release, with just ``js:autofunction``
