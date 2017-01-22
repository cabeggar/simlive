from newtrace import Trace
import pickle

trace = Trace('trace/')
with open('new_trace', 'w+') as output:
    pickle.dump(trace, output)