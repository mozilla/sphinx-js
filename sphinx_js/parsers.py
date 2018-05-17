from re import sub

from parsimonious import Grammar, NodeVisitor


path_and_formal_params = Grammar(r"""
    path_and_formal_params = path formal_params

    # Invalid JS symbol names and wild-and-crazy placement of slashes later in
    # the path (after the FS path is over) will be caught at name-resolution
    # time.
    # Note that "." is a non-separator char only when used at the very front.
    path = maybe_cur_dir middle_segments name

    # A name is a series of non-separator (not ~#/.), non-(, and backslashed
    # characters.
    name = ~r"(?:[^(/#~.\\]|\\.)+"

    sep = ~r"[#~/.]"
    maybe_cur_dir = cur_dir?
    cur_dir = "./"
    middle_segments = name_and_sep*
    name_and_sep = name sep
    formal_params = ~r".*"
    """)


class PathVisitor(NodeVisitor):
    grammar = path_and_formal_params

    def visit_path_and_formal_params(self, node, children):
        return children

    def visit_name(self, node, children):
        # This, for better or worse, also makes Python string escape sequences,
        # like \n for newline, work.
        return _backslash_unescape(node.text)

    def visit_sep(self, node, children):
        return node.text

    def visit_path(self, node, children):
        cur_dir, middle_segments, name = children
        segments = cur_dir[:]
        segments.extend(middle_segments)
        segments.append(name)
        return segments

    def visit_name_and_sep(self, node, children):
        """Concatenate name and separator into one string."""
        return ''.join(x for x in children)

    def visit_formal_params(self, node, children):
        return node.text

    def visit_maybe_cur_dir(self, node, children):
        """Return ['./'] or []."""
        return children

    def visit_cur_dir(self, node, children):
        return node.text

    def visit_middle_segments(self, node, children):
        return children


def _backslash_unescape(str):
    """Return a string with backslash escape sequences replaced with their
    literal meanings.

    Don't respect any of the conventional \n, \v, \t, etc. Keep it simple. Keep
    it safe.

    """
    return sub(r'\\(.)', lambda match: match.group(1), str)
