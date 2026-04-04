"""Fix benchmark references to use native script matching ASR output."""
from pathlib import Path

refs = {
    "hinglish": [
        "आज का दिन बहुत अच्छा है यार",
        "मुझे चाय चाहिए अभी",
        "क्या हाल है भाई सब ठीक",
        "बहुत मुश्किल है यह काम",
        "चलो चलते हैं घर को",
    ],
    "benglish": [
        "আমি খুব ভালো আছি",
        "তুমি কি খাচ্ছো",
        "অনেক সুন্দর এই জায়গাটা",
        "কি খবর বলো",
        "এবার যাওয়া দরকার",
    ],
    "tanglish": [
        "நான் ரொம்ப பிஸியாக இருப்பேன்",
        "என்ன பண்ண யூரிங்க சொல்லுங்க",
        "வேற லெவல் டா இது",
        "சூப்பர் ஆ இருக்கு யார்",
        "எப்படி இருக்கீங்க நல்லா இருக்கீங்க",
    ],
    "tenglish": [
        "మీ ఎలా ఉన్నారో చాలా బాగుండ్రా",
        "నేను ఇల్లు వెల్ట్ అన్నా",
        "చాలా బాగుంది ఈ పద్దం",
        "ఏంటి మీ విషయం",
        "అన్నీ బాగున్నాయ్ కదా",
    ],
    "odiaenglish": [
        "ମୋ ନାମ ଓଡ଼ିଆ ଅଛି",
        "ଆପଣ କେମନ ଅଛନ୍ତି ଭଲ",
        "ଭଲ ଲାଗୁଛି ଏ ଗୀତ ଟା",
        "କଣ ଖବର ଅଛି ଆଜିର",
        "ଏ କାମ ବହୁତ ଖଟିଆ ହେଲା",
    ],
}

for folder, texts in refs.items():
    refs_dir = Path(f"benchmark/data/{folder}_refs")
    refs_dir.mkdir(parents=True, exist_ok=True)
    for i, text in enumerate(texts):
        path = refs_dir / f"clip{i:02d}.txt"
        path.write_text(text, encoding="utf-8")
        print(f"  {folder}/clip{i:02d}: {text}")

print("\nAll references updated to native script!")
