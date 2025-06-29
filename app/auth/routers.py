from fastapi import APIRouter,status,Depends,HTTPException,Body
from .schemas import *
from sqlalchemy.ext.asyncio import AsyncSession
from ..Database.session import get_db
from .views import all_users_view,get_particular_user_view,login_view
from typing import List
from .security import AccessTokenBearer
from .views import UserService,RoleService
from .utils import get_current_user

user_service = UserService()
role_service= RoleService()

user_router = APIRouter(
    prefix="/users",
    tags=["users"]

)



@user_router.post("/create",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
async def Create_user(userData: CreateUser,db: AsyncSession = Depends(get_db)):
    user_details=await user_service.create_user_view(userData,db)
    return user_details
    # try:
    #   return await user_service.create_user_view(userData,db)
    # except Exception as e:
    #     print(f"Error creating user: {e.__class__.__name__}: {e}")
    #     raise HTTPException(
            
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Failed to create user: {type(e).__name__}"
    #     )
       



from .custom_swagger_form import OAuth2EmailRequestForm

from .utils import Hash
from fastapi.responses import JSONResponse
from .security import create_access_token2
from datetime import timedelta
from datetime import datetime
from ..config.errors import InvalidCredentials



@user_router.post("/login", )
async def login(request: UserLoginModel,db:AsyncSession=Depends(get_db)):
    email=request.email
    # print("-----------",email)
    user_data=await user_service.get_user_by_email(email,db)
    # print("us----",user_data)
    if user_data is not None:
        password_valid=Hash.verify_password(user_data.password,request.password)
        if password_valid:
            access_token = create_access_token2(user_data={'user_id':user_data.id,'email':user_data.email,"name":user_data.name})
            refresh_token = create_access_token2(user_data={'user_id':user_data.id,'email':user_data.email,"name":user_data.name},refresh=True,expiry=timedelta(days=2))
    
            return JSONResponse(
                content={
                "message":"Login Successfully",
                "access_token": access_token,
                "refresh_token":refresh_token,
                "user_data":{
                    "user_id":user_data.id,
                    "email":user_data.email,
                    "name":user_data.name
                }
                }
            
            ) 
    raise InvalidCredentials()



from .utils import RefreshTokenBearer


@user_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token2(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
    )



       
from ..auth.utils import AccessTokenBearer

@user_router.get("/all",status_code =status.HTTP_200_OK,response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db),current_user=Depends(AccessTokenBearer())):
    try:
       user_data= await user_service.get_all_user_view(db)
       return user_data
    except Exception as e:
       raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )
    

@user_router.get("/particular",status_code=status.HTTP_200_OK,response_model=UserResponse)
async def get_particular_user(db:AsyncSession=Depends(get_db)):
    try:
        user_data=await get_particular_user_view(db)
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )

        



from pydantic import ValidationError
@user_router.get('/me',response_model=meBookResponse)
async def get_current_user_data(user=Depends(get_current_user)):
    try:
        print("user--------",user)
        
        return user
    except ValidationError as e:
        print("Validation error:", e)
        return JSONResponse(status_code=500, content=e.errors())




# @user_router.get("/{user_id}",status_code =status.HTTP_200_OK,response_model=Getuser)
# def get_user_by_id(user_id:int,db: Session = Depends(get_db)):
#     return get_user_by_id_view(db,user_id)



from ..Database.redis import add_jti_to_blocklist

@user_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )





# roles

@user_router.post("/role/create",response_model=RoleResponse,status_code=status.HTTP_201_CREATED)
async def create_Role(roleData:CreateRole,db:AsyncSession=Depends(get_db)):
    return await role_service.create_role_view(roleData, db)




@user_router.post("/{user_id}/assign-role", response_model=UserWithRole)
async def assign_role(
    user_id: int,
    role_id: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    return await role_service.assign_role_to_user(user_id, role_id, db)



from .permission import require_permission,Permission

@user_router.get("/all/role",response_model=List[RoleResponse],status_code=status.HTTP_200_OK)
async def get_all_role(
    current_user = Depends(require_permission(Permission.READ_ROLES)),
    db:AsyncSession=Depends(get_db)
):
    return await role_service.get_all_role_view(db)

