import os
import sys
from pathlib import Path
import pandas as pd
import pymysql
import sshtunnel
import yaml
from sqlalchemy import create_engine
from yaml.loader import SafeLoader
from typing import Optional

try:
    parent_dir = Path(__file__).parents
    sys.path.append(str(parent_dir[1]))
except Exception as e:
    raise (e)

from python_helper import trace, get_project_logger, parse_config, config_mysql_ssh_args_dict
from file_paths import ProjectPaths

file_paths = ProjectPaths()
logger = get_project_logger(logger_name=__name__)

class DBConnector:
    """
    Class for DB Connection.
    """

    initiated = False

    def __init__(
        self,
        mysql_host: Optional[str] = None,
        mysql_user: Optional[str] = None,
        mysql_db: Optional[str] = None,
        mysql_port: Optional[int] = None,
        mysql_password: Optional[str] = None,
        ssh_tunnel: Optional[bool] = None,
        ssh_tunnel_host: Optional[str] = None,
        ssh_tunnel_user: Optional[str] = None,
        ssh_tunnel_port: Optional[int] = None,
        auto_load_credentials: bool = True,
        connection_name: str = "staging1",
    ):
        """
        Initialize the DBConnector and set up credentials.
        """
        DBConnector.initiated = True
        self.mysql_local_host = "127.0.0.1"
        self.charset = "utf8mb4"
        self.connection = None

        self.initialize_credentials(
            mysql_host, mysql_user, mysql_db, mysql_port, mysql_password,
            ssh_tunnel, ssh_tunnel_host, ssh_tunnel_user, ssh_tunnel_port,
            auto_load_credentials, connection_name
        )

        self.load_ssh_settings(file_paths.CONFIG_DIR)
        self.log_initialization()
        self.open_tunnel()

    def initialize_credentials(
        self, mysql_host, mysql_user, mysql_db, mysql_port, mysql_password,
        ssh_tunnel, ssh_tunnel_host, ssh_tunnel_user, ssh_tunnel_port,
        auto_load_credentials, connection_name
    ):
        """
        Initialize the credentials based on provided inputs or load automatically.
        """
        if all(v is None for v in [mysql_host, mysql_user, mysql_db, mysql_port, mysql_password, ssh_tunnel, ssh_tunnel_host, ssh_tunnel_user, ssh_tunnel_port]):
            if not auto_load_credentials:
                logger.warning("DB credentials not provided, but auto_load_credentials set to False. Defaulting to auto loading.")
            self.load_credentials_automatically(file_paths.CONFIG_DIR, connection_name)
        elif all(v is not None for v in [mysql_host, mysql_user, mysql_db, mysql_port, mysql_password, ssh_tunnel, ssh_tunnel_host, ssh_tunnel_user, ssh_tunnel_port]):
            if auto_load_credentials:
                logger.warning("DB credentials provided, but auto_load_credentials set to True. Using provided credentials.")
            self.set_credentials(mysql_host, mysql_user, mysql_db, mysql_port, mysql_password, ssh_tunnel, ssh_tunnel_host, ssh_tunnel_user, ssh_tunnel_port)
        else:
            logger.error("DB credentials only partially provided.")

    def load_credentials_automatically(self, config_path, connection_name):
        """
        Load credentials either from environment variables or a YAML configuration file.
        """
        if connection_name == "env":
            db_config = self.load_credentials_from_env()
        else:
            db_config = self.load_credentials_from_file(config_path, connection_name)
        
        self.validate_credentials(db_config)
        self.set_credentials(**db_config)

    def load_credentials_from_env(self):
        """
        Load credentials from environment variables.
        """
        return {
            "mysql_host": os.getenv("MYSQL_HOST"),
            "mysql_user": os.getenv("MYSQL_USER"),
            "mysql_db": os.getenv("MYSQL_DB"),
            "mysql_port": int(os.getenv("MYSQL_PORT")),
            "mysql_password": os.getenv("MYSQL_PASSWORD"),
            "ssh_tunnel": os.getenv("SSH_TUNNEL"),
            "ssh_tunnel_host": os.getenv("SSH_TUNNEL_HOST"),
            "ssh_tunnel_user": os.getenv("SSH_TUNNEL_USER"),
            "ssh_tunnel_port": int(os.getenv("SSH_TUNNEL_PORT")),
        }

    def load_credentials_from_file(self, config_path, connection_name):
        """
        Load credentials from a YAML configuration file.
        """
        try:
            with open(config_path.joinpath("db_config.yaml")) as f:
                db_config_yaml = yaml.load(f, Loader=SafeLoader)

                if connection_name in db_config_yaml:
                    return db_config_yaml[connection_name]
                else:
                    raise ValueError(f"{connection_name} not found in db_config.yaml, available: {list(db_config_yaml.keys())}")
        except FileNotFoundError:
            logger.error("db_config.yaml file not found in your config folder!")
            raise

    def validate_credentials(self, db_config):
        """
        Ensure all required credentials are loaded.
        """
        required_keys = ["mysql_host", "mysql_user", "mysql_db", "mysql_port", "mysql_password", "ssh_tunnel", "ssh_tunnel_host", "ssh_tunnel_user", "ssh_tunnel_port"]
        if not all(db_config.get(key) is not None for key in required_keys):
            raise ValueError("Not all credentials loaded")

    def set_credentials(self, mysql_host, mysql_user, mysql_db, mysql_port, mysql_password, ssh_tunnel, ssh_tunnel_host, ssh_tunnel_user, ssh_tunnel_port):
        """
        Set the credentials as instance variables.
        """
        self.mysql_host = mysql_host
        self.mysql_user = mysql_user
        self.mysql_db = mysql_db
        self.mysql_port = mysql_port
        self.__mysql_password = mysql_password
        self.ssh_tunnel = ssh_tunnel
        self.ssh_tunnel_host = ssh_tunnel_host
        self.ssh_tunnel_user = ssh_tunnel_user
        self.ssh_tunnel_port = ssh_tunnel_port

    def load_ssh_settings(self, config_path):
        """
        Load SSH settings from the configuration file or environment variables.
        """
        try:
            with open(config_path.joinpath("ssh_config.yaml")) as f:
                ssh_config_yaml = yaml.load(f, Loader=SafeLoader)
                self.ssh_private_key_path = ssh_config_yaml.get("ssh_private_key_path", "~/.ssh/id_rsa")
                self.ssh_private_key_pass = ssh_config_yaml.get("ssh_private_key_pass", None)
        except FileNotFoundError:
            logger.warning("ssh_config.yaml file not found in your config folder. Falling back to environment variables.")
            self.ssh_private_key_path = os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa")
            self.ssh_private_key_pass = os.getenv("SSH_KEY_PASS", None)

    def log_initialization(self):
        """
        Log the initialized state of the DBConnector.
        """
        logger.info(f"""
            Initialized DBConnector with the following parameters:
            mysql_local_host: {self.mysql_local_host},
            charset: {self.charset},
            mysql_host: {self.mysql_host},
            mysql_user: {self.mysql_user},
            mysql_db: {self.mysql_db},
            mysql_port: {self.mysql_port},
            mysql_password: {'Filled in' if self.__mysql_password else 'Not provided'},
            ssh_tunnel: {self.ssh_tunnel},
            ssh_tunnel_host: {self.ssh_tunnel_host},
            ssh_tunnel_user: {self.ssh_tunnel_user},
            ssh_tunnel_port: {self.ssh_tunnel_port},
            ssh_private_key_path: {self.ssh_private_key_path},
            ssh_private_key_pass: {'Provided' if self.ssh_private_key_pass else 'Not provided'}
        """)

    def get_home_ssh_key(self):
        """
        Return SSH key from the local machine.
        """
        key_path = os.path.expanduser(self.ssh_private_key_path)
        if os.path.exists(key_path):
            with open(key_path) as ssh:
                return ssh.read().rstrip()
        else:
            logger.warning(f"SSH Key not found at {key_path}. DBConnector may fail due to missing SSH private key!")
            return None

    @trace
    def open_tunnel(self):
        """Open a database connection if not already open or if it's closed."""
        if self.connection is None or not self.connection.open:
            self.tunnel = sshtunnel.SSHTunnelForwarder(
                (self.ssh_tunnel_host, self.ssh_tunnel_port),
                ssh_username=self.ssh_tunnel_user,
                ssh_pkey=self.ssh_private_key_path,
                remote_bind_address=(self.mysql_host, self.mysql_port),
                ssh_private_key_password=self.ssh_private_key_pass,
                allow_agent=False
            )
            self.tunnel.start()

    def open_connection(self):            
        self.connection = pymysql.connect(
                host=self.mysql_local_host,
                user=self.mysql_user,
                passwd=self.__mysql_password,
                db=self.mysql_db,
                port=self.tunnel.local_bind_port,
                charset=self.charset,
            )

    @trace
    def close_connection(self):
        """Close the database connection."""
        if self.connection and self.connection.open:
            self.connection.close()
            self.connection = None

    @trace
    def query_data(self, query, params=None):
        """
        Run a query to retrieve data from the database.
        """
        self.open_connection()
        return pd.read_sql_query(query, self.connection, params)

    @trace
    def insert_data(self, query, params=None):
        """
        Run an insert query in the database.
        """
        self.execute_query(query, params)

    @trace
    def execute_query(self, query, params=None):
        """
        Execute a query with the existing database connection.
        """
        self.open_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            self.connection.commit()

    @trace
    def insert_dataframe_in_batch(self, df: pd.DataFrame, target_table_name: str, batch_size: int = 1000):
        """
        Insert a pandas DataFrame into a MySQL table in batches.
        """
        try:
            self.open_connection()
            if self.connection is None or not self.connection.open:
                logger.error("Failed to establish database connection.")
                return

            engine = create_engine('mysql+pymysql://', creator=lambda: self.connection)
            df.to_sql(target_table_name, con=engine, if_exists="append", index=False, chunksize=batch_size)

        except Exception as e:
            logger.exception(f"Skipped insert_dataframe_in_batch due to an exception: {e}")
            if 'engine' in locals():
                engine.dispose()


def example_run():
    # Parse config file
    config_file = file_paths.CONFIG_DIR.joinpath("config.dev.ini")
    config_args = parse_config(config_file)
    config_dict = config_mysql_ssh_args_dict(config_args, "staging2")

    # Use
    db_conn = DBConnector(mysql_password=os.getenv("MYSQL_PASSWORD_DEV"), **config_dict)
    _ = db_conn.query_data("SELECT * FROM news")

# example_run()