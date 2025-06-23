import numpy as np

from ouroboros.helpers.util import unique_lv


def test_unique():
    data = (np.random.randint(0, 5, 300) * 2).reshape(3, 100)

    result, counts = np.unique(data, False, False, True, axis=1)

    lv_result, lv_counts = unique_lv(data, return_counts=True)

    print(data.shape)
    print(result.shape)
    print(lv_result.shape)

    print(data[:, :20])
    print(result[:, :20])
    print(lv_result[:, :20])

    assert np.all(lv_result == result)
    assert np.all(lv_counts == counts)
