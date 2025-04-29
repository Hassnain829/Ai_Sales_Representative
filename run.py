from app import create_app
from app.models import db
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    with app.app_context():
        # Initialize database
        db.create_all()
        
    # Start application
    app.run(host='127.0.0.1', port=5000)