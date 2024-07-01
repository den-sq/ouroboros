from ouroboros.helpers.memory_usage import (
    calculate_gigabytes_in_array,
    calculate_gigabytes_from_dimensions,
)

import numpy as np


def test_calculate_gigabytes_in_array():
    # Create a numpy array with 1 GB size
    array = np.zeros(int(1e9 / np.dtype(np.float64).itemsize))

    # Calculate the expected result
    expected_result = 1.0

    # Call the function and check the result
    assert calculate_gigabytes_in_array(array) == expected_result


def test_calculate_gigabytes_from_dimensions():
    # Define the shape and data type
    shape = (10000, 10000, 100)
    dtype = np.float64

    # Calculate the expected result
    expected_result = 80.0

    # Call the function and check the result
    assert calculate_gigabytes_from_dimensions(shape, dtype) == expected_result
