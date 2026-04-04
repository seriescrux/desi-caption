"""Run Odia benchmark with Hindi fallback for both Sarvam and Whisper."""
import os, sys, json, tempfile, wave
sys.path.insert(0, '.')

from modules.asr_router import ASRRouter
from modules.audio_processor import AudioProcessor
from pathlib import Path
from jiwer import wer as compute_wer
import requests

asr = ASRRouter(
    sarvam_api_key=os.getenv('SARVAM_API_KEY', ''),
    whisper_model_size='large-v3',
)
audio_proc = AudioProcessor()

results = {
    'language': 'odiaenglish',
    'n_clips': 5,
    'sarvam': {'transcripts': [], 'references': [], 'wer_scores': []},
    'whisper': {'transcripts': [], 'references': [], 'wer_scores': []},
}

for i in range(5):
    wav = f'benchmark/data/odiaenglish/clip{i:02d}.wav'
    ref_path = f'benchmark/data/odiaenglish_refs/clip{i:02d}.txt'
    ref = Path(ref_path).read_text(encoding='utf-8').strip()
    chunks, _ = audio_proc.process_file(wav)
    audio_bytes = chunks[0]
    print(f'\nclip{i:02d} | ref: {ref}')

    # Sarvam with hi-IN fallback
    try:
        with open(wav, 'rb') as f:
            resp = requests.post(
                'https://api.sarvam.ai/speech-to-text',
                headers={'api-subscription-key': os.getenv('SARVAM_API_KEY', '')},
                files={'file': ('audio.wav', f, 'audio/wav')},
                data={'language_code': 'hi-IN', 'model': 'saaras:v3'},
                timeout=30,
            )
        transcript = resp.json().get('transcript', '')
        score = compute_wer(ref, transcript) if transcript else 1.0
        results['sarvam']['transcripts'].append(transcript)
        results['sarvam']['references'].append(ref)
        results['sarvam']['wer_scores'].append(score)
        print(f'  sarvam: WER={score*100:.1f}% | {transcript[:60]}')
    except Exception as e:
        print(f'  sarvam FAILED: {e}')
        results['sarvam']['wer_scores'].append(-1)

    # Whisper with hi fallback
    try:
        model = asr._load_whisper()
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
            tmp = tf.name
        with wave.open(tmp, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_bytes)
        result = model.transcribe(tmp, language='hi', task='transcribe')
        transcript = result['text'].strip()
        score = compute_wer(ref, transcript) if transcript else 1.0
        results['whisper']['transcripts'].append(transcript)
        results['whisper']['references'].append(ref)
        results['whisper']['wer_scores'].append(score)
        print(f'  whisper: WER={score*100:.1f}% | {transcript[:60]}')
        os.unlink(tmp)
    except Exception as e:
        print(f'  whisper FAILED: {e}')
        results['whisper']['wer_scores'].append(-1)

# Compute averages
for model in ['sarvam', 'whisper']:
    scores = [s for s in results[model]['wer_scores'] if s >= 0]
    avg = sum(scores) / len(scores) if scores else -1
    results[model]['avg_wer'] = avg
    results[model]['n_scored'] = len(scores)
    print(f'\n{model} avg WER: {avg*100:.1f}%')

Path('results/odiaenglish_results.json').write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print('\nSaved to results/odiaenglish_results.json!')
