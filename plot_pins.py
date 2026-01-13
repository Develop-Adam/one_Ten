from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Sample:
    t: datetime
    d4: Optional[int]
    d5: Optional[int]
    d6: Optional[int]
    d7: Optional[int]


def _parse_ts(ts: str) -> datetime:
    # Handles "2026-01-13T04:32:10.123456Z" or "+00:00"
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def read_ndjson(path: str, since_seconds: Optional[int] = None) -> List[Sample]:
    """
    Reads NDJSON file into a list of Sample.
    If since_seconds is set, filters to only keep samples newer than (now - since_seconds).
    """
    cutoff: Optional[datetime] = None
    if since_seconds is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=since_seconds)

    out: List[Sample] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                t = _parse_ts(rec["ts_utc"])
                if cutoff and t < cutoff:
                    continue
                out.append(
                    Sample(
                        t=t,
                        d4=rec.get("d4"),
                        d5=rec.get("d5"),
                        d6=rec.get("d6"),
                        d7=rec.get("d7"),
                    )
                )
            except Exception:
                # ignore malformed lines
                continue

    out.sort(key=lambda s: s.t)
    return out


def downsample(samples: List[Sample], max_points: int) -> List[Sample]:
    """
    Simple downsample: keep at most max_points evenly spaced samples.
    Good enough for plotting huge logs quickly.
    """
    n = len(samples)
    if max_points <= 0 or n <= max_points:
        return samples
    step = n / max_points
    idx = [int(i * step) for i in range(max_points)]
    # ensure last point is included
    if idx[-1] != n - 1:
        idx[-1] = n - 1
    return [samples[i] for i in idx]


def _series(samples: List[Sample], attr: str) -> Tuple[List[datetime], List[float]]:
    xs: List[datetime] = []
    ys: List[float] = []
    for s in samples:
        v = getattr(s, attr)
        if v is None:
            continue
        xs.append(s.t)
        ys.append(float(v))
    return xs, ys


def plot_digital_traces(samples: List[Sample], title: str = "Pin States") -> None:
    """
    Clean and neat plot:
    - 4 traces with vertical offsets so they don't overlap
    - step plot for digital signals
    """
    if not samples:
        print("No samples to plot.")
        return

    pins = [("d4", 0.0), ("d5", 1.5), ("d6", 3.0), ("d7", 4.5)]
    labels = {"d4": "D4", "d5": "D5", "d6": "D6", "d7": "D7"}

    plt.figure()
    for attr, offset in pins:
        xs, ys = _series(samples, attr)
        if not xs:
            continue
        ys_off = [y + offset for y in ys]
        plt.step(xs, ys_off, where="post", label=labels[attr])

    # y ticks that read nicely
    yticks = []
    yticklabels = []
    for attr, offset in pins:
        yticks.extend([offset + 0.0, offset + 1.0])
        yticklabels.extend([f"{labels[attr]}=0", f"{labels[attr]}=1"])

    plt.yticks(yticks, yticklabels)
    plt.xlabel("Time (UTC)")
    plt.title(title)
    plt.grid(True)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.show()


def main():
    ap = argparse.ArgumentParser(description="Plot D4..D7 pin states from NDJSON log.")
    ap.add_argument("--file", required=True, help="Path to NDJSON log (e.g. pin_samples.ndjson)")
    ap.add_argument("--since", type=int, default=None, help="Only plot last N seconds")
    ap.add_argument("--max-points", type=int, default=5000, help="Downsample to at most N points")
    args = ap.parse_args()

    samples = read_ndjson(args.file, since_seconds=args.since)
    samples = downsample(samples, max_points=args.max_points)

    if samples:
        t0, t1 = samples[0].t, samples[-1].t
        title = f"Pin States (UTC)  {t0.isoformat().replace('+00:00','Z')}  →  {t1.isoformat().replace('+00:00','Z')}"
    else:
        title = "Pin States"

    plot_digital_traces(samples, title=title)


if __name__ == "__main__":
    main()
