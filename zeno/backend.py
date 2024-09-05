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
from inspect import getsource
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

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
from zeno.classes.classes import MetricKey, PlotRequest, TableRequest, ZenoColumn, Prompt, Requirement
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
        self.__inference()
        self.done_running_inference = True

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

    def __inference(self, model_prompt_pairs=[]):
        """Run models on instances."""

        # Check if we need to run inference since Pool is expensive
        models_to_run = []
        if len(model_prompt_pairs) == 0:
            model_prompt_pairs = [(model_name, prompt_id) for prompt_id in self.prompts.keys() for model_name in self.model_names]
        for (model_name, prompt_id) in model_prompt_pairs:
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

            if self.df[model_hash].isna().any():
                models_to_run.append((model_name, prompt_id))
            else:
                self.df[model_hash] = self.df[model_hash].convert_dtypes()
                model_column.metadata_type = get_metadata_type(self.df[model_hash])
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
                for i, (model_name, prompt_id) in enumerate(models_to_run):
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
                    filt_df, metric_key.model, metric_key.metric
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
        self, df: DataFrame, model: Union[str, None], metric: str
    ) -> Union[float, None]:
        if not self.done_running_inference:
            return None

        if model is not None:
            output_col = ZenoColumn(
                column_type=ZenoColumnType.OUTPUT, name="output", model=model, prompt_id=self.current_prompt_id
            )
            output_hash = str(output_col)

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
                    "output_column": output_hash,
                    "output_path": os.path.join(self.cache_path, output_hash),
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
        self.compile_prompt(new_version)
        with open(os.path.join(self.cache_path, "prompts.pickle"), "wb") as f:
            pickle.dump(self.prompts, f)
        return self.prompts[new_version]

    def run_prompt(self, prompt_version):
        self.__inference([(model, prompt_version) for model in self.model_names])
    
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

    def wrap_non_req_text(self, match):
        if match.group(2):  # This is the text outside <req> tags
            return f'<text>{match.group(2).strip()}</text>'
        return match.group(1)  # This is a <req> tag, return it unchanged

    def extract_requirements(self, prompt_id):
        '''Use LLM to extract requirements for prompt_id

        Input: self.prompts[prompt_id].text
        Output: 
        - self.prompts[prompt_id].requirements, extracted from the prompt
        - self.prompts[prompt_id].text, updated with xml tags on requirements
        '''
        prompt = self.prompts[prompt_id].text
        
        api_prompt = f"""
        Given the following prompt, extract a series of success criteria used for evaluating the model outputs from the prompt. 
        Requirements:
        1. List requirements one by one in the format: 
            Name: [name];Prompt Snippet: [prompt snippet];Description: [description];Evaluation Method: [evaluation method].
        2. Use the exact wording from the prompt for the Prompt Snippet.
        3. Only include unique criteria mentioned in the original prompt. Merge the ones that are similar. 
        4. Try to make the evaluation method as clear and objective as possible and give specific steps. 
        5. Be concise.
        Prompt: '''{prompt}'''
        Requirements:
        """

        functions = [
            {
                "name": "extract_requirements",
                "description": "Extract requirements from the prompt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "requirements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "promptSnippet": {"type": "string"},
                                    "description": {"type": "string"},
                                    "evaluationMethod": {"type": "string"}
                                },
                                "required": ["name", "promptSnippet", "description", "evaluationMethod"]
                            }
                        }
                    }
                }
            }
        ]

        payload = {
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': api_prompt}  # Pass the complete prompt with instructions
            ],
            'functions': functions,
            'function_call': "auto",  # Automatically use the function call
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
        }

        if prompt != '<prompt></prompt>':
            client = OpenAIMultiClient()

            client.request(
                data=payload,
                endpoint="chat.completions"
            )
        
            for response in client:
                if response.failed:
                    print("Error generating response")
                    return
            
                result = response.response
                first_choice = result.choices[0]
                function_call = first_choice.message.function_call
                function_call_args = function_call.arguments
        
            # Convert the JSON string to a Python dictionary
                extracted_data = json.loads(function_call_args)
                extracted_requirements = extracted_data.get('requirements', [])


            # Loop through each extracted requirement and add it to the list
                for idx, req in enumerate(extracted_requirements):
                    prompt_snippet=req.get('promptSnippet', '')
                    requirement = Requirement(
                        id=idx,  # Generate a unique ID
                        name=req.get('name', 'Unnamed Requirement'),
                        description=req.get('description', ''),
                        prompt_snippet=req.get('promptSnippet', ''),
                        evaluation_method=req.get('evaluationMethod', '')
                    )
                    self.prompts[prompt_id].requirements.append(requirement)

                    best_match, start_index, end_index = self.find_best_match(prompt, prompt_snippet.strip())
                    wrapped_snippet = f'<req name="{self.prompts[prompt_id].requirements[idx].name}">{best_match}</req>'
                    prompt = prompt[:start_index] + wrapped_snippet + prompt[end_index:]
                break
        pattern = re.compile(r'(<req name=".*?">.*?</req>)|([^<]+)')
        self.prompts[prompt_id].text = pattern.sub(self.wrap_non_req_text, prompt)
        self.prompts[prompt_id].text = f"<prompt>{self.prompts[prompt_id].text}</prompt>"

    def optimize_requirement(self, requirement: Requirement):
        ### [TODO] Use LLM to optimize local requirements
        ### Input: requirement, with description field filled in
        ### Output: requirement, with description optimized (if needed) and other fields filled in
        return requirement

    def compile_prompt(self, prompt_id):
        ### [TODO] Use LLM to compile requirements to prompt
        ### Input: self.prompts[prompt_id].requirements
        ### Output: self.prompts[prompt_id].text with xml tags
        requirements = self.prompts[prompt_id].requirements
        
        api_prompt = f"""
            Given the following requirements, generate a prompt that satisfies all the requirements listed. For each requirement:
            1. If the requirement's prompt_snippet field is empty, generate a prompt snippet that corresponds to the requirement within the generated prompt. Use the exact wording from the generated prompt for the Prompt Snippet. The format should be (requirement_id, prompt snippet), and include it in the output array of all generated prompt snippets for requirements without existing content in the prompt_snippet field.
            2. If the requirement has content in the prompt_snippet field, use the exact words from this field in the generated prompt.
            3. Ensure the generated prompt addresses all the requirements.
            4. The output format should be: Prompt: [generated prompt]; Requirements_prompt_snippets: [(requirement_id, prompt snippet)]
            Requirements: '''{requirements}'''
            Prompt:
            Requirements_prompt_snippets:
        """

        functions = [
                    {
                        "name": "generate_prompts",
                        "description": "Generate prompts from given requirements",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "compile_output": {
                                    "type": "object",
                                    "properties": {
                                        "Prompt": {"type": "string"},  # First element
                                        "Requirements_prompt_snippets": {  # Second element (array of objects)
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "requirement_id": {"type": "integer"},
                                                    "prompt_snippet": {"type": "string"}
                                                },
                                                "required": ["requirement_id", "prompt_snippet"]
                                            }
                                        }
                                    },
                                    "required": ["Prompt", "Requirements_prompt_snippets"]  # Ensure both are present
                                }
                            },
                            "required": ["compile_output"]
                        }
                    }
                ]


        payload = {
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': api_prompt}  # Pass the complete prompt with instructions
            ],
            'functions': functions,
            'function_call': "auto",  # Automatically use the function call
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
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
            
                result = response.response
                first_choice = result.choices[0]
                function_call = first_choice.message.function_call
                function_call_args = function_call.arguments
        
            # Convert the JSON string to a Python dictionary
                res = json.loads(function_call_args)
                compile_output = res.get('compile_output', None)
                if compile_output is None:
                    print("Error: 'compile_output' not found in response")
                    return
                prompt = compile_output.get('Prompt', "")
                Requirements_prompt_snippets = compile_output.get('Requirements_prompt_snippets', [])

                for req_prompt in Requirements_prompt_snippets:
                    id = req_prompt.get("requirement_id",None)
                    prompt_snippet = req_prompt.get("prompt_snippet",'')
                    self.prompts[prompt_id].requirements[id].prompt_snippet = prompt_snippet

                for idx in range(len(self.prompts[prompt_id].requirements)):
                    cur_req = self.prompts[prompt_id].requirements[idx]
                    best_match, start_index, end_index = self.find_best_match(prompt, cur_req.prompt_snippet.strip())
                    wrapped_snippet = f'<req name="{self.prompts[prompt_id].requirements[idx].name}">{best_match}</req>'
                    prompt = prompt[:start_index] + wrapped_snippet + prompt[end_index:]
                break
        
        pattern = re.compile(r'(<req name=".*?">.*?</req>)|([^<]+)')
        self.prompts[prompt_id].text = pattern.sub(self.wrap_non_req_text, prompt)
        self.prompts[prompt_id].text = f"<prompt>{self.prompts[prompt_id].text}</prompt>"
        
        # print(self.prompts[prompt_id].requirements)
        # print(self.prompts[prompt_id].text)
        # self.prompts[prompt_id].text = "<prompt>This is an example prompt.</prompt>"

    def evaluate_requirement(self, prompt_id, requirement_id):
        ### [TODO] Use LLM to evaluate prompt outputs based on requirements
        requirement = self.prompts[prompt_id].requirements[requirement_id]

        ### construct a proper evaluator
        # requirement.evaluation_method


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
