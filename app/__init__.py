from flask import Flask
from .routes.create import create as create_blueprint
from .routes.feed import feed as feed_blueprint
from .routes.index import index as index_blueprint
from config.config import MAX_REQUEST_SIZE
import logging

def create_app():
    app = Flask(__name__)

    # Set maximum request size from config
    app.config['MAX_CONTENT_LENGTH'] = MAX_REQUEST_SIZE

    # Configure logging
    if not app.debug:
        # In production, set up logging only if not in debug mode
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

        # Set up logging for our modules
        for logger_name in ['app.services', 'app.routes']:
            logger = logging.getLogger(logger_name)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            # Prevent log messages from being propagated to the root logger
            logger.propagate = False

    # Register blueprints
    app.register_blueprint(index_blueprint, url_prefix='/')
    app.register_blueprint(create_blueprint, url_prefix='/create')
    app.register_blueprint(feed_blueprint, url_prefix='/feed')

    return app
