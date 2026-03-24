from importlib.metadata import PackageNotFoundError, version as package_version

from .server import FQServer, build_config_from_env, setup_server
from .settings import FQConfig, QueueServerSettings

try:
    __version__ = package_version("queue-server")
except PackageNotFoundError:
    __version__ = "1.0.0"

__all__ = [
    "FQConfig",
    "FQServer",
    "QueueServerSettings",
    "build_config_from_env",
    "setup_server",
]
