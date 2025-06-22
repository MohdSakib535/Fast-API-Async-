
from fastapi import HTTPException,Depends,status
from .models import User
from typing import List,Dict
from .utils import get_current_user







# Permission definitions
class Permission:
    # User permissions
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Book permissions
    CREATE_BOOK = "create_book"
    READ_BOOK = "read_book"
    UPDATE_BOOK = "update_book"
    DELETE_BOOK = "delete_book"
    
    # Role permissions
    MANAGE_ROLES = "manage_roles"
    ASSIGN_ROLES = "assign_roles"
    CREATE_ROLES = "create_roles"
    READ_ROLES = "read_roles"
    UPDATE_ROLES = "update_roles"
    DELETE_ROLES = "delete_roles"
    
    # System permissions
    VIEW_ANALYTICS = "view_analytics"
    SYSTEM_CONFIG = "system_config"

# Role permissions mapping - you can modify these based on your actual role names from database
ROLE_PERMISSIONS = {
    "admin": [
        Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER, Permission.DELETE_USER,
        Permission.CREATE_BOOK, Permission.READ_BOOK, Permission.UPDATE_BOOK, Permission.DELETE_BOOK,
        Permission.MANAGE_ROLES, Permission.ASSIGN_ROLES,Permission.CREATE_ROLES,Permission.READ_ROLES,Permission.UPDATE_ROLES,Permission.UPDATE_ROLES,Permission.DELETE_ROLES,
        Permission.VIEW_ANALYTICS, Permission.SYSTEM_CONFIG
    ],
    "librarian": [
        Permission.READ_USER, Permission.UPDATE_USER,
        Permission.CREATE_BOOK, Permission.READ_BOOK, Permission.UPDATE_BOOK, Permission.DELETE_BOOK,
        Permission.VIEW_ANALYTICS
    ],
    "user": [
        Permission.READ_USER, Permission.READ_BOOK
    ],
    "moderator": [  # Example of additional role
        Permission.READ_USER, Permission.UPDATE_USER,
        Permission.READ_BOOK, Permission.UPDATE_BOOK,
        Permission.VIEW_ANALYTICS
    ]
}







# Dynamic role-based access control
class DynamicRoleChecker:
    def __init__(self, allowed_role_names: List[str] = None, allowed_role_ids: List[int] = None):
        self.allowed_role_names = allowed_role_names or []
        self.allowed_role_ids = allowed_role_ids or []
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        # Check by role names
        if self.allowed_role_names and current_user.role.name not in self.allowed_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {self.allowed_role_names}. Your role: {current_user.role.name}"
            )
        
        # Check by role IDs
        if self.allowed_role_ids and current_user.role_id not in self.allowed_role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role IDs: {self.allowed_role_ids}. Your role ID: {current_user.role_id}"
            )
        
        return current_user
    


# Helper function to create role checker by names
def require_roles_by_name(role_names: List[str]):
    return DynamicRoleChecker(allowed_role_names=role_names)



# Helper function to create role checker by IDs
def require_roles_by_id(role_ids: List[int]):
    return DynamicRoleChecker(allowed_role_ids=role_ids)



# Resource ownership checker
async def require_resource_ownership_or_role(
    resource_user_id: int,
    allowed_role_names: List[str],
    current_user: User = Depends(get_current_user)
):
    """Check if user owns the resource or has specific role"""
    if current_user.id == resource_user_id or current_user.role.name in allowed_role_names:
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. You can only access your own resources or need specific role."
    )






def has_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission based on their role"""
    if not user.role:
        return False
    user_role_name = user.role.name.lower()  # Case insensitive
    print("userrole----",user_role_name)
    user_permissions = ROLE_PERMISSIONS.get(user_role_name, [])
    return permission in user_permissions

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: {permission}. Your role: {current_user.role.name}"
            )
        return current_user
    return permission_checker

def get_user_permissions(user: User) -> List[str]:
    """Get all permissions for a user based on their role"""
    if not user.role:
        return []
    user_role_name = user.role.name.lower()
    return ROLE_PERMISSIONS.get(user_role_name, [])