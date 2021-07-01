"""
Fast efeature operations implemented in cython


@see	http://cython-docs2.readthedocs.io/en/latest/src/tutorial/numpy.html
		for how to extend this module using cython & numpy
"""

# import numpy as np
import numba

@numba.jit("f8(f8[:],f8[:],i8[:],i8[:],i8[:],i8[:],f8,f8,f8)", nopython=True)
def calc_ISI_voltage_distance_dt_equal(
		Va, 
		Vb,
		i_begin_A,
		i_begin_B,
		i_end_A,
		i_end_B,
		tstart,
		tstop,
		dt):
	"""
	@param Va			voltage trace A (must have same dt as voltage trace b)

	@param Vb			voltage trace B (must have same dt as voltage trace a)
	
	@param i_begin_A	np.ndarray containing AP begin indices (same size as i_end_A)

	@param i_end_A		np.ndarray containing AP begin indices (same size as i_begin_A)

	TODO: check that traces A and B are computed using same dt
	"""
	# NOTE: array indexing is only optimized if all indices have a native integer type AND as many indices are provided as the number of array dimensions
	j_milestone_A = -1
	j_milestone_B = -1

	# Find start and stop indices in voltage trace
	findex = tstart / dt
	i_start = int(findex)
	findex = tstop / dt
	i_stop = int(findex)

	# Find index of first spike that will be encountered
	for j_spk in range(max(i_end_A.shape[0], i_end_B.shape[0])):
		if j_milestone_A >=0 and j_milestone_B >= 0:
			break
		if i_end_A[j_spk] > i_start:
			j_milestone_A = j_spk
		if i_end_B[j_spk] > i_start:
			j_milestone_B = j_spk

	# Iterate over matching Voltage values
	dist = 0.0
	num_samples = 0

	for i_V in range(i_start, min(Va.shape[0], Vb.shape[0])):
		if i_V > i_stop:
			break

		# check if we are in a Va spike
		if i_V > i_end_A[j_milestone_A]:
			j_milestone_A += 1 # passed milestone: set next milestone
		# DEBUG:
		# if (i_V > i_end_A[j_milestone_A]) and (j_milestone_A < i_end_A.shape[0]):
		# 	raise Exception("Assertion failed: next spike should be ahead of current index")

		if j_milestone_A < 0 or j_milestone_A >= i_end_A.shape[0]:
			in_spk_A = False
		else:
			in_spk_A = (i_V >= i_begin_A[j_milestone_A]) and (i_V <= i_end_A[j_milestone_A])


		# check if we are in a Vb spike
		if i_V > i_end_B[j_milestone_B]:
			j_milestone_B += 1 # passed milestone: set next milestone
		# DEBUG:
		# if (i_V > i_end_B[j_milestone_B]) and (j_milestone_B < i_end_B.shape[0]):
		# 	raise Exception("Assertion failed: next spike should be ahead of current index")

		if j_milestone_B < 0 or j_milestone_B >= i_end_B.shape[0]:
			in_spk_B = False
		else:
			in_spk_B = (i_V >= i_begin_B[j_milestone_B]) and (i_V <= i_end_B[j_milestone_B])


		# if we are not in any spike: compute distance
		if not (in_spk_A or in_spk_B):
			diff = Va[i_V] - Vb[i_V]
			dist = dist + diff*diff # sum of squared
			num_samples += 1

	dist = dist / num_samples
	return dist