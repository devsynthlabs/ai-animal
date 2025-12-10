import os

class Config:
    """Application configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = 'gemini-2.0-flash'
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # BPA Integration
    BPA_API_URL = os.getenv('BPA_API_URL', '')
    BPA_API_KEY = os.getenv('BPA_API_KEY', '')
    
    # ATC Scoring Configuration
    ATC_TRAITS = {
        'structural': [
            {'id': 'stature', 'name': 'Stature', 'description': 'Height at withers'},
            {'id': 'chest_width', 'name': 'Chest Width', 'description': 'Width between front legs'},
            {'id': 'body_depth', 'name': 'Body Depth', 'description': 'Depth of barrel/body'},
            {'id': 'rump_angle', 'name': 'Rump Angle', 'description': 'Slope from hooks to pins'},
            {'id': 'rump_width', 'name': 'Rump Width', 'description': 'Width between pin bones'},
            {'id': 'rear_legs', 'name': 'Rear Legs', 'description': 'Angle and set of rear legs'},
            {'id': 'foot_angle', 'name': 'Foot Angle', 'description': 'Angle of front feet'},
            {'id': 'body_condition', 'name': 'Body Condition', 'description': 'Overall body condition score'},
        ],
        'udder': [
            {'id': 'fore_udder', 'name': 'Fore Udder Attachment', 'description': 'Strength of fore attachment'},
            {'id': 'rear_udder_height', 'name': 'Rear Udder Height', 'description': 'Height of rear attachment'},
            {'id': 'udder_depth', 'name': 'Udder Depth', 'description': 'Udder floor relative to hocks'},
            {'id': 'teat_placement', 'name': 'Teat Placement', 'description': 'Position of teats'},
            {'id': 'teat_length', 'name': 'Teat Length', 'description': 'Length of teats'},
        ]
    }
    
    # Animal Types
    ANIMAL_TYPES = ['cattle', 'buffalo']
    
    # Score range (1-9 scale)
    SCORE_MIN = 1
    SCORE_MAX = 9
