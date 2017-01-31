from collections import defaultdict
import os
import random


class Trace(object):
    def __init__(self, dir):
        # viewer_id => [position, channel_id, access_id]
        self.viewers = defaultdict(list)
        # channel_id => source
        self.channels = defaultdict(int)
        # timestamp => [[joining channels], [leaving channels], [joining users], [leaving users]]
        self.schedule = [[] for _ in xrange(20)]
        # read from traces in a directory
        self._read_from_directory(dir)

    def _get_expovariate_ttl(self):
        return int(random.expovariate(0.5)+1)

    def _get_uniform_ttl(self):
        return int(random.uniform(1, 20))

    def _read_from_directory(self, dir):
        # prepare temporary data structures
        map = {"Palo Alto": 0,
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
        channels = defaultdict(bool)
        viewer_seq = 0
        viewer_set = [defaultdict(list) for _ in xrange(len(map))]
        viewer_ttl = defaultdict(int)

        trace_no = 0
        while True:
            read_path = str(dir) + str(trace_no+1)
            if not os.path.isfile(read_path):
                print "END"
                break

            # Initialize schedule for current timestamp
            self.schedule[trace_no] = [[], [], [], []]

            request = [defaultdict(int) for _ in xrange(len(map))]

            trace = open(read_path, 'r')
            line = trace.readline()
            while line != "":
                seq, cType, cPos, cPosState, cTarget, cTargetState, liveId = line.strip().split(',')
                pos, target = map[cPos], map[cTarget]
                if cType == "s":
                    if liveId not in channels:
                        # Append new channel
                        self.schedule[trace_no][0].append(liveId)
                        self.channels[liveId] = pos
                    channels[liveId] = True
                elif cType == "v":
                    request[pos][liveId] += 1
                line = trace.readline()

            for channel in channels:
                if not channels[channel]:
                    # Leaving channel
                    self.schedule[trace_no][1].append(channel)
                    # Leaving viewer who are watching leaving channel
                    for i in xrange(len(viewer_set)):
                        if channel in viewer_set[i]:
                            for viewer_id in viewer_set[i][channel]:
                                del viewer_ttl[viewer_id]
                                self.schedule[trace_no][3].append(viewer_id)
                            del viewer_set[i][channel]
            for channel in self.schedule[trace_no][1]:
                del channels[channel]

            for i in xrange(len(viewer_set)):
                for channel, viewer_list in viewer_set[i].iteritems():
                    to_remove = []
                    for viewer_id in viewer_list:
                        if viewer_ttl[viewer_id] == 1:
                            # If viewer has only 1 round left
                            to_remove.append(viewer_id)
                        else:
                            # Decrease viewer TTL
                            viewer_ttl[viewer_id] -= 1
                    for viewer_id in to_remove:
                        # Leaving viewer
                        viewer_list.remove(viewer_id)
                        del viewer_ttl[viewer_id]
                    self.schedule[trace_no][3] += to_remove

            for i in xrange(len(request)):
                for channel, request_no in request[i].iteritems():
                    viewer_list = viewer_set[i][channel]
                    if request_no == len(viewer_list):
                        # No need to increase or remove viewers
                        continue
                    elif request_no < len(viewer_list):
                        # Need to remove viewers
                        while request_no < len(viewer_list):
                            to_remove = random.choice(viewer_list)
                            viewer_list.remove(to_remove)
                            del viewer_ttl[to_remove]
                            self.schedule[trace_no][3].append(to_remove)
                    else:
                        # Need to add new viewers
                        for _ in xrange(request_no - len(viewer_list)):
                            viewer_list.append(viewer_seq)
                            viewer_ttl[viewer_seq] = self._get_expovariate_ttl()
                            self.schedule[trace_no][2].append(viewer_seq)
                            self.viewers[viewer_seq] = [i, channel, None]
                            viewer_seq += 1

            # Set all channel to expiring as default in this round
            for channel in channels:
                channels[channel] = False

            print "{} done".format(read_path)
            trace_no += 1