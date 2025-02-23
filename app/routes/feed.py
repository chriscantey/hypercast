from flask import Blueprint, Response
from ..services.feed_service import generate_feed
import logging

logger = logging.getLogger(__name__)

feed = Blueprint('feed', __name__)

@feed.route('')
def get_feed():
    """Generate and return the RSS feed."""
    try:
        rss_xml = generate_feed()
        return Response(rss_xml, mimetype='application/xml')
    except Exception as e:
        logger.error(f'Error generating feed: {str(e)}')
        return Response('Error generating RSS feed', status=500)
