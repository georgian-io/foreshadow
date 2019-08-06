import pytest

from foreshadow.utils.testing import get_file_path


def test_smart_emtpy_input():
    import numpy as np

    from foreshadow.smart import Scaler

    normal_data = np.array([])
    smart_scaler = Scaler()

    with pytest.raises(ValueError):
        smart_scaler.fit_transform(normal_data).values.size == 0


def test_smart_scaler_normal():
    import numpy as np
    import scipy.stats as ss

    from foreshadow.smart import Scaler
    from foreshadow.concrete import StandardScaler

    np.random.seed(0)
    normal_data = ss.norm.rvs(size=100)
    smart_scaler = Scaler()
    assert isinstance(
        smart_scaler.fit(normal_data).transformer, StandardScaler
    )


def test_smart_scaler_unifrom():
    import numpy as np
    import scipy.stats as ss

    from foreshadow.smart import Scaler
    from foreshadow.concrete import MinMaxScaler

    np.random.seed(0)
    uniform_data = ss.uniform.rvs(size=100)
    smart_scaler = Scaler()
    assert isinstance(smart_scaler.fit(uniform_data).transformer, MinMaxScaler)


def test_smart_scaler_neither():
    import numpy as np
    import scipy.stats as ss

    from foreshadow.smart import Scaler
    from sklearn.pipeline import Pipeline

    np.random.seed(0)
    lognorm_data = ss.lognorm.rvs(size=100, s=0.954)  # one example
    smart_scaler = Scaler()
    assert isinstance(smart_scaler.fit(lognorm_data).transformer, Pipeline)


def test_smart_encoder_less_than_30_levels():
    import numpy as np

    from foreshadow.smart import CategoricalEncoder
    from foreshadow.concrete import OneHotEncoder

    np.random.seed(0)
    leq_30_random_data = np.random.choice(30, size=500)
    smart_coder = CategoricalEncoder()
    assert isinstance(
        smart_coder.fit(leq_30_random_data).transformer, OneHotEncoder
    )


def test_smart_encoder_more_than_30_levels():
    import numpy as np

    from foreshadow.smart import CategoricalEncoder
    from foreshadow.concrete import HashingEncoder

    np.random.seed(0)
    gt_30_random_data = np.random.choice(31, size=500)
    smart_coder = CategoricalEncoder()
    assert isinstance(
        smart_coder.fit(gt_30_random_data).transformer, HashingEncoder
    )


def test_smart_encoder_more_than_30_levels_that_reduces():
    import numpy as np

    from foreshadow.smart import CategoricalEncoder
    from foreshadow.concrete import OneHotEncoder

    np.random.seed(0)
    gt_30_random_data = np.concatenate(
        [np.random.choice(29, size=500), np.array([31, 32, 33, 34, 35, 36])]
    )
    smart_coder = CategoricalEncoder()
    assert isinstance(
        smart_coder.fit(gt_30_random_data).transformer.steps[-1][1],
        OneHotEncoder,
    )


def test_smart_encoder_y_var():
    import numpy as np
    import pandas as pd

    from foreshadow.smart import CategoricalEncoder
    from foreshadow.concrete import FixedLabelEncoder as LabelEncoder

    y_df = pd.DataFrame({"A": np.array([1, 2, 10] * 3)})
    smart_coder = CategoricalEncoder(y_var=True)

    assert isinstance(smart_coder.fit(y_df).transformer, LabelEncoder)
    assert np.array_equal(
        smart_coder.transform(y_df).values.ravel(), np.array([0, 1, 2] * 3)
    )


def test_smart_impute_simple_none():
    import numpy as np
    import pandas as pd
    from foreshadow.smart import SimpleImputer

    heart_path = get_file_path("data", "heart-h.csv")

    impute = SimpleImputer(threshold=0.05)
    df = pd.read_csv(heart_path)

    data = df[["chol"]]

    impute.fit(data)
    out = impute.transform(data)

    assert np.allclose(data, out, equal_nan=True)


def test_smart_impute_simple_mean():
    import numpy as np
    import pandas as pd
    from foreshadow.smart import SimpleImputer

    heart_path = get_file_path("data", "heart-h.csv")
    heart_impute_path = get_file_path("data", "heart-h_impute_mean.csv")

    impute = SimpleImputer()
    df = pd.read_csv(heart_path)

    data = df[["chol"]]

    impute.fit(data)
    out = impute.transform(data)
    truth = pd.read_csv(heart_impute_path, index_col=0)

    assert np.array_equal(out, truth)


def test_smart_impute_simple_median():
    import pandas as pd
    import numpy as np
    from foreshadow.smart import SimpleImputer

    heart_path = get_file_path("data", "heart-h.csv")
    heart_impute_path = get_file_path("data", "heart-h_impute_median.csv")

    impute = SimpleImputer()
    df = pd.read_csv(heart_path)

    data = df["chol"].values
    data = np.append(data, [2 ** 10] * 100)

    impute.fit(data)
    out = impute.transform(data)
    truth = pd.read_csv(heart_impute_path, index_col=0)

    assert np.array_equal(out, truth)


