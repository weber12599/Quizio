import jwt
import models
from core.security import ALGORITHM, SECRET_KEY
from database import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# This tells FastAPI that the token is obtained from this endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> models.User:
    """
    Validate the JWT token and return the current teacher/user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user
