from app import app
import os  # ← needed to read environment variables

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Use Render's port, fallback to 5000 locally
    app.run(host='0.0.0.0', port=port, debug=True)
