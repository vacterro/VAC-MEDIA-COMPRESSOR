import os
import shutil
import subprocess
import threading

_tool_cache = {}
_active_processes = set()
_process_lock = threading.Lock()

def find_tool(name: str) -> str:
    """Find a tool in PATH with caching."""
    if name in _tool_cache:
        return _tool_cache[name]
    found = shutil.which(name)
    result = found if found else ""
    _tool_cache[name] = result
    return result

def run_subprocess(cmd: list, timeout: int = None) -> tuple[bool, str]:
    """Run a subprocess with cancellation support."""
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags
        )
        
        with _process_lock:
            _active_processes.add(proc)
            
        try:
            out, err = proc.communicate(timeout=timeout)
        finally:
            with _process_lock:
                _active_processes.discard(proc)
                
        if proc.returncode != 0:
            # If terminated externally (e.g. cancelled), returncode is usually negative (e.g. -15) or 1
            if proc.returncode < 0 or err.strip() == "":
                return False, "Process was cancelled or terminated."
            return False, (err or out).strip()
            
        return True, out.strip()
    except subprocess.TimeoutExpired:
        with _process_lock:
            _active_processes.discard(proc)
        proc.terminate()
        return False, "Process timed out."
    except Exception as e:
        return False, str(e)

def cancel_all_subprocesses():
    """Gracefully terminate all running subprocesses."""
    with _process_lock:
        for proc in _active_processes:
            try:
                proc.terminate()
            except Exception:
                pass
        _active_processes.clear()
