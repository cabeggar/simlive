from newtrace import Trace
import pickle

trace = Trace('trace/')
with open('new_trace_pickle', 'w+') as output:
    pickle.dump(trace, output)