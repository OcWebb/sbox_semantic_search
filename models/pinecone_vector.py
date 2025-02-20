from pydantic import BaseModel
from datetime import datetime


class PineconeVector(BaseModel):
    id: str
    values: list[float]
    metadata: dict

    def __init__(self, id: str, values: list[float], metadata: dict):
        super().__init__(id=id, values=values, metadata=metadata)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "values": self.values,
            "metadata": self.metadata
        }