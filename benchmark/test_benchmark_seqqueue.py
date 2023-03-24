import multiprocessing as mp
from collections import deque
from queue import PriorityQueue
from threading import Thread

import pytest

from seqqueue import SeqQueue

__author__ = "Adrian Krueger"
__copyright__ = "Adrian Krueger"
__license__ = "MIT"

# Multi-thread benchmark config
Q_TYPES = [SeqQueue, PriorityQueue]
N_THREADS = [1, 2, 20]
MAXSIZES = [0, 2, 8]
N_ITEMS = 5000
ROUNDS = 50

# Multi-processing benchmark config
manager = mp.Manager()
Q_TYPES_MP = [manager.SeqQueue, manager.Queue]
N_PROCESSES = [0, 2, 10]
MAXSIZES_MP = [2, 8]
N_ITEMS_MP = 500
ROUNDS_MP = 10


_stop_object = -1


def _multi_thread(items, queue, n_threads):
    def put_func():
        while True:
            try:
                queue.put(items.popleft())
            except IndexError:
                break

    def get_func():
        while queue.get()[1] is not _stop_object:
            continue

    put_threads = [Thread(target=put_func, daemon=True) for _ in range(n_threads)]
    get_threads = [Thread(target=get_func, daemon=True) for _ in range(n_threads)]

    for get_thread, put_thread in zip(get_threads, put_threads):
        get_thread.start()
        put_thread.start()
    for thread in get_threads:
        thread.join()


def _multi_process(items, queue, n_processes):
    def put_func():
        while True:
            try:
                item = items.pop(0)
                queue.put(item)
            except IndexError:
                break

    def get_func():
        while queue.get()[1] is not _stop_object:
            continue

    put_processes = [
        mp.Process(target=put_func, daemon=True) for _ in range(n_processes)
    ]
    get_processes = [
        mp.Process(target=get_func, daemon=True) for _ in range(n_processes)
    ]

    for get_process, put_process in zip(get_processes, put_processes):
        get_process.start()
        put_process.start()
    for get_process in get_processes:
        get_process.join()


@pytest.mark.parametrize("q_type", Q_TYPES)
@pytest.mark.parametrize("n_threads", N_THREADS)
@pytest.mark.parametrize("maxsize", MAXSIZES)
def test_multi_thread(benchmark, q_type, n_threads, maxsize):
    def setup():
        items = deque([(i, i) for i in range(N_ITEMS)])
        items.extend([(i, _stop_object) for i in range(N_ITEMS, N_ITEMS + n_threads)])
        queue = q_type(maxsize=maxsize)
        return (items, queue, n_threads), {}

    benchmark.pedantic(_multi_thread, setup=setup, rounds=ROUNDS)


@pytest.mark.parametrize("q_type", Q_TYPES_MP)
@pytest.mark.parametrize("n_processes", N_PROCESSES)
@pytest.mark.parametrize("maxsize", MAXSIZES_MP)
def test_multi_process(benchmark, q_type, n_processes, maxsize):
    def setup():
        items = manager.list([(i, i) for i in range(N_ITEMS_MP)])
        items.extend(
            [(i, _stop_object) for i in range(N_ITEMS_MP, N_ITEMS_MP + n_processes)]
        )
        queue = q_type(maxsize=maxsize)
        return (items, queue, n_processes), {}

    benchmark.pedantic(_multi_process, setup=setup, rounds=ROUNDS_MP)
