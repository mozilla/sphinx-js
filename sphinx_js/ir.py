"""Intermediate representation that JS and TypeScript are transformed to for
use by the rest of sphinx-js"""


class Node:
    """A documented entity"""

    def __init__(self, name, path_segments, description, fs_path, line, deprecated, examples, see_alsos, properties):
        # TODO: See if name is always the last item of path_segments. If so, don't make them pass name in.
        #: The human-readable description of the entity or '' if absent
        self.description
        #: String explanation of the deprecation (which implies True) or True or False
        self.deprecated
        self.examples  # list of preformatted textual examples
        self.see_alsos  # list of paths to also refer the reader to
        self.properties  # list of Properties



class Function(Node):
    def __init__(self):


class Param:
    def __init__(self, name, description='', has_default=False, default=None, is_variadic=False):
        self.name = name
        self.description = description
        self.has_default = has_default
        self._default = default
        self.is_variadic = is_variadic

    @property
    def default(self):
        if self.has_default:
            return self._default
        raise AttributeError('default')