def test_smart_impute_multiple():
    import numpy as np
    import pandas as pd
    from foreshadow.smart import MultiImputer

    heart_path = get_file_path("data", "heart-h.csv")
    heart_impute_path = get_file_path("data", "heart-h_impute_multi.csv")

    impute = MultiImputer()
    df = pd.read_csv(heart_path)

    data = df[["thalach", "chol", "trestbps", "age"]]

    impute.fit(data)
    out = impute.transform(data)
    truth = pd.read_csv(heart_impute_path, index_col=0)

    assert np.allclose(truth.values, out.values)


def test_smart_impute_multiple_none():
    import pandas as pd
    from sklearn.pipeline import Pipeline
    from foreshadow.smart import MultiImputer
    from foreshadow.utils import PipelineStep

    boston_path = get_file_path("data", "boston_housing.csv")

    impute = MultiImputer()
    df = pd.read_csv(boston_path)

    data = df[["crim", "nox", "indus"]]

    impute.fit(data)
    impute.transform(data)

    assert isinstance(impute.transformer, Pipeline)
    assert impute.transformer.steps[0][PipelineStep["NAME"]] == "null"


@pytest.mark.skip("THIS IS IMPORTANT FIX")
def test_preprocessor_hashencoder_no_name_collision():
    # This test is expected to only do up to DataCleaning right now.
    import uuid
    import numpy as np
    import pandas as pd
    from foreshadow.preparer import DataPreparer
    from foreshadow.columnsharer import ColumnSharer

    cat1 = [str(uuid.uuid4()) for _ in range(40)]
    cat2 = [str(uuid.uuid4()) for _ in range(40)]

    input = pd.DataFrame(
        {
            "col1": np.random.choice(cat1, 1000),
            "col2": np.random.choice(cat2, 1000),
        }
    )

    dp = DataPreparer(column_sharer=ColumnSharer())
    output = dp.fit_transform(input)
    # since the number of categories for each column are above 30,
    # HashingEncoder will be used with 30 components. The transformed output
    # should have in total 60 unique names.
    assert len(set(output.columns)) == 60


def test_smart_encoder_delimmited():
    import pandas as pd
    from foreshadow.smart import CategoricalEncoder
    from foreshadow.concrete import DummyEncoder

    data = pd.DataFrame({"test": ["a", "a,b,c", "a,b", "a,c"]})
    smart_coder = CategoricalEncoder()
    assert isinstance(smart_coder.fit(data).transformer, DummyEncoder)


def test_smart_encoder_more_than_30_levels_with_overwritten_cutoff():
    import numpy as np
    from foreshadow.smart import CategoricalEncoder
    from foreshadow.concrete import OneHotEncoder

    np.random.seed(0)
    gt_30_random_data = np.random.choice(31, size=500)
    smart_coder = CategoricalEncoder(unique_num_cutoff=35)
    assert isinstance(
        smart_coder.fit(gt_30_random_data).transformer, OneHotEncoder
    )


def test_smart_financial_cleaner_us():
    import numpy as np
    import pandas as pd
    from foreshadow.smart import FinancialCleaner

    x = pd.DataFrame(
        [
            "Test",
            "0",
            "000",
            "1,000",
            "0.9",
            "[0.9]",
            "-.3",
            "30.00",
            "3,000.35",
        ]
    )
    expected = pd.DataFrame(
        [np.nan, 0.0, 0.0, 1000, 0.9, -0.9, -0.3, 30.0, 3000.35]
    ).values
    out = FinancialCleaner().fit_transform(x).values

    assert np.all((out == expected) | (pd.isnull(out) == pd.isnull(expected)))


def test_smart_financial_cleaner_eu():
    import numpy as np
    import pandas as pd
    from foreshadow.smart import FinancialCleaner

    x = pd.DataFrame(
        [
            "Test",
            "0",
            "000",
            "1.000",
            "0,9",
            "[0,9]",
            "-,3",
            "30,00",
            "3.000,35",
        ]
    )
    expected = pd.DataFrame(
        [np.nan, 0.0, 0.0, 1000, 0.9, -0.9, -0.3, 30.0, 3000.35]
    ).values
    out = FinancialCleaner().fit_transform(x).values

    assert np.all((out == expected) | (pd.isnull(out) == pd.isnull(expected)))


@pytest.mark.skip("THIS IS IMPORTANT FIX")
def test_smart_text():  # not sure why this is broken.
    import numpy as np
    import pandas as pd

    from foreshadow.smart import TextEncoder
    from foreshadow.concrete import FixedTfidfVectorizer
    from foreshadow.concrete import HTMLRemover

    X1 = pd.DataFrame(["abc", "def", "1321", "tester"])
    tf1 = TextEncoder().fit(X1)

    assert isinstance(tf1.transformer, FixedTfidfVectorizer)

    X2 = pd.DataFrame(["<p> Hello </p>", "World", "<h1> Tag </h1>"])
    tf2 = TextEncoder().fit(X2)

    assert any(isinstance(tf, HTMLRemover) for n, tf in tf2.transformer.steps)
    assert isinstance(tf2.transformer.steps[-1][1], FixedTfidfVectorizer)

    assert TextEncoder().fit(pd.DataFrame([1, 2, 3, np.nan]))