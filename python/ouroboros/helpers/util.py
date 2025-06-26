import numpy as np


def unique_lv(ar, *bin_weights: np.ndarray,
              return_index: bool = False, return_inverse: bool = False, return_counts: bool = False,
              axis: int = 1, sorted: bool = False, last_axis_sort: bool = False):
    """ Get Unique Integer Values
        Currently limited to 2D arrays and sortying over the first axis, will tweak at some point.

        Parameters:
        -----------
            ar (numpy.ndarray): 2D Integer Array holding values to be searched.
            bin_weights (numpy.ndarray): Arrays matching the second dimension of ar
                                        that weigh bin counts like np.bincount over the unique elemnts.
            return_index (bool): NOTIMPLEMENTED. If True, also return the indices of ar along the second axist
                                    that result in the unique array.
            return_inverse (bool): NOTIMPLEMENTED. If True, also return the indices of the unique array along the
                                    second axis that can be used to reconstruct ar.
            return_counts (bool): If True, also return the number of times each unique item appears in ar.
            axis (int or None): CURRENTLY ALWAYS TREATED AS ONE.
            sorted (bool): IGNORED.  Values are returned in sorted order.
            last_axis_sort (bool): If True, result is sorted by last axis instead of first.
        Returns:
        --------
            unique (np.ndarray): Unique values, sorted by the last row in axis (or first, with first_axis_sort).
            unique_indices (np.ndarray, optional): The indices of the first occurrences of the unique values
                                                    in the original array. Only provided if return_index is True.
            unique_inverse (np.ndarray, optional): The indices to reconstruct the original array from the
                                                    unique array. Only provided if return_inverse is True.
            unique_counts (np.ndarray, optional): The number of times each of the unique values comes up in
                                                    the original array. Only provided if return_counts is True.
            unique_weighted (np.ndarray, optional): 1 or more arrays representing counts of the unique
                                                    occurances, weighted by bin_weights parameter(s).
        """
    # Use smallest dtype that can fit the array - bits of array length * 3
    if return_index or return_inverse:
        return NotImplementedError
    rec_type = np.dtype(np.uint32)
    next_shift = np.dtype(rec_type).type(0)
    result = np.zeros(shape=(1,), dtype=rec_type)
    col_data = []

    for col in ar if last_axis_sort else np.flip(ar, 0):
        col_nbits = np.ceil(np.log2(np.max(col) + 1)).astype(rec_type)
        col_data.append((col_nbits, col.dtype))

        if col_nbits:
            result = (col.astype(rec_type) << next_shift) | result
            next_shift += col_nbits
            if next_shift > (rec_type.itemsize * 8):
                raise NotImplementedError(f"{rec_type} Too Small: {rec_type.itemsize * 8}|{next_shift}")

    counts = np.bincount(result)
    values_set = (np.nonzero(counts)[0]).astype(rec_type)
    restored_cols = []

    ret = ()
    if return_counts:
        ret += (counts[values_set], )

    for weight in bin_weights:
        if weight.shape != ar[0].shape:
            raise ValueError(f"Unique_Int binning weight {weight.shape} did not match dimensions {ar[0].shape})")
        else:
            ret += (np.bincount(result, weights=weight)[values_set], )

    for col_nbits, col_dtype in col_data:
        restored_cols.append((values_set & ((1 << col_nbits) - 1)).astype(col_dtype))
        values_set >>= col_nbits

    ret = (np.array(restored_cols if last_axis_sort else restored_cols[::-1]), ) + ret

    return ret if len(ret) > 1 else ret[0]
