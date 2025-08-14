from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List
import os
from sqlalchemy import func

from core.database import get_db
from core.models import User
import core.schemas as schemas
import core.models as models
from core.dependencies import get_current_admin, get_current_user
import core.crud as crud
import core.auth as auth

router = APIRouter()

# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/admin/users")
async def get_all_users_admin(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users with statistics (Admin only)"""
    try:
        # Get users directly with all fields including last_login
        users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to response format with proper datetime handling
        users_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value if user.role else "user",
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "total_sessions": 0,  # Can be calculated later if needed
                "total_messages": 0   # Can be calculated later if needed
            }
            users_data.append(user_dict)
        
        return users_data
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

@router.put("/admin/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status_data: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user status (activate/suspend) (Admin only)"""
    try:
        is_active = status_data.get("is_active", True)
        
        # Prevent admin from suspending themselves
        if current_admin.id == user_id and not is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot suspend your own account"
            )
        
        updated_user = crud.update_user_status(db, user_id, is_active)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        status_text = "activated" if is_active else "suspended"
        return {"message": f"User {status_text} successfully", "user": updated_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reset user password (Admin only)"""
    try:
        new_password = password_data.get("new_password")
        if not new_password or len(new_password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters long"
            )
        
        # Hash the new password
        hashed_password = auth.get_password_hash(new_password)
        
        # Update user password
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.hashed_password = hashed_password
        db.commit()
        db.refresh(user)
        
        return {"message": "Password reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/users/search")
async def search_users(
    q: str = "",
    role: str = None,
    status: str = None,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Search and filter users (Admin only)"""
    try:
        query = db.query(User)
        
        # Search by name or email
        if q:
            query = query.filter(
                (User.full_name.ilike(f"%{q}%")) | 
                (User.email.ilike(f"%{q}%"))
            )
        
        # Filter by role
        if role and role in ["user", "admin"]:
            role_enum = models.UserRole.ADMIN if role == "admin" else models.UserRole.USER
            query = query.filter(User.role == role_enum)
        
        # Filter by status
        if status and status in ["active", "inactive"]:
            is_active = status == "active"
            query = query.filter(User.is_active == is_active)
        
        users = query.limit(limit).all()
        
        # Convert to response format
        users_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value if user.role else "user",
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }
            users_data.append(user_dict)
        
        return users_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    days: int = 30,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user activity logs (Admin only)"""
    try:
        from datetime import datetime, timedelta
        
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get user's chat sessions and messages (basic activity tracking)
        from core.models import ChatSession, Message
        
        chat_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.created_at >= start_date
        ).count()
        
        messages_sent = db.query(Message).filter(
            Message.user_id == user_id,
            Message.created_at >= start_date,
            Message.message_type == 'user'
        ).count()
        
        # Recent sessions with details
        recent_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.created_at >= start_date
        ).order_by(ChatSession.created_at.desc()).limit(10).all()
        
        session_details = []
        for session in recent_sessions:
            session_details.append({
                "session_id": session.session_id,
                "title": session.title or "Untitled Chat",
                "created_at": session.created_at.isoformat(),
                "has_document_context": session.has_document_context,
                "message_count": db.query(Message).filter(Message.session_id == session.id).count()
            })
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            },
            "period": f"Last {days} days",
            "summary": {
                "chat_sessions": chat_sessions,
                "messages_sent": messages_sent,
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "recent_sessions": session_details
        }
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
            models.SecureFolderPermission.user_id == current_user.id
        ).first()
        
        # User has permission only if record exists AND has_access is True
        has_permission = permission is not None and permission.has_access == True
        
        return {
            "has_permission": has_permission,
            "user_id": current_user.id,
            "user_role": current_user.role,
            "message": "Access granted to secure CV folder" if has_permission else "No access to secure CV folder - upload your own documents to analyze"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check permissions: {str(e)}")

@router.delete("/admin/secure-folders/delete")
async def delete_from_secure_folder(
    request_data: schemas.DeleteFileRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a file from secure folder (Admin only)"""
    try:
        filename = request_data.filename
        folder_name = request_data.folder_name  # This is just for display, all files are in the same directory
        
        if not filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Get the secure folder path from environment
        SECURE_FOLDER_PATH = os.getenv("SECURE_CV_FOLDER_PATH", "C:/secure/cvs")
        
        # Construct the file path (all files are stored directly in SECURE_FOLDER_PATH)
        file_path = os.path.join(SECURE_FOLDER_PATH, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {filename} not found in secure folder")
        
        # Delete the file
        os.remove(file_path)
        
        return {
            "message": f"File {filename} deleted successfully",
            "filename": filename,
            "folder_name": folder_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
