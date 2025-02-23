from app import create_app
from config.config import SERVER_HOST, SERVER_PORT, FLASK_DEBUG

app = create_app()

if __name__ == '__main__':
    if FLASK_DEBUG:
        # Development mode with auto-reload
        app.run(debug=True)
    else:
        # Production mode with waitress
        from waitress import serve
        print(f"Starting server on {SERVER_HOST}:{SERVER_PORT}")
        serve(app, host=SERVER_HOST, port=SERVER_PORT)
