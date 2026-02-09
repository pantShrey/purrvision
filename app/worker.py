from redis import Redis
from rq import Worker, Queue
from app.database import engine # Loads DB models

# Define which queues to listen to
listen = ['default']

# Create the Redis connection explicitly
redis_conn = Redis(host='localhost', port=6379)

if __name__ == '__main__':
    print("Worker started. Listening for tasks...")
    
    # 1. Create the Queue explicitly with the connection
    queue = Queue('default', connection=redis_conn)
    
    # 2. Create the Worker explicitly with the connection
    worker = Worker([queue], connection=redis_conn)
    
    # 3. Start working
    worker.work()