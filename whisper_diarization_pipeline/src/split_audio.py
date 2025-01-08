import os
import librosa
import numpy as np
from pydub import AudioSegment


def split_audio_to_chunks(audio_file_path: str, output_dir: str, chunk_length: int, sample_rate: int) -> None:
    """Splits given audio file into .mp4 chunks.

    Args:
        audio_file_path (str): Path to initial audio file.
        output_dir (str): Directory for .mp4 audio chunks.
        chunk_length (int): Chunk time length in seconds.
        sample_rate (int): Number of samples taken per second of audio signal (waveform).
    """
    chunk_dir = os.path.join(output_dir, "chunk_files")
    os.makedirs(chunk_dir, exist_ok=True)

    try:
        audio_data, sr = librosa.load(audio_file_path, sr=sample_rate, dtype=np.float32)
    except Exception as e:
        return

    chunk_length_samples = int(chunk_length * sr)
    num_samples = len(audio_data)
    num_chunks = int(np.ceil(num_samples / chunk_length_samples))

    full_audio = AudioSegment(
        (audio_data * 32767).astype(np.int16).tobytes(),  # convertion to 16-bit PCM format
        frame_rate=sr,
        sample_width=2,  # 16-bit audio
        channels=1       # mono audio
    )

    for i in range(num_chunks):
        start_ms = i * chunk_length * 1000
        end_ms = min((i + 1) * chunk_length * 1000, len(full_audio))
        audio_chunk = full_audio[start_ms:end_ms]

        output_file = os.path.join(chunk_dir, f"chunk_{i + 1}.mp4")

        try:
            audio_chunk.export(output_file, format="mp4")
        except Exception as e:
            return


if __name__ == "__main__":
    split_audio_to_chunks(r"/home/jbla/Desktop/Audios/Tommes sozpä.m4a",
                          r"/home/jbla/Desktop/lena_audios/Tommes sozpä",
                          120,
                          16000)


