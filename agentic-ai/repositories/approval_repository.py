"""
Approval Repository — Phase 14.
"""
from typing import Optional
from database.collections import get_approval_requests_collection
from models.approval_request import ApprovalRequestModel

class ApprovalRepository:
    """Repository for ApprovalRequestModel data access."""
    
    def __init__(self):
        self.collection = get_approval_requests_collection()

    def save_request(self, request: ApprovalRequestModel) -> str:
        """Create a new approval request document."""
        doc = request.model_dump()
        self.collection.insert_one(doc)
        return request.id

    def find_by_id(self, approval_id: str) -> Optional[ApprovalRequestModel]:
        """Retrieve approval request by ID."""
        doc = self.collection.find_one({"id": approval_id})
        if doc:
            return ApprovalRequestModel(**doc)
        return None

    def update_status(self, approval_id: str, status: str, approver: str, comment: Optional[str], approved_at) -> bool:
        """Update the status of an approval request."""
        update_data = {
            "status": status,
            "approver": approver,
            "approved_at": approved_at
        }
        if comment:
            update_data["comment"] = comment
            
        result = self.collection.update_one(
            {"id": approval_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
