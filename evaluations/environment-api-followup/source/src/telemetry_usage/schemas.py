from pydantic import BaseModel,StrictInt
class SumRequest(BaseModel):
 values:list[StrictInt]
