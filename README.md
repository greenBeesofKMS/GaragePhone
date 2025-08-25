# GaragePhone
**HacklabGarage 2025 Project**

A Raspberry Pi turns a vintage telephone into a playful oracle.  
A nearby sensor triggers a pseudo-random ring; when the handset is lifted, a short, guided dialog runs:

- “What’s your name?”  
- “Which month were you born?”  
- “Touch object X.”  

It culminates in a quirky, personalized prophecy, for example:  

- *“I sense the garage on Ahornstraße is absolutely right for you.”*  
- *“For Alex, born in July: in Chemnitz, check out …”*  

The system works **offline** (no LLM required).  
Optional offline speech-to-text (STT) lets you actually parse the name and birth month.

---

## How It Works (Flow)
1. **Wait for sensor trigger** → sleep a random 3–15 s → play ring (loop).  
2. **If handset lifted** (hook switch low) → stop ring → greeting.  
3. **Ask: “What’s your name?”**  
   - *Fake-Interactive:* wait ~4 s, continue.  
   - *STT-Only:* listen ~4 s, extract name heuristically (e.g., “I’m Alex”).  
4. **Ask: “Which month were you born?”**  
   - *Fake-Interactive:* wait ~3 s.  
   - *STT-Only:* map recognized token to one of 12 months.  
5. **Command:** “Please touch <object X> now.” (random harmless object).  
6. After a short delay, **speak an oracle** generated from templates, e.g.:
**Cooldown** (e.g., 90 s) prevents spamming rings.

English audio end-to-end (TTS via `pico2wave` or pre-recorded MP3s).

---

## Hardware Setup

### Components
- Vintage telephone (with handset speaker & hook switch).
- Raspberry Pi (Pi 4 recommended).
- PIR sensor (or other trigger: ultrasonic, reed switch).
- Hook switch button (detects when handset is lifted).
- Audio wiring: 3.5 mm jack → 2.8 mm flat connectors (to handset speaker).
- Optional: small buzzer for external ringing sound.

### Wiring
- **PIR sensor** → GPIO18 (signal), 5V, GND.  
- **Hook switch** → GPIO23 (to GND when handset lifted).  
- **Handset speaker** → Raspberry Pi audio out:  
- Ground → black/yellow wire.  
- One channel (red/white) → other handset wire.  
- **Audio test:**  
aplay /usr/share/sounds/alsa/Front_Center.wav

### Software & Dependencies
Install on Raspberry Pi OS:

sudo apt-get update
sudo apt-get install -y python3-pip python3-pyaudio sox libttspico-utils ffmpeg
pip3 install pygame vosk

##Configuration (English Defaults)

Audio prompts: record or generate via TTS in English.

TTS language: use pico2wave -l en-GB (or en-US) in the say() helper.

STT model path: ~/models/vosk-model-small-en-us-0.15

Months list (English): ["january", "february", "march", "april", "may", "june",
 "july", "august", "september", "october", "november", "december"]


Cities/locations: seed with your local flavor (e.g., Chemnitz, Ahorngarage, …).
