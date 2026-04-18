import uuid
import os
from pathlib import Path


def generate_job_id() -> str:
    return str(uuid.uuid4())


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def build_temp_path(job_id: str, filename: str, base_dir: str) -> str:
    dir_path = os.path.join(base_dir, job_id)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, filename)


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b != 0 else default
