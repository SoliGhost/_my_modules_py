# -*- coding: utf-8 -*-
# @Author: SoliGhost
# @Date:   2025-04-15 05:59
# @Version: 1.0.0
# @Last Modified by:   SoliGhost
# @Last Modified time: 2025-04-16 01:08

"""
Configuration File Handler Module
=====================================
This module provides functionality to load and save configuration files with extensive error handling and behaviour control capabilities.

This module aims to provide a very lightweighted and easy-to-use method to manage configuration files. While providing many customization options, I also try to make every default setting the most reasonable and common sense, so that you won't need to change a lot of settings when using.
I use such way to provide warnings because I believe that it's better to handle the warning yourself rather than output it here (Or there may be more complex options for warning handling). I don't think such a lightweighted module should logging and pollute the console.

Features
--------
- Load configuration files.
    - Can check according to the default data
    - Can repair the data according to the behaviour settings.
- Save data to configuration files.
- Only supports JSON format for now. But will gradually support INI and other formats in the future.

Functions
---------
- behaviour_config(exception:str, behaviour:str):
    - Set the behaviour for a specific exception when loading.
- load_config_json(file:str, default:Union[dict,list,None]=None, check:bool=True) -> tuple[dict[str,str],Union[dict,list]]:
    - Load a JSON configuration file.
    - Can check and repair at the same time.
- save_config_json(file:str, data:Union[dict,list]) -> None:
    - Save a JSON configuration file.

Behavior Control
---------------
The module allows setting different behaviors for these exceptions, options are in the "BEHAVIOUR_OPTIONS" dictionary:

- NotFound: When file is not found.
- SyntaxError: When syntax is invalid.
- MissingKeys: When there are missing keys in the data.
- ExtraKeys: When there are extra keys in the data.
- DisorderedKeys: When the data's keys are not in the order of default data's keys.
"""

__version__ = "1.0.0"

from typing import Union
import json

BEHAVIOUR_OPTIONS = {
    "NotFound":        ["create","error"],
    "SyntaxError":     ["reset","error"],
    "MissingKeys":     ["append","append+sort","reset","ignore","error"],
    "ExtraKeys":       ["delete","delete+sort","reset","ignore","error"],
    "DisorderedKeys":  ["sort","ignore","error"]
}

__behaviour_settings = {
    "NotFound":"create",
    "SyntaxError":"reset",
    "MissingKeys":"append",
    "ExtraKeys":"delete",
    "DisorderedKeys":"sort"
}

def behaviour_config(exception:str, behaviour:str):
    """
    Set the behaviour for a specific exception when loading.

    The valid options for each exception are in the "BEHAVIOUR_OPTIONS" dictionary.
    Will check if the exception and the behaviour are valid, if not, will raise a ValueError.
    
    :param exception: The exception to set the behaviour for.
    :type exception: str
    :param behaviour: The behaviour to set.
    :type behaviour: str

    :return None:

    :raises ValueError: If the exception or the behaviour is invalid.
    """
    if exception not in BEHAVIOUR_OPTIONS:
        raise ValueError(f"Invalid exception: \"{exception}\".")
    if behaviour not in BEHAVIOUR_OPTIONS[exception]:
        raise ValueError(f"Invalid behaviour \"{behaviour}\" for exception \"{exception}\".")
    __behaviour_settings[exception] = behaviour

class ConfigSyntaxError(Exception): pass

