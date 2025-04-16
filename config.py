# -*- coding: utf-8 -*-
# @Author: SoliGhost
# @Date:   2025-04-15 05:59
# @Version: 2.0.0
# @Last Modified by:   SoliGhost
# @Last Modified time: 2025-04-16 22:26

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
- Register data as variables.
- Only supports JSON format for now. But will gradually support INI and other formats in the future.

Functions
---------
- behaviour_config(exception:str, behaviour:str):
    - Set the behaviour for a specific exception when loading.
- load_config_{format}(file:str, default:<data_types>|None=None, check:bool=True) -> tuple[dict[str,str],<data_types>]:
    - Load a configuration file of a specified format.
    - Can check and repair at the same time.
- save_config_{format}(file:str, data:<data_types>) -> None:
    - Save data to a configuration file of a specified format.
- register_config_{format}(data:<data_types>, in_module:bool=True, ...) -> None|str:
    - Register configuration data as variables.
- load_register_config_{format}(file:str, default:<data_types>|None=None, check:bool=True, list_name:str="CONFIG_LIST", in_module:bool=True) -> dict[str,str]|tuple[dict[str,str],str]:
    - Load a configuration file of a specified format, and register the data.

Function Alias Rules
--------------------
Only config handling functions have aliases.

- {operation code}{format code}config
    - operation:
        - load: L
        - save: S
        - register: R
        - load_register: LR
    - format:
        - json: J
- For example:
    - load_config_json: LJconfig

Behavior Control
---------------
The module allows setting different behaviors for these exceptions, options are in the *'BEHAVIOUR_OPTIONS'* dictionary:

- NotFound: When file is not found.
- SyntaxError: When syntax is invalid.
- MissingKeys: When there are missing keys in the data.
- ExtraKeys: When there are extra keys in the data.
- DisorderedKeys: When the data's keys are not in the order of default data's keys.
"""

__version__ = "2.0.0"

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

    The valid options for each exception are in the *'BEHAVIOUR_OPTIONS'* dictionary.
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
    (alias: LJconfig)
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
    return warnings, data

def save_config_json(file:str, data:Union[dict,list]) -> None:
    """
    (alias: SJconfig)
    Save a JSON configuration file.

    :param file: The path to the JSON file.
    :type file: str
    :param data: The data to save.
    :type data: dict|list

    :return None:

    :raises TypeError: If parameters are not of the correct type.
    """
    if not isinstance(file, str):
        raise TypeError("'file' must be a string.")
    if not isinstance(data, (dict, list)):
        raise TypeError("'data' must be a dict, a list or None.")
        
    with open(file, 'w', encoding='utf-8') as f:    # do not catch exceptions when writing, let them propagate
        json.dump(data, f, indent=2, ensure_ascii=False)

def register_config_json(data:Union[dict,list], list_name:str="CONFIG_LIST", in_module:bool=True) -> Union[None,str]:    # TODO: add upper keys option
    """
    (alias: RJconfig)
    Register a JSON configuration data to variables.
    
    If the data is a dictionary, will register each key-value pair as variables.
    If the data is a list, will register it to a variable with the name specified by *'list_name'*.

    .. Note::
        If choose to register in caller, values in data will need to be serialized using `repr`, this is NOT guaranteed to work in all cases.

    .. Example::
    .. code-block:: python
        data = {"a": 1, "b": 2}

        # in module, import to global (Editor will warn)
        register_config_json(data)
        from config import *
        print(a)

        # in module, keep in module (unconvenient to use)
        register_config_json(data)
        print(config.a)

        # in caller (Editor will warn)
        exec(register_config_json(data, in_module=False))
        print(a)

    :param data: The data to register.
    :type data: dict|list
    :param list_name: The name of the list variable to register if the data is a list.
    :type list_name: str
    :param in_module: register the data in the module or return the registering code to execute.
    :type in_module: bool

    :return None: If in_module is True.
    :return str: The registering code if in_module is False.

    :raises TypeError: If parameters are not of the correct type.
    """
    if not isinstance(data, (dict, list)):
        raise TypeError("'data' must be a dict or a list.")
    if not isinstance(in_module, bool):
        raise TypeError("'in_module' must be a boolean.")
    
    if in_module:
        if isinstance(data, dict):
            for key, value in data.items():
                exec(f"global {key}\n{key} = value")
        else:
            exec(f"global {list_name}\n{list_name} = data")
    else:
        if isinstance(data, dict):
            return "\n".join([f"{key} = {repr(value)}" for key, value in data.items()])    # if do not repr, strings will be parsed as literal values rather than string expressions.
        else:
            return f"{list_name} = {data}"

def load_register_config_json(file:str, default:Union[dict,list,None]=None, check:bool=True, list_name:str="CONFIG_LIST", in_module:bool=True) -> Union[dict[str,str],tuple[dict[str,str],str]]:
    """
    (alias: LRJconfig)

    Load a JSON configuration file and register the data to variables.

    Simply combines the *'load_config_json'* and *'register_config_json'* functions.

    About parameters and exceptions, see *'load_config_json'* and *'register_config_json'* functions.

    :return (warnings, code): If *'in_module'* is False. A tuple containing the warnings and the code to register the data as variables. About the warnings, see *'load_config_json'* function.
    :return warnings: If *'in_module'* is True. About the warnings, see *'load_config_json'* function.
    :rtype: tuple[dict[str,str],dict|list]
    """
    warnings, data = load_config_json(file, default, check)
    if in_module:
        register_config_json(data, list_name, in_module)
        return warnings
    else:
        return warnings,register_config_json(data, list_name, in_module)

LJconfig = load_config_json
SJconfig = save_config_json
RJconfig = register_config_json
LRJconfig = load_register_config_json