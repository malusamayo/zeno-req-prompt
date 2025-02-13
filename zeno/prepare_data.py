import pandas as pd
import dspy
import json



def prepare_dataset(data_path, input_key, data_size=100):

    df = pd.read_csv(data_path)[:data_size]
    df_train = df.sample(frac=0.2, random_state=42)
    df_val = df.drop(df_train.index)
    trainset = []
    for i, row in df_train.iterrows():
        example = dspy.Example(**{input_key: row[input_key]}, output="").with_inputs(input_key)
        trainset.append(example)

    valset = []
    for i, row in df_val.iterrows():
        example = dspy.Example(**{input_key: row[input_key]}, output="").with_inputs(input_key)
        valset.append(example)

    return trainset, valset


def prepare_data_quiz_making():
    data_path = "data/mmlu_econ_100.csv"
    input_key = "question"

    trainset, valset = prepare_dataset(data_path, input_key)

    task_description = "Write quiz answer options for the following question."

    class TaskProgram(dspy.Signature):
        """Write four quiz answer options for the following question. Label the quiz answer options with (A) (B) (C) (D)."""

        question = dspy.InputField(desc="The question for which options are needed.")
        output = dspy.OutputField(desc="List of four possible answers for a quiz question.")
    
    return task_description, TaskProgram, trainset, valset

def prepare_data_quiz_making_v0():
    data_path = "data/mmlu_econ_100.csv"
    input_key = "question"

    trainset, valset = prepare_dataset(data_path, input_key)

    task_description = "Write quiz answer options for the following question."

    class TaskProgram(dspy.Signature):
        """Write quiz answer options for the following question."""

        question = dspy.InputField(desc="The question for which options are needed.")
        output = dspy.OutputField(desc="List of possible answers for a quiz question.")
    
    return task_description, TaskProgram, trainset, valset

def prepare_data_product_descrp_gen():
    data_path = "data/esci_100.csv"
    input_key = "product_bullet_point"

    trainset, valset = prepare_dataset(data_path, input_key)

    task_description = "Generate engaging product description from the bullet points."

    class TaskProgram(dspy.Signature):
        """Generate engaging product description from the bullet points."""

        product_bullet_point = dspy.InputField(desc="The bullet points of the product.")
        output = dspy.OutputField(desc="The generated product description.")
    
    return task_description, TaskProgram, trainset, valset

def prepare_data_recipe_gen():
    data_path = "data/recipe.csv"
    input_key = "ingredients"

    trainset, valset = prepare_dataset(data_path, input_key)

    task_description = "Generate a recipe given the list of ingredients."

    class TaskProgram(dspy.Signature):
        """Generate a recipe given the list of ingredients."""

        ingredients = dspy.InputField(desc="A list of ingredients.")
        output = dspy.OutputField(desc="Generated recipe.")
    
    return task_description, TaskProgram, trainset, valset

def prepare_data_story():
    data_path = "data/stories.csv"
    input_key = "application"

    trainset, valset = prepare_dataset(data_path, input_key)

    task_description = "For the user-given application, generate a 200-word story that causes potential harms to relevant stakeholders."

    class TaskProgram(dspy.Signature):
        """For the user-given application, generate a 200-word story that causes potential harms to relevant stakeholders."""

        application = dspy.InputField(desc="A description of user-given application.")
        output = dspy.OutputField(desc="Generated story.")
    
    return task_description, TaskProgram, trainset, valset

def prepare_data(
    task_name,
    requirement_path
):
    
    with open(requirement_path, "r") as f:
        requirements = json.load(f)

    match task_name:
        case "quiz_making":
            task_description, TaskProgram, trainset, valset = prepare_data_quiz_making_v0()
        case "product_descrp_gen":
            task_description, TaskProgram, trainset, valset = prepare_data_product_descrp_gen()
        case "recipe":
            task_description, TaskProgram, trainset, valset = prepare_data_recipe_gen()
        case "story":
            task_description, TaskProgram, trainset, valset = prepare_data_story()
        case _:
            task_description, TaskProgram, trainset, valset = "", None, [], []

    return task_description, TaskProgram, trainset, valset, requirements