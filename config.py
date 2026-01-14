"""
Configuration settings for Property Registration Blockchain System
This file contains all security and application settings
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask secret key for session management (generate new for production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database configuration (for authentication only)
    DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    
    # Fix for Render PostgreSQL SSL requirement
    if DATABASE_URI and ('postgresql://' in DATABASE_URI or 'postgres://' in DATABASE_URI):
        # Render PostgreSQL requires SSL
        if 'sslmode' not in DATABASE_URI:
            DATABASE_URI = DATABASE_URI + ('&' if '?' in DATABASE_URI else '?') + 'sslmode=require'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy engine options for PostgreSQL SSL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before using
        'pool_recycle': 300,    # Recycle connections after 5 minutes
    }
    
    # Blockchain persistence file
    BLOCKCHAIN_FILE = 'blockchain_data.pkl'
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Application settings
    DEBUG = False
    TESTING = False
