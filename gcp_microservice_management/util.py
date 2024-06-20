import subprocess
import os
import time
from google.api_core.exceptions import NotFound
from .constants import ENDC, WARNING, OKBLUE, BOLD, FAIL


def color_text(text, color_code):
    return f"{color_code}{text}{ENDC}"


def wait_for_deletion(get_func, name):
    while True:
        try:
            get_func(name=name)
            print(
                color_text(
                    f"Waiting for {name} to be completely deleted...", WARNING
                )
            )
            time.sleep(5)
        except NotFound:
            break


def run_command(command, env=None):
    redacted_command = command.replace(
        os.getenv("DATABASE_PASSWORD", ""), "****"
    )
    print(color_text(f"Running command: {redacted_command}", OKBLUE + BOLD))
    result = subprocess.run(
        command, shell=True, env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(color_text(f"Command failed: {redacted_command}", FAIL))
        print(result.stderr)
        raise RuntimeError(result.stderr)
    return result.stdout
