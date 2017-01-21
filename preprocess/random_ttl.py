import random

class RandomTTL(object):
    def __init__(self, mode):
        if type(mode) != type(1) or mode < 1 or mode > 2:
            raise Exception('Wrong Argument!')
        self.mode = mode

    def get_random_ttl(self, x, y, z):
        if self.mode == 1:
            return int(random.uniform(x, y))
        elif self.mode == 2:
            return int(random.expovariate(x))