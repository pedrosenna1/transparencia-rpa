from rq import Queue
from redis import Redis

redis = Redis()
queue = Queue(connection=redis)