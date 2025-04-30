from app import create_app, db  # Change this line

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Initialize database
        db.create_all()
        
    # Start application
    app.run(host='127.0.0.1', port=5000)