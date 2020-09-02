"""Conveniences shared among analyzers"""

from functools import wraps
from json import dump, load
import os


def program_name_on_this_platform(program):
    """Return the name of the executable file on the current platform, given a
    command name with no extension."""
    return program + '.cmd' if os.name == 'nt' else program


class Command(object):
    def __init__(self, program):
        self.program = program_name_on_this_platform(program)
        self.args = []

    def add(self, *args):
        self.args.extend(args)

    def make(self):
        return [self.program] + self.args


def cache_to_file(get_filename):
    """Return a decorator that will cache the result of ``get_filename()`` to a
    file

    :arg get_filename: A function which receives the original arguments of the
        decorated function
    """
    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            filename = get_filename(*args, **kwargs)
            if filename and os.path.isfile(filename):
                with open(filename, encoding='utf-8') as f:
                    return load(f)
            res = fn(*args, **kwargs)
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    dump(res, f, indent=2)
            return res
        return decorated
    return decorator


def is_explicitly_rooted(path):
    """Return whether a relative path is explicitly rooted relative to the
    cwd, rather than starting off immediately with a file or folder name.

    It's nice to have paths start with "./" (or "../", "../../", etc.) so, if a
    user is that explicit, we still find the path in the suffix tree.

    """
    return path.startswith(('../', './')) or path in ('..', '.')


def dotted_path(segments):
    """Convert a JS object path (``['dir/', 'file/', 'class#',
    'instanceMethod']``) to a dotted style that Sphinx will better index.

    Strip off any leading relative-dir segments (./ or ../) because they lead
    to invalid paths like ".....foo". Ultimately, we should thread ``base_dir``
    into this and construct a full path based on that.

    """
    segments_without_separators = [s[:-1] for s in segments[:-1]
                                   if s not in ['./', '../']]
    segments_without_separators.append(segments[-1])
    return '.'.join(segments_without_separators)