def load_config_json(file:str, default:Union[dict,list,None]=None, check:bool=True) -> tuple[dict[str,str],Union[dict,list]]:
    """
    Load a JSON configuration file.

    When exceptions happen, will behave according to the behaviour set and recording the exception name in a warnings dict , which will be returned along with the data.

    :param file: The path to the JSON file.
    :type file: str
    :param default: The default data to check and repair. Must not be None if check is True and the data is a dictionary.
    :type default: dict|list|None
    :param check: Whether to check the data. Will check only if the data is a dictionary and will check if the keys are missing or extra, and if the keys are in the default data's order. And will check the order only if there are no missing or extra keys. 
    :type check: bool

    :return (warnings, data): A tuple containing the warnings and the data. In the warnings dict, the keys are the exception names and the values are the exception messages (sometines may be empty strings). If there are no warnings, it will be an empty dict.
    :rtype: tuple[dict[str,str],dict|list]

    :raises TypeError: If parameters are not of the correct type.
    :raises FileNotFoundError: If the file is not found and the behaviour for "NotFound" is set to "error".
    :raises ConfigSyntaxError: If the syntax is invalid and the behaviour for "SyntaxError" is set to "error".
    :raises ValueError:
        - If the default data is None but check is True and the data is a dictionary.
        - Checking found that there are missing or extra keys and the behaviour for "MissingKeys" or "ExtraKeys" is set to "error".
        - Checking found that the keys are not in the order of default data's keys and the behaviour for "DisorderedKeys" is set to "error".
    """
    warnings = {}
    if not isinstance(file, str):
        raise TypeError("'file' must be a string.")
    if not isinstance(default, (dict, list, type(None))):
        raise TypeError("'default' must be a dict, a list or None.")
    if not isinstance(check, bool):
        raise TypeError("'check' must be a boolean.")
    
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        warnings["NotFound"] = ""
        if __behaviour_settings["NotFound"]=="error":
            raise FileNotFoundError(f"Configuration file not found: {file}.")
        save_config_json(file, default)
        data = default
    except json.JSONDecodeError as e:
        warnings["SyntaxError"] = ""
        if __behaviour_settings["SyntaxError"]=="error":
            raise ConfigSyntaxError(f"JSON syntax error: {e}")
        save_config_json(file, default)
        data = default
    
    if check and isinstance(data, dict):
        if default == None:
            raise ValueError("Default data must be provided if you need to check.")
        missing_keys = set(default.keys()) - set(data.keys())
        extra_keys = set(data.keys()) - set(default.keys())
        if missing_keys:
            warnings["MissingKeys"] = ','.join(missing_keys)
            if __behaviour_settings["MissingKeys"] == "append":
                for key in missing_keys:
                    data[key] = default[key]
            elif __behaviour_settings["MissingKeys"] == "append+sort":
                temp_data = default.copy()
                temp_data.update(data)    # keep the order of the default keys and add the extra keys in original order at the end
                data = temp_data
            elif __behaviour_settings["MissingKeys"] == "reset":
                data = default
            elif __behaviour_settings["MissingKeys"] == "ignore":
                pass
            elif __behaviour_settings["MissingKeys"] == "error":
                raise ValueError(f"Missing keys in {file}: {', '.join(missing_keys)}")
        if extra_keys:
            warnings["ExtraKeys"] = ','.join(extra_keys)
            if not __behaviour_settings["MissingKeys"] == "reset":    # if one is set to "reset" and both happen, reset, no more operations below
                if __behaviour_settings["ExtraKeys"] == "delete":
                    for key in extra_keys:
                        del data[key]
                elif __behaviour_settings["ExtraKeys"] == "delete+sort":
                    temp_data = {}
                    for key in default.keys():
                        if key in data:
                            temp_data[key] = data[key]
                    data = temp_data
                elif __behaviour_settings["ExtraKeys"] == "reset":
                    data = default
                elif __behaviour_settings["ExtraKeys"] == "ignore":
                    pass
                elif __behaviour_settings["ExtraKeys"] == "error":
                    raise ValueError(f"Extra keys in {file}: {', '.join(extra_keys)}")
    
        if not (missing_keys or extra_keys):
            if default.keys() != data.keys():
                warnings["DisorderedKeys"] = ""
                if __behaviour_settings["DisorderedKeys"] == "sort":
                    data = {k: data[k] for k in default.keys()}
                elif __behaviour_settings["DisorderedKeys"] == "ignore":
                    pass
                elif __behaviour_settings["DisorderedKeys"] == "error":
                    raise ValueError(f"Keys are not in the same order as in the default data.")
    return (warnings, data)

def save_config_json(file:str, data:Union[dict,list]) -> None:
    """
    Save a JSON configuration file.

    :param file: The path to the JSON file.
    :type file: str
    :param data: The data to save.
    :type data: dict|list

    :return None:

    :raises TypeError: If parameters are not of the correct type.
    :raises AnyOtherException: If any other exception happens when writing the file.
    """
    if not isinstance(file, str):
        raise TypeError("'file' must be a string.")
    if not isinstance(data, (dict, list)):
        raise TypeError("'data' must be a dict, a list or None.")
        
    with open(file, 'w', encoding='utf-8') as f:    # do not catch exceptions when writing, let them propagate
        json.dump(data, f, indent=2, ensure_ascii=False)