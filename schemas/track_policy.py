from pydantic import BaseModel

class TrackPolicyModel(BaseModel):
    user_id: int 
    policy_id: str