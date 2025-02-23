from pydub import AudioSegment
from pathlib import Path
import shutil
from datetime import datetime
import uuid
import os
import logging
from dotenv import load_dotenv
from config.config import (
    TTS_MODEL,
    TTS_VOICE,
    TTS_SPEED,
    AUDIO_OUTPUT_FORMAT,
    AUDIO_OUTPUT_QUALITY,
    AUDIO_PATH,
    INTRO_SOUND_PATH
)
from mutagen.mp3 import MP3
from .content_service import save_episode_to_db

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
from openai import OpenAI
client = OpenAI()

def split_text(text, length=4096):
    """Split the text into segments, ensuring no segment splits a word in half."""
    segments = []
    while text:
        if len(text) <= length:
            segments.append(text)
            break
        split_index = text.rfind(' ', 0, length)
        if split_index == -1:  # In case there are no spaces, force a split
            split_index = length
        segments.append(text[:split_index])
        text = text[split_index+1:]  # Skip the space when starting the next segment
    return segments

def create_filename(base_filename, extension, is_final=False):
    """Generate a filename with datetime and a short random key."""
    # Sanitize base filename to avoid path issues
    safe_filename = "".join(c if c.isalnum() or c in "-_" else "_" for c in base_filename)
    datetime_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_key = uuid.uuid4().hex[:6]

    if is_final:
        return Path(AUDIO_PATH) / f"{safe_filename}_{datetime_str}_{random_key}.{extension}"
    else:
        return Path(AUDIO_PATH) / 'tmp' / f"{safe_filename}_{datetime_str}_{random_key}_segment.{extension}"

def ensure_temp_directory():
    """Ensure temporary directory exists."""
    tmp_dir = Path(AUDIO_PATH) / 'tmp'
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir

def cleanup_temp_files(temp_files):
    """Clean up temporary segment files."""
    for file_path in temp_files:
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f'Cleaned up temp file: {file_path.name}')
        except Exception as e:
            logger.error(f'Error cleaning up temp file {file_path}: {str(e)}')

def text_to_speech_segment(text_segment, segment_index, base_filename, tmp_dir):
    """Convert a text segment to speech using OpenAI TTS."""
    segment_path = create_filename(base_filename, AUDIO_OUTPUT_FORMAT, is_final=False)

    try:
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=text_segment,
            response_format=AUDIO_OUTPUT_FORMAT,
            speed=TTS_SPEED
        )
        response.stream_to_file(str(segment_path))

        # Verify the file was created
        if not segment_path.exists():
            logger.error(f'Failed to create segment file: {segment_path}')
            return None

        return segment_path
    except Exception as e:
        logger.error(f'Error creating speech segment: {str(e)}')
        if segment_path.exists():
            segment_path.unlink()
        return None

def combine_audio_segments(segment_data, base_filename):
    """Combine multiple audio segments into a single file, prepending a sound effect.

    Args:
        segment_data: List of tuples containing (index, path) for each segment
        base_filename: Base name for the final output file
    """
    final_output_path = create_filename(base_filename, AUDIO_OUTPUT_FORMAT, is_final=True)
    successful_segments = []

    try:
        # Start with the sound effect
        combined = AudioSegment.empty()

        # Add intro sound if available
        if INTRO_SOUND_PATH.exists():
            try:
                sound_effect = AudioSegment.from_file(str(INTRO_SOUND_PATH))
                combined += sound_effect
                logger.info(f'Successfully added intro sound ({sound_effect.duration_seconds:.2f}s)')
            except Exception as e:
                logger.error(f'Could not load intro sound: {str(e)}')
        else:
            logger.warning(f'Intro sound not found at {INTRO_SOUND_PATH}')

        # Sort segments by index to ensure correct order
        sorted_segments = sorted(segment_data, key=lambda x: x[0])

        # Validate segment sequence
        expected_indices = set(range(len(sorted_segments)))
        actual_indices = set(index for index, _ in sorted_segments)
        if expected_indices != actual_indices:
            missing_segments = expected_indices - actual_indices
            logger.error(f'Missing segments: {missing_segments}')
            return None

        # Add all the TTS segments in order
        logger.info('Adding TTS segments to audio')
        for index, segment_path in sorted_segments:
            try:
                if isinstance(segment_path, str):
                    segment_path = Path(segment_path)
                if not segment_path.exists():
                    logger.error(f'Segment file not found: {segment_path}')
                    continue

                segment_audio = AudioSegment.from_file(str(segment_path), format=AUDIO_OUTPUT_FORMAT)
                combined += segment_audio
                successful_segments.append(segment_path)
                logger.info(f'Added segment: {segment_path.name}')
            except Exception as e:
                logger.error(f'Error adding segment {segment_path}: {str(e)}')

        # Only proceed if we have at least one successful segment
        if not successful_segments:
            logger.error('No segments were successfully processed')
            return None

        # Export the final audio file
        combined.export(str(final_output_path), format=AUDIO_OUTPUT_FORMAT, bitrate=AUDIO_OUTPUT_QUALITY)
        logger.info(f'Successfully exported combined audio to: {final_output_path.name}')
        return final_output_path

    except Exception as e:
        logger.error(f'Error combining audio segments: {str(e)}')
        if final_output_path.exists():
            final_output_path.unlink()
        return None
    finally:
        # Clean up temp files after export attempt
        cleanup_temp_files(successful_segments)

def get_audio_duration(filepath):
    """Calculate episode duration from MP3 file."""
    try:
        audio = MP3(filepath)
        duration = int(audio.info.length)
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        logger.error(f'Error calculating duration for {filepath}: {str(e)}')
        return "00:00:00"

def create_episode(text, title, description, base_filename='episode'):
    """Create a complete episode from text."""
    try:
        # Ensure temp directory is clean at start
        tmp_dir = ensure_temp_directory()

        # Split text into segments if needed
        segments = split_text(text)

        # Convert each segment to speech
        segment_data = []  # List of (index, path) tuples to maintain order
        for index, segment in enumerate(segments):
            logger.info(f'Processing segment {index + 1} of {len(segments)}')
            segment_file = text_to_speech_segment(segment, index, base_filename, tmp_dir)
            if segment_file:
                segment_data.append((index, segment_file))
            else:
                logger.error(f'Failed to create segment {index + 1}')
                # Clean up any segments we did create
                cleanup_temp_files([path for _, path in segment_data])
                return None

        # Combine all segments into final audio file
        if segment_data:
            final_path = combine_audio_segments(segment_data, base_filename)

            # Calculate duration and save episode to database
            if final_path:
                duration = get_audio_duration(final_path)
                if save_episode_to_db(final_path.name, title, description, duration=duration):
                    logger.info(f'Episode saved to database: {title}')
                    return final_path
            else:
                logger.error('Failed to save episode to database')
                return None

        return None
    except Exception as e:
        logger.error(f'Error creating episode: {str(e)}')
        return None
