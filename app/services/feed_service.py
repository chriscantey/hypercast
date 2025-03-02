import xml.etree.ElementTree as ET
from xml.dom import minidom
from mutagen.mp3 import MP3
import os
from pathlib import Path
import logging
from config.config import (
    FEED_TITLE,
    FEED_DESCRIPTION,
    BASE_URL,
    FEED_LANGUAGE,
    FEED_IMAGE,
    AUDIO_PATH,
)
from .database_service import db

logger = logging.getLogger(__name__)

def generate_feed():
    """Generate RSS feed XML."""
    rss = ET.Element("rss", version="2.0",
                    attrib={"xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"})
    channel = ET.SubElement(rss, "channel")

    # Add channel information
    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "description").text = FEED_DESCRIPTION
    ET.SubElement(channel, "link").text = f"{BASE_URL}/feed"
    ET.SubElement(channel, "language").text = FEED_LANGUAGE
    ET.SubElement(channel, "itunes:image", href=f"{BASE_URL}/static/images/{FEED_IMAGE}")

    # Get episodes from database
    episodes = db.get_all_episodes()

    # Add episodes to feed
    for filename, title, description, pub_date, duration in episodes:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "description").text = description

        # Create the full URL for the audio file
        audio_url = f"{BASE_URL}/static/audio/{filename}"
        ET.SubElement(item, "enclosure",
                     url=audio_url,
                     type="audio/mpeg")

        ET.SubElement(item, "pubDate").text = pub_date

        # Add duration if available
        if duration:
            ET.SubElement(item, "itunes:duration").text = duration
        else:
            ET.SubElement(item, "itunes:duration").text = "00:00:00"

    # Convert to pretty XML
    rough_string = ET.tostring(rss, 'utf-8', method='xml')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
