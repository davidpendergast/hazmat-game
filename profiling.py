import cProfile
import pstats

import cave_defender

if __name__ == "__main__":
    pr = cProfile.Profile(builtins=False)

    pr.enable()

    cave_defender.Hate().start()

    pr.disable()

    sortby = 'cumulative'
    ps = pstats.Stats(pr)
    ps.strip_dirs()
    ps.sort_stats(sortby)
    ps.print_stats(35)
