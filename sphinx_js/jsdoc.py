from collections import defaultdict
from json import loads
from os.path import abspath, relpath, sep
from subprocess import check_output

from .parsers import path_and_formal_params, PathVisitor
from .suffix_tree import SuffixTree


def run_jsdoc(app):
    """Run JSDoc across a whole codebase, and squirrel away its results."""
    # Uses cwd, which Sphinx seems to set to the dir containing conf.py:
    source_path = abspath(app.config.js_source_path)

    # JSDoc defaults to utf8-encoded output.
    jsdoc_command = ['jsdoc', source_path, '-X']
    if app.config.jsdoc_config_path:
        jsdoc_command.extend(['-c', app.config.jsdoc_config_path])
    doclets = loads(check_output(jsdoc_command).decode('utf8'))

    # 2 doclets are made for classes, and they are largely redundant: one for
    # the class itself and another for the constructor. However, the
    # constructor one gets merged into the class one and is intentionally
    # marked as undocumented, even if it isn't. See
    # https://github.com/jsdoc3/jsdoc/issues/1129.
    doclets = [d for d in doclets if d.get('comment')
                                     and not d.get('undocumented')]

    # Build table for lookup by name, which most directives use:
    app._sphinxjs_doclets_by_path = SuffixTree()
    for d in doclets:
        app._sphinxjs_doclets_by_path.add(
            doclet_full_path(d, source_path),
            d)

    # Build lookup table for autoclass's :members: option. This will also
    # pick up members of functions (inner variables), but it will instantly
    # filter almost all of them back out again because they're undocumented.
    # We index these by unambiguous full path. Then, when looking them up by
    # arbitrary name segment, we disambiguate that first by running it through
    # the suffix tree above. Expect trouble due to jsdoc's habit of calling
    # things (like ES6 class methods) "<anonymous>" in the memberof field, even
    # though they have names. This will lead to multiple methods having each
    # other's members. But if you don't have same-named inner functions or
    # inner variables that are documented, you shouldn't have trouble.
    app._sphinxjs_doclets_by_class = defaultdict(lambda: [])
    for d in doclets:
        of = d.get('memberof')
        if of:  # speed optimization
            segments = doclet_full_path(d, source_path, longname_field='memberof')
            app._sphinxjs_doclets_by_class[tuple(segments)].append(d)


def doclet_full_path(d, base_dir, longname_field='longname'):
    """Return the full, unambiguous list of path segments that points to an
    entity described by a doclet.

    Example: ``['./', 'dir/', 'dir/', 'file/', 'object.', 'object#', 'object']``

    :arg d: The doclet
    :arg base_dir: Absolutized value of the jsdoc_source_path option
    :arg longname_field: The field to look in at the top level of the doclet
        for the long name of the object to emit a path to
    """
    meta = d['meta']
    rel = relpath(meta['path'], base_dir)
    if not rel.startswith(('../', './')) and rel not in ('..', '.'):
        # It just starts right out with the name of a folder in the cwd.
        rooted_rel = './%s' % rel
    else:
        rooted_rel = rel

    # Building up a string and then parsing it back down again is probably
    # not the fastest approach, but it means knowledge of path format is in
    # one place: the parser.
    path = '%s/%s.%s' % (rooted_rel,
                         without_ending(meta['filename'], '.js'),
                         d[longname_field])
    return PathVisitor().visit(
        path_and_formal_params['path'].parse(path))


def without_ending(str, ending):
    if str.endswith(ending):
        return str[:-len(ending)]
    return str
