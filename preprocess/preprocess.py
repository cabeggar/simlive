import os
from collections import defaultdict
import random

def get_ttl():
    return 1

map = {"New York": 0, "Atlanta": 1, "Chicago": 2, "San Francisco": 3, "Los Angeles": 4, "Salt Lake City": 5, "Miami": 6, "Kaiserslautern": 7, "Austin": 8}
channels = defaultdict(bool)
viewer_seq = 0
viewer_set = [[defaultdict(list) for _ in xrange(len(map))] for _ in xrange(len(map))]
viewer_ttl = defaultdict(int)

trace_no = 1
while True:
    read_path = '../trace/' + str(trace_no)
    write_path = '../new_trace/' + str(trace_no)
    if os.path.isfile(read_path):
        trace = open(read_path, 'r')
        new_trace = open(write_path, 'w+')
        line = trace.readline()
        for channel in channels:
            channels[channel] = False
        request = [[defaultdict(int) for _ in xrange(len(map))] for _ in xrange(len(map))]
        while line != "":
            seq, cType, cPos, cTarget, liveId = line.strip().split(',')
            pos, target = map[cPos], map[cTarget]
            if cType == "s":
                if liveId not in channels:
                    new_trace.write('{},s,i,{},{},{}\n'.format(liveId, pos, target, liveId))
                channels[liveId] = True
            elif cType == "v":
                request[pos][target][liveId] += 1
            line = trace.readline()
        for channel in channels:
            if not channels[channel]:
                new_trace.write('{},s,o,-1,-1,{}\n'.format(channel, channel))
                for i in xrange(len(viewer_set)):
                    for j in xrange(len(viewer_set[0])):
                        if channel in viewer_set[i][j]:
                            for viewer_id in viewer_set[i][j][channel]:
                                del viewer_ttl[viewer_id]
                                new_trace.write('{},v,o,{},{},{}\n'.format(viewer_id, i, j, channel))
                            del viewer_set[i][j][channel]
            else:
                channels[channel] = False
        for i in xrange(len(viewer_set)):
            for j in xrange(len(viewer_set[0])):
                for channel, viewer_list in viewer_set[i][j].iteritems():
                    to_remove = []
                    for viewer_id in viewer_list:
                        if viewer_ttl[viewer_id] == 1:
                            to_remove.append(viewer_id)
                        else:
                            viewer_ttl[viewer_id] -= 1
                    for viewer_id in to_remove:
                        viewer_list.remove(viewer_id)
                        del viewer_ttl[viewer_id]
                        new_trace.write('{},v,o,{},{},{}\n'.format(viewer_id, i, j, channel))
        for i in xrange(len(request)):
            for j in xrange(len(request[0])):
                for channel, request_no in request[i][j].iteritems():
                    viewer_list = viewer_set[i][j][channel]
                    if request_no == len(viewer_list):
                        continue
                    elif request_no < len(viewer_list):
                        while request_no < len(viewer_list):
                            to_remove = random.choice(viewer_list)
                            viewer_list.remove(to_remove)
                            del viewer_ttl[to_remove]
                            new_trace.write('{},v,o,{},{},{}\n'.format(to_remove, i, j, channel))
                    else:
                        for _ in xrange(request_no - len(viewer_list)):
                            viewer_list.append(viewer_seq)
                            viewer_ttl[viewer_seq] = get_ttl()
                            new_trace.write('{},v,i,{},{},{}\n'.format(viewer_seq, i, j, channel))
                            viewer_seq += 1
        print '{} done'.format(read_path)
        new_trace.close()
        trace_no += 1
    else:
        print "END"
        break