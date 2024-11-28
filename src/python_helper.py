"""
Python Helper.
"""
import configparser
import logging
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml
from dotenv import dotenv_values

try:
    parent_dir = Path(__file__)
    sys.path.append(str(parent_dir.parents[0]))
    sys.path.append(str(parent_dir.parents[1]))
except Exception as e:
    raise (e)

from file_paths import ProjectPaths

file_paths = ProjectPaths()


def get_project_logger(logger_name: str) -> logging.Logger:
    """
    Set up a logger for the project.

    Args:
        logger_name: The name of the logger.

    Returns:
        A Logger object.
    """
    logger = logging.getLogger(logger_name)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        log_format = "%(asctime)s %(levelname)s -- %(message)s"
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_init_params(cls: type, excluded_vars: Optional[list[str]] = None):
    """
    Log the class initialization parameters. Apply this function as a decorator to the class.

    Args:
        cls (Type): The class to be decorated.
        excluded_vars (List[str]): A list of variable names to exclude from logging. For example, passwords and secrets.

    Returns:
        Type: The decorated class.
    """
    if excluded_vars is None:
        excluded_vars = []
    original_init = cls.__init__
    logger = get_project_logger(__name__)

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        filtered_kwargs = {key: value for key, value in kwargs.items() if key not in excluded_vars}
        output_string = ", \n".join([f"\t\t{key}: {value}" for key, value in filtered_kwargs.items()])
        logger.debug(f"Initialized {cls.__name__} with the following parameters:\n{output_string}")

    cls.__init__ = new_init
    return cls


def trace(func: callable) -> callable:
    """
    Print the execution time for the decorated function.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The decorated function.
    """
    logger = get_project_logger(__name__)

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        dataframe_size = ""
        if isinstance(result, pd.DataFrame):
            dataframe_size = f": Created a dataframe of shape {result.shape}"
        end = time.time()
        logger.debug(f"{func.__name__} ran in {round(end - start, 2)}s {dataframe_size}")
        return result

    return wrapper


def read_yaml(yaml_file: str) -> Any:
    """
    Read and parse a YAML file.

    Args:
        yaml_file (str): Path to YAML file.

    Returns:
        Any: Parsed YAML file.

    Raises:
        Exception: If failed to load YAML file.
    """
    logger = get_project_logger(__name__)

    with open(yaml_file) as stream:
        try:
            yaml_output = yaml.safe_load(stream)
            logger.info(f"Loaded YAML file: {yaml_file}")
        except yaml.YAMLError as exc:
            logger.exception(f"Failed to load YAML file: {yaml_file}")
            raise Exception(f"Failed to load YAML file: {yaml_file}") from exc

    return yaml_output


def save_dataframe(df: pd.DataFrame, filename: str, filepath: Path, filetype: str) -> None:
    """
    Save a pandas dataframe to the stated location.

    Args:
        df: The pandas DataFrame to be saved.
        filename: The name of the output file (without extension).
        filepath: The path to the output file.
        filetype: The type of file to save. Valid options are 'excel' and 'parquet'.
    """
    if filetype == "excel":
        df.to_excel(filepath.joinpath(f"{filename}.xlsx"))
    elif filetype == "parquet":
        df.to_parquet(filepath.joinpath(f"{filename}.parquet"))
    else:
        raise ValueError(f"Invalid file type specified: {filetype}.")


def load_env_var() -> dict[str, str]:
    """
    Load environment variables from a ".env" file using dotenv.

    Returns:
        Dict[str, str]: A dictionary containing environment variables.

    Raises:
        Exception: If failed to load the environment variables.
    """
    logger = get_project_logger(__name__)

    try:
        env_vars = dotenv_values(file_paths.ENV_DIR)
        logger.info(f"Loaded env file: {file_paths.ENV_DIR}")
    except Exception as e:
        logger.exception(f"Failed to load env file: {file_paths.ENV_DIR}")
        raise Exception(f"Failed to load env file: {file_paths.ENV_DIR}") from e

    return env_vars


def find(lst: list[str], find_value: str) -> list[int]:
    """
    Find the indices of a specific value in the input list.

    Args:
        lst (List[str]): The list to search.
        find_value (str): The value to find.

    Returns:
        List[int]: A list of indices where the value was found.
    """
    return [i for i, x in enumerate(lst) if x == find_value]


def parse_config(filename: str) -> configparser.ConfigParser:
    """
    Parse a configuration file.

    Args:
        filename (str): The name of the configuration file.

    Returns:
        configparser.ConfigParser: The parsed configuration object.
    """
    config = configparser.ConfigParser(strict=False)
    config.read(filename)
    return config


def config_mysql_ssh_args_dict(config: configparser.ConfigParser, section: str = "db.config") -> dict:
    """Configure mysql SSH arguments dictionary.
    Args:
        config (configparser.ConfigParser): _description_

    Returns:
        Dict: _description_
    """
    logger = get_project_logger(__name__)
    args = {}

    try:
        # Handle string type arguments
        string_arguments = [
            "mysql_user",
            "mysql_host",
            # "mysql_port",
            "mysql_db",
            # "ssh_tunnel",
            # "ssh_tunnel_port",
            "ssh_tunnel_user",
            "ssh_tunnel_host",
        ]

        for i in string_arguments:
            args[i] = config.get(section, i)

        # Handle other types of arguments
        args["ssh_tunnel"] = config.getboolean(section, "ssh_tunnel")
        args["ssh_tunnel_port"] = config.getint(section, "ssh_tunnel_port")
        args["mysql_port"] = config.getint(section, "mysql_port")
    except configparser.NoSectionError as e:
        str_output = (
            f"Error due to missing section {section} in your config files. "
            "Make sure the section {section} exists your config.dev.ini or config.prod.ini files."
        )
        logger.error(str_output)
        raise e

    return args