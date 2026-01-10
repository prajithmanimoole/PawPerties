"""
Authentication service for user login and session management
Handles all security and access control
"""

from flask import session, redirect, url_for, flash
from models import User, db
from functools import wraps
from typing import Optional


class AuthService:
    """Service class for authentication operations"""

    @staticmethod
    def register_user(full_name: str, customer_key: str, pan: str, aadhar: str, password: str) -> tuple[bool, Optional[User], str]:
        """
        Register a new user with the 'user' role using Customer Key as username.
        Returns: (success, user_object, message)
        """
        # Use Customer Key as the username, ensuring it's unique
        if User.query.filter_by(username=customer_key).first():
            return False, None, "A user with this Customer Key is already registered."

        new_user = User(
            username=customer_key,  # Customer Key is the username
            full_name=full_name,
            aadhar=aadhar,
            pan=pan,
            role='user',
            password=password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return True, new_user, "Registration successful. Please log in."
        except Exception as e:
            db.session.rollback()
            return False, None, f"Registration failed: {str(e)}"
    
    @staticmethod
    def login_user(username: str, password: str) -> tuple[bool, Optional[User], str]:
        """
        Authenticate user and create session
        Accepts username, PAN, or Aadhar for login
        Returns: (success, user_object, message)
        """
        # Try to find user by username, PAN, or Aadhar
        user = User.query.filter(
            (User.username == username) |
            (User.pan == username) |
            (User.aadhar == username)
        ).first()
        
        if not user:
            return False, None, "Invalid login ID or password"
        
        if not user.is_active:
            return False, None, "Account is deactivated"
        
        if user.password != password:
            return False, None, "Invalid login ID or password"
        
        # Update last login
        user.update_last_login()
        
        # Create session
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['full_name'] = user.full_name
        
        return True, user, "Login successful"
    
    @staticmethod
    def logout_user():
        """Clear user session"""
        session.clear()
    
    @staticmethod
    def get_current_user() -> Optional[dict]:
        """Get current logged-in user from session"""
        if 'user_id' in session:
            return {
                'id': session['user_id'],
                'username': session['username'],
                'role': session['role'],
                'full_name': session['full_name']
            }
        return None
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is logged in"""
        return 'user_id' in session
    
    @staticmethod
    def is_admin() -> bool:
        """Check if current user is admin"""
        return session.get('role') == 'admin'
    
    @staticmethod
    def is_officer() -> bool:
        """Check if current user is officer"""
        return session.get('role') == 'officer'

    @staticmethod
    def is_user() -> bool:
        """Check if current user is a regular user"""
        return session.get('role') == 'user'


# Decorator functions for route protection

def login_required(f):
    """
    Decorator to require login for a route
    Redirects to login page if not authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin role for a route
    Officers cannot access admin-only routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        if not AuthService.is_admin():
            flash('Admin privileges required for this action.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def officer_or_admin_required(f):
    """
    Decorator to require officer or admin role
    This is the standard protection for most routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        if not (AuthService.is_officer() or AuthService.is_admin()):
            flash('Insufficient privileges.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    """
    Decorator to require 'user' role for a route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        if not AuthService.is_user():
            flash('This page is for users only.', 'danger')
            return redirect(url_for('dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function
