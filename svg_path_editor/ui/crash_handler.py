import os
import platform
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import Tk, messagebox


LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
CHILD_ENV_KEY = "SVG_EDITOR_CHILD_PROCESS"


class CrashHandler:
    def __init__(self, root):
        self.root = root
        self._installed = False
        self._handling = False

    def install(self):
        if self._installed:
            return
        self.root.report_callback_exception = self._report_tk_exception
        sys.excepthook = self._report_sys_exception
        if hasattr(threading, "excepthook"):
            threading.excepthook = self._report_thread_exception
        self._installed = True

    def wrap(self, callback, source: str):
        def guarded(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception as exc:  # pragma: no cover - UI safety wrapper
                self._handle_exception(type(exc), exc, exc.__traceback__, source=source)
                return None

        return guarded

    def show_exception(self, exc: BaseException, source: str):
        self._handle_exception(type(exc), exc, exc.__traceback__, source=source)

    def _report_tk_exception(self, exc_type, exc_value, exc_traceback):
        self._handle_exception(exc_type, exc_value, exc_traceback, source="Tk 回调")

    def _report_sys_exception(self, exc_type, exc_value, exc_traceback):
        self._handle_exception(exc_type, exc_value, exc_traceback, source="主线程")

    def _report_thread_exception(self, args):
        self._handle_exception(args.exc_type, args.exc_value, args.exc_traceback, source=f"线程 {args.thread.name}")

    def _handle_exception(self, exc_type, exc_value, exc_traceback, source: str):
        if self._handling:
            return
        self._handling = True
        try:
            log_path = write_python_exception_log(exc_type, exc_value, exc_traceback, source)
            summary = f"程序发生异常，已记录到日志：\n{log_path}\n\n异常来源：{source}\n{exc_type.__name__}: {exc_value}"
            try:
                show_topmost_error_dialog("程序异常", summary, parent=self.root)
            except Exception:
                pass
        finally:
            self._handling = False


def ensure_log_dir() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def write_python_exception_log(exc_type, exc_value, exc_traceback, source: str) -> Path:
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"crash_{timestamp}.log"
    traceback_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_path.write_text(
        "\n".join(
            [
                f"time: {datetime.now().isoformat()}",
                f"source: {source}",
                f"python: {sys.version}",
                f"platform: {platform.platform()}",
                "",
                traceback_text,
            ]
        ),
        encoding="utf-8",
    )
    return log_path


def write_process_crash_log(return_code: int, stdout_text: str, stderr_text: str) -> Path:
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"process_crash_{timestamp}.log"
    log_path.write_text(
        "\n".join(
            [
                f"time: {datetime.now().isoformat()}",
                "source: 子进程异常退出",
                f"python: {sys.version}",
                f"platform: {platform.platform()}",
                f"return_code: {return_code}",
                "",
                "[stdout]",
                stdout_text or "<empty>",
                "",
                "[stderr]",
                stderr_text or "<empty>",
            ]
        ),
        encoding="utf-8",
    )
    return log_path


def show_topmost_error_dialog(title: str, message: str, parent=None):
    host = parent
    temp_root = None
    restore_topmost = False
    try:
        if host is None:
            temp_root = Tk()
            host = temp_root
            host.withdraw()

        try:
            host.update_idletasks()
        except Exception:
            pass

        try:
            host.attributes("-topmost", True)
            restore_topmost = True
        except Exception:
            pass

        try:
            host.lift()
        except Exception:
            pass

        try:
            host.focus_force()
        except Exception:
            pass

        messagebox.showerror(title, message, parent=host)
    finally:
        if restore_topmost and host is not None:
            try:
                host.attributes("-topmost", False)
            except Exception:
                pass
        if temp_root is not None:
            try:
                temp_root.destroy()
            except Exception:
                pass


def show_process_crash_dialog(log_path: Path, return_code: int):
    show_topmost_error_dialog(
        "程序崩溃",
        f"程序因严重错误退出。\n\n退出码：{return_code}\n日志文件：{log_path}",
    )


def run_guarded_process(script_path: Path) -> int:
    if os.environ.get(CHILD_ENV_KEY) == "1":
        return 0

    env = os.environ.copy()
    env[CHILD_ENV_KEY] = "1"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log_path = write_process_crash_log(result.returncode, result.stdout, result.stderr)
        show_process_crash_dialog(log_path, result.returncode)
    return result.returncode
