"""
Database models for user authentication
SQLite is used ONLY for authentication - NOT for blockchain data
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """
    User model for officer, admin, and user authentication
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)  # This will store the Customer Key
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    aadhar = db.Column(db.String(20), unique=True, nullable=True)
    pan = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin', 'officer', 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    properties = db.relationship('Property', backref='owner', lazy=True)
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    messages = db.relationship('Message', backref='sender', lazy=True)
    
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role == 'admin'

    def is_officer(self) -> bool:
        """Check if user has officer privileges"""
        return self.role == 'officer'

    def is_user(self) -> bool:
        """Check if user has user privileges"""
        return self.role == 'user'
    
    def to_dict(self) -> dict:
        """Convert user object to dictionary (exclude password)"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Property(db.Model):
    """
    Property model to store property details
    """
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)
    property_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Float, nullable=False)
    survey_no = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Property {self.property_key}>'


class Appointment(db.Model):
    """
    Appointment model for scheduling property transfers and inheritance
    """
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_key = db.Column(db.String(255), nullable=False)
    appointment_type = db.Column(db.String(50), nullable=False)  # 'transfer' or 'inheritance'
    full_name = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'confirmed', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    messages = db.relationship('Message', backref='appointment', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Appointment {self.id} for {self.property_key}>'


class Message(db.Model):
    """
    Message model for chat between users and officials
    """
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id}>'


class BlockchainBackup(db.Model):
    """
    Model to store blockchain backup data in database
    """
    __tablename__ = 'blockchain_backups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # Friendly display name
    filename = db.Column(db.String(255), nullable=False)  # Original filename for reference
    backup_data = db.Column(db.Text, nullable=False)  # Encrypted blockchain data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who created the backup

    creator = db.relationship('User', backref='blockchain_backups')

    def __repr__(self):
        return f'<BlockchainBackup {self.name} - {self.created_at}>'


def init_db(app):
    """Initialize database with default users"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin exists, if not create default users
        if User.query.count() == 0:
            # Create default admin
            admin = User(
                username='admin',
                full_name='System Administrator',
                role='admin',
                is_active=True,
                password='admin123'  # Change in production!
            )

            # Create default officer
            officer = User(
                username='officer1',
                full_name='Property Officer',
                role='officer',
                is_active=True,
                password='officer123'  # Change in production!
            )

            db.session.add(admin)
            db.session.add(officer)
            db.session.commit()

            print("Default users created:")
            print("  Admin   - username: admin, password: admin123")
            print("  Officer - username: officer1, password: officer123")
