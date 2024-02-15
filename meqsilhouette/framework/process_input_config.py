# coding: utf-8
import json


def load_json_parameters_into_dictionary(config):
    """
    Load JSON parameters from a file into a dictionary.

    Parameters
    ----------
        config : str
            The path to the JSON file.

    Returns
    -------
        params : dict
            A dictionary containing the loaded and refactored JSON parameters.
    """
    params = read_json_files(config)
    params = params_refactoring(params)
    return params


def read_json_files(config):
    """
    Load JSON parameters from a file into a dictionary.

    Parameters
    ----------
        config : str
            The path to the JSON file.

    Returns
    -------
        params : dict
            A dictionary containing the loaded JSON parameters.
    """
    with open(config) as jsn_std:
        jparams = json.load(jsn_std)

    # Remove empty strings and convert unicode characters to strings
    params = {}
    for key, val in jparams.items():
        # Make sure all keys are strings
        _key = str(key)

        # ignore empty strings and comments
        if val == "" or _key == "#":
            pass
        # convert unicode values to strings
        elif isinstance(val, str):
            params[_key] = str(val)
        else:
            params[_key] = val

    return params


def params_refactoring(_params):
    """
    Modify input dictionary (hack: be careful!!!).

    Parameters
    ----------
        _params : dict
            The path to the JSON file.

    Returns
    -------
        _params : dict
            The updated dictionary.
    """
    _params['wavelength'] = 1e-9 * 299792458 / _params['ms_nu']

    return _params


def setup_keyword_dictionary(prefix, dictionary):
    """
    Create a dictionary from a dictionary with keys that start with a given prefix.

    Parameters
    ----------
        prefix : str
            The prefix to use for filtering the keys.
        dictionary : dict
            The dictionary to filter.

    Returns
    -------
        dict
            The filtered dictionary.
    """
    f = lambda x: filter(lambda a: a[0].startswith(x), dictionary.items())
    return dict([(key.split(prefix)[-1], val) for (key, val) in f(prefix)])
