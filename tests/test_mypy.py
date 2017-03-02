import ast
from pathlib import Path
import unittest
from unittest import mock

from flake8_mypy import TypingVisitor, MypyChecker, T484, T400


class MypyTestCase(unittest.TestCase):
    maxDiff = None

    def errors(self, *errors):
        return [MypyChecker.adapt_error(e) for e in errors]

    def assert_visit(self, code, should_type_check):
        tree = ast.parse(code)
        v = TypingVisitor()
        v.visit(tree)
        self.assertEqual(v.should_type_check, should_type_check)

    def test_imports(self):
        self.assert_visit("import os", False)
        self.assert_visit("import os.typing", False)
        self.assert_visit("from .typing import something", False)
        self.assert_visit("from something import typing", False)

        self.assert_visit("import typing", True)
        self.assert_visit("import typing.io", True)
        self.assert_visit("import one, two, three, typing", True)
        self.assert_visit("from typing import List", True)
        self.assert_visit("from typing.io import IO", True)

    def test_functions(self):
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

    def test_invalid_types(self):
        current = Path('.').absolute()
        filename = Path(__file__).relative_to(current).parent / 'invalid_types.py'
        with filename.open('r', encoding='utf8', errors='surrogateescape') as f:
            lines = f.readlines()
        options = mock.MagicMock()
        options.mypy_config = None
        mpc = MypyChecker(
            filename=str(filename),
            lines=lines,
            tree=ast.parse(''.join(lines)),
            options=options,
        )
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


if __name__ == '__main__':
    unittest.main()
