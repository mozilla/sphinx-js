from json import loads
from subprocess import check_output


def run_jsdoc(app):
    """Run JSDoc across a whole codebase, and squirrel away its results."""
    # JSDoc defaults to utf8-encoded output.
    doclets = loads(check_output(['jsdoc', app.config.js_source_path, '-X']).decode('utf8'))
    app._sphinxjs_jsdoc_output = dict((d['longname'], d) for d in doclets
                                      if d.get('comment'))
