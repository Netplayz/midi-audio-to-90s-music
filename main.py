import numpy as np
from scipy.io.wavfile import write
from mido import MidiFile

SAMPLE_RATE = 44100

# Convert MIDI note number to frequency
def midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12.0))

# Generate a "car horn" sound (square + slight distortion)
def car_horn_wave(freq, duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)

    # Square wave (harsh like a horn)
    wave = np.sign(np.sin(2 * np.pi * freq * t))

    # Add slight harmonic stuff
    wave += 0.3 * np.sign(np.sin(2 * np.pi * freq * 2 * t))

    # Envelope (quick attack, slow decay)
    attack = int(0.01 * SAMPLE_RATE)
    decay = int(0.2 * SAMPLE_RATE)

    envelope = np.ones_like(wave)
    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[-decay:] = np.linspace(1, 0, decay)

    return wave * envelope

def midi_to_horn(input_midi, output_wav):
    mid = MidiFile(input_midi)

    audio = np.array([], dtype=np.float32)
    current_time = 0.0

    for track in mid.tracks:
        for msg in track:
            time = msg.time / mid.ticks_per_beat
            duration = time

            # Add silence for timing gaps to make it less awkard
            silence = np.zeros(int(SAMPLE_RATE * duration))
            audio = np.concatenate((audio, silence))

            if msg.type == 'note_on' and msg.velocity > 0:
                freq = midi_to_freq(msg.note)
                note_audio = car_horn_wave(freq, 0.3)
                audio = np.concatenate((audio, note_audio))

    # Normalize audio
    audio = audio / np.max(np.abs(audio))

    # Convert to 16 bit PCM to work on actual musical works
    audio_int16 = np.int16(audio * 32767)

    write(output_wav, SAMPLE_RATE, audio_int16)

    print(f"Saved horn audio to {output_wav}")

# Example usage
if __name__ == "__main__":
    midi_to_horn("input.mid", "car_horn.wav")
