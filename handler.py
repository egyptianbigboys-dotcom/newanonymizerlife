# handler.py
import base64, io, os, subprocess, time, uuid
from pathlib import Path

import requests
import runpod

FAWKES_BIN = "/opt/fawkes/protection"  # from Dockerfile

def _save_image_from_input(job_input, work_dir: Path) -> Path:
    img_path = work_dir / "input.jpg"  # binary accepts dir; format is set by flag
    if "image_url" in job_input and job_input["image_url"]:
        r = requests.get(job_input["image_url"], timeout=30)
        r.raise_for_status()
        img_path.write_bytes(r.content)
    elif "image_b64" in job_input and job_input["image_b64"]:
        img_path.write_bytes(base64.b64decode(job_input["image_b64"]))
    else:
        raise ValueError("Provide image_url or image_b64")
    return img_path

def _call_fawkes(directory: Path, mode: str, fmt: str):
    # Example CLI from the official README/release
    # fawkes binary is named "protection", flags are same as pip CLI
    cmd = [FAWKES_BIN, "-d", str(directory), "--mode", mode, "--format", fmt]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Fawkes binary failed:\n{proc.stdout}")
    # Fawkes writes output images next to input; pick the newest/ largest written
    files = [p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    if not files:
        raise RuntimeError("Fawkes produced no files.")
    files.sort(key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)
    return files[0]

def handler(job):
    """
    input: { image_url|image_b64, mode: low|mid|high (default low), format: png|jpg (default png) }
    output: { image_b64, format, processing_ms, mode }
    """
    t0 = time.time()
    try:
        inp = job.get("input") or {}
        mode = (inp.get("mode") or "low").lower()
        fmt  = (inp.get("format") or "png").lower()
        if mode not in {"low","mid","high"}: mode = "low"
        if fmt not in {"png","jpg"}: fmt = "png"

        work = Path("/tmp/in") / str(uuid.uuid4())
        work.mkdir(parents=True, exist_ok=True)

        _ = _save_image_from_input(inp, work)
        out_path = _call_fawkes(work, mode, fmt)

        b64 = base64.b64encode(out_path.read_bytes()).decode("utf-8")
        return {
            "image_b64": b64,
            "format": out_path.suffix.replace(".","").lower(),
            "processing_ms": int((time.time()-t0)*1000),
            "mode": mode
        }
    except Exception as e:
        return {"error": str(e), "processing_ms": int((time.time()-t0)*1000)}

runpod.serverless.start({"handler": handler})
