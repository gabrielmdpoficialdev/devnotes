from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = "sqlite:///./notes.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  email = Column(String, unique=True, index=True)
  hashed_password = Column(String)

  notes = relationship("Note", back_populates="owner")


class Note(Base):
  __tablename__ = "notes"

  id = Column(Integer, primary_key=True, index=True)
  title = Column(String, index=True)
  category = Column(String, index=True)
  content = Column(Text)
  owner_id = Column(Integer, ForeignKey("users.id"))

  owner = relationship("User", back_populates="notes")


def init_db():
  Base.metadata.create_all(bind=engine)