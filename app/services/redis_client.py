# import redis
# from app.core.config import settings

# redis_client=redis.Redis(
#         host=settings.REDIS_HOST,
#         db=settings.REDIS_DB,
#         password=settings.REDIS_PASSWORD,
#         port=settings.REDIS_PORT
#         )

import multiprocessing
import queue
import uuid


# --- Start of user's multiprocessing-safe FakeRedis classes ---
class FakePubSub:
    """
    A multiprocessing-safe PubSub client.
    Each instance has its own unique ID and a local queue for messages.
    """
    def __init__(self, store):
        self.store = store
        self.subscriptions = set()
        self.closed = False
        self._unique_id = str(uuid.uuid4())
        self.local_queue = self.store._manager.Queue()

    def subscribe(self, *channels):
        """Subscribes this client to one or more channels."""
        with self.store._lock:
            for channel in channels:
                if channel not in self.store._subscribers:
                    self.store._subscribers[channel] = self.store._manager.list()
                
                # Add this client's unique ID to the list of subscribers for the channel
                self.store._subscribers[channel].append(self._unique_id)
                self.subscriptions.add(channel)

            # Store the local queue in the shared dictionary, mapped by unique ID
            self.store._queues[self._unique_id] = self.local_queue

    def unsubscribe(self, *channels):
        """Unsubscribes this client from one or more channels."""
        with self.store._lock:
            for channel in channels:
                if channel in self.subscriptions:
                    if self._unique_id in self.store._subscribers.get(channel, []):
                        # Remove our unique ID from the list of subscribers
                        self.store._subscribers[channel].remove(self._unique_id)
                    self.subscriptions.discard(channel)

    def get_message(self, timeout=0.1):
        """Polls for messages from the local queue."""
        if self.closed:
            return None
        try:
            data = self.local_queue.get(timeout=timeout)
            # The data put into the queue already has the channel info
            return data
        except queue.Empty:
            return None
        except Exception as e:
            print(f"Error getting message from local queue: {e}")
        return None

    def close(self):
        self.closed = True
        # Clean up subscriptions and shared queue reference
        with self.store._lock:
            for channel in list(self.subscriptions):
                if self._unique_id in self.store._subscribers.get(channel, []):
                    self.store._subscribers[channel].remove(self._unique_id)
            self.store._queues.pop(self._unique_id, None)


class FakeRedis:
    """
    A fake, multiprocessing-safe Redis client using Manager data structures.
    This version correctly handles multiple subscribers per channel.
    """
    def __init__(self, manager=None):
        ctx = multiprocessing.get_context("spawn")
        self._manager = manager or multiprocessing.Manager()
        self._data = self._manager.dict()
        self._lists = self._manager.dict()
        self._lock = self._manager.Lock()
        
        # New structure for Pub/Sub
        self._subscribers = self._manager.dict() # channel -> list of unique_ids
        self._queues = self._manager.dict()      # unique_id -> shared_queue

    # Key/Value operations
    def set(self, key, value):
        with self._lock:
            self._data[key] = value
            return True

    def get(self, key):
        with self._lock:
            return self._data.get(key)

    # Pub/Sub operations
    def pubsub(self):
        return FakePubSub(self)

    def publish(self, channel, message):
        """Publishes a message to all subscribers of a channel."""
        with self._lock:
            # Check if there are any subscribers for this channel
            subscriber_ids = self._subscribers.get(channel, [])
            if not subscriber_ids:
                return 0

            # Iterate over a copy of the list to avoid issues if a client unsubscribes
            count = 0
            for uid in list(subscriber_ids):
                # Get the shared queue for this subscriber's unique ID
                q = self._queues.get(uid)
                if q:
                    # Put the message in the subscriber's private queue
                    q.put({"type": "message", "channel": channel, "data": message})
                    count += 1
            return count

# --- End of user's multiprocessing-safe FakeRedis classes ---

# Create a shared multiprocessing manager and a single FakeRedis instance.
manager = multiprocessing.Manager()
redis_client = FakeRedis(manager=manager)