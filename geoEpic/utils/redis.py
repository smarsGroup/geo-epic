import os
import shutil
import redis
import shortuuid


class WorkerPool:
    def __init__(self, max_resources, pool_key=None, base_dir=None, host='localhost', port=6379, db=0):
        self.max_resources = max_resources
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.pool_key = pool_key or f"worker_pool_{shortuuid.uuid()}"
        self.base_dir = base_dir

        if self.base_dir:
            os.makedirs(self.base_dir, exist_ok=True)

        self.redis.delete(self.pool_key)  # Clear any existing entries in Redis
        self.initialize_resources()

    def initialize_resources(self):
        """Initialize resources and add them to the Redis queue."""
        if self.base_dir:
            os.makedirs(self.base_dir, exist_ok=True)

        # Loop to create each resource and push to Redis
        for i in range(self.max_resources):
            if self.base_dir:
                resource = os.path.join(self.base_dir, str(i))
                os.makedirs(resource, exist_ok=True)
            else: resource = str(i)
            
            # Push the resource to the Redis queue
            self.redis.rpush(self.pool_key, resource)

    def acquire(self):
        """Acquire a resource by blocking until one is available."""
        _, resource = self.redis.blpop(self.pool_key)
        return resource.decode('utf-8')

    def release(self, resource):
        """Release a resource back to the pool."""
        self.redis.rpush(self.pool_key, resource)

    def close(self):
        """Remove all resources from the pool, deleting directories if applicable."""
        while not self.redis.llen(self.pool_key) == 0:
            resource = self.redis.lpop(self.pool_key).decode('utf-8')
            if self.base_dir and os.path.exists(resource):
                shutil.rmtree(resource, ignore_errors=True)