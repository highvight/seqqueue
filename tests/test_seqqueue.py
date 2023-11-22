import multiprocessing
from queue import Empty, Full
from threading import Thread
from time import sleep
from timeit import default_timer

import pytest

from seqqueue import SeqQueue

__author__ = "Adrian Krueger"
__copyright__ = "Adrian Krueger"
__license__ = "MIT"

Q_TYPES = [SeqQueue, multiprocessing.Manager().SeqQueue]
MAXSIZES = [0, 2, 10]
N_ITEMS = 1000
N_INTERMEDIATE_QUEUES = 10
N_THREADS_PER_QUEUE = 10
MAX_WAIT_TIME_SECONDS = 100

stop_object = -1


def _put_to_next_q(src_q, target_q):
    while True:
        item = src_q.get()
        if item[1] is stop_object:
            target_q.put(item)
            break
        else:
            target_q.put(item)


@pytest.mark.parametrize("q_type", Q_TYPES)
def test_get(q_type):
    q = q_type(maxsize=3)
    q.put((1, "1"))
    q.put((2, "2"))

    three_getters = [Thread(target=lambda: q.get(), daemon=True) for _ in range(3)]
    for thread in three_getters:
        thread.start()
    # Threads should block, no element at 0
    sleep(1)
    assert q.qsize() == 2

    q.put((0, "0"))
    sleep(1)
    assert q.qsize() == 0
    for thread in three_getters:
        thread.join(2)
        assert not thread.is_alive()


@pytest.mark.parametrize("q_type", Q_TYPES)
def test_timeout(q_type):
    q = q_type(maxsize=3)
    q.put((1, "1"), timeout=0.1)
    put_4 = Thread(target=lambda: q.put((4, "4")), daemon=True)
    put_4.start()
    with pytest.raises(Full):
        q.put((3, "3"), timeout=0.1)
    with pytest.raises(Empty):
        q.get(timeout=0.1)
    q.put((0, "0"))
    q.get(timeout=0.1)
    q.put((3, "3"), timeout=0.1)
    q.put((2, "2"), timeout=0.1)
    q.get(timeout=0.1)
    put_4.join(0.1)
    assert not put_4.is_alive()


@pytest.mark.parametrize("q_type", Q_TYPES)
def test_timeout_put_twice(q_type):
    q = q_type(maxsize=1)
    q.put((0, "0"), timeout=0.1)
    with pytest.raises(Full):
        q.put((1, "1"), timeout=0.1)
    with pytest.raises(Full):
        q.put((1, "1"), timeout=0.1)
    q.get()
    q.put((1, "1"), timeout=0.1)
    assert q.get() == (1, "1")


@pytest.mark.parametrize("q_type", Q_TYPES)
@pytest.mark.parametrize("maxsize", MAXSIZES)
def test_random_maxsize(q_type, maxsize):
    items = [(i, "i") for i in range(N_ITEMS)]
    items.extend(
        [(i, stop_object) for i in range(N_ITEMS, N_ITEMS + N_THREADS_PER_QUEUE)]
    )
    qs = [q_type(maxsize) for _ in range(N_INTERMEDIATE_QUEUES)]
    qs.insert(0, q_type(maxsize=0))  # src q
    qs.append(q_type(maxsize=0))  # target q
    for item in items:
        # Fill src q
        qs[0].put(item)

    threads = []
    for i in range(N_INTERMEDIATE_QUEUES + 1):
        for _ in range(N_THREADS_PER_QUEUE):
            thread = Thread(target=_put_to_next_q, args=(qs[i], qs[i + 1]), daemon=True)
            threads.append(thread)

    for thread in threads:
        thread.start()

    start = default_timer()
    while qs[-1].qsize() != len(items):
        assert default_timer() - start < MAX_WAIT_TIME_SECONDS, "Test timeout!"
        sleep(0.1)

    for thread in threads:
        assert not thread.is_alive(), "Threads should be shut down"
    for i in range(len(items)):
        assert qs[-1].get() == items[i], "The final q got mixed up!"
