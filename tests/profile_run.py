import cProfile
import pstats


PROF_FILE = '/tmp/mypy-profile.prof'


pr = cProfile.Profile()
try:
    pr.enable()
    from flake8.main import cli
    cli.main()
finally:
    pr.disable()
    pr.dump_stats(PROF_FILE)
    ps = pstats.Stats(PROF_FILE)
    ps.sort_stats('cumtime')
    ps.print_stats()
