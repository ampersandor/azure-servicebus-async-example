class BatchServiceError(Exception):
    """Base exception for batch service"""
    pass

class BatchJobError(BatchServiceError):
    """Error during batch job creation/execution"""
    pass

class BatchTaskError(BatchServiceError):
    """Error during batch task creation/execution"""
    pass

class TaskExecutionError(BatchServiceError):
    """Error during task execution"""
    pass

class ResultNotFoundError(BatchServiceError):
    """Result not found in database"""
    pass 