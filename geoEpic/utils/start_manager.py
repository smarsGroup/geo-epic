import os
from multiprocessing.managers import BaseManager
import queue

class QueueManager(BaseManager):
    """ Custom manager for managing queues across different processes. """
    pass

shared_queues = {}

def get_pool_queue(name):
    if name not in shared_queues:
        shared_queues[name] = queue.Queue()
    return shared_queues[name]

def is_new_queue(name):
    return name not in shared_queues

manager = QueueManager(address=('', 50001), authkey=b'abc123')
manager.register('get_pool_queue', get_pool_queue)
manager.register('is_new_queue', is_new_queue)
server = manager.get_server()
print(f"Server started at PID {os.getpid()}...")
server.serve_forever()
