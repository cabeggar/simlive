from collections import defaultdict

class Trace(object):
    def __init__(self, dir):
        # viewer_id => [position, channel_id, access_id]
        self.viewers = defaultdict(list)
        # channel_id => source
        self.channels = defaultdict(int)
        # timestamp => [[joining channels], [leaving channels], [joining users], [leaving users]]
        self.schedule = defaultdict(list)

        