# Transcribe un audio (wav 16 kHz mono) con Whisper small.en offline + VAD. Imprime segmentos con tiempos.
import sys, json, numpy as np, soundfile as sf, sherpa_onnx
M = "/opt/asr/sherpa-onnx-whisper-small.en/small.en-"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                 tokens=M + "tokens.txt", language="en", task="transcribe", num_threads=4)
cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = "/opt/asr/silero_vad.onnx"
cfg.silero_vad.min_silence_duration = 0.25; cfg.silero_vad.min_speech_duration = 0.2; cfg.silero_vad.max_speech_duration = 8; cfg.sample_rate = 16000
vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=60)
a, sr = sf.read(sys.argv[1], dtype="float32")
segs = []
def drain():
    while not vad.empty():
        s = vad.front; st = s.start / sr; samples = np.array(s.samples, dtype=np.float32)
        r = rec.create_stream(); r.accept_waveform(sr, samples); rec.decode_stream(r)
        segs.append(dict(start=round(st, 2), end=round(st + len(samples) / sr, 2), text=r.result.text.strip()))
        vad.pop()
w = cfg.silero_vad.window_size
for i in range(0, len(a), w):
    vad.accept_waveform(a[i:i + w]); drain()
vad.flush(); drain()
json.dump(segs, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
for s in segs: print(f"{s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")
