#Importa componentes fundamentais que cria, por exemplo, o motor de conexão, tipos de dados, colunas...
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
#Base para modelos declarativos
from sqlalchemy.ext.declarative import declarative_base
#Transmuta ferramentes para gerenciar sessões de banco de dados e suas relações (nas tabelas).
from sqlalchemy.orm import sessionmaker, relationship

#URL QUE LIGA NA SQLite LOCAL.
SQLALCHEMY_DATABASE_URL = "sqlite:///./notes.db"

#Cria o motor da conexão + múltiplas threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
#Cria sessões para interagir com o banco de dados.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Modelo declarativo para criação de modelos de tabela.
Base = declarative_base()


class User(Base):
  __tablename__ = "users" #nome da tabela.

  id = Column(Integer, primary_key=True, index=True)
  email = Column(String, unique=True, index=True)
  hashed_password = Column(String)

  notes = relationship("Note", back_populates="owner") #Relacionamento com o modelo Note, cujo qual um usuário pode ter várias notas.


class Note(Base):
  __tablename__ = "notes" #nome da tabela na parte dos notes.

  id = Column(Integer, primary_key=True, index=True)
  title = Column(String, index=True)
  category = Column(String, index=True)
  content = Column(Text)
  owner_id = Column(Integer, ForeignKey("users.id")) #chave estrangeira com ID + USUÁRIO

  owner = relationship("User", back_populates="notes") #Relacionamento reverso com o modelo User, cujo cada nota pertence a um dono.


def init_db():
  #Cria-se todas as tabelas definidas herdadas da Base no banco de dados.
  Base.metadata.create_all(bind=engine)