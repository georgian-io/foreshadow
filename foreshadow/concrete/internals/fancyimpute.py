"""Fancy imputation."""

from foreshadow.base import BaseEstimator, TransformerMixin

from foreshadow.wrapper import pandas_wrap


@pandas_wrap
class FancyImputer(BaseEstimator, TransformerMixin):
    """Wrapper for the fancy imputation methods.

    Uses the `FancyImpute <https://github.com/iskandr/fancyimpute>` python
    package.

    Args:
        method (str): String of function from FancyImpute to invoke when
            transforming

    """

    def __init__(self, method="SimpleFill", impute_kwargs={}):
        self.impute_kwargs = impute_kwargs
        self.method = method
        self._load_imputer()

    def _load_imputer(self):
        """Load concrete fancy imputer based on string representation.

        Auto import and initialize fancyimpute class defined by method.

        Raises:
            ValueError: If method is invalid

        """
        try:
            module = __import__("fancyimpute", [self.method], 1)
            self.cls = getattr(module, self.method)
        except Exception:
            raise ValueError(
                "Invalid method. Possible values are BiScaler, KNN, "
                "NuclearNormMinimization and SoftImpute"
            )

        self.imputer = self.cls(**self.impute_kwargs)

    def get_params(self, deep=True):
        """Get parameters for this estimator.

        Args:
            deep (bool): If True, will return the parameters for this estimator
                and contained subobjects that are estimators.

        Returns:
            dict: Parameter names mapped to their values.

        """
        return super().get_params(deep=deep)

    def set_params(self, **params):
        """Set the parameters of this estimator.

        Valid parameter keys can be listed with :meth:`get_params()`.

        Args:
            **params: params to set

        Returns:
            see super.

        """
        out = super().set_params(**params)
        self._load_imputer()
        return out

    def fit(self, X, y=None):
        """Empty function.

        No fit necessary for these.

        Args:
            X: input observations
            y: input labels

        Returns:
            self

        """
        return self

    def transform(self, X):
        """Execute fancyimpute transformer on X data.

        Args:
            X (:obj:`pandas.DataFrame`): Input data

        Returns:
            :obj:`pandas.DataFrame`: Output data

        """
        return self.imputer.complete(X)
