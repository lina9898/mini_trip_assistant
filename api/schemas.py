from pydantic import BaseModel


class GenerateTripRequest(BaseModel):
    origin: str
    destination: str
    start_date: str
    days: int
    people: int
    preference: str
    pace: str
    budget_level: str


class EditTripRequest(BaseModel):
    project_filepath: str
    edit_request: str


class ExportTripRequest(BaseModel):
    project_filepath: str
    export_type: str


class RestoreTripRequest(BaseModel):
    project_filepath: str


class AdoptTripRequest(BaseModel):
    project_filepath: str


class FeedbackTripRequest(BaseModel):
    project_filepath: str
    score: int | None = None
    feedback: str = ""
