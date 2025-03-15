from flask import Blueprint, request, jsonify, render_template
from ..services.background_tasks import process_episode_async
from ..services.content_service import validate_input
from ..middleware.auth import require_api_key
import logging

logger = logging.getLogger(__name__)

create = Blueprint('create', __name__)

@create.route('', methods=['GET'])
def create_form():
    """Render the create episode form."""
    return render_template('create.html')

@create.route('', methods=['POST'])
@require_api_key
def create_episode_endpoint():
    """Create an episode from input (text or URL)."""
    data = request.get_json()

    if not data or 'input' not in data:
        return jsonify({'error': 'Missing input parameter'}), 400

    try:
        # Validate input and fetch URL content if necessary
        # This will raise ValueError if input is empty
        # or RequestException if URL fetch fails
        content, original_url = validate_input(data['input'])

        # Start background processing with pre-validated content
        process_episode_async(content, original_url)

        # Return immediately with acceptance message
        return jsonify({
            'message': 'Request accepted for processing',
            'status': 'processing'
        }), 202

    except ValueError as e:
        logger.error(f'Input validation error: {str(e)}')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Error initiating processing: {str(e)}')
        return jsonify({'error': str(e)}), 500
