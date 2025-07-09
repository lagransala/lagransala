from pydantic import BaseModel


class SimpleData(BaseModel):
    value: str
