from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import *
from .models import User,Role
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from fastapi import HTTPException,status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from ..auth.utils import Hash
from fastapi.security import OAuth2PasswordRequestForm
from .security import create_access_token2
from sqlalchemy.orm import joinedload,selectinload


class UserService:
    async def get_user_by_email(self,email:str,db:AsyncSession):
        stmt=await db.execute(select(User)
            .options(joinedload(User.role))
            .where(User.email==email))
        print("-----",stmt)
        user_data=stmt.scalars().first()
        print("user------",user_data)
        return user_data
    

    async def create_user_view(self,userData:CreateUser,db:AsyncSession):
        print("--------cre------",userData)
        try:
            result=await db.execute(select(User).where(User.email==userData.email))
            existing_user=result.scalars().first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already Exist"
                )
            
            #Hash Password
            hashed_password = Hash.bcrypt(userData.password)

            db_user = User(
                name=userData.name,
                email=userData.email,
                password=hashed_password,
                role_id=userData.role
                
            )

            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists."
            )


        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})
    
    

    async def get_all_user_view(self,db:AsyncSession):
        try:
            result=await db.execute(select(User).options(selectinload(User.role)))
            user_data=result.scalars().all()
            return user_data
        except SQLAlchemyError as e:
            raise e









from sqlalchemy import func 


class RoleService:
    async def create_role_view(self, roleData: CreateRole, db: AsyncSession):
        # First check for existing role
        result = await db.execute(
            select(Role).where(func.lower(Role.name) == func.lower(roleData.name))
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already exists"
            )
        
        # Then try to create
        try:
            db_role = Role(**roleData.model_dump())
            db.add(db_role)
            await db.commit()
            await db.refresh(db_role)
            return db_role
        except SQLAlchemyError as e:
            await db.rollback()
          
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while creating role"
            )
        
    async def assign_role_to_user(self,user_id: int, role_id: int, db: AsyncSession) -> User:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        role = await db.get(Role, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
            
        user.role = role
        await db.commit()
        await db.refresh(user)
        return user
    
    async def get_all_role_view(self,db:AsyncSession):
        try:
            result=await db.execute(select(Role))
            role_Data=result.scalars().all()
            return role_Data
        except SQLAlchemyError as e:
            raise e



















    














from datetime import timedelta
from fastapi.responses import JSONResponse

async def login_view(request:OAuth2PasswordRequestForm,db:AsyncSession):
    print("req------",request)
    result=await db.execute(select(User).where(User.name==request.username))
    user_data=result.scalars().first()
    print("user_data-----",user_data)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid email or password"
        )
    
    if not Hash.verify_password(user_data.password, request.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Password"
        )
    access_token = create_access_token2(user_data={'email':user_data.email,"name":user_data.name})


    refresh_token = create_access_token2(user_data={'email':user_data.email,"name":user_data.name},refresh=True,expiry=timedelta(days=2))
    
    return JSONResponse(
        content={
        "message":"Login Successfully",
        "access_token": access_token,
        "refresh_token":refresh_token,
        "user_data":{
            "email":user_data.email,
            "name":user_data.name
        }
        }
       
    ) 









async def all_users_view(db:AsyncSession):

    """
    🔹 stmt = select(User)
        This uses the SQLAlchemy 2.0 Core syntax to create a SELECT query for the User table.
        select(User) is a query object, not yet executed. It's equivalent to SELECT * FROM users.

    🔹 result = await db.execute(stmt)
        This executes the SQL query asynchronously.
        Returns a Result object, which wraps the raw database response.

    🔹 users = result.scalars().all()
        .scalars() extracts only the actual model instances (User) from the rows.
        Without .scalars(), the result would return full row tuples (e.g., (User(),)).
        .all() collects all matching rows into a Python list.

    """


    try:
        stmt=select(User)  #select(User) is a query object, not yet executed. It's equivalent to SELECT * FROM users.
        result=await db.execute(stmt)
        users=result.scalars().all()
        return users
    except SQLAlchemyError as e:
        raise e
    

async def get_particular_user_view(db:AsyncSession):
    stmt=select(User.name)

    #scalar
    result=await db.execute(stmt)
    scalar_name=result.scalar()

    #scalar_one
    try:
        result1=await db.execute(stmt)
        scalar_one_name = result1.scalar_one()
    except Exception as e:
        print(e)

    # scalar_one_or_none
    result2 = await db.execute(stmt)
    scalar_one_or_none_name = result2.scalar_one_or_none()

    # scalars
    result3 = await db.execute(stmt)
    scalars_names = result3.scalars().all()

    return {
        "scalar_name": scalar_name,
        "scalar_one_name": scalar_one_name,
        "scalar_one_or_none_name": scalar_one_or_none_name,
        "scalars_names": scalars_names
    }

    
        


