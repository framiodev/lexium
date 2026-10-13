"""Seslendirme: Piper (VITS) sesleri, sherpa-onnx ile. Her metin için kadın (-f) ve erkek (-m) mp3 üretir."""
import os, sys, json, glob, hashlib, tarfile, subprocess, urllib.request, urllib.error, shutil
import time, html
AZ_KEY=os.environ.get('AZURE_SPEECH_KEY','').strip(); AZ_REGION=os.environ.get('AZURE_SPEECH_REGION','').strip()
AZURE=bool(AZ_KEY and AZ_REGION)
if not AZURE:
    import numpy as np
    import sherpa_onnx

REL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
EN = {"f": "vits-piper-en_US-amy-medium", "m": "vits-piper-en_US-ryan-medium"}
TR_CANDIDATES = ["vits-piper-tr_TR-dfki-medium", "vits-piper-tr_TR-fahrettin-medium", "vits-piper-tr_TR-fettah-medium"]
CACHE = os.environ.get("AUDIO_CACHE", "audio-cache")
OUT = "www/audio"
os.makedirs(CACHE, exist_ok=True); os.makedirs("models", exist_ok=True)

def fetch(name):
    d = f"models/{name}"
    if os.path.isdir(d): return d
    f = f"models/{name}.tar.bz2"
    print("indiriliyor", name, flush=True)
    urllib.request.urlretrieve(REL + name + ".tar.bz2", f)
    with tarfile.open(f) as t: t.extractall("models")
    os.remove(f); return d

def load(name):
    d = fetch(name)
    onnx = [x for x in glob.glob(d + "/*.onnx")][0]
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=onnx, tokens=d + "/tokens.txt", data_dir=d + "/espeak-ng-data"),
        num_threads=2, provider="cpu"))
    return sherpa_onnx.OfflineTts(cfg)

def synth(tts, text):
    a = tts.generate(text, sid=0, speed=0.95)
    return np.array(a.samples, dtype=np.float32), a.sample_rate

def f0(x, sr):
    n = int(sr * 0.04); hop = n // 2; vals = []
    lo, hi = int(sr / 400), int(sr / 70)
    for i in range(0, len(x) - 2 * n, hop):
        fr = x[i:i + n]; fr = fr - fr.mean()
        if np.sqrt((fr ** 2).mean()) < 0.02: continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        if ac[0] <= 0: continue
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] / ac[0] > 0.5: vals.append(sr / k)
    return float(np.median(vals)) if vals else 0.0

def to_mp3(x, sr, path, shift=1.0):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    flt = ["-af", f"asetrate={int(sr*shift)},aresample=22050,atempo={1/shift:.4f}"] if shift != 1.0 else ["-ar", "22050"]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-"] + flt + ["-ac", "1", "-b:a", "40k", path],
                   input=pcm, check=True)

if not AZURE:
    # --- Türkçe sesleri tanı: hangisi kadın, hangisi erkek? ---
    probe = "Merhaba, bugün hava çok güzel ve ben yeni bir şeyler öğreniyorum."
    tr_models = {}
    tr_f0 = {}
    for n in TR_CANDIDATES:
        try:
            t = load(n); x, sr = synth(t, probe); tr_models[n] = t; tr_f0[n] = f0(x, sr)
            print(f"TR ses {n}: F0 ~ {tr_f0[n]:.0f} Hz", flush=True)
        except Exception as e:
            print("TR ses yüklenemedi", n, e, flush=True)
    if not tr_f0: sys.exit("Türkçe ses yok")
    fem = max(tr_f0, key=tr_f0.get); mal = min(tr_f0, key=tr_f0.get)
    tr_shift = 1.0
    if tr_f0[fem] < 165:
        tr_shift = 1.26
        print(f"UYARI: Türkçe kadın sesi bulunamadı; {fem} sesi yükseltilerek kadın sesi yapılıyor.", flush=True)
        mal = min(tr_f0, key=tr_f0.get)
        if mal == fem and len(tr_f0) > 1: mal = [k for k in tr_f0 if k != fem][0]
    print("TR kadın:", fem, "TR erkek:", mal, flush=True)
    TR = {"f": (tr_models[fem], tr_shift), "m": (tr_models[mal], 1.0)}
    ENM = {v: (load(EN[v]), 1.0) for v in ("f", "m")}
    for v in ("f", "m"):
        x, sr = synth(ENM[v][0], "Hello, this is a test of the English voice.")
        print(f"EN {v} F0 ~ {f0(x, sr):.0f} Hz", flush=True)


AZV = {("en", "f"): ("en-US", "en-US-AvaMultilingualNeural"), ("en", "m"): ("en-US", "en-US-AndrewMultilingualNeural"),
       ("tr", "f"): ("tr-TR", "tr-TR-EmelNeural"), ("tr", "m"): ("tr-TR", "tr-TR-AhmetNeural")}
def azure_mp3(lang, v, text, path):
    loc, name = AZV[(lang, v)]
    ssml = f"<speak version='1.0' xml:lang='{loc}'><voice name='{name}'><prosody rate='-8%'>{html.escape(text)}</prosody></voice></speak>"
    req = urllib.request.Request(f"https://{AZ_REGION}.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml.encode("utf-8"),
        headers={"Ocp-Apim-Subscription-Key": AZ_KEY, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3", "User-Agent": "lexium"})
    for k in range(5):
        try:
            data = urllib.request.urlopen(req, timeout=60).read()
            if len(data) < 800: raise ValueError("boş ses")
            open(path, "wb").write(data); return
        except urllib.error.HTTPError as e:
            if e.code in (401, 403): sys.exit(f"Azure yetki hatası {e.code}: anahtar/bölge yanlış")
            time.sleep(2 * (k + 1))
        except Exception:
            time.sleep(2 * (k + 1))
    raise RuntimeError("Azure başarısız")
if AZURE: print("Motor: Azure Neural", AZ_REGION, flush=True)

texts = json.load(open("tools/texts.json", encoding="utf-8"))
index = {}; made = 0
for lang, text in texts:
    h = hashlib.sha1(f"{lang}|{text}".encode()).hexdigest()[:12]
    ok = True
    for v in ("f", "m"):
        p = f"{CACHE}/{h}-{v}.mp3"
        if not os.path.exists(p):
            try:
                if AZURE:
                    azure_mp3(lang, v, text, p)
                else:
                    tts, shift = (ENM if lang == "en" else TR)[v]
                    x, sr = synth(tts, text)
                    if len(x) < sr * 0.1: raise ValueError("boş ses")
                    to_mp3(x, sr, p, shift)
                made += 1
            except Exception as e:
                print("HATA", lang, text, e, flush=True); ok = False
    if ok: index[f"{lang}|{text}"] = h
print(f"üretilen: {made}, toplam metin: {len(texts)}, indekste: {len(index)}", flush=True)
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
for h in set(index.values()):
    for v in ("f", "m"): shutil.copy(f"{CACHE}/{h}-{v}.mp3", f"{OUT}/{h}-{v}.mp3")
json.dump(index, open(f"{OUT}/index.json", "w", encoding="utf-8"), ensure_ascii=False)
print("MB:", sum(os.path.getsize(x) for x in glob.glob(OUT + "/*")) / 1e6)
