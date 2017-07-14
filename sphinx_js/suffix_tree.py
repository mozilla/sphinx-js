from collections import namedtuple

from six import iterkeys, python_2_unicode_compatible


Value = namedtuple('Value', ['value'])


class SuffixTree(object):
    """A suffix tree where the nodes are segments of a JS object path, like
    "dir/" or "someObject#" or "max"

    """
    def __init__(self):
        self._tree = {}

    def add(self, unambiguous_segments, value):
        tree = self._tree
        for seg in reversed(unambiguous_segments[1:]):
            tree = tree.setdefault(seg, {})
        seg = unambiguous_segments[0]
        if seg in tree:
            raise PathTaken(unambiguous_segments)
        else:
            tree[seg] = Value(value)

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
            key = next(iterkeys(tree))
            value = tree[key]
            full_path.append(key)
            if isinstance(value, Value):
                full_path.reverse()
                return value.value, full_path
            else:
                tree = value

        # We hit a >1-key dict, an ambiguous path:
        raise SuffixAmbiguous(segments, list(iterkeys(tree)))

    def get(self, segments):
        return self.get_with_path(segments)[0]


@python_2_unicode_compatible
class SuffixError(Exception):
    def __init__(self, segments):
        self.segments = segments

    def __str__(self):
        return self._message % ''.join(self.segments)


class PathTaken(SuffixError):
    """Attempted to add a suffix that was already in the tree."""
    _message = 'Attempted to add a path already in the suffix tree: %s.'


class SuffixNotFound(SuffixError):
    """No keys ended in the given suffix."""
    _message = 'No path found ending in %s.'


@python_2_unicode_compatible
class SuffixAmbiguous(SuffixError):
    """There were multiple keys found ending in the suffix."""

    def __init__(self, segments, next_possible_keys):
        super(SuffixAmbiguous, self).__init__(segments)
        self.next_possible_keys = next_possible_keys

    def __str__(self):
        return 'Ambiguous path: %s could continue as any of %s.' % (''.join(self.segments), self.next_possible_keys)
