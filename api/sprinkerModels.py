from typing import Union
from pydantic import BaseModel

class Valve(BaseModel):
    name: Union[str, None] = None
    description: Union[str, None] = None

class ZoneName(BaseModel):
    name: Union[str, None] = None
    description: Union[str,None] = None

class GpioOperate(BaseModel):
    gpio: Union[int,None] = None
    status: Union[int,None] = None
    