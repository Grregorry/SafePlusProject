from pydantic import BaseModel, ConfigDict


class QuestionResponse(BaseModel):
    id: int
    question_number: str
    employee_text: str
    manager_text: str
    is_compulsory: bool
    is_situation_dependent: bool

    model_config = ConfigDict(from_attributes=True)


class DomainQuestionsResponse(BaseModel):
    id: int
    name: str
    display_order: int
    questions: list[QuestionResponse]

    model_config = ConfigDict(from_attributes=True)