from sqlalchemy.orm import sessionmaker
from .model import Base, FFGSPrecip
import csv
import os


def init_hydroviewer_hispaniola_db(engine, first_time):
    """
    A persistent store initializer function
    """
    # Create tables
    Base.metadata.create_all(engine)

    # Initial data
    if first_time:
        # Make session
        SessionMaker = sessionmaker(bind=engine)
        session = SessionMaker()

        # Initialize database with ffgs data_staging.csv values
        current_path = os.path.dirname(os.path.realpath(__file__))
        data_staging_file = os.path.join(
            current_path, "staging/data_staging.csv")

        with open(data_staging_file, 'r') as f:
            reader = csv.reader(f)
            data_list = map(tuple, reader)
            id_list = []
            value_list = []
            for n in data_list:
                if len(n) == 2:
                    id_list.append(n[0])
                    value_list.append(n[1])

                new_row = FFGSPrecip(id=n[0], value=n[1])
                session.add(new_row)

        session.commit()
        session.close()