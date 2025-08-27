#!/usr/bin/env python3

import os, time, random, re
import RPi.GPIO as GPIO
import pygame

# --- Configuration ---
USE_STT = False  # set to True if you have Vosk EN installed and configured

# GPIO pins (BCM mode)
PIN_SENSOR = 18   # PIR or other trigger sensor
PIN_HOOK   = 23   # Hook switch (LOW = off-hook / lifted)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PIN_HOOK,  GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Audio system
pygame.mixer.init()

def play(file, block=True, loop=False):
    """Play an audio file (mp3 or wav)."""
    pygame.mixer.music.load(file)
    pygame.mixer.music.play(-1 if loop else 0)
    if block:
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

def stop():
    pygame.mixer.music.stop()

# --- Optional STT (Vosk EN) ---
if USE_STT:
    from vosk import Model, KaldiRecognizer
    import pyaudio, json
    MODEL_PATH = "/home/pi/models/vosk-model-small-en-us-0.15"
    model = Model(MODEL_PATH)
    pa = pyaudio.PyAudio()

def recognize(seconds=4):
    """Record and return transcribed text using Vosk EN model."""
    if not USE_STT:
        return ""
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000,
                     input=True, frames_per_buffer=8000)
    rec = KaldiRecognizer(model, 16000)
    stream.start_stream()
    t0 = time.time()
    text = ""
    while time.time() - t0 < seconds:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text += " " + res.get("text", "")
    stream.stop_stream(); stream.close()
    final = json.loads(rec.FinalResult()).get("text","").strip()
    return (text + " " + final).strip()

# --- Helpers for extracting name/month ---
MONTHS = ["january","february","march","april","may","june",
          "july","august","september","october","november","december"]

def extract_name(t):
    """Simple heuristic to find a name in text."""
    t = t.lower()
    m = re.search(r"(i am|my name is)\s+([a-z\-]+)", t)
    if m: return m.group(2).capitalize()
    words = [w for w in re.findall(r"[a-z\-]+", t) if w not in MONTHS]
    return words[-1].capitalize() if words else "Friend"

def extract_month(t):
    """Find English month in transcript or fallback random."""
    t = t.lower()
    for m in MONTHS:
        if m in t: return m.capitalize()
    return random.choice(["January","May","October"])

# --- Audio prompt files ---
SOUNDS = {
    "ring": "audio/ring.mp3",
    "hello": "audio/hello.mp3",        # "Hello?"
    "ask_name": "audio/ask_name.mp3",  # "What is your name?"
    "ask_month": "audio/ask_month.mp3" # "Which month were you born?"
}

# --- Dynamic content ---
OBJECTS = [
    "a pen", "the door frame", "your keychain", "a spoon",
    "the table edge", "an apple", "your left shoulder"
]

ORACLE_TEMPLATES = [
    "I see it clearly: the Ahorngarage is exactly right for you.",
    "For {name}, born in {month}: in Chemnitz you should definitely check the Schlossteich.",
    "{name}, today your path leads to {district} — watch for red doors.",
    "My feeling says: call an old friend tomorrow — it will be worth it."
]

DISTRICTS = ["Sonnenberg", "Schlossberg", "City Center"]

# --- Timing / cooldown ---
COOLDOWN_S = 90

def wait_for_off_hook(timeout=20):
    """Wait until handset is lifted or timeout."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if GPIO.input(PIN_HOOK) == GPIO.LOW:
            return True
        time.sleep(0.05)
    return False

def say(text):
    """Text-to-speech using pico2wave (offline TTS)."""
    try:
        wav = "/tmp/out.wav"
        os.system(f'pico2wave -l en-GB -w {wav} "{text}"')
        play(wav)
        os.remove(wav)
    except Exception:
        # fallback: just pause for length of text
        time.sleep(min(3, 0.06*len(text)))

# --- Main logic loop ---
def main_loop():
    last_ring = 0
    print("Mystery phone ready.")
    while True:
        if GPIO.input(PIN_SENSOR) == GPIO.HIGH and (time.time()-last_ring) > COOLDOWN_S:
            # add random delay before ringing
            time.sleep(random.uniform(3, 15))
            play(SOUNDS["ring"], block=False, loop=True)

            if wait_for_off_hook(timeout=25):
                stop()
                # Greeting
                play(SOUNDS["hello"]); time.sleep(0.4)

                # Ask name
                play(SOUNDS["ask_name"])
                heard = recognize(4)
                name = extract_name(heard) if USE_STT else random.choice(["Alex","Mona","Chris"])

                # Ask month
                play(SOUNDS["ask_month"])
                heard = recognize(3)
                month = extract_month(heard) if USE_STT else random.choice(["April","July","October"])

                # Command: touch object
                obj = random.choice(OBJECTS)
                say(f"Please touch {obj} now.")
                time.sleep(random.uniform(1.0, 2.5))

                # Oracle prophecy
                tpl = random.choice(ORACLE_TEMPLATES)
                oracle = tpl.format(name=name, month=month, city=random.choice(CITIES))
                say(oracle)

                # Wait until hang up or timeout
                t0 = time.time()
                while time.time()-t0 < 10 and GPIO.input(PIN_HOOK) == GPIO.LOW:
                    time.sleep(0.1)

                last_ring = time.time()
            else:
                stop()
                last_ring = time.time()
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        main_loop()
    finally:
        GPIO.cleanup()
        stop()
