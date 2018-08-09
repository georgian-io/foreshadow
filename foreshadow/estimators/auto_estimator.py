"""
AutoEstimator and its selection
"""

import inspect
import operator

import numpy as np
from sklearn.base import BaseEstimator
from autosklearn.classification import AutoSklearnClassifier
from autosklearn.regression import AutoSklearnRegressor
from tpot import TPOTClassifier
from tpot import TPOTRegressor

from ..utils import check_df
from .config import get_tpot_config


class AutoEstimator(BaseEstimator):
    """An automatic machine learning solution wrapper selects the appropriate solution
    for a given problem.
    
    Args:
        problem_type (str): The problem type, 'regression' or 'classification'
        auto_estimator (str): The automatic estimator, 'tpot' or 'autosklearn'
        include_preprocessors (bool): Whether include preprocessors in automl pipelines
        estimator_kwargs (dict): A dictionary of args to pass to the specified 
            auto estimator (both problem_type and auto_estimator must be specified)
    """

    estimator_choices = {
        "autosklearn": {
            "classification": AutoSklearnClassifier,
            "regression": AutoSklearnRegressor,
        },
        "tpot": {"classification": TPOTClassifier, "regression": TPOTRegressor},
    }

    def __init__(
        self,
        problem_type=None,
        auto_estimator=None,
        include_preprocessors=False,
        estimator_kwargs=None,
    ):
        self.problem_type = problem_type
        self.auto_estimator = auto_estimator
        self.include_preprocessors = include_preprocessors
        self.estimator_kwargs = estimator_kwargs  # this needs to be checked last
        self.estimator_class = None
        self.estimator = None

    problem_type = property(operator.attrgetter("_problem_type"))

    @problem_type.setter
    def problem_type(self, pt):
        pt_options = ["classification", "regression"]
        if pt is not None and pt not in pt_options:
            raise ValueError("problem type must be in {}".format(pt_options))
        self._problem_type = pt

    auto_estimator = property(operator.attrgetter("_auto_estimator"))

    @auto_estimator.setter
    def auto_estimator(self, ae):
        ae_options = ["tpot", "autosklearn"]
        if ae is not None and ae not in ae_options:
            raise ValueError("auto_estimator must be in {}".format(ae_options))
        self._auto_estimator = ae

    estimator_kwargs = property(operator.attrgetter("_estimator_kwargs"))

    @estimator_kwargs.setter
    def estimator_kwargs(self, ek):
        if ek is not None:
            if self.problem_type is None or self.auto_estimator is None:
                raise ValueError(
                    "estimator_kwargs can only be set when estimator and problem are "
                    "specified"
                )
            elif not isinstance(ek, dict) or not all(
                isinstance(k, str) for k in ek.keys()
            ):
                raise ValueError("estimator_kwargs must be a valid kwarg dictionary")

            self.estimator_class = self.estimator_choices[self.auto_estimator][
                self.problem_type
            ]
            self._validate_estimator_kwargs(ek)  # estimator class is required for this
            self._estimator_kwargs = ek
        else:
            self._estimator_kwargs = {}

    def _determine_problem_type(self, y):
        """Simple heuristic to determine problem type"""
        return (
            "classification" if np.unique(y.values.ravel()).size == 2 else "regression"
        )

    def _pick_estimator(self):
        """Pick auto estimator based on benchmarked results"""
        return "tpot" if self.problem_type == "regression" else "autosklearn"

    def _validate_estimator_kwargs(self, auto_params):
        """Confirm that passed in dictionary arguments belong to the selected auto
        estimator class
        """
        keys = auto_params.keys()
        argspec = inspect.getargspec(self.estimator_class)
        invalid_kwargs = [k for k in keys if k not in argspec.args]
        if len(invalid_kwargs) != 0:
            raise ValueError(
                "The following invalid kwargs were passed in: {}".format(invalid_kwargs)
            )

    def _pre_configure_estimator_kwargs(self):
        """Configure auto estimators to perform similarly (time scale) and remove 
        preprocessors if necessary
        """
        if self.auto_estimator == "tpot" and "config_dict" not in self.estimator_kwargs:
            self.estimator_kwargs["config_dict"] = get_tpot_config(
                self.problem_type, self.include_preprocessors
            )
            if "max_time_mins" not in self.estimator_kwargs:
                self.estimator_kwargs["max_time_mins"] = 60
        elif (
            self.auto_estimator == "autosklearn"
            and not any(
                k in self.estimator_kwargs
                for k in ["include_preprocessors", "exclude_preprocessors"]
            )
            and not self.include_preprocessors
        ):
            self.estimator_kwargs["include_preprocessors"] = "no_preprocessing"
        return self.estimator_kwargs

    def _setup_estimator(self, y):
        """Construct and return the auto estimator instance"""
        self.problem_type = (
            self._determine_problem_type(y)
            if self.problem_type is None
            else self.problem_type
        )
        self.auto_estimator = (
            self._pick_estimator()
            if self.auto_estimator is None
            else self.auto_estimator
        )
        self.estimator_class = self.estimator_choices[self.auto_estimator][
            self.problem_type
        ]  # update estimator class in case of autodetect
        self._pre_configure_estimator_kwargs()  # validate estimator kwargs
        return self.estimator_class(**self.estimator_kwargs)

    def fit(self, X, y):
        """Fits the AutoEstimator instance using a selected automatic machine learning
        estimator

        Args:
            data_df (pandas.DataFrame or numpy.ndarray or list): The input feature(s)
            y_df (pandas.DataFrame or numpy.ndarray or list): The response feature(s)
        """
        X = check_df(X)
        y = check_df(y)
        self.estimator = self._setup_estimator(y)
        self.estimator.fit(X, y)

    def predict(self, X):
        """Uses the trained estimator to predict the response for an input dataset

        Args:
            data_df (pandas.DataFrame or numpy.ndarray or list): The input feature(s)

        Returns:
            pandas.DataFrame: The response feature(s)
        """
        X = check_df(X)
        return self.estimator.predict(X)

    def predict_proba(self, X):
        """Uses the trained estimator to predict the probabilities of responses
        for an input dataset

        Args:
            data_df (pandas.DataFrame or numpy.ndarray or list): The input feature(s)

        Returns:
            pandas.DataFrame: The probability associated with each response feature
        """
        X = check_df(X)
        return self.estimator.predict_proba(X)

    def score(self, X, y):
        """Uses the trained estimator to compute the evaluation score defined
        by the estimator

        Note: sample weight is not implemented as tpot does not accept it in 
        its score field

        Args:
            X (pandas.DataFrame or numpy.ndarray or list): The input feature(s)
            y (pandas.DataFrame or numpy.ndarray or list): The response feature(s)
        
        Returns:
            (float): A computed prediction fitness score
        """
        X = check_df(X)
        y = check_df(y)
        return self.estimator.score(X, y)