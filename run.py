import pandas as pd
import yaml
import argparse
from zeno.runner import zeno
from zeno.api import model
from zeno.api import ZenoParameters, ZenoOptions, ModelReturn
from zeno.classes.classes import Prompt
from zeno.openai_client import OpenAIMultiClient


@model
def openai_inference(model_name, prompt):
    client = OpenAIMultiClient(endpoint="chats", data_template={"model": model_name})
    def chat_completion(inputs):
        for i, x in enumerate(inputs):
            client.request(
                data={
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": x}
                    ],
                }, metadata={'num': i}
            )

    def pred(df, ops: ZenoOptions):
        client.run_request_function(chat_completion, list(df[ops.data_column]))
        out = {}
        for result in client:
            num = result.metadata['num']
            response = result.response.choices[0].message.content
            out[num] = response
        out = [item[1] for item in sorted(out.items())]
        return ModelReturn(model_output=out)

    return pred

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yaml')
    args = parser.parse_args()
    
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    data = pd.read_csv(config["data"]["data_path"]).sample(config["data"]["sample_size"], random_state=42).reset_index(drop=True)
    data["label"] = ""
    prompt = "<prompt></prompt>"

    params = ZenoParameters(
        metadata=data,
        functions=[openai_inference],
        models=config["models"],
        prompts={'v1': Prompt(text=prompt, version='v1', requirements={})},
        view='text-classification',
        data_column=config["data"]["data_column"],
        label_column="label",
        cache_path=config["settings"]["cache_path"],
        multiprocessing=False,
        port=config["settings"]["port"]
    )
    zeno(params)