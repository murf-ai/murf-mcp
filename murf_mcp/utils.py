import io
import os
import platform
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from murf import ApiVoice
from pydub import AudioSegment
from rapidfuzz import fuzz


class MurfError(Exception):
    pass


class FileMissingError(MurfError):
    pass


class AudioPlayerError(MurfError):
    pass


class PathNotWritableError(MurfError):
    pass


def get_file_name(text: str, num_letters: int = 10) -> str:
    """
    Generate a file name based on the given text and number of letters.
    Args:
        text: The text to base the file name on
        num_letters: The number of letters to include in the file name
    Returns:
        A string representing the generated file name
    """
    trimmed = text[:num_letters].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{trimmed}_{timestamp}"


def open_audio(file_path: str) -> None:
    """
    Open an audio file using the default audio player of the system.
    Args:
        file_path: Path to the audio file
    """

    if not file_path:
        raise MurfError("File path is empty or None.")

    if not os.path.isfile(file_path):
        raise MurfError(f"File not found: {file_path}")

    system = platform.system()
    if system == "Windows":
        os.startfile(file_path)
    elif system == "Darwin":
        code = os.system(f"open '{file_path}'")
    else:
        code = os.system(f"xdg-open '{file_path}'")

    if system != "Windows" and code != 0:
        raise MurfError("Failed to open file — no default audio player found.")


def is_path_writable(path: str) -> bool:
    return os.access(path, os.W_OK)


def download_and_save_audio(
    urls: List[str],
    output_filename: Optional[str] = None,
    output_dir: Path = Path.home() / "Desktop",
    audio_format: str = "WAV",
) -> None:
    """
    Download audio files from given URLs and save them as a single audio file.
    Args:
        urls: List of URLs to download audio files from
        output_filename: Name of the output file
        output_dir: Directory to save the output file
        audio_format: Format to save the output file ('WAV', 'MP3', etc.)
    """
    if not urls:
        raise MurfError("No URLs provided for audio download.")

    if not is_path_writable(str(output_dir)):
        raise MurfError(f"Cannot write to desktop path: {output_dir}")

    audio_format = audio_format.lower()

    if output_filename is None:
        output_filename = get_file_name("unknown", 10) + f".{audio_format}"
    else:
        output_filename = get_file_name(output_filename, 10) + f".{audio_format}"

    audio_segments = []
    for url in urls:
        with urllib.request.urlopen(url) as response:
            audio_data = response.read()
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            audio_segments.append(audio)

    if not audio_segments:
        raise MurfError("No audio files downloaded or valid.")

    combined = (
        audio_segments[0]
        if len(audio_segments) == 1
        else sum(audio_segments[1:], audio_segments[0])
    )
    output_path = output_dir / output_filename
    combined.export(output_path, format=audio_format)


def search_voice(
    voices: List[ApiVoice],
    query: Optional[str] = None,
    voice_id: Optional[str] = None,
    keyword_threshold: int = 90,
    max_results: int = 1,
    min_keyword_match_percentage: int = 50,
) -> List[ApiVoice]:
    if not voices:
        raise ValueError("The 'voices' parameter cannot be empty or whitespace.")

    GENDER_ENUM = {"female", "male", "nonbinary"}
    BASE_SCORE = 70
    BOOST_FACTOR = 30

    if voice_id:
        for voice in voices:
            if voice.voice_id == voice_id:
                return [voice]

    keywords = [k.strip().lower() for k in (query or "").split() if k.strip()]
    gender_keyword = next((k for k in keywords if k in GENDER_ENUM), None)
    filtered_keywords = [k for k in keywords if k not in GENDER_ENUM]

    def score_voice(voice: ApiVoice) -> int:
        if gender_keyword and voice.gender.lower() != gender_keyword:
            return 0

        if not filtered_keywords:
            return 100 if gender_keyword else 0

        fields = [
            f.lower()
            for f in [
                voice.display_name,
                voice.accent,
                voice.description,
                " ".join(voice.available_styles),
                *[
                    f"{locale_code} {locale_data.detail} {' '.join(locale_data.available_styles)}"
                    for locale_code, locale_data in voice.supported_locales.items()
                ],
            ]
            if f
        ]

        matches = sum(
            any(
                fuzz.partial_ratio(keyword, field) >= keyword_threshold
                for field in fields
            )
            for keyword in filtered_keywords
        )

        match_percentage = (matches / len(filtered_keywords)) * 100

        if match_percentage < min_keyword_match_percentage:
            return BASE_SCORE if gender_keyword else int(match_percentage)

        return int(BASE_SCORE + (BOOST_FACTOR * match_percentage / 100))

    scored = [(voice, score_voice(voice)) for voice in voices]
    scored = [item for item in scored if item[1] > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    # always return results
    if not scored:
        return voices[:max_results]

    return [v[0] for v in scored[:max_results]]


def format_voices(voices: List[ApiVoice]) -> str:
    """
    Format the list of voices into a string for display, including styles and locales/languages.

    Args:
        voices: List of ApiVoice objects

    Returns:
        Formatted string of voice details
    """
    if not voices:
        return "No voices available."

    formatted_voices = []
    for voice in voices:
        display_name = voice.display_name or "Unknown"
        voice_id = voice.voice_id or "Unknown"
        styles = ", ".join(voice.available_styles) if voice.available_styles else "None"
        supported_locales = voice.supported_locales or {}

        locale_details = []
        for locale, details in supported_locales.items():
            locale_name = getattr(details, "detail", "Unknown")
            locale_styles = (
                ", ".join(getattr(details, "available_styles", [])) or "None"
            )
            locale_details.append(f"{locale_name}={locale}  (Styles: {locale_styles})")

        locales = "\n    ".join(locale_details) if locale_details else "None"

        formatted_voices.append(
            f"{display_name} ({voice_id})\n"
            f"  Styles: {styles}\n"
            f"  Locales/Languages:\n    {locales}"
        )

    return "\n\n".join(formatted_voices)
