import threading
import logging
from .tts_service import create_episode
from .content_service import process_validated_input

logger = logging.getLogger(__name__)

def process_episode_async(content, original_url=None):
    """Process episode creation in a background thread."""
    def _process():
        try:
            # Process the pre-validated content
            processed = process_validated_input(content, original_url)

            # Create the episode with all necessary information
            output_path = create_episode(
                text=processed['text'],
                title=processed['title'],
                description=processed['description'],
                base_filename=processed['title'].lower().replace(' ', '-')[:50]  # Use title as base filename
            )

            if output_path:
                logger.info(f'Successfully processed episode: {processed["title"]}')
            else:
                logger.error('Failed to create episode')
        except Exception as e:
            logger.error(f'Error in background processing: {str(e)}')

    # Start processing in background thread
    thread = threading.Thread(target=_process)
    thread.daemon = True  # Thread will be terminated when main program exits
    thread.start()
