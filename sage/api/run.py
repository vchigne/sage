"""Server runner for SAGE API."""
import os
import logging
from .app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the server."""
    try:
        logger.info("Starting SAGE API server preparation...")
        app = create_app()
        logger.info("Flask app created successfully")
        logger.info("Configuring server parameters...")

        # ALWAYS serve the app on port 5000 and bind to all interfaces
        port = 5000
        host = '0.0.0.0'
        logger.info(f"Starting server on {host}:{port}")

        app.run(
            host=host,
            port=port,
            debug=True,
            use_reloader=False  # Disable reloader to prevent duplicate processes
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

if __name__ == '__main__':
    main()
