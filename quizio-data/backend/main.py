from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Column, Integer, String, select
from pydantic import BaseModel
import os
import jwt
from datetime import datetime, timedelta

from database import engine, Base, get_db
from sqlalchemy.ext.asyncio import AsyncSession

# --- 0. JWT & Auth Configuration ---
# Secret key for signing the JWT (Should be kept secret in production)
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_super_secret_jwt_key_here')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token expires in 24 hours

# Admin credentials for login
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# This tells FastAPI where the login endpoint is, so Swagger UI knows how to authenticate
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

# Helper function to generate JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to verify the dynamic JWT
def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token has expired')
    except jwt.InvalidTokenError:
        raise credentials_exception

# --- 1. SQLAlchemy Models ---
class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)

# --- 2. FastAPI Setup ---
app = FastAPI(
    title='Quizio Data API',
    description='Quizio 快問快答的資料中心，支援 JWT 動態驗證。',
    version='0.0.0'
)

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- 3. Pydantic Schemas ---
class AuthRequest(BaseModel):
    student_id: str
    password: str

class StudentCreate(BaseModel):
    student_id: str
    name: str
    password: str

# --- 4. API Endpoints ---

@app.post('/api/auth/login', tags=['驗證與登入 (Auth)'], summary='管理員登入獲取 Token')
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    '''
    Teacher/Admin login endpoint.
    Send username and password as form data to receive a JWT Bearer token.
    '''
    if form_data.username != ADMIN_USERNAME or form_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    # Generate token if credentials are correct
    access_token = create_access_token(data={'sub': form_data.username})
    
    # Return format required by OAuth2
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.post('/api/auth/student', tags=['驗證與登入 (Auth)'], summary='驗證學生身分')
async def verify_student_identity(
    request: AuthRequest, 
    db: AsyncSession = Depends(get_db),
    # Require dynamic JWT token
    current_user: str = Depends(verify_token)
):
    '''Verify student credentials (called by the Laptop Game Server).'''
    stmt = select(Student).where(Student.student_id == request.student_id)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    if student and student.password == request.password:
        return {
            'status': 'success',
            'name': student.name,
            'student_id': student.student_id
        }
    
    raise HTTPException(status_code=401, detail='Invalid student_id or password')


@app.post('/api/students', tags=['學生管理 (Students)'], summary='新增學生')
async def create_student(
    student: StudentCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(verify_token) # Protect this endpoint too
):
    '''Add a new student to the database. Requires Token.'''
    stmt = select(Student).where(Student.student_id == student.student_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
         raise HTTPException(status_code=400, detail='Student ID already exists')

    new_student = Student(
        student_id=student.student_id,
        name=student.name,
        password=student.password
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return {'message': 'Student created successfully', 'name': new_student.name}


@app.get('/api/students', tags=['學生管理 (Students)'], summary='取得所有學生名單')
async def get_all_students(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(verify_token) # Protect this endpoint too
):
    '''List all students. Requires Token.'''
    stmt = select(Student).order_by(Student.student_id)
    result = await db.execute(stmt)
    students = result.scalars().all()
    return [{'student_id': s.student_id, 'name': s.name, 'password': s.password} for s in students]