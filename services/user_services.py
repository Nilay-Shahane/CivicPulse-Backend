from database.supabase import supabase
from core.security import hash_password , verify_password
from schemas.user import UserSignUpModel , UserLoginModel
from postgrest.exceptions import APIError
def create_user(user:UserSignUpModel):
    try:
        data = {
            "username": user.username,
            "password": hash_password(user.password)
        }

        response = supabase.table("users").insert(data).execute()
        return response.data

    except APIError as e:
        raise Exception(e.message)
    
def user_login(user: UserLoginModel):
    try:
        response = (
            supabase
            .table("users")
            .select("*")
            .eq("username", user.username)
            .single()
            .execute()
        )

        db_user = response.data
        if db_user is None:
            raise Exception("User not found")

        if not verify_password(user.password, db_user["password"]):
            raise Exception("Invalid credentials")

        return db_user

    except APIError as e:
        raise Exception(e.message)
    