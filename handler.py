# handler.py
import base64, io, shutil, subprocess, time, uuid
from pathlib import Path
import requests
from PIL import Image
import runpod

def _load_image_bytes(image_b64=None, image_url=None, max_edge=2048) -> bytes:
    if not (image_b64 or image_url):
        raise ValueError("Provide image_b64 or image_url")
    if image_url:
        r = requests.get(image_url, timeout=30)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
    else:
        raw = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")

    w, h = img.size
    if max(w, h) > max_edge:
        if w >= h:
            img = img.resize((max_edge, int(h * (max_edge / w))), Image.LANCZOS)
        else:
            img = img.resize((int(w * (max_edge / h)), max_edge), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def _run_fawkes_on_dir(src_dir: Path, mode: str, fmt: str) -> Path:
    # clean any prior derived folders
    for p in src_dir.iterdir():
        if p.is_dir():
            shutil.rmtree(p)
    # fawkes CLI: fawkes -d <dir> --mode low|mid|high --format png|jpg
    proc = subprocess.run(
        ["fawkes", "-d", str(src_dir), "--mode", mode, "--format", fmt],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Fawkes failed:\n{proc.stdout}")

    # pick newest/largest image written anywhere under src_dir
    files = [p for p in src_dir.rglob("*")
             if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    if not files:
        raise RuntimeError("No output produced by Fawkes.")
    files.sort(key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)
    return files[0]

def handler(job):
    """
    Input:
      {
        "image_url": "https://...",  // or "image_b64": "<base64>"
        "mode": "low|mid|high",      // default "low"
        "format": "png|jpg",         // default "png"
        "max_edge": 2048             // optional
      }
    Output:
      {
        "image_b64": "<base64>",
        "format": "png|jpg",
        "processing_ms": 12345,
        "mode": "low"
      }
    """
    t0 = time.time()
    try:
        inp = job.get("input") or {}
        mode = (inp.get("mode") or "low").lower()
        fmt  = (inp.get("format") or "png").lower()
        max_edge = int(inp.get("max_edge") or 2048)
        if mode not in {"low", "mid", "high"}: mode = "low"
        if fmt not in {"png", "jpg"}: fmt = "png"

        job_dir = Path("/tmp") / "in" / str(uuid.uuid4())
        job_dir.mkdir(parents=True, exist_ok=True)

        img = _load_image_bytes(inp.get("image_b64"), inp.get("image_url"), max_edge=max_edge)
        (job_dir / "input.png").write_bytes(img)

        out_path = _run_fawkes_on_dir(job_dir, mode=mode, fmt=fmt)
        out_b64 = base64.b64encode(out_path.read_bytes()).decode("utf-8")
        return {
            "image_b64": out_b64,
            "format": out_path.suffix.replace(".", "").lower(),
            "processing_ms": int((time.time() - t0) * 1000),
            "mode": mode
        }
    except Exception as e:
        return {"error": str(e), "processing_ms": int((time.time() - t0) * 1000)}

runpod.serverless.start({"handler": handler})
