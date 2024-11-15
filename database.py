from sqlalchemy import create_engine, Column, Integer, String, TEXT, DATE
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

Base = declarative_base()


class Image_data(Base):
    __tablename__: String = 'image'
    image_path: String = Column(String(255), primary_key=True)
    image_feature: TEXT = Column(TEXT(1024))
    date: DATE = Column(DATE)


def create_db_session(connection_string) -> scoped_session:
    engine = create_engine(connection_string, echo=True)
    Session = scoped_session(sessionmaker(bind=engine))
    Base.metadata.create_all(engine)
    return Session
