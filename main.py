"""Executable entry point used by the packaged Flet desktop shell."""

from insightforge.runtime_log import log_runtime, reset_runtime_log

reset_runtime_log()
log_runtime("Package entry point loaded")

try:
    from insightforge.desktop import main, run_app
except BaseException as error:
    log_runtime("Package imports failed", error)
    raise

__all__ = ["main", "run_app"]


if __name__ == "__main__":
    log_runtime("Starting Flet runner")
    try:
        run_app()
    except BaseException as error:
        log_runtime("Flet runner failed", error)
        raise
