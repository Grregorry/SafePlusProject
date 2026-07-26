from pydantic import BaseModel


class QuestionProgressResponse(BaseModel):
    question_id: int
    question_number: str
    employee_complete: bool
    manager_complete: bool
    fully_complete: bool


class AssessmentProgressResponse(BaseModel):
    assessment_id: int
    active_question_count: int
    employee_complete_count: int
    manager_complete_count: int
    fully_complete_count: int
    overall_progress_percentage: int
    questions: list[QuestionProgressResponse]