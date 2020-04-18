import sqlalchemy
import random
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import dotenv
import os

dotenv.load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


engine: sqlalchemy.engine.Engine = sqlalchemy.create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base(bind=engine)



