from collections import defaultdict
from json import loads
from subprocess import check_output


def run_jsdoc(app):
    """Run JSDoc across a whole codebase, and squirrel away its results."""
    # JSDoc defaults to utf8-encoded output.
    jsdoc_command = ['jsdoc', app.config.js_source_path, '-X']
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
    app._sphinxjs_doclets_by_longname = {d['longname']: d for d in doclets}

    # Build lookup table for autoclass's :members: option. This will also
    # pick up members of functions (inner variables), but it will instantly
    # filter almost all of them back out again because they're undocumented:
    app._sphinxjs_doclets_by_class = defaultdict(lambda: [])
    for d in doclets:
        of = d.get('memberof')
        if of:
            app._sphinxjs_doclets_by_class[of].append(d)
