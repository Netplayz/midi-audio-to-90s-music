#!/usr/bin/env python3

import numpy as np
import wave
from mido import MidiFile

SAMPLE_RATE = 44100


# MIDI note → frequency
def midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12.0))


# Car horn waveform
def car_horn_wave(freq, duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)

    wave1 = np.sign(np.sin(2 * np.pi * freq * t))
    wave2 = 0.5 * np.sign(np.sin(2 * np.pi * freq * 1.5 * t))
    wave3 = 0.3 * np.sign(np.sin(2 * np.pi * freq * 2.0 * t))

    wave_combined = wave1 + wave2 + wave3

    # Envelope
    attack = int(0.01 * SAMPLE_RATE)
    release = int(0.2 * SAMPLE_RATE)

    envelope = np.ones_like(wave_combined)

    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[-release:] = np.linspace(1, 0, release)

    return wave_combined * envelope


# Write WAV
def write_wav(filename, audio):
    audio = audio / np.max(np.abs(audio))
    audio_int16 = np.int16(audio * 32767)

    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(audio_int16.tobytes())


# Convert ticks → seconds
def ticks_to_seconds(ticks, ticks_per_beat, tempo):
    return (ticks * tempo) / (ticks_per_beat * 1_000_000)


# MAIN ENGINE (accurate playback)
def midi_to_horn(input_midi, output_wav):
    mid = MidiFile(input_midi)
    ticks_per_beat = mid.ticks_per_beat

    # Default tempo (120 BPM)
    tempo = 500000

    events = []
    current_time = 0.0

    # Collect ALL events with absolute time
    for track in mid.tracks:
        track_time = 0.0
        track_tempo = tempo

        for msg in track:
            delta = ticks_to_seconds(msg.time, ticks_per_beat, track_tempo)
            track_time += delta

            if msg.type == 'set_tempo':
                track_tempo = msg.tempo

            events.append((track_time, msg))

    # Sort all events globally
    events.sort(key=lambda x: x[0])

    # Track active notes
    active_notes = {}
    rendered_notes = []

    for time, msg in events:
        if msg.type == 'note_on' and msg.velocity > 0:
            active_notes[(msg.note, msg.channel)] = time

        elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
            key = (msg.note, msg.channel)

            if key in active_notes:
                start_time = active_notes.pop(key)
                duration = time - start_time

                if duration > 0:
                    rendered_notes.append((start_time, msg.note, duration))

    # Determine total length
    if not rendered_notes:
        print("No notes found.")
        return

    total_length = max(start + dur for start, _, dur in rendered_notes)
    total_samples = int(total_length * SAMPLE_RATE) + 1

    # Create full audio buffer
    audio = np.zeros(total_samples, dtype=np.float32)

    # Render each note into buffer (polyphony!)
    for start, note, duration in rendered_notes:
        freq = midi_to_freq(note)

        note_audio = car_horn_wave(freq, duration)
        start_sample = int(start * SAMPLE_RATE)
        end_sample = start_sample + len(note_audio)

        # Prevent overflow
        if end_sample > len(audio):
            note_audio = note_audio[:len(audio) - start_sample]
            end_sample = len(audio)

        audio[start_sample:end_sample] += note_audio

    write_wav(output_wav, audio)
    print(f"Fully accurate horn audio saved to {output_wav}")


# Run
if __name__ == "__main__":
    input_file = "input.mid"
    output_file = "car_horn.wav"

    midi_to_horn(input_file, output_file)