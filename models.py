from sqlalchemy import Column, Integer, String

from database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    gender = Column(String, nullable=False) 
    birthdate = Column(String, nullable=False) 
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    hr = Column(Integer, nullable=False)

