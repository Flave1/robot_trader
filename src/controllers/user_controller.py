from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.models import UserCreate, UserResponse, UserUpdate, SectionalizedProfileResponse, ProfileCompletionResponse
from ..users import services as user_services
from ..database import get_db, Base, engine

router = APIRouter(tags=["User"])

# Dependency to get the database session
# This get_db function is now imported from src.database

@router.post("/user/create", response_model=UserResponse)
async def create_user_endpoint(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        if user.is_google_auth:
            print(f"DEBUG: Google Auth User Create Request: {user.google_user_id}")
            # For Google auth, check if user already exists by ID
            existing_user = await user_services.get_user_by_id(db, user.google_user_id)
            if existing_user:
                print(f"DEBUG: Existing Google user found: {existing_user.id}")
                return existing_user
            new_user = await user_services.create_user(db=db, user=user)
            print(f"DEBUG: New Google user created: {new_user.id}")
            return new_user
        else:
            # For regular auth, check if email is already registered
            if not user.email:
                raise HTTPException(status_code=400, detail="Email is required for non-Google authentication")
            existing_user = await user_services.get_user_by_email(db, email=user.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            new_user = await user_services.create_user(db=db, user=user)
            print(f"DEBUG: New email/password user created: {new_user.id}")
            return new_user
    except ValueError as e:
        print(f"ERROR: Value Error in create_user_endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"ERROR: Exception in create_user_endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.put("/user/update/{user_id}", response_model=UserResponse)
async def update_user_endpoint(user_id: str, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    db_user = await user_services.update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/user/profile/{user_id}", response_model=SectionalizedProfileResponse)
async def get_user_profile_endpoint(user_id: str, db: AsyncSession = Depends(get_db)):
    profile = await user_services.get_sectionalized_user_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile

@router.get("/user/profile/{user_id}/completion", response_model=ProfileCompletionResponse)
async def get_user_profile_completion_endpoint(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        print('user_id', user_id)
        # First check if user exists
        user_exists = await user_services.get_user_by_id(db, user_id)
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get completion percentage
        percentage = await user_services.get_user_profile_completion(db, user_id)
        return {"percentage_completion": percentage}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating profile completion: {str(e)}") 