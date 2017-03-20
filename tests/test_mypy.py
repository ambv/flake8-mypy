import ast
from pathlib import Path
import subprocess
from typing import List, Union
import unittest
from unittest import mock

from flake8_mypy import TypingVisitor, MypyChecker, T484, T400
from flake8_mypy import Error, _Flake8Error


class MypyTestCase(unittest.TestCase):
    maxDiff = None  # type: int

    def errors(self, *errors: Error) -> List[_Flake8Error]:
        return [MypyChecker.adapt_error(e) for e in errors]

    def assert_visit(self, code: str, should_type_check: bool) -> None:
        tree = ast.parse(code)
        v = TypingVisitor()
        v.visit(tree)
        self.assertEqual(v.should_type_check, should_type_check)

    def get_mypychecker(self, file: Union[Path, str]) -> MypyChecker:
        current = Path('.').absolute()
        filename = Path(__file__).relative_to(current).parent / file
        with filename.open('r', encoding='utf8', errors='surrogateescape') as f:
            lines = f.readlines()
        options = mock.MagicMock()
        options.mypy_config = None
        return MypyChecker(
            filename=str(filename),
            lines=lines,
            tree=ast.parse(''.join(lines)),
            options=options,
        )

    def test_imports(self) -> None:
        self.assert_visit("import os", False)
        self.assert_visit("import os.typing", False)
        self.assert_visit("from .typing import something", False)
        self.assert_visit("from something import typing", False)
        self.assert_visit("from . import typing", False)

        self.assert_visit("import typing", True)
        self.assert_visit("import typing.io", True)
        self.assert_visit("import one, two, three, typing", True)
        self.assert_visit("from typing import List", True)
        self.assert_visit("from typing.io import IO", True)

    def test_functions(self) -> None:
        self.assert_visit("def f(): ...", False)
        self.assert_visit("def f(a): ...", False)
        self.assert_visit("def f(a, b=None): ...", False)
        self.assert_visit("def f(a, *, b=None): ...", False)
        self.assert_visit("def f(a, *args, **kwargs): ...", False)

        self.assert_visit("def f() -> None: ...", True)
        self.assert_visit("def f(a: str): ...", True)
        self.assert_visit("def f(a, b: str = None): ...", True)
        self.assert_visit("def f(a, *, b: str = None): ...", True)
        self.assert_visit("def f(a, *args: str, **kwargs: str): ...", True)

    def test_invalid_types(self) -> None:
        mpc = self.get_mypychecker('invalid_types.py')
        errors = list(mpc.run())
        self.assertEqual(
            errors,
            self.errors(
                T484(5, 0, vars=('Missing return statement',)),
                T484(
                    10,
                    4,
                    vars=(
                        'Incompatible return value type (got "int", expected "str")',
                    ),
                ),
                T484(
                    10,
                    11,
                    vars=(
                        'Unsupported operand types for + ("int" and "str")',
                    ),
                ),
                T400(
                    13,
                    0,
                    vars=(
                        "unused 'type: ignore' comment",
                    )
                )
            ),
        )

    def test_clash(self) -> None:
        mpc = self.get_mypychecker('clash/london_calling.py')
        errors = list(mpc.run())
        self.assertEqual(
            errors,
            self.errors(
                T484(
                    6,
                    4,
                    vars=(
                        'Incompatible return value type (got "UserDict", '
                        'expected Counter[Any])',
                    ),
                ),
                T484(
                    6,
                    11,
                    vars=(
                        "Cannot instantiate abstract class 'UserDict' with "
                        "abstract attributes '__delitem__', '__getitem__', "
                        "'__iter__', '__len__' and '__setitem__'",
                    ),
                ),
            ),
        )

    def test_relative_imports(self) -> None:
        mpc = self.get_mypychecker('relative_imports.py')
        errors = list(mpc.run())
        self.assertEqual(errors, [])

    def test_selfclean_flake8_mypy(self) -> None:
        filename = Path(__file__).absolute().parent.parent / 'flake8_mypy.py'
        proc = subprocess.run(
            ['flake8', str(filename)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout.decode('utf8'))
        self.assertEqual(proc.stdout, b'')
        # self.assertEqual(proc.stderr, b'')

    def test_selfclean_test_mypy(self) -> None:
        filename = Path(__file__).absolute()
        proc = subprocess.run(
            ['flake8', str(filename)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout.decode('utf8'))
        self.assertEqual(proc.stdout, b'')
        # self.assertEqual(proc.stderr, b'')


if __name__ == '__main__':
    unittest.main()
