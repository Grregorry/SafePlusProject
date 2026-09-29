from pydantic import BaseModel


class QuestionProgressResponse(BaseModel):
    question_id: int
    question_number: str
    employee_complete: bool
    manager_complete: bool
    employee_manual_entries_recorded: int
    manager_manual_entries_recorded: int
    fully_complete: bool


class AssessmentProgressResponse(BaseModel):
    assessment_id: int
    active_question_count: int
    employee_complete_count: int
    manager_complete_count: int
    fully_complete_count: int
    overall_progress_percentage: int
    expected_manual_entries_employee: int
    expected_manual_entries_manager: int
    digital_employee_complete_count: int
    digital_manager_complete_count: int
    manual_employee_complete_count: int
    manual_manager_complete_count: int
    questions: list[QuestionProgressResponse]