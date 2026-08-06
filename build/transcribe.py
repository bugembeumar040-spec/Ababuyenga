from faster_whisper import WhisperModel
import json
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe("media/vo.mp3", language="en", word_timestamps=True,
                          vad_filter=False, beam_size=5)
out=[]
for s in segs:
    words=[{"w":w.word.strip(),"s":round(w.start,3),"e":round(w.end,3)} for w in (s.words or [])]
    out.append({"start":round(s.start,3),"end":round(s.end,3),"text":s.text.strip(),"words":words})
    print(f"[{s.start:7.3f} -> {s.end:7.3f}] {s.text.strip()}")
json.dump(out, open("vo_words.json","w"), indent=1)
print("\nWORD COUNT:", sum(len(s['words']) for s in out))
