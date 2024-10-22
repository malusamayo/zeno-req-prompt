import pandas as pd
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
    data = pd.read_csv('data/travel_data.csv').sample(10, random_state=42).reset_index(drop=True)
    data["label"] = ""
    prompt = "<prompt></prompt>"
    
    # client = OpenAIMultiClient(endpoint="chats", data_template={"model": "gpt-4o-mini"})
    # def chat_completion(inputs):
    #     for i, x in enumerate(inputs):
    #         client.request(
    #             data={
    #                 "messages": [
    #                     {"role": "system", "content": prompt},
    #                     {"role": "user", "content": x}
    #                 ],
    #             }, metadata={'num': i}
    #         )
    # client.run_request_function(chat_completion, list(data["question"]), stop_at_end=False)
    # out = {}
    # for result in client:
    #     num = result.metadata['num']
    #     response = result.response.choices[0].message.content
    #     out[num] = response
    # out = [item[1] for item in sorted(out.items())]

    # from tqdm import trange
    # zeno_options = ZenoOptions(
    #         id_column="index",
    #         data_column="question",
    #         label_column="label",
    #         distill_columns=dict(),
    #         data_path="",
    #         label_path="",
    #         output_column="",
    #         output_path="",
    #     )
    # out = openai_inference("gpt-4o-mini", prompt)(data, zeno_options)
    # print(out)

    params = ZenoParameters(
        metadata=data,
        functions=[openai_inference],
        models=['gpt-4o-mini'],
        prompts={'v1': Prompt(text=prompt, version='v1', requirements={})},
        view='text-classification',
        data_column="query",
        label_column="label",
        cache_path='.zeno_cache_1022242',
        multiprocessing=False,
    )
    zeno(params)