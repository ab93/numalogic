# Copyright 2022 The Numaproj Authors.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import numpy as np
import numpy.typing as npt
from typing_extensions import Self

from numalogic.base import BaseThresholdModel


class StaticThreshold(BaseThresholdModel):
    r"""Simple and stateless static thresholding as an estimator.

    Values more than upper_limit is considered an outlier,
    and are given an outlier_score.

    Values less than the upper_limit is considered an inlier,
    and are given an inlier_score.

    Args:
    ----
        upper_limit: upper threshold
        outlier_score: static score given to values above upper threshold;
                       this has to be greater than inlier_score
        inlier_score: static score given to values below upper threshold
    """

    __slots__ = ("upper_limit", "outlier_score", "inlier_score")

    def __init__(self, upper_limit: float, outlier_score: float = 10.0, inlier_score: float = 0.5):
        self.upper_limit = float(upper_limit)
        self.outlier_score = float(outlier_score)
        self.inlier_score = float(inlier_score)

        if self.outlier_score < self.inlier_score:
            raise ValueError("Outlier score needs to be greater than inlier score")

    def fit(self, _: npt.NDArray[float]) -> Self:
        """Does not do anything. Only for API compatibility."""
        return self

    def predict(self, x: npt.NDArray[float]) -> npt.NDArray[int]:
        """Returns an integer array of same shape as input.
        1 denotes anomaly.
        """
        y = np.zeros_like(x, dtype=int)
        y[x < self.upper_limit] = 0
        y[x >= self.upper_limit] = 1
        return y

    def score_samples(self, x: npt.NDArray[float]) -> npt.NDArray[float]:
        """Returns an array of same shape as input
        with values being anomaly scores.
        """
        x = x.copy()
        x[x < self.upper_limit] = self.inlier_score
        x[x >= self.upper_limit] = self.outlier_score
        return x


class SigmoidThreshold(BaseThresholdModel):
    r"""Smooth and stateless static thesholding using sigmoid function as an estimator.

    Score is given by:
            score = score_limit * 1/ exp(-coeff * (x - upper_limits))

    Args:
    ----
        upper_limits: is the desired threshold limit of x;
            can be a float or a list of floats
            list of floats represents the upper limits for each feature;
            a single float represents the upper limit used for all features;
        slope_factor: determines the slope of the curve
        score_limit: is the scaler multiplier for the score
            e.g. a value of 10 means that the output score
            will be between 0 and 10.

    Raises
    ------
        ValueError: If the input data shape does not match the provided upper_limits
    """

    __slots__ = ("upper_limits", "coeff", "score_limit")

    def __init__(self, *upper_limits: float, slope_factor: int = 5, score_limit: int = 10):
        self.upper_limits = np.asarray(upper_limits, dtype=np.float32)
        self.coeff = slope_factor * np.pi
        self.score_limit = score_limit

    def fit(self, _: npt.NDArray[float]) -> Self:
        """Does not do anything. Only for API compatibility."""
        return self

    def _validate_input(self, x: npt.NDArray[float]) -> None:
        if len(self.upper_limits) == 1:
            return
        if x.shape[1] != len(self.upper_limits):
            raise ValueError("Input data shape does not match provided upper_limits")

    def predict(self, x: npt.NDArray[float]) -> npt.NDArray[int]:
        """Returns an integer array of same shape as input.
        1 denotes anomaly.

        This is calculated as a hard threshold at upper limit.
        """
        self._validate_input(x)
        y = np.zeros_like(x, dtype=int)
        y[x < self.upper_limits] = 0
        y[x >= self.upper_limits] = 1
        return y

    def score_samples(self, x: npt.NDArray[float]) -> npt.NDArray[float]:
        """Returns an array of same shape as input
        with values being anomaly scores.
        """
        self._validate_input(x)
        exp_arg = -self.coeff * (x - self.upper_limits)
        exp_arg = np.clip(exp_arg, -88.72, 88.72)
        return self.score_limit / (1.0 + np.exp(exp_arg))
