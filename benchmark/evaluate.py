"""
DesiCaptions — Evaluation & Chart Generation
Reads benchmark results JSON → computes WER stats → generates matplotlib charts.

Usage:
    python benchmark/evaluate.py --results_dir results --charts_dir results/charts
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import matplotlib
    matplotlib.use("Agg")   # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: matplotlib not installed. Run: pip install matplotlib")


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

SARVAM_COLOR = "#FF6B35"   # Orange (Indian flag inspired)
WHISPER_COLOR = "#4A90D9"  # Blue


def generate_charts(results_dir: str, charts_dir: str):
    """Load JSON results and generate bar charts for project report."""
    Path(charts_dir).mkdir(parents=True, exist_ok=True)

    summary_path = Path(results_dir) / "summary.json"
    if not summary_path.exists():
        print(f"ERROR: No summary.json found at {results_dir}")
        print("Run benchmark.py first.")
        return

    with open(summary_path) as f:
        summary = json.load(f)

    rows = summary.get("rows", [])
    if not rows:
        print("No data in summary.json")
        return

    # Filter valid rows
    valid_rows = [r for r in rows if r["sarvam_wer"] >= 0 or r["whisper_wer"] >= 0]
    if not valid_rows:
        print("No valid WER data to chart")
        return

    languages = [r["language"].title() for r in valid_rows]
    sarvam_wers = [r["sarvam_wer"] * 100 if r["sarvam_wer"] >= 0 else 0 for r in valid_rows]
    whisper_wers = [r["whisper_wer"] * 100 if r["whisper_wer"] >= 0 else 0 for r in valid_rows]

    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib unavailable — skipping chart generation")
        _print_ascii_chart(languages, sarvam_wers, whisper_wers)
        return

    # -------------------------------------------------------
    # Chart 1: Grouped bar — WER by language
    # -------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(languages))
    bar_width = 0.35

    bars_sarvam = ax.bar(x - bar_width/2, sarvam_wers, bar_width,
                         label="Sarvam AI Saaras", color=SARVAM_COLOR, edgecolor="white")
    bars_whisper = ax.bar(x + bar_width/2, whisper_wers, bar_width,
                          label="OpenAI Whisper large-v3", color=WHISPER_COLOR, edgecolor="white")

    # Add value labels on bars
    for bar in bars_sarvam:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2., h + 0.3,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    for bar in bars_whisper:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2., h + 0.3,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xlabel("Language Mix", fontsize=12)
    ax.set_ylabel("Word Error Rate (%)", fontsize=12)
    ax.set_title("DesiCaptions — WER Benchmark: Sarvam AI vs OpenAI Whisper\n(Lower is Better)", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(languages, fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, max(max(sarvam_wers), max(whisper_wers)) * 1.2 + 5)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    chart1_path = Path(charts_dir) / "wer_comparison_by_language.png"
    plt.tight_layout()
    plt.savefig(chart1_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {chart1_path}")

    # -------------------------------------------------------
    # Chart 2: Average WER comparison (single grouped bar)
    # -------------------------------------------------------
    valid_sarvam = [r["sarvam_wer"] * 100 for r in valid_rows if r["sarvam_wer"] >= 0]
    valid_whisper = [r["whisper_wer"] * 100 for r in valid_rows if r["whisper_wer"] >= 0]
    avg_sarvam = sum(valid_sarvam) / len(valid_sarvam) if valid_sarvam else 0
    avg_whisper = sum(valid_whisper) / len(valid_whisper) if valid_whisper else 0

    fig, ax = plt.subplots(figsize=(6, 5))
    models = ["Sarvam AI\nSaaras v1", "OpenAI Whisper\nlarge-v3"]
    avgs = [avg_sarvam, avg_whisper]
    colors = [SARVAM_COLOR, WHISPER_COLOR]

    bars = ax.bar(models, avgs, color=colors, width=0.4, edgecolor="white")
    for bar, val in zip(bars, avgs):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=13, fontweight="bold")

    ax.set_ylabel("Average WER (%)", fontsize=12)
    ax.set_title("Average WER Across All Languages\n(Lower is Better)", fontsize=13)
    ax.set_ylim(0, max(avgs) * 1.3 + 3)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    chart2_path = Path(charts_dir) / "wer_average_comparison.png"
    plt.tight_layout()
    plt.savefig(chart2_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {chart2_path}")

    # -------------------------------------------------------
    # Print summary table
    # -------------------------------------------------------
    print("\n" + "="*65)
    print("WER RESULTS SUMMARY")
    print("="*65)
    print(f"{'Language':<18} {'Sarvam WER':>12} {'Whisper WER':>12} {'Winner':>10}")
    print("-"*65)
    for row in valid_rows:
        sw = f"{row['sarvam_wer']*100:.1f}%" if row['sarvam_wer'] >= 0 else "N/A"
        ww = f"{row['whisper_wer']*100:.1f}%" if row['whisper_wer'] >= 0 else "N/A"
        print(f"{row['language']:<18} {sw:>12} {ww:>12} {row['better_model']:>10}")
    print("-"*65)
    print(f"{'AVERAGE':<18} {avg_sarvam:>11.1f}% {avg_whisper:>11.1f}%")
    print("="*65)


def _print_ascii_chart(languages, sarvam_wers, whisper_wers):
    """Fallback ASCII chart when matplotlib is unavailable."""
    print("\nASCII WER Chart (S = Sarvam, W = Whisper):")
    max_val = max(max(sarvam_wers), max(whisper_wers))
    for lang, sw, ww in zip(languages, sarvam_wers, whisper_wers):
        s_bar = "█" * int(sw / max_val * 30)
        w_bar = "█" * int(ww / max_val * 30)
        print(f"{lang:<12} S: {s_bar:<30} {sw:.1f}%")
        print(f"{'':12} W: {w_bar:<30} {ww:.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DesiCaptions — WER Evaluation & Charts")
    parser.add_argument("--results_dir", default="results")
    parser.add_argument("--charts_dir", default="results/charts")
    args = parser.parse_args()

    print("Generating evaluation charts...")
    generate_charts(args.results_dir, args.charts_dir)
    print("Done!")
