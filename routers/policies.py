from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from database.supabase import supabase
from postgrest.exceptions import APIError
from schemas.track_policy import TrackPolicyModel 

router = APIRouter(
    prefix='/policies',
    tags=['Policies']
)

@router.post('/track')
def track_policy(data: TrackPolicyModel):
    try:
        insert_data = {
            "user_id": data.user_id,
            "policy_id": data.policy_id
        }

        response = supabase.table("tracked_policies").insert(insert_data).execute()
        
        return {
            "status": "success", 
            "message": "Policy tracked successfully!"
        }

    except APIError as e:
        if e.code == '23505':
            return {"status": "info", "message": "You are already tracking this policy."}
        raise HTTPException(status_code=400, detail=e.message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get('/check')
def check_tracking_status(user_id: int, policy_id: str): 
    try:
        response = supabase.table("tracked_policies") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("policy_id", policy_id) \
            .execute()
        
        is_tracked = len(response.data) > 0
        
        return {"is_tracked": is_tracked}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/user-tracked/{user_id}")
def get_user_tracked_policies(user_id: int):
    response = supabase.table("tracked_policies").select("policy_id").eq("user_id", user_id).execute()
    return response.data

@router.get("/history/{policy_id}")
def get_policy_history(policy_id: str):
    response = supabase.table("policy_sentiment_history") \
        .select("*") \
        .eq("policy_id", policy_id) \
        .order("created_at", desc=False) \
        .execute()
    return response.data