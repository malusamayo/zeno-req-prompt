from enum import Enum
from typing import Optional

from pandas import Series
from pydantic import BaseModel


def to_camel(string):
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ZenoColumnType(str, Enum):
    METADATA = "METADATA"
    PREDISTILL = "PREDISTILL"
    OUTPUT = "OUTPUT"
    EMBEDDING = "EMBEDDING"
    POSTDISTILL = "POSTDISTILL"


class MetadataType(str, Enum):
    NOMINAL = "NOMINAL"
    CONTINUOUS = "CONTINUOUS"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    OTHER = "OTHER"


class ZenoColumn(CamelModel):
    column_type: ZenoColumnType
    name: str
    metadata_type: Optional[MetadataType] = MetadataType.OTHER
    model: Optional[str] = ""
    prompt_id: Optional[str] = ""

    # Append the column type to the name unless it is a vanilla metadata column.
    # We don't save the metadata_type since we dynamically change it
    # and it's not identifying.
    def __str__(self):
        m = ""
        if self.model is not None:
            m = self.model
        p = ""
        if self.prompt_id is not None and self.prompt_id != "":
            p = "_" + self.prompt_id
        t = ""
        if self.column_type is not ZenoColumnType.METADATA:
            t = self.column_type
        return t + self.name + m + p

    def __hash__(self):
        return hash(str(self))


class DataProcessingReturn(BaseModel):
    """Return type for data processing functions."""

    column: ZenoColumn
    output: Series

    class Config:
        arbitrary_types_allowed = True
