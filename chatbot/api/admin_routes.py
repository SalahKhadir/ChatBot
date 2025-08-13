from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List
import os
from sqlalchemy import func

from database import get_db
from models import User
import schemas
import models
from dependencies import get_current_admin, get_current_user
import crud
import auth

router = APIRouter()

# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/admin/users", response_model=List[schemas.UserManagement])
async def get_all_users_admin(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users with statistics (Admin only)"""
    try:
        users = crud.get_all_users(db, skip=skip, limit=limit)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/stats")
async def get_platform_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get platform statistics (Admin only)"""
    try:
        stats = crud.get_platform_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user role (Admin only)"""
    try:
        new_role = role_data.get("role")
        if not new_role or new_role not in ["user", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # Prevent admin from demoting themselves
        if current_admin.id == user_id and new_role != "admin":
            raise HTTPException(
                status_code=400,
                detail="Cannot demote yourself from admin role"
            )
        
        updated_user = crud.update_user_role(db, user_id, new_role)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": f"User role updated to {new_role}", "user": updated_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SECURE FOLDER MANAGEMENT
# ============================================================================

@router.get("/admin/secure-folders")
async def get_secure_folders(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get secure folders and their contents (Admin only)"""
    try:
        SECURE_FOLDER_PATH = os.getenv("SECURE_CV_FOLDER_PATH", "C:/secure/cvs")
        
        # Create directory if it doesn't exist
        if not os.path.exists(SECURE_FOLDER_PATH):
            os.makedirs(SECURE_FOLDER_PATH, exist_ok=True)
        
        # Get all PDF files in the folder
        files = []
        for filename in os.listdir(SECURE_FOLDER_PATH):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(SECURE_FOLDER_PATH, filename)
                file_stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": file_stat.st_size,
                    "uploaded_at": file_stat.st_mtime
                })
        
        # Return folder structure
        return [{
            "name": "CVs",
            "path": SECURE_FOLDER_PATH,
            "files": files
        }]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get secure folders: {str(e)}")

@router.post("/admin/secure-folders/upload")
async def upload_to_secure_folder(
    files: List[UploadFile] = File(...),
    folder_name: str = Form("CVs"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload files to secure folder (Admin only)"""
    try:
        SECURE_FOLDER_PATH = os.getenv("SECURE_CV_FOLDER_PATH", "C:/secure/cvs")
        
        # Create directory if it doesn't exist
        if not os.path.exists(SECURE_FOLDER_PATH):
            os.makedirs(SECURE_FOLDER_PATH, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            # Validate file type (PDF only)
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Only PDF files are allowed. {file.filename} is not a PDF."
                )
            
            # Save file to secure folder
            file_path = os.path.join(SECURE_FOLDER_PATH, file.filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} already exists in the secure folder"
                )
            
            # Write file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "size": len(content),
                "path": file_path
            })
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
            "files": uploaded_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload files: {str(e)}")

@router.get("/admin/secure-folders/permissions")
async def get_secure_folder_permissions(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all user permissions for secure folder access (Admin only)"""
    try:
        # Get all permissions with user details
        permissions = db.query(models.SecureFolderPermission).all()
        result = []
        
        for permission in permissions:
            user = db.query(User).filter(User.id == permission.user_id).first()
            if user:
                result.append({
                    "user_id": permission.user_id,
                    "has_access": permission.has_access,
                    "user_email": user.email,
                    "user_name": user.full_name,
                    "granted_at": permission.created_at
                })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get permissions: {str(e)}")

@router.put("/admin/secure-folders/permissions")
async def update_secure_folder_permissions(
    request_data: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user permissions for secure folder access (Admin only)"""
    try:
        user_id = request_data.get("user_id")
        has_access = request_data.get("has_access")
        
        if user_id is None or has_access is None:
            raise HTTPException(status_code=400, detail="user_id and has_access are required")
        
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if permission record exists
        permission = db.query(models.SecureFolderPermission).filter(
            models.SecureFolderPermission.user_id == user_id
        ).first()
        
        if permission:
            # Update existing permission
            permission.has_access = has_access
            permission.granted_by = current_admin.id
            permission.updated_at = func.now()
        else:
            # Create new permission record
            permission = models.SecureFolderPermission(
                user_id=user_id,
                has_access=has_access,
                granted_by=current_admin.id
            )
            db.add(permission)
        
        db.commit()
        db.refresh(permission)
        
        action = "granted" if has_access else "revoked"
        return {
            "message": f"Access {action} for user {user.email}",
            "user_id": user_id,
            "has_access": has_access
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update permissions: {str(e)}")

@router.get("/user/secure-folder/permission")
async def check_secure_folder_permission(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if current user has permission to access secure folder"""
    try:
        # Admins have automatic access
        if current_user.role == "admin":
            return {
                "has_permission": True,
                "user_id": current_user.id,
                "user_role": current_user.role,
                "message": "Admin access granted to secure CV folder"
            }
        
        # For regular users, check permission record
        permission = db.query(models.SecureFolderPermission).filter(
            models.SecureFolderPermission.user_id == current_user.id,
            models.SecureFolderPermission.has_access == True
        ).first()
        
        return {
            "has_permission": permission is not None,
            "user_id": current_user.id,
            "user_role": current_user.role,
            "message": "Access granted to secure CV folder" if permission else "No access to secure CV folder - upload your own documents to analyze"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check permissions: {str(e)}")
