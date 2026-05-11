import logging

from flask import Flask
from flask_cors import CORS

from app.config import config
from app.routes.filter_routes import filter_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smart-filter-selector")

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(filter_bp)

    # Startup message
    @app.before_request
    def startup():
        if not hasattr(app, 'startup_done'):

            logger.info("🚀 Smart Filter Selector Service Started")
            logger.info(f"📊 Ollama URL: {config.OLLAMA_URL}")
            logger.info(f"🤖 LLM Model: {config.OLLAMA_LLM_MODEL}")
            logger.info(f"📝 Embedding Model: {config.OLLAMA_EMBEDDING_MODEL}")
            app.startup_done = True

    return app

app = create_app()