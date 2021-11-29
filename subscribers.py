import sqlalchemy

from sqlalchemy import create_engine, Column, Integer, String
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
    emails = []
    for subscriber in subscribers:
        emails.append(subscriber.email)
    return emails

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

def add_subscriber_to_db(new_sub_info):
    new_subscriber = Subsribers(first_name = new_sub_info[1], last_name = new_sub_info[2], email = new_sub_info[0], informed = 0)
    session.add(new_subscriber)
    session.commit()
