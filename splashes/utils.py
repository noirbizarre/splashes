import os
import sys


class ObjectDict(dict):
    '''A dictionnary with object-like value access'''

    def __getattr__(self, key):
        if key in self:
            return self[key]
        return None

    def __setattr__(self, key, value):
        self[key] = value


def is_tty():
    '''Check wether the current process output to a tty or not'''
    return os.isatty(sys.stdout.fileno()) and not sys.platform.startswith('win')
