"""
DesiCaptions — Benchmarking Script
WER comparison: Sarvam AI vs OpenAI Whisper on code-mixed Indian audio.
Dataset: Kathbath (AI4Bharat, IIT Madras)

Usage:
    python benchmark/benchmark.py --data_dir benchmark/data --output_dir results
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.asr_router import ASRRouter
from modules.audio_processor import AudioProcessor

try:
    from jiwer import wer as compute_wer, cer as compute_cer
    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False
    print("WARNING: jiwer not installed. Run: pip install jiwer")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LANGUAGES = ["hinglish", "benglish", "tanglish", "tenglish", "odiaenglish"]
CLIPS_PER_LANGUAGE = 50   # Adjust based on Kathbath subset you download


def run_benchmark(
    data_dir: str,
    output_dir: str,
    languages: List[str] = LANGUAGES,
    clips_per_lang: int = CLIPS_PER_LANGUAGE,
):
    """
    Main benchmark runner.
    
    Expected data_dir structure:
        data/hinglish/  → audio .wav files
        data/hinglish_refs/ → matching .txt reference transcripts
        data/tanglish/
        data/tanglish_refs/
        ... etc
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    asr = ASRRouter(
        sarvam_api_key=os.getenv("SARVAM_API_KEY", ""),
        whisper_model_size="large-v3",  # Use best model for benchmarking
    )
    audio_proc = AudioProcessor()

    all_results = {}

    for lang in languages:
        print(f"\n{'='*60}")
        print(f"Benchmarking: {lang}")
        print(f"{'='*60}")

        audio_dir = Path(data_dir) / lang
        refs_dir = Path(data_dir) / f"{lang}_refs"

        if not audio_dir.exists():
            print(f"  SKIP — no data at {audio_dir}")
            continue

        audio_files = sorted(list(audio_dir.glob("*.wav")))[:clips_per_lang]
        if not audio_files:
            print(f"  SKIP — no .wav files found")
            continue

        lang_results = {
            "language": lang,
            "n_clips": len(audio_files),
            "sarvam": {"transcripts": [], "references": [], "wer_scores": []},
            "whisper": {"transcripts": [], "references": [], "wer_scores": []},
        }

        for i, audio_path in enumerate(audio_files):
            ref_path = refs_dir / (audio_path.stem + ".txt")
            if not ref_path.exists():
                print(f"  [{i+1}/{len(audio_files)}] SKIP {audio_path.name} — no reference")
                continue

            reference = ref_path.read_text(encoding="utf-8").strip()
            print(f"  [{i+1}/{len(audio_files)}] {audio_path.name}")

            try:
                chunks, _ = audio_proc.process_file(str(audio_path))
                if not chunks:
                    print("    → no speech detected, skipping")
                    continue

                # Use first chunk for per-clip benchmark
                audio_bytes = chunks[0]

                # Run both models
                sarvam_seg, whisper_seg = asr.transcribe_both(audio_bytes, lang)

                for model_name, seg in [("sarvam", sarvam_seg), ("whisper", whisper_seg)]:
                    if seg is None:
                        print(f"    → {model_name}: FAILED")
                        continue

                    hyp = seg.text.strip()

                    if JIWER_AVAILABLE and reference:
                        try:
                            score = compute_wer(reference, hyp)
                        except Exception:
                            score = -1.0
                    else:
                        score = -1.0

                    lang_results[model_name]["transcripts"].append(hyp)
                    lang_results[model_name]["references"].append(reference)
                    lang_results[model_name]["wer_scores"].append(score)

                    wer_str = f"{score*100:.1f}%" if score >= 0 else "N/A"
                    print(f"    → {model_name}: WER={wer_str} | {hyp[:60]}")

            except Exception as e:
                print(f"  ERROR on {audio_path.name}: {e}")
                continue

            # Rate limiting for Sarvam API
            time.sleep(0.5)

        # Compute averages
        for model in ["sarvam", "whisper"]:
            scores = [s for s in lang_results[model]["wer_scores"] if s >= 0]
            if scores:
                lang_results[model]["avg_wer"] = sum(scores) / len(scores)
                lang_results[model]["n_scored"] = len(scores)
            else:
                lang_results[model]["avg_wer"] = -1
                lang_results[model]["n_scored"] = 0

        all_results[lang] = lang_results

        # Save per-language JSON
        lang_out = Path(output_dir) / f"{lang}_results.json"
        with open(lang_out, "w", encoding="utf-8") as f:
            json.dump(lang_results, f, ensure_ascii=False, indent=2)

        print(f"\n  Sarvam avg WER: {lang_results['sarvam']['avg_wer']*100:.1f}%")
        print(f"  Whisper avg WER: {lang_results['whisper']['avg_wer']*100:.1f}%")

    # Save summary
    summary = _build_summary(all_results)
    summary_path = Path(output_dir) / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print_summary_table(summary)
    return summary


def _build_summary(all_results: Dict) -> Dict:
    rows = []
    for lang, data in all_results.items():
        rows.append({
            "language": lang,
            "n_clips": data["n_clips"],
            "sarvam_wer": data["sarvam"].get("avg_wer", -1),
            "whisper_wer": data["whisper"].get("avg_wer", -1),
            "better_model": _pick_better(
                data["sarvam"].get("avg_wer", 99),
                data["whisper"].get("avg_wer", 99),
            ),
        })
    return {"rows": rows}


def _pick_better(sarvam_wer: float, whisper_wer: float) -> str:
    if sarvam_wer < 0 and whisper_wer < 0:
        return "unknown"
    if sarvam_wer < 0:
        return "whisper"
    if whisper_wer < 0:
        return "sarvam"
    return "sarvam" if sarvam_wer <= whisper_wer else "whisper"


def print_summary_table(summary: Dict):
    rows = summary.get("rows", [])
    print("\n" + "="*65)
    print("BENCHMARK SUMMARY")
    print("="*65)
    print(f"{'Language':<18} {'Clips':>6} {'Sarvam WER':>12} {'Whisper WER':>12} {'Better':>10}")
    print("-"*65)
    for row in rows:
        s_wer = f"{row['sarvam_wer']*100:.1f}%" if row['sarvam_wer'] >= 0 else "N/A"
        w_wer = f"{row['whisper_wer']*100:.1f}%" if row['whisper_wer'] >= 0 else "N/A"
        print(f"{row['language']:<18} {row['n_clips']:>6} {s_wer:>12} {w_wer:>12} {row['better_model']:>10}")
    print("="*65)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DesiCaptions WER Benchmarking")
    parser.add_argument("--data_dir", default="benchmark/data",
                        help="Root directory with language subfolders")
    parser.add_argument("--output_dir", default="results",
                        help="Where to save JSON results")
    parser.add_argument("--languages", nargs="+", default=LANGUAGES,
                        help="Language keys to benchmark")
    parser.add_argument("--clips", type=int, default=CLIPS_PER_LANGUAGE,
                        help="Max clips per language")
    args = parser.parse_args()

    run_benchmark(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        languages=args.languages,
        clips_per_lang=args.clips,
    )
