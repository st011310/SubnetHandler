import random, os
from test.unit import unitTest

def run():
    for n in range(1, 5):
        for _ in range(n):
            tt_str = random.sample([0,1], 2**n, counts=[2**n, 2**n])
            unitTest(tt_str, os.path.join(os.curdir, "test", "output", ""))