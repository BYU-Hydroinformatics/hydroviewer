from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float

# DB Engine, sessionmaker, and base
Base = declarative_base()


# SQLAlchemy ORM definition for the ffgs_precip table
class FFGSPrecip (Base):
    """
    Example SQLAlchemy DB Model
    """
    __tablename__ = 'ffgs_precip'

    # Columns
    id = Column(Integer, primary_key=True)
    value = Column(Integer)

    def __init__(self, id, value):
        """
        Constructor for a ffgs results table
        """
        self.id = id
        self.value = value
