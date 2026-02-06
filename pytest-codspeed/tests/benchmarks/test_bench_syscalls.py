import concurrent.futures
import mmap
import multiprocessing
import os
import socket
from socket import gethostbyname
from tempfile import NamedTemporaryFile
from time import sleep

import pytest


@pytest.mark.parametrize("sleep_time", [0.001, 0.01, 0.05, 0.1])
def test_sleep(benchmark, sleep_time):
    benchmark(sleep, sleep_time)


@pytest.mark.parametrize("array_size", [100, 1_000, 10_000, 100_000])
def test_array_alloc(benchmark, array_size):
    benchmark(lambda: [0] * array_size)


@pytest.mark.parametrize("num_fds", [10, 100, 1000])
def test_open_close_fd(benchmark, num_fds):
    def open_close_fds():
        fds = [os.open("/dev/null", os.O_RDONLY) for _ in range(num_fds)]
        for fd in fds:
            os.close(fd)

    benchmark(open_close_fds)


def test_dup_fd(benchmark):
    def dup_fd():
        fd = os.open("/dev/null", os.O_RDONLY)
        new_fd = os.dup(fd)
        os.close(new_fd)
        os.close(fd)

    benchmark(dup_fd)


@pytest.mark.parametrize("content_length", [100, 1000, 10_000, 100_000, 1_000_000])
def test_fs_write(benchmark, content_length):
    content = "a" * content_length
    f = NamedTemporaryFile(mode="w")

    @benchmark
    def write_to_file():
        f.write(content)
        f.flush()

    f.close()


@pytest.mark.parametrize("content_length", [100, 1000, 10_000, 100_000, 1_000_000])
def test_fs_read(benchmark, content_length):
    with open("/dev/urandom", "rb") as f:
        benchmark(f.read, content_length)


@pytest.mark.parametrize(
    "host",
    ["localhost", "127.0.0.1", "1.1.1.1", "8.8.8.8", "google.com", "amazon.com"],
)
def test_hostname_resolution(benchmark, host):
    benchmark(gethostbyname, host)


@pytest.mark.parametrize(
    "host, port",
    [("8.8.8.8", 53), ("1.1.1.1", 53), ("google.com", 443), ("wikipedia.org", 443)],
)
def test_tcp_connection(benchmark, host, port):
    def connect():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
        finally:
            sock.close()

    benchmark(connect)


@pytest.mark.parametrize("command", ["echo hello", "ls -l", "cat /dev/null"])
def test_process_creation(benchmark, command):
    def create_process():
        process = os.popen(command)
        process.read()
        process.close()

    benchmark(create_process)


@pytest.mark.parametrize("message_size", [10, 100, 1000, 10000])
def test_pipe_communication(benchmark, message_size):
    def pipe_comm():
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:  # child process
            os.close(r)
            os.write(w, b"x" * message_size)
            os._exit(0)
        else:  # parent process
            os.close(w)
            os.read(r, message_size)
            os.waitpid(pid, 0)
            os.close(r)

    benchmark(pipe_comm)


@pytest.mark.parametrize("map_size", [4096, 40960, 409600])
def test_mmap_operation(benchmark, map_size):
    # Create a temporary file outside the benchmarked function
    temp_file = NamedTemporaryFile(mode="w+b", delete=False)
    temp_file.write(b"\0" * map_size)
    temp_file.flush()
    temp_file.close()

    mfd = os.open(temp_file.name, os.O_RDONLY)

    def mmap_op():
        mm = mmap.mmap(mfd, map_size, access=mmap.ACCESS_READ)
        mm.read(map_size)

    benchmark(mmap_op)
    os.close(mfd)


def multi_task(x):
    """Multiprocessing need this function to be defined at the top level."""
    return x * x


@pytest.mark.parametrize("num_tasks", [10, 100, 1000, 10000, 100000])
def test_threadpool_map(benchmark, num_tasks):
    def threadpool_map():
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(multi_task, range(num_tasks)))

    benchmark(threadpool_map)


@pytest.mark.parametrize("num_tasks", [10, 100, 1000, 10000, 100000])
def test_multiprocessing_map(benchmark, num_tasks):
    def multiprocessing_map():
        with multiprocessing.Pool(processes=8) as pool:
            list(pool.map(multi_task, range(num_tasks)))

    benchmark(multiprocessing_map)
