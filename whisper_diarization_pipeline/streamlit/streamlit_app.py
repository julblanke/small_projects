import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import os
import streamlit as st
from src.split_audio import split_audio_to_chunks
from src.whisper_speaker_annotation import process_audio


def get_transcription_files(output_dir: str) -> list:
    """Returns a list of finished chunk transcription files.

    Args:
        output_dir (str): Directory to transcription text files.

    Returns:
        (list): List of finished chunk transcription text files.
    """
    transcriptions_dir = os.path.join(output_dir, "transcriptions")
    if not os.path.exists(transcriptions_dir):
        return []
    return [os.path.join(transcriptions_dir, f) for f in os.listdir(transcriptions_dir) if f.endswith(".txt")]


def main() -> None:
    """Executes Streamlit App."""
    st.set_page_config(layout="wide")
    st.title("WhisperX Audio Transcription and Diarization")

    tab1, tab2 = st.tabs(["Process Audio", "Transcriptions"])

    with st.sidebar:
        st.header("Configuration")
        st.session_state.audio_input_path = st.text_input("Input audio file path", "/home/jbla/Desktop/audio_file.m4a")
        st.session_state.output_dir = st.text_input("Output directory", "/home/jbla/Desktop/whisper_output_dir")
        st.session_state.split_audio = st.checkbox("Split audio to chunks", True)
        st.session_state.transcription_method = st.sidebar.selectbox(
            "Choose a transcription method:",
            ("Plain", "Speaker Annotation")
        )
        st.session_state.chunk_length = st.number_input("Chunk length [s]", 120)
        st.session_state.sample_rate = st.number_input("Sample rate [Hz]", 16000)

    with tab1:
        st.header("Process Audio")

        if st.session_state.split_audio:
            if st.button(f'Split Audio Data'):
                with st.spinner('Splitting Audio Data...'):
                    split_audio_to_chunks(audio_file_path=st.session_state.audio_input_path,
                                          output_dir=st.session_state.output_dir,
                                          chunk_length=st.session_state.chunk_length,
                                          sample_rate=st.session_state.sample_rate)
                    st.success("Done!")

        if st.button(f'Transcribe Audio Data'):
            with st.spinner('Transcribing...'):
                progress_bar = st.progress(0)
                status_text = st.empty()

                process_audio(output_dir=st.session_state.output_dir, progress_bar=progress_bar,
                              status_text=status_text, transcription_method=st.session_state.transcription_method)

                st.success("Transcription complete!")

    with tab2:
        st.header("Transcriptions")
        transcription_files = get_transcription_files(st.session_state.output_dir)

        if not transcription_files:
            st.info("No transcription files found. Please process audio first.")
        else:
            selected_file = st.selectbox("Select a transcription file to view:", transcription_files)
            if selected_file:
                with open(selected_file, "r") as f:
                    file_content = f.read()
                st.text_area(f"Content of {os.path.basename(selected_file)}", file_content, height=500)


if __name__ == "__main__":
    main()
