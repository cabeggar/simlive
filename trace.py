class Trace(object):
    def __init__(self, trace, number_of_nodes):
        data = open(trace, 'r')
        self.map = {"Palo Alto": 0,
                    "Seattle": 1,
                    "San Diego": 2,
                    "Salt Lake City": 3,
                    "Boulder": 4,
                    "Houston": 5,
                    "Lincoln": 6,
                    "Champaign": 7,
                    "Ann Arbor": 8,
                    "Pittsburgh": 9,
                    "Atlanta": 10,
                    "Ithaca": 11,
                    "College Park": 12,
                    "Princeton": 13}
        self.requests = {}
        self.channels = {}

        line = data.readline()
        while line != "":
            seq, cType, cPos, cPosState, cTarget, cTargetState, liveId = line.strip().split(',')
            pos, target = self.map[cPos], self.map[cTarget]
            if cType == "v":
                if liveId not in self.requests:
                    self.requests[liveId] = [0] * number_of_nodes
                self.requests[liveId][pos] += 1
            elif cType == "s":
                self.channels[liveId] = pos
            line = data.readline()

        

        data.close()