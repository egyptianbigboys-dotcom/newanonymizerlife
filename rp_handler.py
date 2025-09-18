import base64, io, shutil, subprocess, time, uuid
from pathlib import Path
import requests
from PIL import Image
import runpod

def load_image_to_bytes(image_b64=None, image_url=None, max_edge=2048):
    if not (image_b64 or image_url):
        raise ValueError("Provide image_b64 or image_url")
    if image_url:
        r = requests.get(image_url, timeout=30); r.raise_for_status()
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
    out = io.BytesIO(); img.save(out, format="PNG")
    return out.getvalue()

def run_fawkes_on_dir(src_dir: Path, mode: str, fmt: str):
    # clean derived folders (idempotent)
    for p in src_dir.iterdir():
        if p.is_dir():
            shutil.rmtree(p)
    # call CLI per Fawkes usage: fawkes -d ./imgs --mode low --format png
    proc = subprocess.run(
        ["fawkes", "-d", str(src_dir), "--mode", mode, "--format", fmt],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Fawkes failed: {proc.stdout}")

def pick_output(src_dir: Path):
    before = set()
    after = set(p for p in src_dir.rglob("*") if p.is_file())
    # Prefer newly generated files (largest / latest)
    files = sorted(after, key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)
    for p in files:
        if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
            return p
    raise RuntimeError("No output produced by Fawkes.")

def handler(event):
    t0 = time.time()
    inp = event.get("input") or {}
    mode = (inp.get("mode") or "low").lower()
    fmt  = (inp.get("format") or "png").lower()
    max_edge = int(inp.get("max_edge") or 2048)
    if mode not in {"low", "mid", "high"}: mode = "low"
    if fmt not in {"png", "jpg"}: fmt = "png"

    job_dir = Path(f"/tmp/in/{uuid.uuid4()}"); job_dir.mkdir(parents=True, exist_ok=True)
    raw = load_image_to_bytes(inp.get("image_b64"), inp.get("image_url"), max_edge=max_edge)
    (job_dir / "input.png").write_bytes(raw)

    run_fawkes_on_dir(job_dir, mode, fmt)
    out_path = pick_output(job_dir)

    b64 = base64.b64encode(out_path.read_bytes()).decode("utf-8")
    return {"status": "COMPLETED",
            "output": {"image_b64": b64,
                       "format": out_path.suffix.replace('.', '').lower(),
                       "processing_ms": int((time.time() - t0) * 1000),
                       "mode": mode}}

runpod.serverless.start({"handler": handler})
