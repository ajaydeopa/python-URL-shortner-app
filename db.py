import os
import sys
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

class URLs(Base):
    __tablename__ = 'url_map'
    id = Column(Integer, primary_key=True)
    longURL = Column(String(500), nullable=False)
    shortURL = Column(String(250), nullable=False)
    visitCount = Column(Integer, nullable=False)

engine = create_engine('sqlite:///hackerEarth.db')

# Create all tables in the engine.
Base.metadata.create_all(engine)