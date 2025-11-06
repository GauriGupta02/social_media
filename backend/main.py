from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from . import models, schemas
from .database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Social Media Backend")

# ----------------- STATIC FILES -----------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ----------------- CORS -----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------------- DATABASE DEPENDENCY -----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------- SIGNUP -----------------
@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        return {"success": False, "message": "Email already registered"}

    hashed_password = pwd_context.hash(user.password[:72])
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"success": True, "message": "Signup successful!"}


# ----------------- LOGIN -----------------
@app.post("/login")
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Invalid email or password")
    if not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Login successful", "user": user.email}


# ----------------- PROFILE -----------------
@app.get("/profile/{email}", response_model=schemas.ProfileResponse)
def get_profile(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user.username,
        "email": user.email,
        "joined_on": user.created_at,
        "profile_pic": user.profile_pic if user.profile_pic else None
    }


# ----------------- UPLOAD PROFILE PIC -----------------
@app.post("/upload-profile-pic/{email}")
async def upload_profile_pic(
    email: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Save uploaded file
    filename = f"{user.id}_{file.filename}"
    file_location = os.path.join(UPLOAD_DIR, filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Update DB with public URL
    user.profile_pic = f"/uploads/{filename}"
    db.commit()
    db.refresh(user)

    return {"message": "Profile picture uploaded successfully", "path": user.profile_pic}
