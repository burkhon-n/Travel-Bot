import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Base, engine
from models.Trip import Trip
from models.User import User
from models.TripMember import TripMember
import logging
from utils.logging_config import setup_logging

if __name__ == '__main__':
    setup_logging()
    logging.info('db.reset dropping tables')
    Base.metadata.drop_all(bind=engine)
    logging.info('db.reset creating tables')
    Base.metadata.create_all(bind=engine)
    logging.info('db.reset complete')
