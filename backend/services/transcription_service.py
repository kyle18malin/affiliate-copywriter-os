"""
Affiliate Copywriter OS - Video Transcription Service
Transcribes video ads using OpenAI Whisper API
"""
import tempfile
import os
from pathlib import Path

# Try OpenAI first for Whisper
openai_client = None

try:
    from openai import OpenAI
    from backend.config import settings
    if settings.openai_api_key:
        openai_client = OpenAI(api_key=settings.openai_api_key)
except ImportError:
    pass


async def transcribe_video(file_content: bytes, filename: str) -> dict:
    """
    Transcribe a video/audio file to text.
    Returns the transcription and metadata.
    
    Supports: mp4, mov, avi, mkv, webm, mp3, wav, m4a, ogg
    """
    if not openai_client:
        raise ValueError(
            "OpenAI API key required for transcription. "
            "Please set OPENAI_API_KEY in your environment variables."
        )
    
    # Get file extension
    ext = Path(filename).suffix.lower()
    
    # Supported formats for Whisper
    supported_formats = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.mov', '.avi', '.mkv', '.ogg'}
    
    if ext not in supported_formats:
        raise ValueError(f"Unsupported file format: {ext}. Supported: {', '.join(supported_formats)}")
    
    # Write to temp file (Whisper API needs a file)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        # Transcribe using Whisper
        with open(tmp_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        return {
            "text": transcript.text,
            "duration": getattr(transcript, 'duration', None),
            "language": getattr(transcript, 'language', None),
            "segments": getattr(transcript, 'segments', None)
        }
    finally:
        # Always clean up temp file
        os.unlink(tmp_path)


def format_transcription_as_ad(transcription: dict) -> str:
    """
    Format the transcription text nicely for ad storage.
    Cleans up and structures the text.
    """
    text = transcription.get("text", "").strip()
    
    # Basic cleanup - remove excessive whitespace
    import re
    text = re.sub(r'\s+', ' ', text)
    
    return text
