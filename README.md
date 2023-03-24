# SeqQueue

Python queue implementations for incrementally indexed, sequential data. SeqQueue makes sure any `get()` call returnes the next `(index, item)` pair from the queue.

## Installation

```bash
pip3 install seqqueue
```

Install from source:
```bash
git clone https://github.com/highvight/seqqueue
cd seqqueue
pip3 install .
```

To run tests and benchmarks:

```bash
pip3 install .[testing]
```
Or just copy and paste and one of the classes to your project

## Usage

```python
from seqqueue import SeqQueue

q = SeqQueue(start_index=0)
q.put((1, "1"))
q.put((2, "2"))
q.put((0, "0"))
print(q.get())  # (0, "0")
print(q.get())  # (1, "1")
print(q.get())  # (2, "2")
```

Note that Empty and Full exceptions are raised with respect to the index

```python
from seqqueue import SeqQueue

q = SeqQueue(start_index=0, maxsize=2)
q.put((1,"1"))
print(q.qsize())  # 1
q.get(block=False)  #  Raises Empty, index=0 not available
q.put((2,"2"), block=False)  #  Raises Full, index=2 > maxindex
```

For multiprocessing, use `multiprocessing.Manager`

```python
import multiprocessing as mp

from seqqueue import SeqQueue

manager = mp.Manager()
q = manager.SeqQueue(start_index=0)
```

## Benchmark
Make sure to install `[testing]` (see Usage). In the project root run:

```python
pytest benchmark
```

This will run some benchmarks for concurrent `put()` and `get()` calls in comparison to `PriorityQueue` from the standard library. As you can see, depending on the number of threads and maxsize of the queue, keeping incremental index order comes at a cost. For instance, for a `maxsize=8` and `n_threads=[1,2,20]`, on my Laptop, SeqQeue is ~ 2x-3x slower:

|                | put=1, get=1   | put=2, get=2   | put=20, get=20  |
|----------------|----------------|----------------|-----------------|
| PriorityQueue | 31.8575 (1.0)  | 56.9946 (1.79) | 76.1026 (2.39)  |
| SeqQeue        | 59.4795 (1.87) | 82.9272 (2.60) | 197.6096 (6.20) |

If you find faster implementations please open a MR!

*In real-world applications the costs of queue management are often negligible. Adjust the benchmark scripts with your real data and thread target functions to find out :)* 

## License

[MIT](https://choosealicense.com/licenses/mit/)