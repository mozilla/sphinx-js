"""JavaScript analyzer

Analyzers run jsdoc or typedoc or whatever, squirrel away their output, and
then lazily constitute IR objects as requested.

"""
from .ir import Function


class Analyzer:
    def __init__(self, json, base_dir):
        """Index and squirrel away the JSON for later lazy conversion to IR
        objects.

        """
        # Build path and memberof suffix trees.

    @classmethod
    def from_disk(cls, abs_source_paths, app, base_dir)
        # ...Insert analyze_jsdoc() contents here...
        return cls(json_file_contents, base_dir)

    def get_object(path_suffix, as_type):
        """Return the IR object with the given path suffix.

        If helpful, use the ``as_type`` hint, which identifies which autodoc
        directive the user called.

        """
        doclet, full_path = self._doclets_by_path.get_with_path(path_suffix)
        if as_type == 'function':
            return doclet_as_function(doclet, full_path)
        elif as_type == 'class':
            ...Class
        elif as_type == 'attribute':
            # Proably go with Function again.
        else:
            raise NotImplementedError('Unknown autodoc directive: auto%s' % as_type)


def jsdoc_to_ir(doclets, base_dir):
    # This stuff used to be in gather_doclets but is JS-specific:

    # Actually, I don't like this scanning over all doclets and converting them. First, it's hard to tell unambiguously what class each doclet is. If we instead lazily convert each doclet to IR as it's referenced by an autodoc directive, we can use the hint we currently do: the user saying "this is a function (autofunction)", "this is a class". Second, being lazy lets us avoid converting unused doclets alogether.

    for doclet in doclets:
        if not doclet.get('comment') or doclet.get('undocumented'):
            continue
        kind = doclet['kind']
        node_args = {
            name=doclet['name'],
            path_segments=path_segments(doclet, base_dir),
            description=doclet.get('description', ''),
            fs_path=join(doclet['meta']['path'], doclet['meta']['filename']),
            line=doclet['meta']['lineno'],
            deprecated=doclet.get('deprecated', False),
            examples=doclet.get('examples', []),
            see_alsos=doclet.get('see', []),
            properties=properties_to_ir(doclet.get('properties', [])),
        }
        if kind == 'function':
            return Function(
                params=params_to_ir(doclet, doclet.get('params', [])),
                exceptions=exceptions_to_ir(doclet.get('exceptions', [])),
                returns=returns_to_ir(params.get('returns', [])),
                **node_args)


def properties_to_ir(properties):
    """Turn jsdoc-emitted properties JSON into a list of Properties."""



def params_to_ir(function, params):
    ret = []

    # First, go through the explicitly documented params:
    MARKER = object()
    for p in params:
        types = get_types(p)
        default = p.get('defaultvalue', MARKER)
        formatted_default = None if default is MARKER else format_default_according_to_type_hints(default, types)
        ret.append(Param(
            name=p['name'].split('.')[0],
            description=p.get('description', ''),
            has_default=default is MARKER,
            default=formatted_default,
            is_variadic=p.get('variable', False),
            types=params.get('type', {}).get('names', [])))

    # Use params from JS code if there are no documented params:
    if not ret:
        ret = [Param(name=p) for p in
               function['meta']['code'].get('paramnames', [])]

    return ret


def exceptions_to_ir(exceptions):
    """Turn jsdoc's JSON-formatted exceptions into a list of Exceptions."""
    return [Exception_(types=get_types(e),
                       description=unwrap(e.get('description', '')))
            for e in exceptions]


def returns_to_ir(returns):
    return [Return(types=get_types(r),
                   description=unwrap(r.get('description', '')))
            for r in returns]


def get_types(props):
    """Given an arbitrary object from a jsdoc-emitted JSON file, go get the
    ``type`` property, and return a list of all the type names."""
    return [field.get('type', {}).get('names', [])]


def format_default_according_to_type_hints(value, declared_types):
    """Return the default value for a param, formatted as a string
    ready to be used in a formal parameter list.

    JSDoc is a mess at extracting default values. It can unambiguously
    extract only a few simple types from the function signature, and
    ambiguity is even more rife when extracting from doclets. So we use
    any declared types to resolve the ambiguity.

    :arg value: The extracted value, which may be of the right or wrong type
    :arg declared_types: A list of types declared in the doclet for
        this param. For example ``{string|number}`` would yield ['string',
        'number'].

    """
    def first(list, default):
        try:
            return list[0]
        except IndexError:
            return default

    declared_type_implies_string = first(declared_types, '') == 'string'

    # If the first item of the type disjunction is "string", we treat
    # the default value as a string. Otherwise, we don't. So, if you
    # want your ambiguously documented default like ``@param
    # {string|Array} [foo=[]]`` to be treated as a string, make sure
    # "string" comes first.
    if isinstance(value, str):  # JSDoc threw it to us as a string in the JSON.
        if declared_types and not declared_type_implies_string:
            # It's a spurious string, like ``() => 5`` or a variable name.
            # Let it through verbatim.
            return value
        else:
            # It's a real string.
            return dumps(value)  # Escape any contained quotes.
    else:  # It came in as a non-string.
        if declared_type_implies_string:
            # It came in as an int, null, or bool, and we have to
            # convert it back to a string.
            return '"%s"' % (dumps(value),)
        else:
            # It's fine as the type it is.
            return dumps(value)
