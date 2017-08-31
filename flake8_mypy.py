#!/usr/bin/env python3
import ast
from collections import namedtuple
from functools import partial
import itertools
import logging
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time
import traceback
from typing import (
    Any,
    Iterator,
    List,
    Optional,
    Pattern,
    Tuple,
    Type,
    TYPE_CHECKING,
    Union,
)

import attr
import mypy.api

if TYPE_CHECKING:
    import flake8.options.manager.OptionManager  # noqa


__version__ = '17.8.0'


noqa = re.compile(r'# noqa\b', re.I).search
Error = namedtuple('Error', 'lineno col message type vars')


def make_arguments(**kwargs: Union[str, bool]) -> List[str]:
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


def calculate_mypypath() -> List[str]:
    """Return MYPYPATH so that stubs have precedence over local sources."""

    typeshed_root = None
    count = 0
    started = time.time()
    for parent in itertools.chain(
        # Look in current script's parents, useful for zipapps.
        Path(__file__).parents,
        # Look around site-packages, useful for virtualenvs.
        Path(mypy.api.__file__).parents,
        # Look in global paths, useful for globally installed.
        Path(os.__file__).parents,
    ):
        count += 1
        candidate = parent / 'lib' / 'mypy' / 'typeshed'
        if candidate.is_dir():
            typeshed_root = candidate
            break

        # Also check the non-installed path, useful for `setup.py develop`.
        candidate = parent / 'typeshed'
        if candidate.is_dir():
            typeshed_root = candidate
            break

    LOG.debug(
        'Checked %d paths in %.2fs looking for typeshed. Found %s',
        count,
        time.time() - started,
        typeshed_root,
    )

    if not typeshed_root:
        return []

    stdlib_dirs = ('3.6', '3.5', '3.4', '3.3', '3.2', '3', '2and3')
    stdlib_stubs = [
        typeshed_root / 'stdlib' / stdlib_dir
        for stdlib_dir in stdlib_dirs
    ]
    third_party_dirs = ('3.6', '3', '2and3')
    third_party_stubs = [
        typeshed_root / 'third_party' / tp_dir
        for tp_dir in third_party_dirs
    ]
    return [
        str(p) for p in stdlib_stubs + third_party_stubs
    ]


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
    follow_imports='skip',

    # since we're ignoring imports, writing .mypy_cache doesn't make any sense
    cache_dir=os.devnull,

    # suppress errors about unsatisfied imports
    ignore_missing_imports=True,

    # allow untyped calls as a consequence of the options above
    disallow_untyped_calls=False,

    # allow returning Any as a consequence of the options above
    warn_return_any=False,

    # treat Optional per PEP 484
    strict_optional=True,

    # ensure all execution paths are returning
    warn_no_return=True,

    # lint-style cleanliness for typing needs to be disabled; returns more errors
    # than the full run.
    warn_redundant_casts=False,
    warn_unused_ignores=False,

    # The following are off by default.  Flip them on if you feel
    # adventurous.
    disallow_untyped_defs=False,
    check_untyped_defs=False,
)


_Flake8Error = Tuple[int, int, str, Type['MypyChecker']]


