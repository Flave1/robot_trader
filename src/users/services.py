from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.users.models import User, UserCreate, UserUpdate, UserResponse, TraderAccountCreate
from src.users.trader_account_service import TraderAccountService
from passlib.context import CryptContext
from typing import Dict, Any, List

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the sections and their required fields from ARBIX_Business_Plan.md
# This dictionary will be used for both sectionalized profile and completion percentage calculation
USER_PROFILE_SECTIONS = {
    "Personal Identification Information (KYC)": [
        "full_legal_name", "date_of_birth", "nationality", "phone_number"
    ],
    "Residential Information": [
        "residential_address", "proof_of_address_url"
    ],
    "Identity Verification Documents": [
        "government_id_url"
    ],
    "Financial Information": [
        "employment_status", "occupation", "annual_income",
        "source_of_funds", "net_worth", "bank_account_details"
    ],
    "Trading Experience and Knowledge (Suitability Assessment)": [
        "trading_experience", "knowledge_assessment_score", "risk_tolerance"
    ],
    "Account and Security Information": [
        "account_type", "trading_currency", "tax_identification_number"
    ],
    "Regulatory Disclosures and Agreements": [
        "agreed_terms", "agreed_risk_disclosure", "agreed_privacy_policy", "agreed_aml_kyc_policy"
    ]
}

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    if user.is_google_auth:
        # For Google auth, use the google_user_id as the user's ID
        db_user = User(
            id=user.google_user_id,
            email=user.email,
            password=get_password_hash("GOOGLE_AUTH_PASSWORD")  # Placeholder password for Google auth
        )
    else:
        # For regular email/password auth
        if not user.email or not user.password:
            raise ValueError("Email and password are required for non-Google authentication")
        hashed_password = get_password_hash(user.password)
        db_user = User(email=user.email, password=hashed_password)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Create default TraderAccount for the new user
    try:
        trader_account_data = TraderAccountCreate(
            user_id=db_user.id,
            account_name="Default Account",
            account_type="demo"
        )
        await TraderAccountService.create_trader_account(db, trader_account_data)
    except Exception as e:
        print(f"Warning: Failed to create trader account for user {db_user.id}: {e}")
        # Don't fail user creation if trader account creation fails
    
    return db_user

async def update_user(db: AsyncSession, user_id: str, user_update: UserUpdate):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    if db_user:
        for key, value in user_update.model_dump(exclude_unset=True).items():
            setattr(db_user, key, value)
        await db.commit()
        await db.refresh(db_user)
    return db_user

async def get_sectionalized_user_profile(db: AsyncSession, user_id: str) -> Dict[str, Dict[str, Any]]:
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    if not db_user:
        return {}

    profile = {}
    for section, fields in USER_PROFILE_SECTIONS.items():
        section_data = {}
        for field in fields:
            section_data[field] = getattr(db_user, field, None)
        profile[section] = section_data
    return profile

async def get_user_profile_completion(db: AsyncSession, user_id: str) -> float:
    print(f"DEBUG: Entering get_user_profile_completion for user_id: {user_id}")
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        print(f"DEBUG: Executed select query for user_id: {user_id}")
        db_user = result.scalars().first()
        print(f"DEBUG: Retrieved db_user: {db_user}")
    except Exception as e:
        print(f"ERROR: Exception during user retrieval in get_user_profile_completion: {e}")
        import traceback
        traceback.print_exc()
        raise # Re-raise the exception after printing

    if not db_user:
        print(f"DEBUG: User {user_id} not found, returning 0.0")
        return 0.0

    total_fields = 0
    completed_fields = 0

    print(f"DEBUG: Starting profile completion calculation for user: {user_id}")
    for section, fields in USER_PROFILE_SECTIONS.items():
        for field in fields:
            total_fields += 1
            attr_value = getattr(db_user, field, None)
            print(f"DEBUG: Checking field: {field}, value: {attr_value}, type: {type(attr_value)}")
            # Consider a field complete if it's not None, and for booleans, if it's True
            if attr_value is not None:
                if isinstance(attr_value, bool):
                    if attr_value is True:
                        completed_fields += 1
                else:
                    # For string fields, consider empty strings as incomplete
                    if isinstance(attr_value, str) and not attr_value.strip():
                        pass # Skip empty strings
                    else:
                        completed_fields += 1

    if total_fields == 0:
        print(f"DEBUG: Total fields is 0, returning 0.0")
        return 0.0
    completion_percentage = (completed_fields / total_fields) * 100
    print(f"DEBUG: Calculated completion percentage: {completion_percentage}")
    return completion_percentage 