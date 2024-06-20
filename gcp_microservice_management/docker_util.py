import docker
from docker.errors import DockerException
import sys
from .util import color_text
from .constants import OKGREEN, FAIL


def build_docker_client():
    try:
        docker_client = docker.from_env()
        docker_client.ping()
        print(color_text("Docker daemon is running.", OKGREEN))
        return docker_client
    except DockerException as e:
        print(color_text(f"Docker error: {e}", FAIL))
        sys.exit(1)
