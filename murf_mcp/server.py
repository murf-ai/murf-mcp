import asyncio
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from murf import AsyncMurf

from murf_mcp.model import TTSDetail, TTSSpeaker
from murf_mcp.utils import (
    AudioPlayerError,
    FileMissingError,
    MurfError,
    download_and_save_audio,
    format_voices,
    get_file_name,
    open_audio,
    search_voice,
)

load_dotenv()
api_key = os.getenv("MURF_API_KEY")
output_dir = os.getenv("MURF_OUTPUT_DIR")

if not api_key:
    raise ValueError("MURF_API_KEY environment variable is not set.")


client = AsyncMurf(
    api_key=api_key,
)
mcp = FastMCP("MurfAi")


@mcp.tool(
    description="""
    This tool generates audio files from text using the Murf text-to-speech API.
    You need your Murf API key to use this tool. You can get it from https://murf.ai/api/dashboard

    For adding pauses between words, you can use pause syntax "[pause <duration>s]" in the text to make the voiceover natural
    where duration is supported from 0.1 to 5 seconds. Example: [pause 0.5s] will add a 0.5 second pause.
    

    Args:
        speakers (List[TTSSpeaker]): List of TTSSpeaker objects containing speaker and voice details.
            speaker_index (int): Index of the speaker in the speakers list.
            query (str): Search string with keywords like locale to find a matching voice using: 
                enum for genders {"male", "female", "nonbinary"}
                accent
                voice name
                locales like en-US, en-UK, es-ES, etc.
                styles like Conversational, Narration etc
            Always use query if voice and locale specific styles for the voice are not known
            voice_id (Optional[str]): Specific voice ID to use. Use only if voice_id explicitly provided by user.

        content List[TTSDetail]: List of TTSDetail objects containing text and voice details.
            text (str): The text to convert to speech.
            voice_id (Optional[str]): Specific voice ID to use. If provided, it overrides voice_query, do not use this unless you know the exact voice_id.
            audio_duration (float): Target duration of the output audio in seconds. Defaults to 0 (auto).
            channel_type (str): Audio channel type, e.g., "MONO" or "STEREO". Defaults to "MONO".
            format (str): Audio format, Defaults to "WAV". Every object in the list should have same format. Valid values: MP3, WAV, FLAC, ALAW, ULAW
            model_version (str): Model version to use for synthesis. Defaults to "GEN2".
            multi_native_locale (Optional[str]): Preferred language locale for multilingual voices.  Example of valid values: "en-US”, "en-UK”, "es-ES”, etc.
            pitch (int): Pitch adjustment for the voice. Positive for higher pitch, negative for lower, ranges from -50 to 50.
            pronunciation_dictionary (Optional[Dict[str, Dict[str, str]]]): Custom pronunciation overrides. Example 1: {"live":{"type": "IPA", "pronunciation": "laɪv"}}. Example 2: {"2022":{"type": "SAY_AS”, "pronunciation”: "twenty twenty two”}}
            rate (int): Speaking rate adjustment. Positive for faster, negative for slower, ranges from -50 to 50.
            sample_rate (float): Sample rate in Hz. Defaults to 24000.0. Valid values are 8000, 24000, 44100, 48000
            style (Optional[str]): Speaking style such as "cheerful", "sad", etc. Always check locale specific styles for the voice are available.
            variation (int): Variation index for voices that support multiple variants. Defaults to 1, ranges from 0 to 5.
            speaker_index [int]: Index of the speaker, if single speaker this is 0 by default.
    """,
)
async def text_to_speech(
    speakers: List[TTSSpeaker],
    content: List[TTSDetail],
):
    if not speakers:
        raise ValueError("The 'speakers' parameter cannot be empty or whitespace.")

    content = [item for item in content if item.text.strip()]
    if not content:
        raise ValueError("The 'content' parameter cannot be empty or whitespace.")

    voices = await client.text_to_speech.get_voices()

    for speaker in speakers:
        if not speaker.voice_id:
            matched_voice = search_voice(
                voices=voices,
                query=speaker.query,
                voice_id=None,
                max_results=1,
            )
            if matched_voice:
                speaker.voice_id = matched_voice[0].voice_id
            else:
                speaker.voice_id = "en-US-natalie"

    for item in content:
        if item.speaker_index is not None:
            if 0 <= item.speaker_index < len(speakers):
                item.voice_id = speakers[item.speaker_index].voice_id
            else:
                raise IndexError(
                    f"speaker_index {item.speaker_index} is out of range for speakers list."
                )
        else:
            raise ValueError(f"speaker_index is missing for content: {item.text}")

    results = await asyncio.gather(
        *[
            client.text_to_speech.generate(
                text=item.text,
                voice_id=item.voice_id,
                audio_duration=item.audio_duration,
                channel_type=item.channel_type,
                encode_as_base_64=False,
                format=item.format,
                model_version=item.model_version,
                multi_native_locale=item.multi_native_locale,
                pitch=item.pitch,
                pronunciation_dictionary=item.pronunciation_dictionary,
                rate=item.rate,
                sample_rate=item.sample_rate,
                style=item.style,
                variation=item.variation,
            )
            for item in content
        ]
    )

    if results:
        urls = [result.audio_file for result in results if result.audio_file]
        if not urls:
            raise ValueError("No audio URLs returned from the API.")

    output_dir = Path.home() / "Desktop"

    filename = get_file_name(content[0].text, 10)

    download_and_save_audio(
        urls=urls,
        output_dir=output_dir,
        output_filename=filename,
        audio_format=content[0].format.lower(),
    )

    return TextContent(
        type="text",
        text=f"Audio file saved to file_path= {output_dir}/{filename}.{content[0].format.lower()}",
    )


@mcp.tool(
    description="""
    Recommends/Searches voices for the given speakers based on user queries. 
    Can be used before generating text-to-speech for getting locale/language specific voice styles.

    Args:
        speakers (List[TTSSpeaker]): List of TTSSpeaker with voice query.
        max_results (int): Maximum number of results to return. Default is 1.
    """
)
async def recommend_or_search_voices(speakers: List[TTSSpeaker], max_results: int = 1):
    if not speakers:
        raise ValueError("The 'speakers' parameter cannot be empty or whitespace.")

    voices = await client.text_to_speech.get_voices()
    recommended_voices = []

    for speaker in speakers:
        if not speaker.voice_id:
            if not speaker.query:
                raise ValueError("Missing voice query for a speaker.")

            matched = search_voice(
                voices=voices,
                query=speaker.query,
                voice_id=None,
                max_results=max_results,
            )
            if matched:
                speaker.voice_id = matched[0].voice_id
                recommended_voices.extend(matched)
            else:
                speaker.voice_id = "en-US-natalie"

    return TextContent(
        type="text", text=f"Recommended voices with voice_id: {format_voices(voices)}"
    )


@mcp.tool(
    description="""
    Plays the audio file from the given file path using the default audio player of the system.
    """,
)
def play_audio(
    file_path: str,
):
    if not os.path.isfile(file_path):
        raise ValueError(f"The file {file_path} does not exist.")

    try:
        open_audio(file_path)
    except FileMissingError:
        return TextContent(type="text", text="Audio file is missing")
    except AudioPlayerError:
        return TextContent(type="text", text="Audio player not found on the system")
    except MurfError as e:
        return TextContent(type="text", text=f"Unknown Murf error: {e}")
    except Exception as e:
        return TextContent(type="text", text=f"Unexpected error: {e}")

    return TextContent(type="text", text=f"Audio file {file_path} opened successfully.")


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
