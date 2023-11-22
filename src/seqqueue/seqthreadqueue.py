from heapq import heappop, heappush, heapify
from queue import Empty, Full, Queue, time
from threading import Condition
from typing import Sequence

__author__ = "Adrian Krueger"
__copyright__ = "Adrian Krueger"
__license__ = "MIT"


class SeqQueue(Queue):
    """Priority queue that leaves no item behind!"""

    def __init__(self, maxsize: int = 0, start_index: int = 0) -> None:
        """Create a queue that removes (index, item) pairs in incremental order.

        Args:
            maxsize (int, optional): The maxsize of the queue. If maxsize <= 0, the
                queue size is infinite. Defaults to 0 (infinite).
            start_index (int, optional): The index of the first object on the queue.
                Defaults to 0.
        """
        self._index_shift = start_index
        self._waiting_to_put = []

        super().__init__(maxsize)

    def put(self, item: Sequence, block=True, timeout=None):
        """Put an (index, item) pair into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        # Unlike in standard python queues, put threads hold individual put
        # conditions for their slot. Note that once the slot becomes
        # available, it remains empty until the put finishes, as no other put
        # or get function can close the slot.
        slot_empty = Condition(self.mutex)
        with slot_empty:
            index = item[0]
            if self.maxsize > 0:
                if not block:
                    if not self._slot_empty(index):
                        raise Full
                elif timeout is None:
                    if not self._slot_empty(index):
                        heappush(self._waiting_to_put, (index, slot_empty))
                        slot_empty.wait()  # When notified, it is safe to resume
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    if not self._slot_empty(index):
                        heappush(self._waiting_to_put, (index, slot_empty))
                        slot_empty.wait(timeout)
                        if not self._slot_empty(index):
                            # Remove the condition from the waiters
                            cond_index = self._waiting_to_put.index((index, slot_empty))
                            self._waiting_to_put.pop(cond_index)
                            # Re-heapify waiter queue
                            heapify(self._waiting_to_put)
                            raise Full
            self._put(item)
            self.unfinished_tasks += 1
            # A single put can make 0...maxsize slots available to get
            if self._slot_ready():
                self.not_empty.notify()  # Recursive get calls

    def get(self, block=True, timeout=None) -> Sequence:
        """Remove and return the next (index, item) pair from the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).
        """
        with self.not_empty:
            if not block:
                if not self._slot_ready():
                    raise Empty
            elif timeout is None:
                while not self._slot_ready():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = time() + timeout
                while not self._slot_ready():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._get()

            # A single get can make 0 or 1 slot available to put
            if len(self._waiting_to_put) and self._slot_empty(
                self._waiting_to_put[0][0]
            ):
                heappop(self._waiting_to_put)[1].notify()
            elif self._slot_ready():
                # Another slot might be available from the last put call
                self.not_empty.notify()
            return item

    def _init(self, maxsize: int) -> None:
        self.queue = []

    def _slot_empty(self, index: int) -> bool:
        """Return True, if item with index can be put on queue."""
        return (index - self._index_shift) < self.maxsize

    def _slot_ready(self) -> bool:
        """Return True, if next item can be retrieved from queue."""
        return self._qsize() and self.queue[0][0] - self._index_shift == 0

    def _get(self) -> Sequence:
        item = heappop(self.queue)
        self._index_shift += 1
        return item

    def _put(self, item: Sequence):
        heappush(self.queue, item)

    def _qsize(self) -> int:
        return len(self.queue)
