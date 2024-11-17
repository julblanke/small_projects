import os
import re
import torch
import shutil
import dotenv
import whisperx
import pandas as pd
from typing import Any


def process_audio(output_dir: str, progress_bar: Any, status_text: Any) -> None:
    """Processes audio chunks and transcribes them using WhisperX.

    Args:
        output_dir (str): Path to the user defined output directory.
        progress_bar (Any): Streamlit progress bar widget.
        status_text (Any): Streamlit status text widget.
    """
    torch.cuda.empty_cache()

    # set/create output directories
    audio_src_dir = os.path.join(output_dir, "chunk_files")
    transcriptions_dir = os.path.join(output_dir, "transcriptions")
    os.makedirs(transcriptions_dir, exist_ok=True)
    processed_chunks = os.path.join(output_dir, "processed_chunks")
    os.makedirs(processed_chunks, exist_ok=True)

    # sort audio files
    audio_files = sorted(
        [f for f in os.listdir(audio_src_dir) if f.endswith('.mp4')],
        key=lambda x: int(re.search(r'(\d+)', x).group())
    )
    total_chunks = len(audio_files)

    # model config
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "large-v2"
    compute_type = "int8" if device == "cpu" else "float16"
    model = whisperx.load_model(model_id, device, compute_type=compute_type, asr_options={"hotwords": None})

    # process audio files
    for idx, file in enumerate(audio_files, start=1):
        audio_path = os.path.join(audio_src_dir, file)

        result = model.transcribe(audio_path)
        language = result.get("language", "de")

        model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
        result_aligned = whisperx.align(result["segments"], model_a, metadata, audio_path, device)

        dotenv.load_dotenv()
        HG_ACCESS_TOKEN = os.getenv("HG_ACCESS_TOKEN")
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=HG_ACCESS_TOKEN, device=device)
        diarization_result = diarize_model(audio_path)

        if not isinstance(diarization_result, pd.DataFrame):
            diarization_result = pd.DataFrame(diarization_result)

        if 'start' not in diarization_result.columns or 'end' not in diarization_result.columns:
            diarization_result['start'] = diarization_result['segment'].apply(lambda x: x.start)
            diarization_result['end'] = diarization_result['segment'].apply(lambda x: x.end)

        result_with_speakers = whisperx.assign_word_speakers(diarization_result, result_aligned)

        transcription_text = ""
        current_speaker = None
        for segment in result_with_speakers["segments"]:
            speaker = segment['speaker']
            text = segment['text']
            if speaker != current_speaker:
                transcription_text += f"\n{speaker}: "
                current_speaker = speaker
            transcription_text += f"{text} "

        transcription_text = transcription_text.strip()

        # file handling
        chunk_name = file.split(".mp4")[0]
        with open(os.path.join(transcriptions_dir, f"{chunk_name}.txt"), 'a') as f:
            f.write(transcription_text + "\n")
        shutil.move(audio_path, processed_chunks)

        # streamlit widgets
        if progress_bar and status_text:
            progress_bar.progress(idx / total_chunks)
            status_text.write(f"Processed {idx}/{total_chunks} chunks")
