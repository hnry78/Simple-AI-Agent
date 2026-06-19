import ast
import subprocess
from pathlib import Path
from typing import Any, Dict

WORKSPACE = Path("./agent_workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)

def safe_eval(expr: str) -> Dict[str, Any]:
    """安全计算器：仅允许数学运算"""
    try:
        # 限制全局变量，防止代码注入
        result = eval(expr, {"__builtins__": {}}, {})
        return {"status": "success", "output": str(result)}
    except Exception as e:
        return {"status": "error", "output": f"CalcError: {e}"}

def read_file(filepath: str) -> Dict[str, Any]:
    target = (WORKSPACE / filepath).resolve()
    if not str(target).startswith(str(WORKSPACE)):
        return {"status": "error", "output": "AccessDenied: Path escapes workspace"}
    try:
        return {"status": "success", "output": target.read_text(encoding="utf-8")}
    except Exception as e:
        return {"status": "error", "output": str(e)}

def write_file(filepath: str, content: str) -> Dict[str, Any]:
    target = (WORKSPACE / filepath).resolve()
    if not str(target).startswith(str(WORKSPACE)):
        return {"status": "error", "output": "AccessDenied: Path escapes workspace"}
    try:
        target.write_text(content, encoding="utf-8")
        return {"status": "success", "output": f"Written {len(content)} chars"}
    except Exception as e:
        return {"status": "error", "output": str(e)}
    
def delete_file(filepath: str) -> Dict[str, Any]:
    target = (WORKSPACE / filepath).resolve()
    if not str(target).startswith(str(WORKSPACE)):
        return {"status": "error", "output": "AccessDenied: Path escapes workspace"}
    try:
        target.unlink()
        return {"status": "success", "output": f"Deleted {filepath}"}
    except FileNotFoundError:
        return {"status": "error", "output": f"FileNotFound: {filepath}"}
    except Exception as e:
        return {"status": "error", "output": str(e)}

def run_bash(cmd: str) -> Dict[str, Any]:
    banned = ["rm -rf", "sudo", "curl", "wget", "nc", "mkfs", "dd"]
    #防止危险命令
    if any(b in cmd.lower() for b in banned):
        return {"status": "error", "output": "CommandBlocked: Potentially dangerous"}
    try:
        res = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True, timeout=15,
            cwd=WORKSPACE,
        )
        output = res.stdout if res.returncode == 0 else res.stderr
        return {"status": "success" if res.returncode == 0 else "error", "output": output.strip()}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Timeout: >15s"}
    except Exception as e:
        return {"status": "error", "output": f"BashError: {e}"}

# 工具注册表
TOOL_REGISTRY = {
    "calculator": safe_eval,
    "read_file": read_file,
    "write_file": write_file,
    "run_bash": run_bash,
    "delete_file": delete_file,
}