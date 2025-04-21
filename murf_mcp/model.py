from typing import Dict, Optional

from pydantic import BaseModel


class TTSDetail(BaseModel):
    text: str
    voice_id: Optional[str] = "en-US-natalie"
    audio_duration: float = 0.0
    channel_type: str = "MONO"
    encode_as_base64: bool = False
    format: str = "WAV"
    model_version: str = "GEN2"
    multi_native_locale: Optional[str] = None
    pitch: int = 0
    pronunciation_dictionary: Optional[Dict[str, Dict[str, str]]] = None
    rate: int = 0
    sample_rate: float = 24000.0
    style: Optional[str] = None
    variation: int = 1
    speaker_index: Optional[int] = None


class TTSSpeaker(BaseModel):
    speaker_index: Optional[int] = None
    query: Optional[str] = None
    voice_id: Optional[str] = None