@attr.s(hash=False)
class MypyChecker:
    name = 'flake8-mypy'
    version = __version__

    tree = attr.ib(default=None)
    filename = attr.ib(default='(none)')
    lines = attr.ib(default=[])
    options = attr.ib(default=None)
    visitor = attr.ib(default=attr.Factory(lambda: TypingVisitor))

    def run(self) -> Iterator[_Flake8Error]:
        if not self.lines:
            return  # empty file, no need checking.

        visitor = self.visitor()
        visitor.visit(self.tree)

        if not visitor.should_type_check:
            return  # typing not used in the module

        if not self.options.mypy_config and 'MYPYPATH' not in os.environ:
            os.environ['MYPYPATH'] = ':'.join(calculate_mypypath())

        # Always put the file in a separate temporary directory to avoid
        # unexpected clashes with other .py and .pyi files in the same original
        # directory.
        with TemporaryDirectory(prefix='flake8mypy_') as d:
            with NamedTemporaryFile(
                'w', prefix='tmpmypy_', suffix='.py', dir=d
            ) as f:
                self.filename = f.name
                for line in self.lines:
                    f.write(line)
                f.flush()
                yield from self._run()

    def _run(self) -> Iterator[_Flake8Error]:
        mypy_cmdline = self.build_mypy_cmdline(self.filename, self.options.mypy_config)
        mypy_re = self.build_mypy_re(self.filename)
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

                if self.omit_error(e):
                    continue

                yield self.adapt_error(e)

            for line in stderr.splitlines():
                    last_t499 += 1
                    yield self.adapt_error(T499(last_t499, 0, vars=(line,)))

    @classmethod
    def adapt_error(cls, e: Any) -> _Flake8Error:
        """Adapts the extended error namedtuple to be compatible with Flake8."""
        return e._replace(message=e.message.format(*e.vars))[:4]

    def omit_error(self, e: Error) -> bool:
        """Returns True if error should be ignored."""
        if (
            e.vars and
            e.vars[0] == 'No parent module -- cannot perform relative import'
        ):
            return True

        return bool(noqa(self.lines[e.lineno - 1]))

    @classmethod
    def add_options(cls, parser: 'flake8.options.manager.OptionManager') -> None:
        parser.add_option(
            '--mypy-config',
            parse_from_config=True,
            help="path to a custom mypy configuration file",
        )

    def make_error(self, line: str, regex: Pattern) -> Error:
        m = regex.match(line)
        if not m:
            raise ValueError("unmatched line")

        lineno = int(m.group('lineno'))
        column = int(m.group('column') or 0)
        message = m.group('message').strip()
        if m.group('class') == 'note':
            return T400(lineno, column, vars=(message,))

        return T484(lineno, column, vars=(message,))

    def build_mypy_cmdline(
        self, filename: str, mypy_config: Optional[str]
    ) -> List[str]:
        if mypy_config:
            return ['--config-file=' + mypy_config, filename]

        return DEFAULT_ARGUMENTS + [filename]

    def build_mypy_re(self, filename: Union[str, Path]) -> Pattern:
        filename = Path(filename)
        if filename.is_absolute():
            prefix = Path('.').absolute()
            try:
                filename = filename.relative_to(prefix)
            except ValueError:
                pass   # not relative to the cwd

        re_filename = str(filename).replace('.', r'\.')
        if re_filename.startswith(r'\./'):
            re_filename = re_filename[3:]
        return re.compile(
            MYPY_ERROR_TEMPLATE.format(filename=re_filename),
            re.VERBOSE,
        )


@attr.s
class TypingVisitor(ast.NodeVisitor):
    """Used to determine if the file is using annotations at all."""
    should_type_check = attr.ib(default=False)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.returns:
            self.should_type_check = True
            return

        for arg in itertools.chain(node.args.args, node.args.kwonlyargs):
            if arg.annotation:
                self.should_type_check = True
                return

        va = node.args.vararg
        kw = node.args.kwarg
        if (va and va.annotation) or (kw and kw.annotation):
            self.should_type_check = True

    def visit_Import(self, node: ast.Import) -> None:
        for name in node.names:
            if (
                isinstance(name, ast.alias) and
                name.name == 'typing' or
                name.name.startswith('typing.')
            ):
                self.should_type_check = True
                break

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if (
            node.level == 0 and
            node.module == 'typing' or
            node.module and node.module.startswith('typing.')
        ):
            self.should_type_check = True

    def generic_visit(self, node: ast.AST) -> None:
        """Called if no explicit visitor function exists for a node."""
        for _field, value in ast.iter_fields(node):
            if self.should_type_check:
                break

            if isinstance(value, list):
                for item in value:
                    if self.should_type_check:
                        break
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)


# Generic mypy error
T484 = partial(
    Error,
    message="T484 {}",
    type=MypyChecker,
    vars=(),
)

# Generic mypy note
T400 = partial(
    Error,
    message="T400 note: {}",
    type=MypyChecker,
    vars=(),
)

# Internal mypy error (summary)
T498 = partial(
    Error,
    message="T498 Internal mypy error '{}': {}",
    type=MypyChecker,
    vars=(),
)

# Internal mypy error (traceback, stderr, unmatched line)
T499 = partial(
    Error,
    message="T499 {}",
    type=MypyChecker,
    vars=(),
)
