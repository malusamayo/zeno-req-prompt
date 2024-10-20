from typing import Callable, Dict, List, Optional, Union, Tuple
import random
import dsp
import dspy
from dspy import LabeledFewShot

from zeno.classes.classes import MetricKey, PlotRequest, InferenceRequest, FeedbackRequest, TableRequest, ZenoColumn, Prompt, Requirement, Example, EvaluatorFeedback, SuggestNewReqRequest, RemoveExampleFeedback

def example2text(example: Example) -> str:

    if example.is_positive:
        return f"Input: {example.input}\nExpected Output: {example.output}"
    else:
        return f"Input: {example.input}\nIncorrect Output: {example.output}\nFeedback: {example.feedback}"

def examples2text(examples: Union[str, List[Example]]) -> str:
    """Formats the given one or more examples into a single structured string."""
    if isinstance(examples, str):
        return examples
    
    return "\n".join([f"[{idx+1}] «{example2text(example)}»" for idx, example in enumerate(examples)])


class BasicCompilePrompt(dspy.Signature):
    """You are a prompt writer for large language models. I will give you a task description, and a list of requirements that the large language model must satisfy when performing the task. 
    
Your task is to propose a prompt will lead a good language model to perform the task well and meet all the requirements. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(format=dsp.passages2text, desc="A list of requirements that the prompt must satisfy")
    prompt = dspy.OutputField(desc="The proposed prompt")

class BasicCompilePromptWithExamples(dspy.Signature):
    """You are a prompt writer for large language models. I will give you a task description, and a list of requirements that the large language model must satisfy when performing the task.
I will also provide you with some positive ``examples`` of the expected inputs and outputs for this task, as well as some negative ``examples`` that the model should avoid. You can incorporate these examples in your prompt.

Your task is to propose a prompt will lead a good language model to perform the task well and meet all the requirements. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(format=dsp.passages2text, desc="A list of requirements that the prompt must satisfy")
    incorrect_examples = dspy.InputField(format=examples2text, desc="A list of incorrect examples")
    prompt = dspy.OutputField(desc="The proposed prompt")

