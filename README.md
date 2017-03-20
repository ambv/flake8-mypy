# flake8-mypy

[![Build Status](https://travis-ci.org/ambv/flake8-mypy.svg?branch=master)](https://travis-ci.org/ambv/flake8-mypy)

A plugin for [Flake8](http://flake8.pycqa.org/) integrating
[mypy](http://mypy-lang.org/). The idea is to enable limited type
checking as a linter inside editors and other tools that already support
*Flake8* warning syntax and config.

NOTE: This plugin requires *mypy* >=0.500, as of Mar 1st no released
version satisfies this yet.  You can use master in the mean time.


## List of warnings

*flake8-mypy* reserves **T4** for all current and future codes, T being
the natural letter for typing-related errors.  There are other plugins
greedily reserving the entire letter **T**.  To this I say: `¯\_(ツ)_/¯`.

**T400**: any typing note.

**T484**: any typing error (after PEP 484, geddit?).

**T498**: internal *mypy* error.

**T499**: internal *mypy* traceback, stderr output, or an unmatched line.

I plan to support more fine-grained error codes for specific *mypy*
errors in the future.


## Two levels of type checking

*mypy* shines when given a full program to analyze.  You can then use
options like `--follow-imports` or `--disallow-untyped-calls` to
exercise the full transitive closure of your modules, catching errors
stemming from bad API usage or incompatible types.  That being said,
those checks take time, and require access to the entire codebase.  For
some tools, like an editor with an open file, or a code review tool,
achieving this is not trivial.  This is where a more limited approach
inside a linter comes in.

*Flake8* operates on unrelated files, it doesn't perform full program
analysis.  In other words, it doesn't follow imports.  This is a curse
and a blessing.  We cannot find complex problems and the number of
warnings we can safely show without risking false positives is lower.
In return, we can provide useful warnings with great performance, usable
for realtime editor integration.

As it turns out, in this mode of operation, *mypy* is still able to
provide useful information on the annotations within and at least usage
of stubbed standard library and third party libraries.  However, for
best effects, you will want to use separate configuration for *mypy*'s
standalone mode and for usage as a *Flake8* plugin.


## Configuration

Due to the reasoning above, by default *flake8-mypy* will operate with
options equivalent to the following:

```ini
[mypy]
# Specify the target platform details in config, so your developers are
# free to run mypy on Windows, Linux, or macOS and get consistent
# results.
python_version=3.6
platform=linux

# flake8-mypy expects the two following for sensible formatting
show_column_numbers=True
show_error_context=False

# do not follow imports (except for ones found in typeshed)
follow_imports=skip

# suppress errors about unsatisfied imports
ignore_missing_imports=True

# allow untyped calls as a consequence of the options above
disallow_untyped_calls=False

# allow returning Any as a consequence of the options above
warn_return_any=False

# treat Optional per PEP 484
strict_optional=True

# ensure all execution paths are returning
warn_no_return=True

# lint-style cleanliness for typing
warn_redundant_casts=True
warn_unused_ignores=True

# The following are off by default.  Flip them on if you feel
# adventurous.
disallow_untyped_defs=False
check_untyped_defs=False
```

If you disagree with the defaults above, you can specify your own *mypy*
configuration by providing the `--mypy-config=` command-line option to
*Flake8* (with the .flake8/setup.cfg equivalent being called
`mypy_config`). The value of that option should be a path to a mypy.ini
or setup.cfg compatible file.  For full configuration syntax, follow
[mypy documentation](http://mypy.readthedocs.io/en/latest/config_file.html).

For the sake of simplicity and readability, the config you provide will
fully replace the one listed above.  Values left out will be using
*mypy*'s own defaults.

Remember that for the best user experience, your linter integration mode
shouldn't generally display errors that a full run of *mypy* wouldn't.
This would be confusing.

Note: chaing the `follow_imports` option might have surprising effects.
If the file you're linting with Flake8 has other files around it, then in
"silent" or "normal" mode those files will be used to follow imports.
This includes imports from [typeshed](https://github.com/python/typeshed/).


## Tests

Just run:

```
python setup.py test
```

## OMG, this is Python 3 only!

Yes, so is *mypy*.  Relax, you can run *Flake8* with all popular plugins
**as a tool** perfectly fine under Python 3.5+ even if you want to
analyze Python 2 code.  This way you'll be able to parse all of the new
syntax supported on Python 3 but also *effectively all* the Python 2
syntax at the same time.

By making the code exclusively Python 3.5+, I'm able to focus on the
quality of the checks and re-use all the nice features of the new
releases (check out [pathlib](docs.python.org/3/library/pathlib.html))
instead of wasting cycles on Unicode compatibility, etc.


## License

MIT


## Change Log

### 17.3.3

* suppress *mypy* messages about relative imports

### 17.3.2

* bugfix: using *Flake8* with absolute paths now correctly matches *mypy*
  messages

* bugfix: don't crash on relative imports in the form `from . import X`

### 17.3.1

* switch `follow_imports` from "silent" to "skip" to avoid name clashing
  files being used to follow imports within
  [typeshed](https://github.com/python/typeshed/)

* set MYPYPATH by default to give stubs from typeshed higher priority
  than local sources

### 17.3.0

* performance optimization: skip running *mypy* over files that contain
  no annotations or imports from `typing`

* bugfix: when running over an entire directory, T484 is now correctly
  used instead of T499

### 17.2.0

* first published version

* date-versioned


## Authors

Glued together by [Łukasz Langa](mailto:lukasz@langa.pl).
