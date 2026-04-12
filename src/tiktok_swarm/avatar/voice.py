"""Voice synthesis — ElevenLabs or local TTS."""
import time
from pathlib import Path
import httpx
from ..config import load_config, VIDEOS_DIR
from ..security import validate_filename

AUDIO_DIR = VIDEOS_DIR / "raw"


def synthesize_speech(text: str, filename: str = "") -> str:
    """Generate speech audio from text."""
    cfg = load_config()
    backend = cfg.get("voice_backend", "none")

    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{timestamp}.mp3"
    else:
        filename = validate_filename(filename)

    output_path = AUDIO_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if backend == "elevenlabs":
        return _elevenlabs_tts(text, output_path, cfg)
    elif backend == "local":
        return _local_tts(text, output_path, cfg)
    else:
        # Save text for manual recording
        txt_path = output_path.with_suffix(".txt")
        txt_path.write_text(text)
        return f"Script saved for manual recording: {txt_path}"


def _elevenlabs_tts(text: str, output_path: Path, cfg: dict) -> str:
    api_key = cfg.get("elevenlabs_api_key", "")
    voice_id = cfg.get("elevenlabs_voice_id", "")

    if not api_key or not voice_id:
        return "[ERROR] ElevenLabs API key or voice ID not configured. Run: tt setup"

    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    try:
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            json=payload,
            headers=headers,
            timeout=60.0,
        )
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        return f"Audio generated: {output_path}"
    except Exception as e:
        return f"[ERROR] ElevenLabs TTS failed: {e}"


def _local_tts(text: str, output_path: Path, cfg: dict) -> str:
    try:
        from TTS.api import TTS
        model = cfg.get("local_voice_model", "tts_models/en/ljspeech/tacotron2-DDC")
        tts = TTS(model_name=model)
        tts.tts_to_file(text=text, file_path=str(output_path.with_suffix(".wav")))
        return f"Audio generated (local): {output_path.with_suffix('.wav')}"
    except ImportError:
        return "[ERROR] Local TTS requires Coqui TTS: pip install TTS"
    except Exception as e:
        return f"[ERROR] Local TTS failed: {e}"
