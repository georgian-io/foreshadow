"""SmartFlattener for the CleanerMapper step in DataPreparer."""
from .smart import SmartTransformer
from foreshadow.utils import dynamic_import
import foreshadow.logging as logging
from foreshadow.concrete.internals import NoTransform


class Flatten(SmartTransformer):
    """Smartly determine how to flatten an input DataFrame."""

    def __init__(self, check_wrapped=True, **kwargs):
        super().__init__(check_wrapped=check_wrapped, **kwargs)

    def pick_transformer(self, X, y=None, **fit_params):
        """Get best transformer for a given column.

        Args:
            X: input DataFrame
            y: input labels
            **fit_params: fit_params

        Returns:
            Best data flattening transformer

        """
        from foreshadow.concrete.internals import (
            __all__ as flatteners,
        )

        flatteners = [
            (
                dynamic_import(
                    flattener, "foreshadow.concrete.internals"
                ),
                flattener,
            )
            for flattener in flatteners
            if flattener.lower().find("flatten") != -1
        ]

        best_score = 0
        best_flattener = None
        for flattener, name in flatteners:
            flattener = flattener()
            score = flattener.metric_score(X)
            if score > best_score:
                best_score = score
                best_flattener = flattener
        if best_flattener is None:
            return NoTransform()
        return best_flattener

    def resolve(self, X, *args, **kwargs):
        """Resolve the underlying concrete transformer.

        Sets self.column_sharer with the domain tag.

        Args:
            X: input DataFrame
            *args: args to super
            **kwargs: kwargs to super

        Returns:
            Return from super.

        """
        ret = super().resolve(X, *args, **kwargs)
        if self.column_sharer is not None:
            self.column_sharer[
                "domain", X.columns[0]
            ] = self.transformer.__class__.__name__
        else:
            logging.debug("column_sharer was None")
        return ret