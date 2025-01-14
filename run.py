import pandas as pd
import os
import yaml
import argparse
import litellm
import mlflow
from zeno.runner import run_zeno
from zeno.api import model
from zeno.api import ZenoParameters, ZenoOptions, ModelReturn
from zeno.classes.classes import Prompt, Requirement
from zeno.util import read_config

litellm.api_key = os.environ.get("LITELLM_API_KEY")
litellm.api_base = "https://cmu-aiinfra.litellm-prod.ai/"
litellm.verbose = True

mlflow.litellm.autolog()
mlflow.dspy.autolog()
mlflow.set_experiment("reqprompt")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yaml')
    args = parser.parse_args()
    
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    data = pd.read_csv(config["data"]["data_path"]).sample(config["data"]["sample_size"], random_state=42).reset_index(drop=True)
    data["label"] = ""
    baseline = config["settings"]["baseline"]
    if not baseline:
        prompt = "<prompt></prompt>"
    else:
        prompt = config["prompt"]['task_description']
    requirements = {}

    if not baseline:
        for i, req in enumerate(config["prompt"]["requirements"]):
            requirements[str(i)] = Requirement(
                id=str(i),
                name=req["name"],
                description=req["description"],
                prompt_snippet="",
                evaluation_method="",
                priority=req["priority"],
                category=req["category"],
                feature=req["feature"],
            )
    else:
        for i, req in enumerate(config["prompt"]["requirements"]):
            requirements[str(i)] = Requirement(
                id=str(i),
                name=req["name"],
                description=req["description"],
                prompt_snippet="",
                evaluation_method="",
            )


    params = ZenoParameters(
        metadata=data,
        models=config["models"],
        prompts={'v1': Prompt(text=prompt, version='v1', requirements=requirements, task=config["prompt"]["task_description"])},
        task_description=config["prompt"]["task_description"],
        view='text-classification',
        data_column=config["data"]["data_column"],
        label_column="label",
        cache_path=config["settings"]["cache_path"],
        multiprocessing=False,
        host=config["settings"]["host"],
        port=config["settings"]["port"],
        baseline=baseline,
    )
    params = read_config(params)
    run_zeno(params)