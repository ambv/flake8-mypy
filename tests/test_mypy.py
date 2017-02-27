from pathlib import Path
import unittest
from unittest import mock

from flake8_mypy import MypyChecker, T484


class MypyTestCase(unittest.TestCase):
    maxDiff = None

    def errors(self, *errors):
        return [MypyChecker.adapt_error(e) for e in errors]

    def test_invalid_types(self):
        current = Path('.').absolute()
        filename = Path(__file__).relative_to(current).parent / 'invalid_types.py'
        with filename.open('r', encoding='utf8', errors='surrogateescape') as f:
            lines = f.readlines()
        options = mock.MagicMock()
        options.mypy_config = None
        mpc = MypyChecker(filename=str(filename), lines=lines, options=options)
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
            ),
        )


if __name__ == '__main__':
    unittest.main()
