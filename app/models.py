from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
Base = declarative_base()

class Activity(Base):
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Route(Base):
    __tablename__ = 'routes'
    
    id = Column(Integer, primary_key=True)
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)
    end_latitude = Column(Float)
    end_longitude = Column(Float)
    distance = Column(Float)
    duration = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    activities = relationship('Activity', secondary='route_activities')

class RouteActivity(Base):
    __tablename__ = 'route_activities'
    
    route_id = Column(Integer, ForeignKey('routes.id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), primary_key=True)
    distance_from_route = Column(Float)

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    preference = Column(JSONB, nullable=False)

class Reservation(Base):
    __tablename__ = 'reservations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False)
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=True)
    
    # Informations de réservation
    reservation_date = Column(DateTime, nullable=False)
    number_of_people = Column(Integer, default=1)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="eur")
    
    # Statut de la réservation
    status = Column(String(20), default="pending")  # pending, confirmed, cancelled, completed
    
    # Informations de paiement Stripe
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_client_secret = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relations
    user = relationship("Users", backref="reservations")
    activity = relationship("Activity", backref="reservations")
    route = relationship("Route", backref="reservations")