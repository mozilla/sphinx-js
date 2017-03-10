from json import loads
from subprocess import check_output


def run_jsdoc(app):
    """Run JSDoc across a whole codebase, and squirrel away its results."""
    # JSDoc defaults to utf8-encoded output.
    jsdoc_command = ['jsdoc', app.config.js_source_path, '-X']
    if app.config.jsdoc_config_path:
        jsdoc_command.extend(['-c', app.config.jsdoc_config_path])
    doclets = loads(check_output(jsdoc_command).decode('utf8'))
    app._sphinxjs_jsdoc_output = dict((d['longname'], d) for d in doclets
                                      if d.get('comment')
                                      and not d.get('undocumented'))
    # 2 doclets are made for classes, and they are largely redundant: one for
    # the class itself and another for the constructor. However, the
    # constructor one gets merged into the class one and is intentionally
    # marked as undocumented, even if it isn't. See
    # https://github.com/jsdoc3/jsdoc/issues/1129.
