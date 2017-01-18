import random

class RandomTTL(object):
    def __init__(self, mode):
        if type(mode) != type(1) or mode < 1 or mode > 11:
            raise Exception('Wrong Argument!')
        self.mode = mode

    def get_random_ttl(self, x, y, z):
        if self.mode == 1:
            return int(random.uniform(x, y))
        elif self.mode == 2:
            return int(random.triangular(x, y, z))
        elif self.mode == 3:
            return int(random.betavariate(x, y))
        elif self.mode == 4:
            return int(random.expovariate(x))
        elif self.mode == 5:
            return int(random.gammavariate(x, y))
        elif self.mode == 6:
            return int(random.gauss(x, y))
        elif self.mode == 7:
            return int(random.lognormvariate(x, y))
        elif self.mode == 8:
            return int(random.normalvariate(x, y))
        elif self.mode == 9:
            return int(random.vonmisesvariate(x, y))
        elif self.mode == 10:
            return int(random.paretovariate(x))
        else:
            return int(random.weibullvariate(x, y))