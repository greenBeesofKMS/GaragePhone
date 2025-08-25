# GaragePhone
Project of HacklabGarage 2025
A Raspberry Pi turns a vintage telephone into a playful oracle. A nearby sensor triggers a pseudo‑random ring; when the handset is lifted, a short, guided dialog runs (“What’s your name?” → “Which month were you born?” → “Touch object X.”) and culminates in a quirky, personalized prophecy (e.g., “I sense the garage on Ahornstraße is absolutely right for you,” or “For Alex, born in July: in Chemnitz, check out …”).
The system works offline (no LLM required). Optional offline speech‑to‑text (STT) lets you actually parse the name and birth month.

How It Works (Flow)
Wait for sensor trigger → sleep a random 3–15 s → play ring (loop).
If handset lifted (hook switch low) → stop ring → greeting.
Ask: “What’s your name?”
Fake‑Interactive: wait ~4 s, continue.
STT‑Only: listen ~4 s, extract name heuristically (e.g., “I’m Alex”).
Ask: “Which month were you born?”
Fake‑Interactive: wait ~3 s.
STT‑Only: map any recognized month token to English month name.
Command: “Please touch <object X> now.” (random harmless object)
After a short delay, speak an oracle generated from templates, e.g.
"{name}, born in {month}: you should explore {poi} in Chemnitz today."
Cooldown (e.g., 90 s) to avoid spamming rings.

 English audio end‑to‑end (TTS via pico2wave or pre‑recorded MP3s).


Software & Dependencies
Install on Raspberry Pi OS: 
sudo apt-get update
sudo apt-get install -y python3-pip python3-pyaudio sox libttspico-utils ffmpeg
pip3 install pygame vosk

Optional (STT, English small model): download and unpack a Vosk EN model, e.g.
~/models/vosk-model-small-en-us-0.15

mystery-phone/
  main.py
  audio/
    ring.mp3
    hello.mp3
    ask_name.mp3
    ask_month.mp3
    touch.mp3   

    Configuration (English defaults)

Audio prompts: record or TTS in English.

TTS language: pico2wave -l en-GB (or en-US) in the say() helper.

STT model path: ~/models/vosk-model-small-en-us-0.15

Months list (English): ["january","february","march", ... ,"december"]

Cities/locations: seed with your local flavor (Chemnitz, Ahorn Garage, etc.).
