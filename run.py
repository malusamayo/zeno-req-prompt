import pandas as pd
from openai import OpenAI
from zeno.runner import zeno
from zeno.api import model
from zeno.api import ZenoParameters, ZenoOptions, ModelReturn
from zeno.classes.classes import Prompt

client = OpenAI()

@model
def openai_inference(model_name, prompt):
    def chat_completion(inputs):
        outputs = []
        for x in inputs:
            result = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": x}
                ],
                stream=False,
            )
            outputs.append(result.choices[0].message.content)
        return outputs

    def pred(df, ops: ZenoOptions):
        out = chat_completion(list(df[ops.data_column]))

        return ModelReturn(model_output=out)

    return pred

if __name__ == '__main__':
    data = pd.read_csv('data/mmlu.csv').sample(5, random_state=42).reset_index(drop=True)
    data["label"] = ""
    prompt = "Create 4 answer options for the test question."
    params = ZenoParameters(
        metadata=data,
        functions=[openai_inference],
        models=['gpt-4o-mini'],
        prompts={'v1': Prompt(text=prompt, version='v1')},
        view='text-classification',
        data_column="question",
        label_column="label",
        cache_path='.zeno_cache',
    )
    zeno(params)