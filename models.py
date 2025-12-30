from database_config import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100))
    email = Column(String(100), nullable=False, unique=True)
    entreprise = Column(String(100), nullable=False)
    telephone = Column(String(30))
    adresse = Column(String(500))
    ville = Column(String(100))
    code_postal = Column(String(10))
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    # Relation vers les abonnements
    abonnements = relationship('Abonnement', back_populates='client')

class Abonnement(Base):
    __tablename__ = 'abonnements'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    plan = Column(String(50), nullable=False)  # starter, pro, enterprise
    prix_mensuel = Column(Numeric(10, 2), nullable=False)
    date_debut = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_fin = Column(DateTime)
    statut = Column(String(20), default='actif')  # actif, suspendu, annule, expire
    periode_essai = Column(Boolean, default=True)
    date_fin_essai = Column(DateTime)
    
    # Relation vers le client
    client = relationship('Client', back_populates='abonnements')

class DemoRequest(Base):
    __tablename__ = 'demo_requests'
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    entreprise = Column(String(100), nullable=False)
    telephone = Column(String(30), nullable=False)
    effectif = Column(String(20), nullable=True)
    plan_choisi = Column(String(50), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
