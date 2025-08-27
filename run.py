#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HacklabGarage 2025 – Retro Oracle Phone (WAV-only + Fritz!Box via pyVoIP)
- PIR trigger → random delay → Fritz!Box ring (**1) → pickup → guided dialogue
- Spotlight follows ringing/interaction (GPIO 27)
- WAV playback only (aplay). No TTS/LLM required.
- Device stories are individual WAV files (radio, mixer, table, Erika).
"""

import os, time, random, subprocess, signal, sys
from datetime import datetime

# ========= GPIO PINS =========
PIR_PIN   = 17   # input – motion sensor
HOOK_PIN  = 23   # input – LOW when handset lifted
LIGHT_PIN = 27   # output – spotlight/relay (HIGH = on)

# ========= TIMING / BEHAVIOR =========
DELAY_MIN_S = 3
DELAY_MAX_S = 15
RING_TIMEOUT_S = 30
COOLDOWN_S = 90

FAKE_WAIT_NAME_S  = 7   # pause after "What's your name?"
FAKE_WAIT_MONTH_S = 10  # pause after "Which month were you born?"

# ========= AUDIO CONFIG =========
AUDIO_DIR = "/home/pi/hacklabgarage/audio"   # adjust to your path
AUDIO_DEV = None  # e.g. "plughw:1,0" for USB card; None = default device

# Dialogue prompt WAVs
WAV_GREETING   = "greeting.wav"
WAV_ASK_NAME   = "ask_name.wav"
WAV_ASK_MONTH  = "ask_month.wav"

# Device stories (individual WAVs, played in order or randomly)
DEVICE_STORIES = [
    "device_radio.wav",
    "device_mixer.wav",
    "device_table.wav",
    "device_erika.wav",
]

# POIs (one per run). Each has a dedicated WAV.
POI_POOL = [
    ("Bagaklut Garage",                "poi_bagaklut_garage.wav"),
    ("Viadukt with Park & TableTennis","poi_viadukt_park_tt.wav"),
    ("Fablab Chemnitz",                "poi_fablab_chemnitz.wav"),
    ("Chaostreff Chemnitz",            "poi_chaostreff_chemnitz.wav"),
    ("Zietenaugust Community Garden",  "poi_zietenaugust_garden.wav"),
    ("Hochgarage (exhibition)",        "poi_hochgarage_exhibition.wav"),
    ("Repair Café Sonnenberg",         "poi_repaircafe_sonnenberg.wav"),
]

# ========= FRITZ!BOX CALL via pyVoIP =========
from pyVoIP.VoIP import VoIPPhone, InvalidStateError, CallState

FRITZBOX_IP   = "192.168.188.1"   # Fritz!Box IP
FRITZBOX_PORT = 5060
SIP_USER      = "raspiphone"      # Fritz!Box SIP username (Telefoniegerät)
SIP_PASS      = "..."     # SIP password
LOCAL_IP      = "..."  # IP of the Raspberry Pi (for RTP)
DIAL_TARGET   = "**1"             # internal target that drives your bells

_PHONE = None

def init_phone():
    """Singleton VoIPPhone; registers on start, reused for all calls."""
    global _PHONE
    if _PHONE is None:
        _PHONE = VoIPPhone(
            FRITZBOX_IP, FRITZBOX_PORT,
            SIP_USER, SIP_PASS,
            myIP=LOCAL_IP,
            callCallback=None  # not handling inbound calls here
        )
        _PHONE.start()
    return _PHONE

def start_ring():
    """
    Start Fritz!Box ringing by placing a call to DIAL_TARGET.
    Returns the 'call' handle; we won't wait for ANSWERED (bells ring while RINGING).
    """
    phone = init_phone()
    call = phone.call(DIAL_TARGET)
    return call

def stop_ring(call):
    """Hang up the active call to stop the mechanical bells."""
    try:
        if call and call.state in (CallState.CALLING, CallState.RINGING, CallState.ANSWERED):
            call.hangup()
    except InvalidStateError:
        pass
    except Exception:
        try: call.hangup()
        except: pass

def _stop_phone():
    global _PHONE
    try:
        if _PHONE is not None:
            _PHONE.stop()
    except Exception:
        pass
    finally:
        _PHONE = None

# ========= GPIO =========
def setup_gpio():
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(HOOK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LIGHT_PIN, GPIO.OUT)
    GPIO.output(LIGHT_PIN, GPIO.LOW)

def hook_lifted():
    import RPi.GPIO as GPIO
    return GPIO.input(HOOK_PIN) == GPIO.LOW

def motion_detected():
    import RPi.GPIO as GPIO
    return GPIO.input(PIR_PIN) == GPIO.HIGH

def lights_on():
    import RPi.GPIO as GPIO
    GPIO.output(LIGHT_PIN, GPIO.HIGH)

def lights_off():
    import RPi.GPIO as GPIO
    GPIO.output(LIGHT_PIN, GPIO.LOW)

# ========= AUDIO =========
def play_wav(name_or_path):
    """Play a WAV by basename (from AUDIO_DIR) or absolute path (blocking)."""
    path = name_or_path if os.path.isabs(name_or_path) else os.path.join(AUDIO_DIR, name_or_path)
    cmd = ["aplay"]
    if AUDIO_DEV:
        cmd += ["-D", AUDIO_DEV]
    cmd.append(path)
    subprocess.run(cmd, check=True)

# ========= DIALOG STEPS (WAV-only) =========
def step_greeting():
    play_wav(WAV_GREETING)

def step_ask_name():
    play_wav(WAV_ASK_NAME)
    time.sleep(FAKE_WAIT_NAME_S)  # Fake-interactive pause

def step_ask_month():
    play_wav(WAV_ASK_MONTH)
    time.sleep(FAKE_WAIT_MONTH_S)  # Fake-interactive pause

def step_devices_story(play_all=False):
    """
    If play_all=True: play all device story WAVs in order.
    If play_all=False: play exactly one random device WAV.
    """
    if play_all:
        for wav in DEVICE_STORIES:
            play_wav(wav)
    else:
        play_wav(random.choice(DEVICE_STORIES))

def step_poi_once():
    """Pick exactly one POI and play its WAV."""
    name, wav = random.choice(POI_POOL)
    play_wav(wav)
    return name

# ========= COOLDOWN =========
COOLDOWN_FILE = "/tmp/hacklabgarage_oracle_cooldown"

def within_cooldown():
    try:
        ts = float(open(COOLDOWN_FILE).read().strip())
        return (time.time() - ts) < COOLDOWN_S
    except:
        return False

def mark_cooldown():
    with open(COOLDOWN_FILE, "w") as f:
        f.write(str(time.time()))

# ========= WORKFLOW =========
def run_workflow_once():
    # 1) Random suspense delay after trigger
    time.sleep(random.randint(DELAY_MIN_S, DELAY_MAX_S))

    # 2) Start ringing + lights on
    lights_on()
    ring_handle = start_ring()
    t0 = time.time()

    # 3) Wait for pickup (hook low) or timeout
    while True:
        if hook_lifted():
            break
        if time.time() - t0 > RING_TIMEOUT_S:
            # no pickup → stop & cooldown
            try: stop_ring(ring_handle)
            except: pass
            lights_off()
            mark_cooldown()
            return
        time.sleep(0.05)

    # 4) Pickup: stop ringing
    try: stop_ring(ring_handle)
    except: pass

    # 5) Dialogue (abort gracefully if user hangs up mid-way)
    try:
        if not hook_lifted(): raise InterruptedError
        step_greeting()

        if not hook_lifted(): raise InterruptedError
        step_ask_name()

        if not hook_lifted(): raise InterruptedError
        step_ask_month()

        if not hook_lifted(): raise InterruptedError
        step_devices_story(play_all=True)  # set to False for "one device per run"

        if not hook_lifted(): raise InterruptedError
        poi = step_poi_once()
        print(f"[oracle] POI this run: {poi}")

        if not hook_lifted(): raise InterruptedError
        step_bye()   # << hier Bye-Ansage abspielen

    except InterruptedError:
        pass
    finally:
        # 6) Cooldown + lights off; wait for handset replacement (optional)
        mark_cooldown()
        lights_off()
        t_end = time.time()
        while hook_lifted() and time.time() - t_end < 60:
            time.sleep(0.1)

# ========= MAIN LOOP =========
def main():
    setup_gpio()
    init_phone()
    print("HacklabGarage 2025 – WAV-only oracle ready (pyVoIP).")
    try:
        while True:
            if within_cooldown():
                time.sleep(0.2); continue

            if not motion_detected():
                time.sleep(0.05); continue

            # PIR triggered: run full workflow
            run_workflow_once()

    except KeyboardInterrupt:
        pass
    finally:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except Exception:
            pass
        _stop_phone()

if __name__ == "__main__":
    # Ensure clean exit on SIGTERM (systemd)
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    main()
