"""Measure response time: of the running API (what a user experiences) and of the model alone.

    pip install requests
    # 1) End to end, against the running Django server (start it first, in another terminal):
    python benchmark.py api --url http://127.0.0.1:8000/api/predict/ --image leaf.jpg --n 50
    python benchmark.py api --url http://127.0.0.1:8000/api/predict/ --image data/processed/test/neem --n 100 --concurrency 4

    # 2) The model alone, no web server (run from the folder that contains root/ml_models):
    python benchmark.py model --ckpt root/ml_models/efficientnet_b0_best.pt --image leaf.jpg --n 100

--image may be one file or a folder of images (the images are used in turn). Times are in milliseconds.
The first request/prediction is reported separately: it includes one-off start-up work (loading the model, CUDA set-up),
so it is much slower than the steady state ("warm") requests that follow.
"""
import argparse, io, os, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def load_images(path):
    if os.path.isdir(path):
        files = sorted(os.path.join(path, f) for f in os.listdir(path) if os.path.splitext(f)[1].lower() in IMG_EXT)
    else:
        files = [path]
    if not files:
        sys.exit(f"no images found in {path}")
    return [(os.path.basename(f), open(f, "rb").read()) for f in files]


def summarize(name, ms):
    ms = sorted(ms)
    n = len(ms)
    p95 = ms[min(n - 1, int(0.95 * n))]
    sd = statistics.pstdev(ms) if n > 1 else 0.0
    print(f"{name:<24} mean {statistics.mean(ms):8.1f}  median {statistics.median(ms):8.1f}  p95 {p95:8.1f}  "
          f"min {ms[0]:8.1f}  max {ms[-1]:8.1f}  sd {sd:7.1f}   (n={n})")


def bench_api(a):
    import requests
    images = load_images(a.image)
    kb = sum(len(b) for _, b in images) / len(images) / 1024
    print(f"{len(images)} image(s), average size {kb:.0f} KB; {a.n} requests, concurrency {a.concurrency}")
    session = requests.Session()

    def one(i):
        name, data = images[i % len(images)]
        t0 = time.perf_counter()
        r = session.post(a.url, files={"file": (name, data, "image/jpeg")}, timeout=120)
        return (time.perf_counter() - t0) * 1000, r.status_code

    first_ms, code = one(0)
    print(f"first request (cold)     {first_ms:8.1f} ms   status {code}")
    if code != 200:
        sys.exit("the first request did not return 200; fix that before benchmarking")
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        results = list(ex.map(one, range(a.n)))
    wall = time.perf_counter() - t_start
    ok = [ms for ms, c in results if c == 200]
    bad = len(results) - len(ok)
    if ok:
        summarize("warm requests", ok)
    print(f"failed: {bad} of {len(results)}   throughput: {len(results) / wall:.1f} requests/s (wall time {wall:.1f} s)")


def bench_model(a):
    sys.path.insert(0, a.module_dir)
    import torch
    from PIL import Image, ImageOps
    from ml_models.classifier import PlantClassifier

    images = load_images(a.image)
    t0 = time.perf_counter()
    clf = PlantClassifier(a.ckpt)
    load_ms = (time.perf_counter() - t0) * 1000
    on_gpu = str(clf.device).startswith("cuda")
    print(f"device {clf.device}; {len(clf.classes)} classes; model load {load_ms:.0f} ms")

    def sync():
        if on_gpu:
            torch.cuda.synchronize()

    def run(data):
        t = time.perf_counter()
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        t_decode = time.perf_counter()
        x = clf.tf(im).unsqueeze(0).to(clf.device)
        sync()
        t_prep = time.perf_counter()
        with torch.inference_mode():
            probs = torch.softmax(clf.model(x), dim=1)[0]
            sync()
        t_fwd = time.perf_counter()
        return ((t_decode - t) * 1000, (t_prep - t_decode) * 1000, (t_fwd - t_prep) * 1000, (t_fwd - t) * 1000)

    first = run(images[0][1])
    print(f"first prediction (warm-up) {first[3]:8.1f} ms")
    for _ in range(a.warmup):
        run(images[0][1])
    rows = [run(images[i % len(images)][1]) for i in range(a.n)]
    for k, label in enumerate(["decode image", "resize + normalise", "model forward + softmax", "total prediction"]):
        summarize(label, [r[k] for r in rows])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("api"); p.set_defaults(fn=bench_api)
    p.add_argument("--url", required=True); p.add_argument("--image", required=True)
    p.add_argument("--n", type=int, default=50); p.add_argument("--concurrency", type=int, default=1)
    m = sub.add_parser("model"); m.set_defaults(fn=bench_model)
    m.add_argument("--ckpt", required=True); m.add_argument("--image", required=True)
    m.add_argument("--n", type=int, default=100); m.add_argument("--warmup", type=int, default=5)
    m.add_argument("--module-dir", default="root", help="folder that contains ml_models/ (default: root)")
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
