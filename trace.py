class Trace(object):
    def __init__(self, trace, number_of_nodes):
        data = open(trace, 'r')
        self.map = {"New York": 0, "Atlanta": 1, "Chicago": 2, "San Francisco": 3, "Los Angeles": 4, "Salt Lake City": 5, "Miami": 6, "Kaiserslautern": 7, "Austin": 8}
        self.requests = {}
        self.channels = {}

        line = data.readline()
        while line != "":
            seq, cType, cPos, cTarget, liveId = line.strip().split(',')
            pos, target = self.map[cPos], self.map[cTarget]
            if cType == "v":
                if liveId not in self.requests:
                    self.requests[liveId] = [0] * number_of_nodes
                self.requests[liveId][pos] += 1
            elif cType == "s":
                self.channels[liveId] = pos
            line = data.readline()

        

        data.close()