# BSD 4-Clause License

# Copyright (c) 2021, University of Rome Tor Vergata
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * All advertising materials mentioning features or use of this software
#    must display the following acknowledgement: This product includes
#    software developed by University of Rome Tor Vergata and its contributors.
#  * Neither the name of University of Rome Tor Vergata nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import random
import os
from concurrent.futures import ThreadPoolExecutor, wait
import jsonmerge
import string
import logging
import time

logger = logging.getLogger(__name__)

params_processed = False
params = dict()

def cpu_loader_job(params):
    """
    Compute pi N times to X decimals, where X is between params

    range_complexity[0] and range_complexity[1]

    and N is params["trials"]
    """
    cpu_load = random.randint(params["range_complexity"][0], params["range_complexity"][1])
    trials = int(params["trials"])

    for x in range(trials):
        pi_greco = list()
        q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
        counter = 0
        while True:
            if 4 * q + r - t < m * t:
                # yield m
                pi_greco.append(str(m))
                q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))//t - 10*m, x
                if counter > cpu_load-1:
                    break
                else:
                    counter = counter+1
            else:
                q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)//(t*x), x+2
        #print("Service complexity: %d - Number of cycles for pi computation: %d" % (cpu_load, cpu_load + 1))
        # print(f"Value: 3.{''.join(pi_greco[1:])}\n")

def cpu_loader(params):
    """
    Run cpu_loader_job X times in parallel, where

    X = params["thread_pool_size"]
    """
    start_time = time.time()
    logging.debug("CPU stress start")
    pool_size = int(params["thread_pool_size"])
    pool = ThreadPoolExecutor(pool_size)
    futures = list()
    for thread in range(pool_size):
        futures.append(pool.submit(cpu_loader_job, params))
    pool.shutdown()
    run_duration_millis = (time.time() - start_time) * 1000
    logging.debug(f"CPU stress took {run_duration_millis} millis")
    return

def bandwidth_loader(params):
    logging.debug("Creating random response")
    bandwidth_load = random.expovariate(1 / params["mean_response_size"])
    num_chars = int(max(1, 1000 * bandwidth_load))  # Response in kB
    response_body = ''.join(random.choice(string.ascii_letters) for i in range(num_chars))
    return response_body

def memory_loader(params):
    """
    Read and write X times into a buffer of size N

    X = params["memory_io"]

    N = params["memory_size"]
    """
    start_time = time.time()
    logging.debug("Memory stress start")
    memory_size = params["memory_size"]
    memory_io = params["memory_io"]
    
    # allocate memory_size kB of memory
    dummy_buffer = ['A' * 1000 for _ in range(0, int(memory_size))]
    
    for i in range(0, int(memory_io)):
        v = dummy_buffer[i % int(memory_size)]  # read operation
        dummy_buffer[i % int(memory_size)] = ['A' * 1000] # write operation
    run_duration_millis = (time.time() - start_time) * 1000
    logging.debug(f"Memory stress took {run_duration_millis} millis")
    del dummy_buffer
    return

def disk_loader(params):
        write_start_time = time.time()
        # logging.debug("Disk stress - Write start")
        filename_base = params["tmp_file_name"]
        rnd_str = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        filename = f"{rnd_str}-{filename_base}"
        blocks_count = params["disk_write_block_count"]
        block_size = params["disk_write_block_size"]
        f = os.open(filename, os.O_CREAT | os.O_WRONLY, 0o777)  # low-level I/O
        for i in range(blocks_count):
            buff = os.urandom(block_size)
            os.write(f, buff)
        os.fsync(f)  # force write to disk
        os.close(f)
        write_duration_millis = (time.time() - write_start_time) * 1000
        logging.debug(f"Disk stress - Write took {write_duration_millis} millis")

        read_start_time = time.time()
        # logging.debug("Disk stress - Read start")
        f = os.open(filename, os.O_RDONLY, 0o777)  # low-level I/O
        # generate random read positions
        offsets = list(range(0, blocks_count * block_size, block_size))
        random.shuffle(offsets)

        for i, offset in enumerate(offsets, 1):
            os.lseek(f, offset, os.SEEK_SET)  # set position
            buff = os.read(f, block_size)  # read from position
            if not buff: break  # if EOF reached
        os.close(f)
        read_duration_millis = (time.time() - read_start_time) * 1000
        logging.debug(f"Disk stress - Read took {read_duration_millis} millis")
        logging.debug(f"Disk stress - TOTAL took {read_duration_millis + write_duration_millis} millis")
        os.remove(filename)
        return

def loader(input_params):
    global params_processed, params

    if not params_processed:
        default_params = {
            "cpu_stress": {"run":False,"range_complexity": [100, 100], "thread_pool_size": 1, "trials": 1},
            "memory_stress":{"run":False, "memory_size": 10000, "memory_io": 1000},
            "disk_stress":{"run":False,"tmp_file_name":  "mubtestfile.txt", "disk_write_block_count": 1000, "disk_write_block_size": 1024},
            "mean_response_size": 11}

        params = jsonmerge.merge(default_params,input_params)
        if "mean_bandwidth" in params:
            # for backward compatibility
            params["mean_response_size"] = params["mean_bandwidth"]
        params_processed = True
    loader_count = 3
    pool = ThreadPoolExecutor(loader_count)
    start_time = time.time()
    logging.debug("Loader start")
    if params['cpu_stress']['run']:
        pool.submit(cpu_loader, params['cpu_stress'])
    if params['memory_stress']['run']:
        pool.submit(memory_loader, params['memory_stress'])
    if params['disk_stress']['run']:
        pool.submit(disk_loader, params['disk_stress'])
    pool.shutdown()
    run_duration_millis = (time.time() - start_time) * 1000
    logging.info(f"Loader took {run_duration_millis} millis")
    body = bandwidth_loader(params)
    return body

if __name__ == '__main__':
    loader({})