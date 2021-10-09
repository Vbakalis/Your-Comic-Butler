import sqlalchemy

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base



engine = create_engine("sqlite:///subscribers.db")
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()



class Subsribers(Base):
    __tablename__ = "subscriber"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50))
    informed = Column(Integer)

    def __repr__(self):
        return f"{self.id} {self.last_name} {self.first_name} {self.email} {self.informed}"

subscribers = session.query(Subsribers).all()

def fetch_emails():
    email = []
    for subscriber in subscribers:
        email.append(subscriber.email)
    return email

def is_informed():
    informed = []
    for info in subscribers:
        informed.append(bool(info.informed))
    return informed

def is_everyone_informed(informed):
    info = session.query(Subsribers).first()
    info.informed = informed
    session.add(info)
    session.commit()
