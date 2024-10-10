"""Primary backend for Zeno. Handles all data processing and caching."""

import asyncio
import glob
import logging
import os
import pickle
import sys
import json
import re
import threading
import copy
from inspect import getsource
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union, Tuple
from pydantic import BaseModel
from openai import OpenAI
import random

import pandas as pd
from pandas import DataFrame
from pathos.multiprocessing import ProcessingPool as Pool

from zeno.api import (
    DistillReturn,
    MetricReturn,
    ModelReturn,
    ZenoOptions,
    ZenoParameters,
)
from zeno.classes.base import DataProcessingReturn, MetadataType, ZenoColumnType
from zeno.openai_client import OpenAIMultiClient
from zeno.classes.classes import MetricKey, PlotRequest, InferenceRequest, FeedbackRequest, TableRequest, ZenoColumn, Prompt, Requirement, Example, EvaluatorFeedback, SuggestNewReqRequest
from zeno.classes.report import Report
from zeno.classes.slice import FilterIds, FilterPredicateGroup, GroupMetric, Slice
from zeno.classes.tag import Tag, TagMetricKey
from zeno.processing.data_processing import (
    postdistill_data,
    predistill_data,
    run_inference,
)
from zeno.processing.filtering import filter_table
from zeno.util import (
    generate_diff_cols,
    get_metadata_type,
    load_series,
    read_functions,
    read_metadata,
    read_pickle,
    requirements_to_str,
)
from zeno.prompt_templates import (
    REQUIREMENT_CREATOR_PROMPT, 
    REQUIREMENT_OPTIMIZER_PROMPT, 
    PROMPT_COMPILER_PROMPT, 
    REQUIREMENT_EXTRACTOR_PROMPT, 
    REQUIREMENT_EVALUATION_PROMPT,
    REQUIREMENT_SUGGESTION_PROMPT,
    REQUIREMENT_UPDATE_PROMPT,
    REQUIREMENT_UPDATE_REQUEST_PROMPT
)


