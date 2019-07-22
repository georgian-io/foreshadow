"""General base classes used across Foreshadow."""
from copy import deepcopy

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from foreshadow.core import logging

from foreshadow.transformers.base import ParallelProcessor


class PreparerStep(BaseEstimator, TransformerMixin):
    """Base class for any pipeline step of DataPreparer.

    This class automatically wraps the defined pipeline to make it
    parallelizable across a DataFrame. To make this possible and still be
    customizable, subclasses must implement get_transformer_list and
    get_transformer_weights, which are two inputs the ParallelProcessor
    (the class used to make parallelization possible).


    The transformer_list represents the mapping from columns to
    transformers, in the form of ['name', 'transformer', ['cols']],
    where the [cols] are the cols for transformer 'transformer. These
    transformers should be SmartTransformers for any subclass.

    The transformer_weights are multiplicative weights for features per
    transformer. Keys are transformer names, values the weights.

    """

    def __init__(self, *args, **kwargs):
        """Set the original pipeline steps internally.

        Takes a list of desired SmartTransformer steps and stores them as
        self._steps. Constructs self an sklearn pipeline object.

        Args:
            steps: list of ('name', 'Mapping') tuples, where the latter is a
                function that
            *args: args to Pipeline constructor.
            **kwargs: kwargs to PIpeline constructor.
        """
        self._parallel_process = None
        super().__init__(*args, **kwargs)

    @staticmethod
    def separate_cols(transformer_per_col=()):
        """Return a valid mapping where each col has a separate transformer.

        Args:
            transformer_per_col: list of (transformer, col) tuples where col is
                a single column.

        Returns:
            A list where each entry can be used to separately access an
            individual column from X.

        """
        return {i: [trans_col] for i, trans_col in
                enumerate(transformer_per_col)}

    @classmethod
    def logging_name(cls):
        return "DataPreparerStep: %s " % cls.__name__

    @staticmethod
    def parallelize_mapping(column_mapping):
        final_mapping = {}
        parallelized = {}  # we will first map all groups that have no
        # interdependencies with other groups. Then, we will do all the rest
        # of the groups after as they will be performed step-by-step
        # parallelized.
        for group_number in column_mapping:
            list_of_steps = column_mapping[group_number]
            cols_across_steps = [mapping[1] for mapping in list_of_steps]
            if all([x == cols_across_steps[0] for x in cols_across_steps]):
                # if we enter here, this step has the same columns across
                # all steps. This means that we can create one Pipeline for
                # this group of columns and let it run parallel to
                # everything else as its inputs are never dependent on the
                # result from any step in another pipeline.
                transformer_list = ['group: %d' % group_number,
                                    Pipeline([m[0] for m in list_of_steps]),
                                    cols_across_steps[0]]
                # transformer_list = [name, pipeline of transformers, cols]
                # cols here is the same for each step, so we just pass it in
                # once as a single group.
                final_mapping[group_number] = transformer_list
                parallelized[group_number] = True
                # TODO this is a very simple check, this could be optimized
                #  further
            else:
                parallelized[group_number] = False  # this group could not
                # be separated out.
        if len(final_mapping) < len(column_mapping):  # then there must be
            # groups of columns that have interdependcies.
            total_steps = len(column_mapping[0])
            steps = []  # each individual step, or dim1, will go in here.
            all_cols = set()
            for step_number in range(total_steps):
                groups = []
                for group_number in parallelized:
                    if not parallelized[group_number]:  # we do not have a
                        # transformer_list yet for this group.
                        list_of_steps = column_mapping[group_number]
                        step_for_group = list_of_steps[step_number]
                        transformer = step_for_group[0]
                        cols = step_for_group[1]
                        groups.append((group_number, transformer, cols))
                        for col in cols:
                            all_cols.add(col)
                transformer_list = [
                    ["group: %d, transformer: %s" % (group_number,
                                                     transformer.__name__),
                     transformer,
                     cols,
                     ] for group_number, transformer, cols in groups
                ]  # this is one step parallelized across the columns (dim1
                # parallelized across dim2).
                steps.append(
                    ("step: %d" % step_number, ParallelProcessor(transformer_list))
                )  # list of steps for final pipeline.
            final_mapping['grouped_pipeline'] = ['grouped_pipeline',
                                                 Pipeline(steps),
                                                 list(all_cols)]

        return final_mapping

    def parallelize_smart_steps(self, X):
        """Make self.steps for internal pipeline methods parallelized.

        Takes self._steps passed at construction time and wraps each step
        with ParallelProcessor to parallelize it across a DataFrame's columns.
        Made possible sing get_transformer_list and get_transformer_weights
        which must be implemented by the subclass.

        get_transformer_list must return a mapping where each column shows
        up only once

        ['name', 'transformer', ['cols']] format where each column
            should be included exactly once.

        Args:
            X: DataFrame

        """
        # TODO consider overlapping cols
        # TODO consider checking on parent or child
        # TODO consider child making pipeline or parent making pipeline.
        column_mapping = self.get_mapping(X)
        logging.debug(self.logging_name() + 'column_mapping: {}'.format(
            column_mapping
        ))
        logging.debug(self.logging_name() + 'called ')
        parallelized_mapping = self.parallelize_mapping(column_mapping)
        group_transformer_list = [
            transformer_list for transformer_list in
            parallelized_mapping.values()
        ]
        return ParallelProcessor(group_transformer_list)

    def get_mapping(self, X):
        """Return dict of lists of tuples representing columns:transformers.

        The return can be viewed as a third order tensor, where:
        dim 1: the number of operations to be performed on a given set of
            columns. For instance, you could have this dimension = 3 where you
            would then view that a given column would have 3 Smart transformers
            associated with it.

        dim 2: the number of groups of operations. This can be viewed as
        groups of columns being passed to a single smart transformer. For
        instance, you may pass a single column each to its on smart
        transformer (say, to clean each column individually), or all columns
        to a single smart transformer (for instance, for dimensionality
        reduction).

        dim 3: This is ways a tuple, where the first argument is smart
        transformer, the second argument is the list of columns (by name in
        the DataFrame). This represents the actual mapping of individual
        instances of smart transformers to groups of columns. That
        individual SmartTransformer instance will be passed all the columns
        in the second argument as an input.

        Of course, any SmartTranformer can be replaced with a concrete
        transformer, as a SmartTransformer is just a wrapper shadowing an
        underlying concrete transformer.

        # Here, step is a useful argument to define concrete end points in
        # your parallelized operations. This class will automatically
        # parallelize as much as possible, but if the decision of which
        # SmartTransformer to apply to a group of columns is dependent on the
        # results from the previous run, then you would make a step 1 take
        # perform those operations, and step 2 can access that information
        # from ColumnSharer to make that decision.
        # This method should be implemented s.t. it is expected ot be
        # continuously called until None is returned.
        #
        # Currently, multiple calls to this function is not supported in
        # HyperParameter tuning as scikit-learn tuners require the entire
        # pipeline to be defined up front.

        Args:
            # step: integer representing the step number.
            X: DataFrame

        Returns:
            third order list of lists, then None when finished.
        """
        raise NotImplementedError('Must implement this method.')

    def fit(self, X, *args, **kwargs):
        """fit

        Args:
            X: input DataFrame
            *args: args to _fit
            **kwargs: kwargs to _fit

        Returns:
            transformed data handled by Pipeline._fit

        """
        self.check_process(X)
        self._parallel_process.fit(X, *args, **kwargs)

    def check_process(self, X):
        if self._parallel_process is None:
            logging.debug('DataPreparerStep: %s called check_process' %
                          self.__class__.__name__)
            self._parallel_process = self.parallelize_smart_steps(X)

    def fit_transform(self, X, y=None, **fit_params):
        self.check_process(X)

    def transform(self, X, *args, **kwargs):
        self.check_process(X)
        self._parallel_process.transform(X, *args, **kwargs)

    def inverse_transform(self, X, *args, **kwargs):
        self.check_process(X)
        self._parallel_process.transform(X, *args, **kwargs)
