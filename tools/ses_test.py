import sys, os, traceback
engine = sys.argv[1]
OUT = f"www/test-audio/{engine}"; os.makedirs(OUT, exist_ok=True)
S = {"en": ["Good morning! My name is Anna, and I am from Istanbul.", "Could you tell me how to get to the train station, please?"],
     "tr": ["Günaydın! Benim adım Ayşe, İstanbul'danım.", "Bu hafta sonu arkadaşlarımla sinemaya gideceğim."]}
if engine == "xtts":
    os.environ["COQUI_TOS_AGREED"] = "1"
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    voices = {"f1": "Claribel Dervla", "f2": "Daisy Studios", "m1": "Andrew Chipper", "m2": "Viktor Eka"}
    for v, name in voices.items():
        for lang, texts in S.items():
            for i, t in enumerate(texts):
                try:
                    tts.tts_to_file(text=t, speaker=name, language=lang, file_path=f"{OUT}/{lang}-{v}-{i}.wav"); print("ok", lang, v, i, flush=True)
                except Exception: traceback.print_exc()
else:
    import torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    for lang, texts in S.items():
        for i, t in enumerate(texts):
            try:
                w = m.generate(t, language_id=lang); torchaudio.save(f"{OUT}/{lang}-default-{i}.wav", w, m.sr); print("ok", lang, i, flush=True)
            except Exception: traceback.print_exc()
