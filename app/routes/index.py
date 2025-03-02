from flask import Blueprint, render_template
from ..services.feed_service import generate_feed
from ..services.database_service import db
from config.config import FEED_TITLE, FEED_DESCRIPTION, FEED_IMAGE
from datetime import datetime
from email.utils import parsedate_to_datetime
from datetime import timezone

index = Blueprint('index', __name__)

@index.route('/')
def home():
    """Render the home page with feed episodes."""
    episodes = db.get_all_episodes()

    # Format episodes with local time
    formatted_episodes = []
    for episode in episodes:
        filename, title, description, pub_date, duration = episode

        # Parse the GMT timestamp and convert to local time
        dt = parsedate_to_datetime(pub_date)
        local_dt = dt.astimezone()

        # Format in desired format
        formatted_date = local_dt.strftime("%a, %b %d, %Y %I:%M %p")

        formatted_episodes.append((
            filename,
            title,
            description.strip().replace('\r\n', '\n').replace('\r', '\n').replace('\n\n', '\n').replace('\n', '<br>'),
            formatted_date,
            duration
        ))

    return render_template('index.html',
                         episodes=formatted_episodes,
                         feed_title=FEED_TITLE,
                         feed_description=FEED_DESCRIPTION,
                         feed_image=FEED_IMAGE)
