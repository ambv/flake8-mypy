#!/usr/bin/env python3
from collections import namedtuple
from functools import partial
import logging
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
import traceback

import attr
import pycodestyle
import mypy.api


__version__ = '17.2.0'


def make_arguments(**kwargs):
    result = []
    for k, v in kwargs.items():
        k = k.replace('_', '-')
        if v is True:
            result.append('--' + k)
        elif v is False:
            continue
        else:
            result.append('--{}={}'.format(k, v))
    return result


# invalid_types.py:5: error: Missing return statement
MYPY_ERROR_TEMPLATE = r"""
^
.*                                     # whatever at the beginning
{filename}:                            # this needs to be provided in run()
(?P<lineno>\d+)                        # necessary for the match
(:(?P<column>\d+))?                    # optional but useful column info
:[ ]                                   # ends the preamble
((?P<class>error|warning|note):)?      # optional class
[ ](?P<message>.*)                     # the rest
$"""
LOG = logging.getLogger('flake8.mypy')
DEFAULT_ARGUMENTS = make_arguments(
    python_version='3.6',
    platform='linux',

    # flake8-mypy expects the two following for sensible formatting
    show_column_numbers=True,
    show_error_context=False,

    # suppress error messages from unrelated files
    follow_imports='silent',

    # suppress errors about unsatisfied imports
    ignore_missing_imports=True,

    # allow untyped calls as a consequence of the options above
    disallow_untyped_calls=False,

    # allow returning Any as a consequence of the options above
    warn_return_any=False,

    # treat Optional per PEP 484
    strict_optional=True,
    # show_none_errors=True,  # it's in the docs but not in master?

    # ensure all execution paths are returning
    warn_no_return=True,

    # lint-style cleanliness for typing
    warn_redundant_casts=True,
    warn_unused_ignores=True,

    # The following are off by default.  Flip them on if you feel
    # adventurous.
    disallow_untyped_defs=False,
    check_untyped_defs=False,
)


@attr.s(hash=False)
class MypyChecker:
    name = 'flake8-mypy'
    version = __version__

    tree = attr.ib(default=None)
    filename = attr.ib(default='(none)')
    lines = attr.ib(default=[])
    options = attr.ib(default=None)

    def run(self):
        if not self.lines:
            return  # empty file, no need checking.

        if self.filename in ('(none)', 'stdin'):
            with NamedTemporaryFile('w', prefix='tmpmypy_', suffix='.py') as f:
                self.filename = f.name
                for line in self.lines:
                    f.write(line)
                f.flush()
                yield from self._run()
        else:
            yield from self._run()

    def _run(self):
        mypy_cmdline = self.build_mypy_cmdline(self.filename, self.options.mypy_config)
        re_filename = self.filename.replace('.', r'\.')
        mypy_re = re.compile(
            MYPY_ERROR_TEMPLATE.format(filename=re_filename),
            re.VERBOSE,
        )
        last_t499 = 0
        try:
            stdout, stderr, returncode = mypy.api.run(mypy_cmdline)
        except Exception as exc:
            # Pokémon exception handling to guard against mypy's internal errors
            last_t499 += 1
            yield self.adapt_error(T498(last_t499, 0, vars=(type(exc), str(exc))))
            for line in traceback.format_exc().splitlines():
                last_t499 += 1
                yield self.adapt_error(T499(last_t499, 0, vars=(line,)))
        else:
            # FIXME: should we make any decision based on `returncode`?
            for line in stdout.splitlines():
                try:
                    e = self.make_error(line, mypy_re)
                except ValueError:
                    # unmatched line
                    last_t499 += 1
                    yield self.adapt_error(T499(last_t499, 0, vars=(line,)))
                    continue

                if pycodestyle.noqa(self.lines[e.lineno - 1]):
                    continue

                yield self.adapt_error(e)

            for line in stderr.splitlines():
                    last_t499 += 1
                    yield self.adapt_error(T499(last_t499, 0, vars=(line,)))

    @classmethod
    def adapt_error(cls, e):
        """Adapts the extended error namedtuple to be compatible with Flake8."""
        return e._replace(message=e.message.format(*e.vars))[:4]

    @classmethod
    def add_options(cls, parser):
        parser.add_option(
            '--mypy-config',
            parse_from_config=True,
            help="path to a custom mypy configuration file",
        )

    def make_error(self, line, regex):
        m = regex.match(line)
        if not m:
            raise ValueError("unmatched line")

        lineno = int(m.group('lineno'))
        column = int(m.group('column') or 0)
        message = m.group('message').strip()
        if m.group('class') == 'note':
            return T400(lineno, column, vars=(message,))

        return T484(lineno, column, vars=(message,))

    def ensure_lines(self):
        """Read the file if it wasn't yet. Populate `sys.lines`."""
        if self.lines:
            return

        path = Path(self.filename)
        text = path.read_text(encoding='utf8', errors='surrogateescape')
        self.lines = text.splitlines()

    def build_mypy_cmdline(self, filename, mypy_config):
        if mypy_config:
            return ['--config-file=' + mypy_config, filename]

        return DEFAULT_ARGUMENTS + [filename]


error = namedtuple('error', 'lineno col message type vars')
Error = partial(partial, error, type=MypyChecker, vars=())


# Generic mypy error
T484 = Error(
    message="T484 {}",
)

# Generic mypy note
T400 = Error(
    message="T400 note: {}",
)

# Internal mypy error (summary)
T498 = Error(
    message="T498 Internal mypy error '{}': {}",
)

# Internal mypy error (traceback, stderr, unmatched line)
T499 = Error(
    message="T499 {}",
)
