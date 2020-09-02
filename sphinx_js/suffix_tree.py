from collections import namedtuple


Value = namedtuple('Value', ['value'])


class SuffixTree(object):
    """A suffix tree where the nodes are segments of a JS object path, like
    "dir/" or "someObject#" or "max"

    """
    def __init__(self):
        self._tree = {}

    def add(self, unambiguous_segments, value):
        """Add an item to the tree.

        :arg unambiguous_segments: A list of path segments that correspond
            uniquely to the object
        :arg value: Any value representing the JS object

        """
        tree = self._tree
        for seg in reversed(unambiguous_segments[1:]):
            tree = tree.setdefault(seg, {})
        seg = unambiguous_segments[0]
        if seg in tree:
            raise PathTaken(unambiguous_segments)
        else:
            tree[seg] = Value(value)

    def add_many(self, segments_and_values):
        """Add a batch of items to the tree all at once, and collect any
        errors.

        :arg segments_and_values: An iterable of (unambiguous segment path,
            value)

        If any of the segment paths are duplicates, raise PathsTaken.

        """
        conflicts = []
        for segs, value in segments_and_values:
            try:
                self.add(segs, value)
            except PathTaken as conflict:
                conflicts.append(conflict.segments)
        if conflicts:
            raise PathsTaken(conflicts)

    def get_with_path(self, segments):
        """Return the value stored at a path ending in the given segments,
        along with the full path found.

        :arg segments list: A possibly ambiguous suffix of a path

        If zero or multiple paths are found with the given suffix, raise an
        error.

        """
        full_path = []
        tree = self._tree
        for seg in reversed(segments):
            try:
                tree = tree[seg]
                full_path.append(seg)
            except KeyError:
                raise SuffixNotFound(segments)

        # Follow all the 1-key dicts. These are the paths that are unambiguous.
        while len(tree) == 1:
            if isinstance(tree, Value):
                full_path.reverse()
                return tree.value, full_path
            # It's a dict. Traverse the only key:
            key = next(iter(tree.keys()))
            tree = tree[key]
            full_path.append(key)

        # We hit a >1-key dict, an ambiguous path:
        raise SuffixAmbiguous(segments, list(tree.keys()))

    def get(self, segments):
        return self.get_with_path(segments)[0]


class SuffixError(Exception):
    def __init__(self, segments):
        self.segments = segments

    def __str__(self):
        return self._message % ''.join(self.segments)


class PathTaken(SuffixError):
    """Attempted to add a suffix that was already in the tree."""
    _message = 'Attempted to add a path already in the suffix tree: %s.'


class PathsTaken(Exception):
    """One or more JS objects had the same paths.

    Rolls up multiple PathTaken exceptions for mass reporting.

    """
    def __init__(self, conflicts):
        """
        :arg conflicts: A list of paths, each given as a list of segments
        """
        self.conflicts = conflicts

    def __str__(self):
        return ('Your code contains multiple documented objects at each of '
                "these paths:\n\n  %s\n\nWe won't know which one you're "
                'talking about.' %
                '\n  '.join(''.join(c) for c in self.conflicts))


class SuffixNotFound(SuffixError):
    """No keys ended in the given suffix."""
    _message = 'No path found ending in %s.'


class SuffixAmbiguous(SuffixError):
    """There were multiple keys found ending in the suffix."""

    def __init__(self, segments, next_possible_keys):
        super(SuffixAmbiguous, self).__init__(segments)
        self.next_possible_keys = next_possible_keys

    def __str__(self):
        return 'Ambiguous path: %s could continue as any of %s.' % (''.join(self.segments), self.next_possible_keys)
