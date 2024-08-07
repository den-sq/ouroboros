from ouroboros.helpers.memory_usage import (
    GIGABYTE,
    calculate_chunk_size,
    calculate_gigabytes_in_array,
    calculate_gigabytes_from_dimensions,
)

import numpy as np


def test_calculate_gigabytes_in_array():
    # Create a numpy array with 1 GB size
    array = np.zeros(int((GIGABYTE) / np.dtype(np.float64).itemsize), dtype=np.float64)

    # Calculate the expected result
    expected_result = 1.0

    # Call the function and check the result
    assert calculate_gigabytes_in_array(array) == expected_result


def test_calculate_gigabytes_from_dimensions():
    # Define the shape and data type
    shape = (1024, 1024, 1024)
    dtype = np.float64

    # Calculate the expected result
    expected_result = 8 * 1

    # Call the function and check the result
    assert calculate_gigabytes_from_dimensions(shape, dtype) == expected_result


def test_calculate_chunk_size():
    shape = (1024, 1024, 1024)
    dtype = np.float64
    max_ram_gb = 8
    expected_chunk_size = 1024  # Expected result based on the function logic
    assert calculate_chunk_size(shape, dtype, max_ram_gb) == expected_chunk_size

    shape = (1024, 1024, 1024)
    dtype = np.float64
    max_ram_gb = 0
    expected_chunk_size = 1  # Expected result based on the function logic
    assert calculate_chunk_size(shape, dtype, max_ram_gb) == expected_chunk_size
