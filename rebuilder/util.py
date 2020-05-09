from subprocess import run
from os import environ


def run_command(cmd, cwd=".", ignore_errors=False, capture=False, env={}, timeout=None):
    """
    Run a command in shell
    """
    print("Running {} in {}".format(cmd, cwd))
    current_env = environ.copy()
    current_env.update(env)
    proc = run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        env=current_env,
        timeout=timeout,
    )

    if proc.returncode and not ignore_errors:
        print("Error running {}".format(cmd))
        quit()

    if capture:
        print(proc.stderr)
        return proc.stdout
