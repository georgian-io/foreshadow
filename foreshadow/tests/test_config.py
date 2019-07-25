"""Test config resolution."""

import pytest


def test_get_config_does_not_exists(mocker):
    from foreshadow.config import get_config

    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.path.isfile", return_value=False)

    assert get_config("test") == {}


@pytest.mark.parametrize(
    "data",
    [("test:\n  - hello".encode(), {"test": ["hello"]}), ("".encode(), {})],
)
def test_get_config_exists(data, mocker):
    from foreshadow.config import get_config

    read_data, test_data = data

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.isfile", return_value=True)
    m = mocker.mock_open(read_data=read_data)
    mocker.patch("builtins.open", m, create=True)

    assert get_config("test") == test_data


def test_resolve_config_only_sys():
    import pickle

    from foreshadow.config import resolve_config
    from foreshadow.utils.testing import get_file_path

    resolved = resolve_config()

    test_data_path = get_file_path("configs", "configs_default.pkl")

    # # Un comment to regenerate this file (if you change default configs)
    # with open(test_data_path, 'wb+') as fopen:
    #     pickle.dump(resolved, fopen)

    with open(test_data_path, "rb") as fopen:
        test_data = pickle.load(fopen)

    assert resolved == test_data


@pytest.mark.parametrize(
    "data",
    [
        ({}, {}, {}, "configs_empty.json"),
        ({"cleaner": ["T1", "T2"]}, {}, {}, "configs_override1.json"),
        (
            {"cleaner": ["T1", "T2"]},
            {"cleaner": ["T3"]},
            {},
            "configs_override2.json",
        ),
        (
            {"cleaner": ["T1", "T2"]},
            {"cleaner": ["T3"]},
            {"cleaner": ["T4"]},
            "configs_override3.json",
        ),
        (
            {"cleaner": ["T1", "T2"]},
            {},
            {"cleaner": ["T4"]},
            "configs_override4.json",
        ),
    ],
)
def test_resolve_config_overrides(data, mocker):
    import json

    from foreshadow.config import resolve_config, reset_config
    from foreshadow.utils.testing import get_file_path

    from functools import partial

    def test_get_config(base, d1, d2):
        if base == "USER":
            return d1
        else:
            return d2

    framework, user, local, test_data_fname = data

    test_get_config = partial(test_get_config, d1=user, d2=local)

    mocker.patch("foreshadow.config.DEFAULT_CONFIG", return_value=framework)
    mocker.patch("foreshadow.config.get_config_path", return_value="USER")
    mocker.patch("os.path.abspath", return_value="LOCAL")
    mocker.patch("foreshadow.config.get_config", side_effect=test_get_config)
    mocker.patch("foreshadow.config.get_transformer", side_effect=lambda x: x)

    # Clear the config cache
    reset_config()

    resolved = resolve_config()

    test_data_path = get_file_path("configs", test_data_fname)

    # # This shouldn't need to be done again (unless re-factor)
    # with open(test_data_path, 'w+') as fopen:
    #     json.dump(resolved, fopen, indent=4)

    with open(test_data_path, "r") as fopen:
        test_data = json.load(fopen)

    assert resolved == test_data


# def test_cfg_caching(mocker):
#     pass  # TODO: write tests for this.