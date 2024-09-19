"""Internal classes for Zeno."""

from typing import List, Optional, Tuple, Union, Dict

from pydantic import BaseModel

from zeno.classes.base import CamelModel, ZenoColumn
from zeno.classes.slice import FilterIds, FilterPredicateGroup, Slice


class ZenoSettings(CamelModel):
    view: str
    id_column: ZenoColumn
    label_column: ZenoColumn
    data_column: ZenoColumn
    samples: int
    calculate_histogram_metrics: bool
    total_size: int


class ZenoVariables(CamelModel):
    metrics: List[str]
    models: List[str]
    folders: List[str]


class StatusResponse(CamelModel):
    status: str
    done_processing: bool
    complete_columns: List[ZenoColumn]


class MetricKey(CamelModel):
    sli: Slice
    model: str
    metric: str
    prompt_id: Optional[str] = None
    requirement_id: Optional[str] = None


class MetricRequest(CamelModel):
    metric_keys: List[MetricKey]
    tag_ids: Optional[FilterIds] = None
    filter_ids: Optional[FilterIds] = None
    tag_list: Optional[List[str]] = None

class InferenceRequest(CamelModel):
    model: str
    prompt_id: str
    filter_ids: Optional[FilterIds] = None
    requirement_id: Optional[str] = None

class FeedbackRequest(CamelModel):
    model: str
    prompt_id: str
    example_id: str
    is_positive: bool
    feedback: str = ""

class EvaluatorFeedback(CamelModel):
    model: str
    prompt_id: str
    example_id: str
    corrected_eval: bool
    requirement_id: str

class TableRequest(CamelModel):
    columns: List[ZenoColumn]
    diff_column_1: Optional[ZenoColumn] = None
    diff_column_2: Optional[ZenoColumn] = None
    slice_range: List[int]
    filter_predicates: FilterPredicateGroup
    sort: Tuple[Union[ZenoColumn, str, None], bool]
    tag_ids: FilterIds
    filter_ids: Optional[FilterIds] = None
    tag_list: List[str]


class PlotRequest(CamelModel):
    filter_predicates: FilterPredicateGroup
    tag_ids: FilterIds


class EmbedProject2DRequest(CamelModel):
    model: str
    column: ZenoColumn


class ColorsProjectRequest(CamelModel):
    column: ZenoColumn


class EntryRequest(BaseModel):
    id: Union[int, str]
    columns: List[ZenoColumn] = []


class Example(CamelModel):
    id: Union[int, str]
    input: str
    output: str
    is_positive: bool
    feedback: Optional[str] = ""

class Requirement(CamelModel):
    id: str
    name: str
    description: str
    prompt_snippet: str
    evaluation_method: str
    examples: List[Example] = []

class Prompt(CamelModel):
    text: str
    version: str
    requirements: Dict[str, Requirement]