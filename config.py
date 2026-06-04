import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///guntur.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Web Push VAPID keys (generate your own for production)
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', 'your-private-vapid-key')
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 'your-public-vapid-key')
    VAPID_CLAIMS = {
        'sub': 'mailto:admin@gunturmunicipal.com'
    }