class RefinePromptWithFeedback(dspy.Signature):
    """You are a prompt re-writer for large language models. I will give you a task description, a list of requirements that the large language model must satisfy when performing the task, and a prompt that was previously used for the task. I will also provide you with some feedback on the previous prompt.

Your task is to propose a new prompt will lead a good language model to perform the task well, meet all the requirements, and incorporate the feedback. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(format=dsp.passages2text, desc="A list of requirements that the prompt must satisfy")
    previous_prompt = dspy.InputField(desc="The previous prompt")
    past_input = dspy.InputField(desc="The input that was used with the previous prompt")
    past_output = dspy.InputField(desc="The output that was generated with the previous prompt")
    feedback = dspy.InputField(desc="Feedback on the previous prompt")
    prompt = dspy.OutputField(desc="The proposed prompt")


class GenerateFieldDescription(dspy.Signature):
    """Generate a concise and informative description for a given field based on the provided name and task description. This description should be no longer than 10 words and should be in simple english."""

    task_description = dspy.InputField(
        prefix="Task Description:",
        desc="Description of the task the field is an input to.",
    )
    field_name = dspy.InputField(
        prefix="Field Name:",
        desc="Name of the field to generate synthetic data for.",
    )
    field_description = dspy.OutputField(
        prefix="Field Description:",
        desc="Description of the field.",
    )

class TaskProgram(dspy.Signature):
    pass

def construct_task_program(
    task_description: str,
    input_variable: str,
    output_variable: str,
    prompt: str,
) -> dspy.Module:
    """Construct a task program that takes in an input variable, performs a task, and outputs the result.

    Args:
        task_description (str): Description of the task.
        input_variable (str): Name of the input variable.
        output_variable (str): Name of the output variable.
        prompt (str): Prompt for the task.
        field_description (str): Description of the input field.

    Returns:
        TaskProgram: A task program that performs the task.
    """
    
    generate_field_description = dspy.Predict(GenerateFieldDescription)

    task_program = TaskProgram
    
    field_details = generate_field_description(
        task_description=task_description,
        field_name=input_variable,
    )
    input_field = dspy.InputField(
        prefix=f"{input_variable.capitalize()}:",
        desc=field_details.field_description,
    )
    task_program = task_program.insert(
        -1,
        input_variable,
        input_field,
    )

    field_details = generate_field_description(
        task_description=task_description,
        field_name=output_variable,
    )
    output_field = dspy.OutputField(
        prefix=f"{output_variable.capitalize()}:",
        desc=field_details.field_description,
    )
    task_program = task_program.insert(
        -1,
        output_variable,
        output_field,
    )

    task_program.__doc__ = prompt
    return task_program

class HITLPromptOptimizer:

    def __init__(self):
        super().__init__()
        self.prompt_compiler = dspy.Predict(BasicCompilePrompt)
        self.prompt_refiner = dspy.Predict(RefinePromptWithFeedback)
        self.optimizer = LabeledFewShot()

    def forward(self, 
        task_description: str, 
        input_variable: str, 
        requirements: List[str], 
        examples: List[str],
        trainset: List[dspy.Example],
        optimization_flag: str = "o0",
    ) -> str:
        """Forward pass of the HITL
        Args:
            task_description (str): Description of the task.
            input_variable (str): Name of the input variable.
            requirements (List[str]): A list of requirements that the prompt must satisfy.
            examples (List[str]): A list of examples for the task.
            optimization_flag (str): Optimization flag for the model.
        Returns:
            str: The optimized prompt.
        """

        task_program = construct_task_program(
            task_description=task_description,
            input_variable=input_variable,
            output_variable="output",
            prompt=task_description,
        )

        prompt = self.prompt_compiler(
            task_description=task_description,
            requirements=requirements,
        ).prompt

        task_program.__doc__ = prompt

        feedback = ""
        while True:
            if optimization_flag == "o0":
                task_program_predictor = dspy.Predict(task_program)
            elif optimization_flag == "o1":
                task_program_predictor = dspy.Predict(task_program)
                task_program_predictor = self.optimizer.compile(student=task_program_predictor, trainset=trainset)

            if feedback == "":
                sampled_example = random.choice(examples)
            output = task_program_predictor(
                **{input_variable: sampled_example},
            ).output
            dspy.inspect_history(n=1)
            print("Prompt: ", prompt)
            print("Input: ", sampled_example)
            print("Output: ", output)
            feedback = input("Provide feedback on the prompt: ")
            if feedback == "":
                continue
            elif feedback == "done":
                break
            prompt = self.prompt_refiner(
                task_description=task_description,
                requirements=requirements,
                previous_prompt=prompt,
                past_input=sampled_example,
                past_output=output,
                feedback=feedback
            ).prompt
            task_program.__doc__ = prompt

        return prompt
        

if __name__ == '__main__':
    turbo = dspy.LM(model='gpt-4o-mini', max_tokens=4096)
    dspy.settings.configure(lm=turbo)

    task_description = "Classify the sentiment of a tweet"
    input_variable = "tweet"
    requirements=[
        "The classification result must be one of 'positive', 'negative', or 'neutral'",
        "The model should be able to detect sarcasm",
        "The model should be able to detect sentiment in emojis",
    ]
    examples = [
        "I'm feeling great 😊",
        "I'm feeling terrible 😭",
        "Feeling great lol",
        "I'm feeling great 😭",
    ]
    trainset = [
        dspy.Example(tweet="Feeling great lol", output="negative"),
        dspy.Example(tweet="I'm feeling great 😭", output="negative"),
        dspy.Example(tweet="I'm feeling great 😊", output="positive"),
        dspy.Example(tweet="I'm feeling terrible 😭", output="negative"),
    ]

    optimizer = HITLPromptOptimizer()
    prompt = optimizer.forward(
        task_description=task_description,
        input_variable=input_variable,
        requirements=requirements,
        examples=examples,
        trainset=trainset,
        optimization_flag="o1",
    )

    turbo.inspect_history(n=10)