class ZenoBackend(object):
    def __init__(self, args: ZenoParameters):
        logging.basicConfig(level=logging.INFO)
        self.params = args
        self.initial_setup()

    def initial_setup(self) -> None:
        self.metadata = self.params.metadata
        self.functions = self.params.functions
        self.batch_size = self.params.batch_size
        self.data_path = self.params.data_path
        self.label_path = self.params.label_path
        self.cache_path = self.params.cache_path
        self.multiprocessing = self.params.multiprocessing
        self.editable = self.params.editable
        self.samples = self.params.samples
        self.view = self.params.view
        self.calculate_histogram_metrics = self.params.calculate_histogram_metrics
        self.model_names = self.params.models

        self.df = read_metadata(self.metadata)
        self.tests = read_functions(self.functions)

        self.data_prefix = ""
        if self.data_path.startswith("http"):
            self.data_prefix = self.data_path
        elif self.data_path != "":
            self.data_prefix = "/data/"
        self.done_running_inference = False

        self.predistill_functions: Dict[
            str, Callable[[DataFrame, ZenoOptions], DistillReturn]
        ] = {}
        self.postdistill_functions: Dict[
            str, Callable[[DataFrame, ZenoOptions], DistillReturn]
        ] = {}
        self.metric_functions: Dict[
            str, Callable[[DataFrame, ZenoOptions], MetricReturn]
        ] = {}
        self.predict_function: Optional[
            Callable[[str], Callable[[DataFrame, ZenoOptions], ModelReturn]]
        ] = None
        self.gradio_input_columns: List[str] = []

        self.status: str = "Initializing"
        self.folders: List[str] = read_pickle("folders.pickle", self.cache_path, [])
        self.reports: List[Report] = read_pickle("reports.pickle", self.cache_path, [])
        self.slices: Dict[str, Slice] = read_pickle(
            "slices.pickle", self.cache_path, {}
        )
        self.tags: Dict[str, Tag] = read_pickle("tags.pickle", self.cache_path, {})
        self.prompts: Dict[str, Prompt] = read_pickle(
            "prompts.pickle", self.cache_path, self.params.prompts
        )
        self.current_prompt_id = list(self.prompts.keys())[-1]

        # for pid, prompt in self.prompts.items():
        #     if len(prompt.requirements) == 0:
        #         self.extract_requirements(pid)
        
        if "All Instances" not in self.slices:
            orig_slices = self.slices
            all_instance = Slice(
                slice_name="All Instances",
                folder="",
                filter_predicates=FilterPredicateGroup(predicates=[], join=""),
            )
            self.slices = {"All Instances": all_instance}
            self.slices.update(orig_slices)

        self.__setup_dataframe(
            self.params.id_column, self.params.data_column, self.params.label_column
        )
        self.__parse_test_functions(self.tests)


        def calculate_pass_rate(df: DataFrame, ops: ZenoOptions) -> MetricReturn:
            """Calculate pass rate for a requirement."""
            pass_rate = df[ops.output_column].mean()
            return MetricReturn(metric=pass_rate)

        self.metric_functions["pass-rate"] = calculate_pass_rate

        # Options passed to Zeno functions.
        self.zeno_options = ZenoOptions(
            id_column=str(self.id_column),
            data_column=str(self.data_column),
            label_column=str(self.label_column),
            distill_columns=dict(),
            data_path=self.data_path,
            label_path=self.label_path,
            output_column="",
            output_path="",
        )

    def __setup_dataframe(self, id_column: str, data_column: str, label_column: str):
        if data_column != "":
            if data_column != id_column:
                self.data_column = ZenoColumn(
                    column_type=ZenoColumnType.METADATA,
                    metadata_type=get_metadata_type(self.df[data_column]),
                    name=data_column,
                )
            else:  # make sure id and data column are different
                self.df["data"] = self.df[data_column]
                self.data_column = ZenoColumn(
                    column_type=ZenoColumnType.METADATA,
                    metadata_type=get_metadata_type(self.df["data"]),
                    name="data",
                )
        else:
            self.data_column = ZenoColumn(
                column_type=ZenoColumnType.METADATA,
                metadata_type=MetadataType.OTHER,
                name="",
            )

        if label_column != "":
            self.label_column = ZenoColumn(
                column_type=ZenoColumnType.METADATA,
                metadata_type=get_metadata_type(self.df[label_column]),
                name=label_column,
            )
        else:
            self.label_column = ZenoColumn(
                column_type=ZenoColumnType.METADATA,
                metadata_type=MetadataType.OTHER,
                name="",
            )

        if id_column != "":
            self.id_column = ZenoColumn(
                column_type=ZenoColumnType.METADATA,
                metadata_type=MetadataType.OTHER,
                name=id_column,
            )
            self.df[str(self.id_column)].astype(str)
        else:
            self.df = self.df.reset_index()
            self.id_column = ZenoColumn(
                column_type=ZenoColumnType.METADATA,
                metadata_type=MetadataType.OTHER,
                name="index",
            )

        self.columns: List[ZenoColumn] = []
        self.complete_columns: List[ZenoColumn] = []

        self.df = self.df.set_index(str(self.id_column), drop=False)
        # Set index name to None to prevent name overlaps w/ columns.
        self.df.index.name = None
        for metadata_col in self.df.columns:
            col = ZenoColumn(
                column_type=ZenoColumnType.METADATA,
                metadata_type=get_metadata_type(self.df[metadata_col]),
                name=str(metadata_col),
            )
            self.columns.append(col)
            self.complete_columns.append(col)

    def __parse_test_functions(self, tests: List[Callable]):
        for test_fn in tests:
            if hasattr(test_fn, "predict_function"):
                if self.predict_function is None:
                    self.predict_function = test_fn
                else:
                    print("ERROR: Multiple model functions found, can only have one")
                    sys.exit(1)
            if hasattr(test_fn, "distill_function"):
                src = getsource(test_fn)
                if "output_column" in src:
                    self.postdistill_functions[test_fn.__name__] = test_fn
                else:
                    self.predistill_functions[test_fn.__name__] = test_fn
            if hasattr(test_fn, "metric_function"):
                self.metric_functions[test_fn.__name__] = test_fn

    def start_processing(self):
        """Parse testing files, distill, and run inference."""

        if not self.tests:
            self.done_running_inference = True
            self.status = "Done processing"
            return

        for fn in self.predistill_functions.values():
            self.columns.append(
                ZenoColumn(column_type=ZenoColumnType.PREDISTILL, name=fn.__name__)
            )
        for fn in self.postdistill_functions.values():
            for m in self.model_names:
                self.columns.append(
                    ZenoColumn(
                        column_type=ZenoColumnType.POSTDISTILL,
                        name=fn.__name__,
                        model=m,
                    )
                )

        self.__thread = threading.Thread(
            target=asyncio.run, args=(self.__process(),), daemon=True
        )
        self.__thread.start()

    async def __process(self):
        self.status = "Running predistill functions"
        print(self.status)
        self.__predistill()

        self.status = "Running inference"
        print(self.status)
        self.__inference(run_additional_inference=False)
        self.done_running_inference = True

        self.status = "Running evaluators"
        print(self.status)
        self.__run_evaluation(run_additional_inference=False)

        self.status = "Running postdistill functions"
        print(self.status)
        self.__postdistill()

        self.status = "Done processing"
        print(self.status)

    def __set_data_processing_returns(self, rets: List[List[DataProcessingReturn]]):
        """Update DataFrame with new columns from processing functions.

        Args:
            rets (List[List[DataProcessingReturn]]): List of returns from decorated
            functions.
        """
        for ret in rets:
            for out in ret:
                c_hash = str(out.column)
                self.df.loc[:, c_hash] = out.output
                self.df[c_hash] = self.df[c_hash].convert_dtypes()
                out.column.metadata_type = get_metadata_type(self.df[c_hash])
                if out.column not in self.complete_columns:
                    self.complete_columns.append(out.column)

    def __predistill(self) -> None:
        """Run distilling functions not dependent on model outputs."""

        # Check if we need to preprocess since Pool is expensive
        predistill_to_run: List[ZenoColumn] = []
        for predistill_column in [
            c for c in self.columns if c.column_type == ZenoColumnType.PREDISTILL
        ]:
            save_path = Path(self.cache_path, str(predistill_column) + ".pickle")

            load_series(self.df, predistill_column, save_path)

            predistill_hash = str(predistill_column)
            if self.df[predistill_hash].isna().any():
                predistill_to_run.append(predistill_column)
            else:
                self.df[predistill_hash] = self.df[predistill_hash].convert_dtypes()
                predistill_column.metadata_type = get_metadata_type(
                    self.df[predistill_hash]
                )
                self.complete_columns.append(predistill_column)

        if len(predistill_to_run) > 0:
            if self.multiprocessing:
                with Pool() as pool:
                    predistill_outputs = pool.map(
                        predistill_data,
                        [
                            self.predistill_functions[col.name]
                            for col in predistill_to_run
                        ],
                        [col for col in predistill_to_run],
                        [self.zeno_options] * len(predistill_to_run),
                        [self.cache_path] * len(predistill_to_run),
                        [self.df] * len(predistill_to_run),
                        [self.batch_size] * len(predistill_to_run),
                        range(len(predistill_to_run)),
                    )
                    self.__set_data_processing_returns(predistill_outputs)
            else:
                predistill_outputs = []
                for i, predistill in enumerate(predistill_to_run):
                    predistill_outputs.append(
                        predistill_data(
                            self.predistill_functions[predistill.name],
                            predistill,
                            self.zeno_options,
                            self.cache_path,
                            self.df,
                            self.batch_size,
                            i,
                        )
                    )
                self.__set_data_processing_returns(predistill_outputs)

    def __inference(self, requests: List[InferenceRequest] =[], run_additional_inference=True) -> None:
        """Run models on instances."""

        # Check if we need to run inference since Pool is expensive
        models_to_run = []
        if len(requests) == 0:
            requests = [InferenceRequest(model=model_name, prompt_id=prompt_id) for prompt_id in self.prompts.keys() for model_name in self.model_names]
        for req in requests:
            (model_name, prompt_id, tag_ids) = (req.model, req.prompt_id, req.filter_ids)
            model_column = ZenoColumn(
                column_type=ZenoColumnType.OUTPUT, name="output", model=model_name, prompt_id=prompt_id
            )
            embedding_column = ZenoColumn(
                column_type=ZenoColumnType.EMBEDDING, name="embedding", model=model_name, prompt_id=prompt_id
            )
            model_hash = str(model_column)
            embedding_hash = str(embedding_column)

            model_save_path = Path(self.cache_path, model_hash + ".pickle")
            embedding_save_path = Path(self.cache_path, embedding_hash + ".pickle")

            load_series(self.df, model_column, model_save_path)
            load_series(self.df, embedding_column, embedding_save_path)

            if self.df[model_hash].isna().any() and run_additional_inference:
                models_to_run.append(req)
            elif not self.df[model_hash].isna().all():
                self.df[model_hash] = self.df[model_hash].convert_dtypes()
                model_column.metadata_type = get_metadata_type(self.df[model_hash])
                if model_hash not in [str(col) for col in self.complete_columns]:
                    self.complete_columns.append(model_column)

                # Check if there were saved postdistill columns:
                for f in glob.glob(
                    os.path.join(
                        self.cache_path, "POSTDISTILL*" + model_name + ".pickle"
                    )
                ):
                    name = os.path.basename(f).split(model_name)[0][11:]
                    col = ZenoColumn(
                        column_type=ZenoColumnType.POSTDISTILL,
                        name=name,
                        model=model_name,
                    )
                    series = pd.read_pickle(f)
                    self.df.loc[:, str(col)] = series
                    self.df[str(col)] = self.df[str(col)].convert_dtypes()
                    col.metadata_type = get_metadata_type(self.df[str(col)])
                    if col not in self.complete_columns:
                        self.complete_columns.append(col)
        
        if len(models_to_run) > 0 and self.predict_function is not None:
            if self.multiprocessing:
                with Pool() as pool:
                    inference_outputs = pool.map(
                        run_inference,
                        [self.predict_function] * len(models_to_run),
                        [self.zeno_options] * len(models_to_run),
                        [mp[0] for mp in models_to_run],
                        [self.prompts[mp[1]] for mp in models_to_run],
                        [self.cache_path] * len(models_to_run),
                        [self.df] * len(models_to_run),
                        [self.batch_size] * len(models_to_run),
                        range(len(models_to_run)),
                    )
            else:
                inference_outputs = []
                for i, req in enumerate(models_to_run):
                    (model_name, prompt_id, tag_ids) = (req.model, req.prompt_id, req.filter_ids)
                    inference_outputs.append(
                        run_inference(
                            self.predict_function,
                            self.zeno_options,
                            model_name,
                            self.prompts[prompt_id],
                            self.cache_path,
                            self.df,
                            self.batch_size,
                            i,
                            tag_ids,
                        )
                    )
            self.__set_data_processing_returns(inference_outputs)

    def __postdistill(self) -> None:
        """Run distill functions dependent on model outputs."""

        # Check if we need to run postprocessing since Pool is expensive
        postdistill_to_run: List[ZenoColumn] = []
        for postdistill_column in [
            c for c in self.columns if c.column_type == ZenoColumnType.POSTDISTILL
        ]:
            col_name = postdistill_column.copy(
                update={
                    "model": postdistill_column.model,
                }
            )
            col_hash = str(col_name)

            # If we already loaded in inference, skip.
            if col_hash in self.df.columns:
                continue

            save_path = Path(self.cache_path, col_hash + ".pickle")

            load_series(self.df, col_name, save_path)

            if self.df[col_hash].isna().any():
                postdistill_to_run.append(col_name)
            else:
                self.df[col_hash] = self.df[col_hash].convert_dtypes()
                col_name.metadata_type = get_metadata_type(self.df[col_hash])
                self.complete_columns.append(col_name)

        if len(postdistill_to_run) > 0:
            if self.multiprocessing:
                with Pool() as pool:
                    post_outputs = pool.map(
                        postdistill_data,
                        [
                            self.postdistill_functions[e.name]
                            for e in postdistill_to_run
                        ],
                        [e.model for e in postdistill_to_run],
                        [self.zeno_options] * len(postdistill_to_run),
                        [self.cache_path] * len(postdistill_to_run),
                        [self.df] * len(postdistill_to_run),
                        [self.batch_size] * len(postdistill_to_run),
                        range(len(postdistill_to_run)),
                    )
            else:
                post_outputs = []
                for i, postdistill in enumerate(postdistill_to_run):
                    post_outputs.append(
                        postdistill_data(
                            self.postdistill_functions[postdistill.name],
                            postdistill.model if postdistill.model else "",
                            self.zeno_options,
                            self.cache_path,
                            self.df,
                            self.batch_size,
                            i,
                        )
                    )
            self.__set_data_processing_returns(post_outputs)

    
    def __run_evaluation(self, requests: List[InferenceRequest]=[], run_additional_inference=True) -> None:
        
        evaluations_to_run = []
        if len(requests) == 0:
            requests = [
                InferenceRequest(model=model_name, prompt_id=prompt_id, filter_ids=None, requirement_id=requirement_id)
                for model_name in self.model_names
                for prompt_id in self.prompts.keys() 
                for requirement_id in self.prompts[prompt_id].requirements.keys()
            ]
        
        for req in requests:
            (model_name, prompt_id, requirement_id, tag_ids) = (req.model, req.prompt_id, req.requirement_id, req.filter_ids)

            # print(f"Running evaluation for model {model_name} on prompt {prompt_id} and requirement {requirement_id}")
            
            score_col = ZenoColumn(
                column_type=ZenoColumnType.POSTDISTILL, name=f"evalR{requirement_id}", model=model_name, prompt_id=prompt_id
            )
            rationale_col = ZenoColumn(
                column_type=ZenoColumnType.POSTDISTILL, name=f"evalR{requirement_id}Rationale", model=model_name, prompt_id=prompt_id
            )
            score_hash = str(score_col)
            rationale_hash = str(rationale_col)

            load_series(self.df, score_col, Path(self.cache_path, score_hash + ".pickle"))
            load_series(self.df, rationale_col, Path(self.cache_path, rationale_hash + ".pickle"))

            if (self.df[score_hash].isna().any() or self.df[rationale_hash].isna().any()) and run_additional_inference:
                evaluations_to_run.append(req)
            elif not self.df[score_hash].isna().all():
                self.df[score_hash] = self.df[score_hash].convert_dtypes()
                score_col.metadata_type = get_metadata_type(self.df[score_hash])
                if score_col not in self.complete_columns:
                    self.complete_columns.append(score_col)
                
                self.df[rationale_hash] = self.df[rationale_hash].convert_dtypes()
                rationale_col.metadata_type = get_metadata_type(self.df[rationale_hash])
                if rationale_col not in self.complete_columns:
                    self.complete_columns.append(rationale_col)

        if len(evaluations_to_run) > 0:
            inference_outputs = []
            for i, req in enumerate(evaluations_to_run):
                (model_name, prompt_id, requirement_id, tag_ids) = (req.model, req.prompt_id, req.requirement_id, req.filter_ids)

                inference_outputs.append(
                    self.evaluate_requirement(model_name, prompt_id, requirement_id, tag_ids)
                )

            self.__set_data_processing_returns(inference_outputs)

    def get_metrics_for_slices(
        self,
        requests: List[MetricKey],
        filter_ids: Optional[FilterIds] = None,
    ) -> List[GroupMetric]:
        """Calculate result for each requested combination."""

        return_metrics: List[GroupMetric] = []
        for metric_key in requests:
            # If we refresh, might not have columns for a slice.
            try:
                filt_df = filter_table(
                    self.df, metric_key.sli.filter_predicates, filter_ids
                )
            except pd.errors.UndefinedVariableError:
                return_metrics.append(GroupMetric(metric=None, size=0))
                continue

            if metric_key.metric == "" or self.label_column.name == "":
                return_metrics.append(GroupMetric(metric=None, size=filt_df.shape[0]))
            else:
                metric = self.calculate_metric(
                    filt_df, metric_key.model, metric_key.metric, metric_key.prompt_id, metric_key.requirement_id
                )
                return_metrics.append(GroupMetric(metric=metric, size=filt_df.shape[0]))
        return return_metrics

    def get_metrics_for_slices_and_tags(
        self,
        requests: List[MetricKey],
        tag_ids: Optional[FilterIds] = None,
        filter_ids: Optional[FilterIds] = None,
        tag_list: Optional[List[str]] = None,
    ) -> List[GroupMetric]:
        """Calculate result for each requested combination."""
        return_metrics: List[GroupMetric] = []
        for metric_key in requests:
            filt_df = filter_table(
                self.df, metric_key.sli.filter_predicates, tag_ids, filter_ids, tag_list
            )
            if metric_key.metric == "" or self.label_column.name == "":
                return_metrics.append(GroupMetric(metric=None, size=filt_df.shape[0]))
            else:
                metric = self.calculate_metric(
                    filt_df, metric_key.model, metric_key.metric
                )
                return_metrics.append(GroupMetric(metric=metric, size=filt_df.shape[0]))
        return return_metrics

    def get_metrics_for_tags(self, requests: List[TagMetricKey]) -> List[GroupMetric]:
        return_metrics: List[GroupMetric] = []
        for tag_metric_key in requests:
            filt_df = filter_table(self.df, None, tag_metric_key.tag.selection_ids)
            if tag_metric_key.metric == "" or self.label_column.name == "":
                return_metrics.append(GroupMetric(metric=None, size=filt_df.shape[0]))
            else:
                # if the tag is empty
                if len(tag_metric_key.tag.selection_ids.ids) == 0:
                    filt_df = self.df.iloc[0:0]
                metric = self.calculate_metric(
                    filt_df, tag_metric_key.model, tag_metric_key.metric
                )
                return_metrics.append(GroupMetric(metric=metric, size=filt_df.shape[0]))
        return return_metrics

    def calculate_metric(
        self, df: DataFrame, model: Union[str, None], metric: str, prompt_id: Optional[str] = None, requirement_id: Optional[str] = None
    ) -> Union[float, None]:
        if not self.done_running_inference:
            return None
        
        if prompt_id is None or requirement_id is None:
            return None

        if model is not None:
            # print(f"Calculating metric {metric} for model {model} on prompt {prompt_id} and requirement {requirement_id}")

            score_col = ZenoColumn(
                column_type=ZenoColumnType.POSTDISTILL, name=f"evalR{requirement_id}", model=model, prompt_id=prompt_id
            )
            score_hash = str(score_col)

            if score_hash not in self.df.columns:
                return None

            distill_fns = [
                c
                for c in self.columns
                if (
                    c.column_type == ZenoColumnType.PREDISTILL
                    or c.column_type == ZenoColumnType.POSTDISTILL
                )
                and c.model == model
            ]

            local_ops = self.zeno_options.copy(
                update={
                    "output_column": score_hash,
                    "output_path": os.path.join(self.cache_path, score_hash + ".pickle"),
                    "distill_columns": dict(
                        zip(
                            [c.name for c in distill_fns], [str(c) for c in distill_fns]
                        )
                    ),
                }
            )
        else:
            distill_fns = [
                c
                for c in self.columns
                if (
                    c.column_type == ZenoColumnType.PREDISTILL
                    or c.column_type == ZenoColumnType.POSTDISTILL
                )
            ]

            local_ops = self.zeno_options.copy(
                update={
                    "distill_columns": dict(
                        zip(
                            [c.name for c in distill_fns], [str(c) for c in distill_fns]
                        )
                    ),
                }
            )

        return self.metric_functions[metric](df, local_ops).metric

    def set_folders(self, folders: List[str]):
        if not self.editable:
            return
        self.folders = folders
        with open(os.path.join(self.cache_path, "folders.pickle"), "wb") as f:
            pickle.dump(self.folders, f)

    def get_new_prompt_version(self,):
        prompt_versions = list(self.prompts.keys())
        prompt_versions = [int(x[1:]) for x in prompt_versions]
        return 'v' + str(max(prompt_versions) + 1)

    def create_new_prompt(self, req: Prompt):
        if not self.editable:
            return
        new_version = self.get_new_prompt_version()
        req.version = new_version
        self.prompts[new_version] = req
        self.current_prompt_id = new_version
        update_req = True
        if req.text == "":
            self.compile_prompt(new_version)
            update_req = False
        else:
            self.extract_requirements(new_version)
            update_req = False
        if update_req:
            current_requirements = req.requirements
            for rid in current_requirements:
                r = current_requirements[rid]
                if r.implementationUpdateFlag:
                    res = self.update_req(r)
                    current_requirements[rid] = res
                    r.implementationUpdateFlag = False

        self.add_tags_to_prompt(new_version)
        with open(os.path.join(self.cache_path, "prompts.pickle"), "wb") as f:
            pickle.dump(self.prompts, f)
        return self.prompts[new_version]

    def run_prompt(self, req: InferenceRequest):
        self.__inference([req])
        requests_with_requirement = []
        for requirement_id in self.prompts[req.prompt_id].requirements.keys():
            innerdict = req.dict()
            innerdict.update({"requirement_id": requirement_id})
            requests_with_requirement.append(InferenceRequest(**innerdict))
        self.__run_evaluation(requests_with_requirement)
    
    def find_best_match(self, prompt, snippet):
        normalized_snippet = " ".join(snippet.split())
        prompt_length = len(prompt)
        snippet_length = len(normalized_snippet)
        best_match = ""
        highest_ratio = 0.0
        start_index = -1
        end_index = -1

        # Use a sliding window approach to find the best match
        for i in range(prompt_length - snippet_length + 1):
            substring = prompt[i:i + snippet_length]
            normalized_substring = " ".join(substring.split())
            ratio = SequenceMatcher(None, normalized_snippet, normalized_substring).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = substring
                start_index = i
                end_index = i + snippet_length

        return best_match, start_index, end_index

    def add_tags_to_prompt(self, prompt_id):
        prompt = self.prompts[prompt_id].text
        for _, req in self.prompts[prompt_id].requirements.items():
            best_match, start_index, end_index = self.find_best_match(prompt, req.prompt_snippet.strip())
            wrapped_snippet = f'<req name="{req.name}" id="{req.id}">{best_match}</req>'
            prompt = prompt[:start_index] + wrapped_snippet + prompt[end_index:]
        self.prompts[prompt_id].text = f"<prompt>{prompt}</prompt>"

    def extract_requirements(self, prompt_id):
        '''Use LLM to extract requirements for prompt_id

        Input: self.prompts[prompt_id].text
        Output: 
        - self.prompts[prompt_id].requirements, extracted from the prompt
        - self.prompts[prompt_id].text, updated with xml tags on requirements
        '''
        prompt = self.prompts[prompt_id].text
        
        api_prompt = REQUIREMENT_EXTRACTOR_PROMPT.format(prompt=prompt)

        payload = {
            'model': 'gpt-4-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant. Please return the response as valid JSON.'},
                {'role': 'user', 'content': api_prompt}  # Pass the complete prompt with instructions
            ],
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'response_format': {"type": "json_object"}  
        }

        client = OpenAIMultiClient()

        client.request(
            data=payload,
            endpoint="chat.completions"
        )
    
        for response in client:
            if response.failed:
                print("Error generating response")
                return

            output_text = response.response.choices[0].message.content

            try:
                # Parse the JSON response
                extracted_data = json.loads(output_text)
            except json.JSONDecodeError:
                print("Failed to parse the response as JSON.")
                return
            
            extracted_requirements = extracted_data.get('requirements', [])

            # Loop through each extracted requirement and add it to the list
            for idx, req in enumerate(extracted_requirements):
                prompt_snippet=req.get('prompt_snippet', '')
                requirement = Requirement(
                    id=idx,  # Generate a unique ID
                    name=req.get('name', 'Unnamed Requirement'),
                    description=req.get('description', ''),
                    prompt_snippet=req.get('prompt_snippet', ''),
                    evaluation_method=req.get('evaluation_method', '')
                )
                self.prompts[prompt_id].requirements[str(idx)] = requirement

            break

        self.prompts[prompt_id].text = prompt

    def update_req(self, req : Requirement) -> Requirement:

        api_prompt = REQUIREMENT_UPDATE_REQUEST_PROMPT.format(
            requirement_name=req.name,
            requirement_description = req.description,
            requirement_evaluation_method = req.evaluation_method,
            requirement_prompt_snippet = req.prompt_snippet
        )

        payload = {
            'model': 'gpt-4-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant. Please return the response as valid JSON.'},
                {'role': 'user', 'content': api_prompt}  # Pass the complete prompt with instructions
            ],
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'response_format': {"type": "json_object"}  
        }

        client = OpenAIMultiClient()

        client.request(
            data=payload,
            endpoint="chat.completions"
        )

        for response in client:
            if response.failed:
                print("Error generating response")
                return

            output_text = response.response.choices[0].message.content

            try:
            # Parse the JSON response
                updated_req = json.loads(output_text)
            except json.JSONDecodeError:
                print("Failed to parse the response as JSON.")
                return
            
            need_update = updated_req.get('need_update', "")
            if int(need_update):
                updated_r = updated_req.get('updated_requirement', "")
                req.name = updated_r.get('name',"")
                req.description = updated_r.get('description',"")
                req.evaluation_method = updated_r.get('evaluation_method',"")
            break

        return req

    def optimize_requirement(self, requirement: Requirement):
        '''Use LLM to optimize local requirements

        Input: requirement, with description field filled in
        Output: requirement, with description optimized (if needed) and other fields filled in
        '''

        api_prompt = REQUIREMENT_CREATOR_PROMPT.format(
            user_input=requirement.description, 
        )

        payload = {
            'model': 'gpt-4-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant. Please return the response as valid JSON.'},
                {'role': 'user', 'content': api_prompt}  # Pass the complete prompt with instructions
            ],
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'response_format': {"type": "json_object"}  
        }

        client = OpenAIMultiClient()

        client.request(
            data=payload,
            endpoint="chat.completions"
        )

        for response in client:
            if response.failed:
                print("Error generating response")
                return

            output_text = response.response.choices[0].message.content

            try:
            # Parse the JSON response
                optimize_req = json.loads(output_text)
            except json.JSONDecodeError:
                print("Failed to parse the response as JSON.")
                return
            
            name = optimize_req.get('name', "")
            description = optimize_req.get('description', "")
            evaluation_method = optimize_req.get('evaluation_method', "")
            if isinstance(evaluation_method, list):
                evaluation_method = "\n".join(evaluation_method)  # Join list elements into a single string

            if requirement.name == "":
                requirement.name = name
            # requirement.description = description
            requirement.evaluation_method = evaluation_method
            requirement.prompt_snippet = ""
            break
        
        return requirement

    def compile_prompt(self, prompt_id):
        ''' Use LLM to compile requirements to a prompt

        Input: self.prompts[prompt_id].requirements
        Output: 
        - self.prompts[prompt_id].text with xml tags
        - self.prompts[prompt_id].requirements with prompt_snippets filled in
        '''

        requirements = self.prompts[prompt_id].requirements
        
        api_prompt = PROMPT_COMPILER_PROMPT.format(requirements=requirements_to_str(requirements))

        payload = {
            'model': 'gpt-4-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant. Please return the response as valid JSON.'},
                {'role': 'user', 'content': api_prompt}  # Pass the complete prompt with instructions
            ],
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'response_format': {"type": "json_object"}  
        }


        client = OpenAIMultiClient()

        client.request(
            data=payload,
            endpoint="chat.completions"
        )

        for response in client:
            if response.failed:
                print("Error generating response")
                return
        
            output_text = response.response.choices[0].message.content
    
            try:
            # Parse the JSON response
                compile_output = json.loads(output_text)
            except json.JSONDecodeError:
                print("Failed to parse the response as JSON.")
                return
            
            prompt = compile_output.get('prompt', "")
            requirements_prompt_snippets = compile_output.get('requirements_prompt_snippets', [])

            for req_prompt in requirements_prompt_snippets:
                id = req_prompt.get("requirement_id", None)
                prompt_snippet = req_prompt.get("prompt_snippet",'')
                self.prompts[prompt_id].requirements[str(id)].prompt_snippet = prompt_snippet
    
            break
        
        self.prompts[prompt_id].text = prompt


    def evaluate_requirement(self, model_name, prompt_id, requirement_id, to_predict_indices: Optional[FilterIds] = None,):
        ''' Use LLM to evaluate prompt outputs based on requirements

        Input: model_name, prompt_id, requirement_id, to_predict_indices
        Output: 
        - A pd.Series of 0/1 evaluation scores to indicate whether the requirement is met
        - A pd.Series of rationale for the evaluation
        '''
        # print(f"Evaluating requirement {requirement_id} for prompt {prompt_id}")
    


        # evaluate prompt outputs based on requirements, on to_predict_indices only
        # refer to data_proceesing.py/run_inference to see how to select indices for prediction


        score_col_obj = ZenoColumn(
            column_type=ZenoColumnType.POSTDISTILL, name=f"evalR{requirement_id}", model=model_name, prompt_id=prompt_id
        )
        rationale_col_obj = ZenoColumn(
            column_type=ZenoColumnType.POSTDISTILL, name=f"evalR{requirement_id}Rationale", model=model_name, prompt_id=prompt_id
        )
        score_hash = str(score_col_obj)
        rationale_hash = str(rationale_col_obj)
        score_col = self.df[score_hash].copy()
        rationale_col = self.df[rationale_hash].copy()

        if to_predict_indices is None:
            to_predict_indices = score_col.loc[pd.isna(score_col)].index
        else:
            to_predict_indices = pd.Index(to_predict_indices.ids)

        requirement = self.prompts[prompt_id].requirements[requirement_id]

        model_col_obj = ZenoColumn(
            column_type=ZenoColumnType.OUTPUT, name="output", model=model_name, prompt_id=prompt_id
        )
        model_hash = str(model_col_obj)
        model_col = self.df[model_hash].copy()

        client = OpenAIMultiClient(endpoint="chats", data_template={"model": model_name})

        def chat_completion(indices):
            for i in indices:
                model_ouput = model_col[i]
                api_prompt = REQUIREMENT_EVALUATION_PROMPT.format(prompt=self.prompts[prompt_id].text, requirement = requirement.description,evaluation_method=requirement.evaluation_method, modelOutput=model_ouput)
                client.request(
                    data={
                        "messages": [
                            {"role": "system", "content": 'You are a helpful assistant. Please return the response as valid JSON.'},
                            {"role": "user", "content": api_prompt}
                        ],
                        'response_format': {"type": "json_object"}  
                    }, metadata={'num': i}, endpoint = "chat.completions"
                )

        client.run_request_function(chat_completion,to_predict_indices)
        count = 0
        for result in client:
            num = result.metadata['num']
            response = result.response.choices[0].message.content

            evaluation_res = json.loads(response)

            str_score = int(evaluation_res.get('pass/fail', '0'))
            if str_score == 1:
                score_col[num] = True
            else:
                score_col[num] = False

            rationale_col[num] = evaluation_res.get('rationale', '')
            count += 1
            if count == len(to_predict_indices):
                break

        score_col.to_pickle(os.path.join(self.cache_path, score_hash + ".pickle"))
        rationale_col.to_pickle(os.path.join(self.cache_path, rationale_hash + ".pickle"))
                        
        return [
            DataProcessingReturn(column=score_col_obj, output=score_col),
            DataProcessingReturn(column=rationale_col_obj, output=rationale_col)
        ]

    def update_evaluator(self, feedback: EvaluatorFeedback)-> Dict[str, Requirement]:
        # Your logic to modify the custom prompt
        data_col = self.df[str(self.data_column)]
        model_col_obj = ZenoColumn(
            column_type=ZenoColumnType.OUTPUT, name="output", model=feedback.model, prompt_id=feedback.prompt_id
        )
        model_col = self.df[str(model_col_obj)]
        requirement = self.prompts[feedback.prompt_id].requirements[feedback.requirement_id]
        corrected_eval = feedback.corrected_eval

        requirement.examples += [Example(
                            id=feedback.example_id,
                            input=data_col.at[int(feedback.example_id)],
                            output=model_col.at[int(feedback.example_id)],
                            is_positive=corrected_eval,
                            feedback=f'''The evaluation should return "{corrected_eval}" based on the requirement.''',
                        )]
        new_requirements = copy.copy(self.prompts[feedback.prompt_id].requirements)

        return new_requirements

    def suggest_requirements(self,cur_info: SuggestNewReqRequest) -> Dict[str, Requirement]:
        ''' Use LLM to brainstorm new requirements

        Output:
        - new requirements: Dict[str, Requirement]
        '''
        print("suggest_new_reqs")
        data_col = self.df[str(self.data_column)]
        model_col_obj = ZenoColumn(
            column_type=ZenoColumnType.OUTPUT, name="output", model=cur_info.model, prompt_id=cur_info.prompt_id
        )
        model_col = self.df[str(model_col_obj)]
        requirements = self.prompts[cur_info.prompt_id].requirements

        input_data = []
        output_data = []
        random_indices = random.sample(range(len(data_col)), 5)
        for i in random_indices:
            input_data.append(data_col.at[i])
            output_data.append(model_col.at[i])

        api_prompt = REQUIREMENT_SUGGESTION_PROMPT.format(prompt=self.prompts[cur_info.prompt_id].text, current_requirements = requirements,input_data=input_data, model_output=output_data)

        client = OpenAIMultiClient(endpoint="chats", data_template={"model": cur_info.model})

        def chat_completion():
            client.request(
                data={
                    "messages": [
                        {"role": "system", "content": "You are an experienced requirement engineer for an LLM application. Please return the response as valid JSON."},
                        {"role": "user", "content": api_prompt}
                    ],
                    'response_format': {"type": "json_object"}
                }
            )

        client.run_request_function(chat_completion)

        suggested_requirements ={}
        rid = str(len(self.prompts[cur_info.prompt_id].requirements)+1)

        for result in client:
            response = result.response.choices[0].message.content
            new_reqs = json.loads(response).get("new_reqs", [])
            for new_req in new_reqs:
                suggested_requirements[rid] = Requirement(
                    id = rid,
                    name = new_req["name"],
                    description = new_req["description"],
                    prompt_snippet = "",
                    evaluation_method = new_req["evaluation_method"])
                rid = str(int(rid)+1)
            break

        # # use REQUIREMENT_SUGGESTION_PROMPT for implementation
        # ## MOCKUP CODE
        # suggested_requirements = {
        #     "100": Requirement(
        #         id = "100",
        #         name = "new-requirement",
        #         description = "This is a new requirement",
        #         prompt_snippet = "",
        #         evaluation_method = "",
        #     ),
        #     "101": Requirement(
        #         id = "101",
        #         name = "new-requirement-v2",
        #         description = "This is also a new requirement",
        #         prompt_snippet = "",
        #         evaluation_method = "",
        #     )
        # }
        return suggested_requirements

    def update_requirement_feedback(self, req: FeedbackRequest) -> Dict[str, Requirement]:
        data_col = self.df[str(self.data_column)]
        model_col_obj = ZenoColumn(
            column_type=ZenoColumnType.OUTPUT, name="output", model=req.model, prompt_id=req.prompt_id
        )
        model_col = self.df[str(model_col_obj)]
        requirement = self.prompts[req.prompt_id].requirements[req.requirement_id]
        is_positive = req.is_positive

        new_example = Example(
                            id=req.example_id,
                            input=data_col.at[int(req.example_id)],
                            output=model_col.at[int(req.example_id)],
                            is_positive=is_positive,
                            feedback=req.feedback,
                    )

        for ex in requirement.examples:
            if ex.id == new_example.id and ex.input == new_example.input and ex.output == new_example.output and ex.is_positive == new_example.is_positive and ex.feedback == new_example.feedback:
                return self.prompts[req.prompt_id].requirements
        
        requirement.examples += [new_example]
        new_requirements = copy.copy(self.prompts[req.prompt_id].requirements)

        return new_requirements
    
    def suggest_requirement_updates(self, req: FeedbackRequest) -> Dict[str, Requirement]:
        ''' Use LLM to update requirements based on user-provided feedback
        - If there is a closely related requirement -- update requirement description & implementation
        - If there is a conflicting requirement -- delete the requirement
        - If there is no related requirements -- add a new one


        Input: 
        - self.prompts[req.prompt_id].requirements
        - req.is_positive, req.feedback
        - data_col.at[req.example_id], model_col.at[req.example_id] # example inputs/outputs
        Output: 
        - new requirements: Dict[str, Requirement], the original requirements can be deleted, updated, or appended
        '''
        ## MOCKUP CODE
        print(f"suggesting new requirements for positive={req.is_positive} example_id={req.example_id} with feedback {req.feedback}")

        data_col = self.df[str(self.data_column)]
        model_col_obj = ZenoColumn(
            column_type=ZenoColumnType.OUTPUT, name="output", model=req.model, prompt_id=req.prompt_id
        )
        model_col = self.df[str(model_col_obj)]

        # Prepare the prompt to send to the OpenAI API for suggestions
        # current_requirements = "\n".join(
        #     [f"{req_id}: {requirement.description}" for req_id, requirement in self.prompts[req.prompt_id].requirements.items()]
        # )
        current_requirements = {
            req_id: {  # Here req_id is the key
                "id": req_id,  # Including the req_id explicitly as part of the values
                "name": requirement.name,
                "description": requirement.description,
                "evaluation_method": requirement.evaluation_method,
                "prompt_snippet": requirement.prompt_snippet
            }
            for req_id, requirement in self.prompts[req.prompt_id].requirements.items()
        }

        api_prompt = REQUIREMENT_UPDATE_PROMPT.format(
            current_requirements=current_requirements,
            input_data=data_col.at[int(req.example_id)],
            model_output=model_col.at[int(req.example_id)],
            feedback=req.feedback
        )

        # Send the API request to OpenAI
        client = OpenAIMultiClient(endpoint="chats", data_template={"model": req.model})

        def chat_completion():
            client.request(
                data={
                    "messages": [
                        {"role": "system", "content": "You are an experienced requirement engineer for an LLM application. Given user feedback on an example, update the requirements."},
                        {"role": "user", "content": api_prompt}
                    ],
                    'response_format': {"type": "json_object"}
                }
            )

        client.run_request_function(chat_completion)

        new_requirements = copy.copy(self.prompts[req.prompt_id].requirements)

        for result in client:
            response = result.response.choices[0].message.content
            actions = json.loads(response).get("actions", [])

            # Handle actions: update, delete, add
            for action in actions:
                if action["action"] == "update":
                    req_id = action["requirement_id"]
                    if req_id in new_requirements:
                        new_requirements[req_id].description = action["updated_description"]
                        new_requirements[req_id].evaluation_method = action["updated_evaluation_method"]
                        new_requirements[req_id].prompt_snippet = action["updated_prompt_snippet"]
                        new_requirements[req_id].examples +=[Example(
                            id=req.example_id,
                            input=data_col.at[int(req.example_id)],
                            output=model_col.at[int(req.example_id)],
                            is_positive=req.is_positive,
                            feedback=req.feedback,
                        )]

                elif action["action"] == "delete":
                    req_id = action["requirement_id"]
                    if req_id in new_requirements:
                        del new_requirements[req_id]

                elif action["action"] == "add":
                    new_req = action["new_requirement"]
                    new_req_id = str(max([int(x) for x in new_requirements.keys()]) + 1)
                    new_requirements[new_req_id] = Requirement(
                        id=new_req_id,
                        name=new_req["name"],
                        description=new_req["description"],
                        prompt_snippet=new_req["prompt_snippet"],
                        evaluation_method=new_req["evaluation_method"],
                        examples=[Example(
                            id=req.example_id,
                            input=data_col.at[int(req.example_id)],
                            output=model_col.at[int(req.example_id)],
                            is_positive=req.is_positive,
                            feedback=req.feedback,
                        )]
                    )
            break


        # new_req_id = str(max([int(x) for x in new_requirements.keys()]) + 1)
        # new_requirements[new_req_id] = Requirement(
        #     id = new_req_id,
        #     name = "new-requirement",
        #     description = "This is a new requirement",
        #     prompt_snippet = "",
        #     evaluation_method = "",
        #     examples = [Example(
        #         id = req.example_id,
        #         input = data_col.at[int(req.example_id)],
        #         output = model_col.at[int(req.example_id)],
        #         is_positive = req.is_positive, 
        #         feedback = req.feedback,
        #     )], 
        # )
        print(new_requirements)
        return new_requirements

    def create_new_tag(self, req: Tag):
        if not self.editable:
            return
        self.tags[req.tag_name] = req
        with open(os.path.join(self.cache_path, "tags.pickle"), "wb") as f:
            pickle.dump(self.tags, f)

    def delete_tag(self, tag_name: str):
        if not self.editable:
            return
        del self.tags[tag_name]
        with open(os.path.join(self.cache_path, "tags.pickle"), "wb") as f:
            pickle.dump(self.tags, f)

    def set_reports(self, reports: List[Report]):
        if not self.editable:
            return
        self.reports = reports
        with open(os.path.join(self.cache_path, "reports.pickle"), "wb") as f:
            pickle.dump(self.reports, f)

    def create_new_slice(self, req: Slice):
        if not self.editable:
            return
        self.slices[req.slice_name] = req
        with open(os.path.join(self.cache_path, "slices.pickle"), "wb") as f:
            pickle.dump(self.slices, f)

    def delete_slice(self, slice_name: str):
        if not self.editable:
            return
        del self.slices[slice_name]
        with open(os.path.join(self.cache_path, "slices.pickle"), "wb") as f:
            pickle.dump(self.slices, f)

    def get_filtered_ids(self, req: PlotRequest):
        return filter_table(self.df, req.filter_predicates, req.tag_ids)[
            str(self.id_column)
        ].to_json(orient="records")

    def get_filtered_table(self, req: TableRequest):
        """Return filtered table from list of filter predicates."""
        filt_df = filter_table(
            self.df, req.filter_predicates, req.filter_ids, req.tag_ids, req.tag_list
        )
        req_columns = [str(col) for col in req.columns]
        if req.diff_column_1 and req.diff_column_2:
            filt_df = generate_diff_cols(filt_df, req.diff_column_1, req.diff_column_2)
            req_columns.append("diff")
        if req.sort[0]:
            filt_df = filt_df.sort_values(str(req.sort[0]), ascending=req.sort[1])
        filt_df = filt_df.iloc[req.slice_range[0] : req.slice_range[1]].copy()
        if self.data_prefix != "":
            # Add data prefix to data column depending on type of data_path.
            filt_df.loc[:, str(self.data_column)] = (
                self.data_prefix + filt_df[str(self.data_column)]
            )
        return filt_df.loc[:, req_columns].to_json(orient="records")
