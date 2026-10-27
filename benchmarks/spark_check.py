"""Read-only NVIDIA DGX Spark readiness report; installs and changes nothing."""
from __future__ import annotations

import json
import platform
from shutil import disk_usage, which
import subprocess


def check() -> dict:
    result = {"architecture": platform.machine(), "os": platform.platform(),
              "free_disk_gb": round(disk_usage(".").free / (1024 ** 3), 2),
              "nvidia_smi_available": bool(which("nvidia-smi")),
              "docker_available": bool(which("docker"))}
    if which("nvidia-smi"):
        try:
            cp = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used",
                                 "--format=csv,noheader"], capture_output=True, text=True,
                                timeout=8, check=True)
            result["gpu"] = cp.stdout.strip()
        except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            result["gpu_error"] = str(e)
    try:
        import torch
        result["torch_version"] = torch.__version__
        result["cuda_available"] = torch.cuda.is_available()
    except ImportError:
        result["torch_version"] = "not installed"
    return result


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
