"""Conveniences shared among analyzers"""
from functools import wraps
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


class PathsTaken(Exception):
    """One or more JS objects had the same paths.

    Rolls up multiple PathTaken exceptions for mass reporting.

    """
    def __init__(self, conflicts):
        # List of paths, each given as a list of segments:
        self.conflicts = conflicts

    def __str__(self):
        return ('Your JS code contains multiple documented objects at each of '
                "these paths:\n\n  %s\n\nWe won't know which one you're "
                'talking about. Using JSDoc tags like @class might help you '
                'differentiate them.' %
                '\n  '.join(''.join(c) for c in self.conflicts))
