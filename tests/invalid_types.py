import os
from typing import List


def no_return_value() -> int:
    print("Forgot to actually return!")


def call_stdlib_and_wrong_type() -> str:
    return os.getpid() + " is my PID"


def main():
    for num in range(100):
        print()


if __name__ == '__main__':
    main()
