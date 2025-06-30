from dotenv import load_dotenv
from app import create_app

load_dotenv()
app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)


    '# To run the application, use the command:\n# python run.py\n'
    '# Ensure that the .env file is properly configured with the necessary environment variables.\n'