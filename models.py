from typing import Optional, List
from typing_extensions import Annotated

from pydantic import ConfigDict, BaseModel, Field, EmailStr, BaseModel, BeforeValidator


from bson import ObjectId


# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class Request(BaseModel):
    method: str
    params: Optional[dict] = None
    qhc: str

