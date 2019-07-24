import pytest


def test_data_cleaner_fit():
    import pandas as pd
    import numpy as np
    from numpy import testing as npt
    from foreshadow.cleaners import DataCleaner

    data = pd.DataFrame(
        {
            "dates": ["2019-02-11", "2019/03/12", "2000-04-15", "1900/01/55"],
            "json": [
                '{"date": "2019-04-11"}',
                '{"financial": "$1.0"}',
                '{"financial": "$1000.00"}',
                '{"random": "asdf"}',
            ],
            "financials": ["$1.00", "$550.01", "$1234", "$12353.3345"],
        },
        columns=["dates", "json", "financials"],
    )
    dc = DataCleaner()
    dc.fit(data)
    data = dc.transform(data)
    check = pd.DataFrame([['2019', '02', '11', '2019', '04', '11', np.nan,
                           np.nan, '1.0'],
                          ['2019', '03', '12', np.nan, '', '', '1.0', np.nan,
                           '550.0'],
                          ['2000', '04', '15', np.nan, '', '', '1000.0',
                           np.nan, '$1234'],
                          ['1900', '01', '55', np.nan, '', '', np.nan, 'asdf',
                           '12353.3']])
    print(data)
    assert False

def test_financials():
    import pandas as pd
    from foreshadow.cleaners import DataCleaner

    data = pd.DataFrame(
        {
            "financials": ["$1.00", "$550.01", "$1234", "$12353.3345"],
        },
        columns=["financials"],
    )
    dc = DataCleaner()
    dc.fit(data)
    transformed_data = dc.transform(data)
    print(transformed_data)
    assert False


def test_data_cleaner_json():
    import pandas as pd
    from foreshadow.cleaners import DataCleaner

    data = pd.DataFrame(
        {
            "json": [
                '{"date": "2019-04-11"}',
                '{"financial": "$1.0"}',
                '{"financial": "$1000.00"}',
                '{"random": "asdf"}',
            ]
        },
        columns=["json"],
    )
    print(data)
    dc = DataCleaner()
    dc.fit(data)
    dc.transform(data)