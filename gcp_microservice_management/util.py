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
    db_password = os.getenv("DATABASE_PASSWORD", "")
    if db_password:
        redacted_command = command.replace(db_password, "****")
    else:
        redacted_command = command
    print(color_text(f"Running command: {redacted_command}", OKBLUE + BOLD))

    process = subprocess.Popen(
        command,
        shell=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # line-buffered
    )

    # Stream output line by line as it arrives.
    for line in process.stdout:
        print(line, end="")  # already includes newline

    process.wait()
    if process.returncode != 0:
        print(color_text(f"Command failed: {redacted_command}", FAIL))
        raise RuntimeError(
            f"Command failed with return code {process.returncode}"
        )
