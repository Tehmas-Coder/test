def get_candidate_self_preparation_permission() -> dict:
    """
    Retrieve the permission details for a candidate to create a self preparatory exam.
    Returns:
        dict: A dictionary containing the permission details, including status, context, description, and metadata.
    """

    return {
        "is_active": True,
        "permission": {
            "name": "Candidate Self Preparatory Exam",
            "context_value": "candidates",
            "description": "Allow a candidate to create a self preparatory exam",
            "created_at": "1995-07-27T00:00:00Z",
            "created_by": None,
            "updated_at": "1995-07-27T00:00:00Z",
            "updated_by": None,
            "meta_status": "active",
        },
        "description": "",
        "created_at": "1995-07-27T00:00:00Z",
        "created_by": None,
        "updated_at": "1995-07-27T00:00:00Z",
        "updated_by": None,
        "meta_status": "active",
    }
