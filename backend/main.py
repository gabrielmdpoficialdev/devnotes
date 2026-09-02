from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

SECRET_KEY = "sua_chave_secreta_super_segura_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

app = FastAPI(title="DevNotes Auth API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
  from database import init_db

  init_db()


def get_db():
  from database import SessionLocal

  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


class UserCreate(BaseModel):
  email: str
  password: str


class UserLogin(BaseModel):
  email: str
  password: str


class NoteCreate(BaseModel):
  title: str
  category: str
  content: str


def verify_password(plain_password, hashed_password):
  return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
  pwd_bytes = password.encode("utf-8")
  if len(pwd_bytes) > 72:
    pwd_bytes = pwd_bytes[:72]
  return pwd_context.hash(pwd_bytes.decode("utf-8"))


def create_access_token(data: dict):
  to_encode = data.copy()
  expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  to_encode.update({"exp": expire})
  return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
  from database import User

  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Credenciais inválidas",
      headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email: str = payload.get("sub")
    if email is None:
      raise credentials_exception
  except JWTError:
    raise credentials_exception
  user = db.query(User).filter(User.email == email).first()
  if user is None:
    raise credentials_exception
  return user


@app.post("/api/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  from database import User

  existing_user = db.query(User).filter(User.email == user_data.email).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="E-mail já cadastrado")

  hashed_password = get_password_hash(user_data.password)
  new_user = User(email=user_data.email, hashed_password=hashed_password)
  db.add(new_user)
  db.commit()
  return {"message": "Usuário criado com sucesso"}


@app.post("/api/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
  from database import User

  user = db.query(User).filter(User.email == user_data.email).first()
  if not user or not verify_password(user_data.password, user.hashed_password):
    raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")

  access_token = create_access_token(data={"sub": user.email})
  return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/notes")
def list_notes(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
  return current_user.notes


@app.post("/api/notes", status_code=status.HTTP_201_CREATED)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
  from database import Note

  word_count = len(note.content.split())
  enhanced_content = (
      f"{note.content}\n\n[Auto-Análise: {word_count} palavras]"
  )

  db_note = Note(
      title=note.title,
      category=note.category,
      content=enhanced_content,
      owner_id=current_user.id,
  )
  db.add(db_note)
  db.commit()
  db.refresh(db_note)
  return db_note


@app.delete("/api/notes/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
  from database import Note

  db_note = (
      db.query(Note)
      .filter(Note.id == note_id, Note.owner_id == current_user.id)
      .first()
  )
  if not db_note:
    raise HTTPException(status_code=404, detail="Nota não encontrada")
  db.delete(db_note)
  db.commit()
  return {"message": "Nota deletada com sucesso"}