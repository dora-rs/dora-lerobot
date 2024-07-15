import pyarrow as pa

pa.array([])  # initialize pyarrow array

a = pa.array([i % 256 for i in range(10000)], type=pa.uint8())

