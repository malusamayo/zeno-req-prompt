from typing import Callable, Dict, List, Optional, Union, Tuple
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import random
import os
import re
import dsp
import dspy
import litellm
from dspy import LabeledFewShot
import threading
import queue

from zeno.classes.classes import MetricKey, PlotRequest, InferenceRequest, FeedbackRequest, TableRequest, ZenoColumn, Prompt, Requirement, Example, EvaluatorFeedback, SuggestNewReqRequest, RemoveExampleFeedback
from zeno.signatures import *

litellm.api_key = os.environ.get("LITELLM_API_KEY")
litellm.api_base = "https://cmu-aiinfra.litellm-prod.ai/"

def example2text(example: Example) -> str:

    if example.is_positive:
        return f"Input: {example.input}\nOutput: {example.output}"
    else:
        return f"Input: {example.input}\nIncorrect Output: {example.output}\nFeedback: {example.feedback}"

def examples2text(examples: Union[str, List[Example]]) -> str:
    """Formats the given one or more examples into a single structured string."""
    if isinstance(examples, str):
        return examples
    
    return "\n".join([f"[{idx+1}] «{example2text(example)}»" for idx, example in enumerate(examples)])

def requirement2text(requirement: Requirement) -> str:
    return f'''{requirement.name}: {requirement.description}'''

def requirements2text(requirements: Union[str, List[Requirement]]) -> str:
    """Formats the given one or more requirements into a single structured string."""
    if isinstance(requirements, str):
        return requirements
    
    requirements = sorted(requirements, key=lambda x: x.id)
    return "\n".join([f"[{requirement.id}] «{requirement2text(requirement)}»" for requirement in requirements])

def text2requirement(text: str) -> Requirement:
    pattern = r"\[(\d+)\] «(.+): (.+)»"
    match = re.search(pattern, text)
    if match:
        req_name = match.group(2)
        req_description = match.group(3)
        new_req = Requirement(
            id="-1",
            name=req_name,
            description=req_description,
            prompt_snippet="",
            evaluation_method="",
        )
        return new_req
    else:
        return None

def text2requirements(text: str) -> List[Requirement]:
    lines = text.split("\n")
    requirements = []
    for line in lines:
        requirement = text2requirement(line)
        if requirement is not None:
            requirements.append(requirement)
    return requirements

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

class ReqHITLPromptOptimizer:

    def __init__(self):
        super().__init__()
        self.prompt_compiler = dspy.Predict(BasicCompilePrompt)
        self.prompt_refiner = dspy.Predict(RefinePromptWithFeedback)
        self.feedback_converter = dspy.Predict(ConvertFeedbackToRequirement)
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
            print("Requirements: ", requirements)
            print("Input: ", sampled_example)
            print("Output: ", output)
            feedback = input("Provide feedback on the requirements: ")
            if feedback == "":
                continue
            elif feedback == "done":
                break

            new_requirement = self.feedback_converter(
                task_description=task_description,
                existing_requirements=requirements,
                feedback=feedback,
            ).requirement
            requirements.append(new_requirement)
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

class PromptAgent:

    def __init__(self, task_description, input_variable="input"):
        super().__init__()
        self.turbo = dspy.LM(model='openai/gpt-4o-2024-08-06')
        self.mini = dspy.LM(model='openai/gpt-4o-mini-2024-07-18')        
        dspy.settings.configure(lm=self.turbo)

        self.input_variable = input_variable
        self.task_description = task_description
        self.task_program = construct_task_program(
            task_description=self.task_description,
            input_variable=self.input_variable,
            output_variable="output",
            prompt="",
        )

        self.basic_compiler = dspy.Predict(BasicCompilePrompt)
        self.compiler = dspy.Predict(CompilePrompt)

        self.prompt_refiner = dspy.Predict(RefinePromptWithFeedback)
        self.feedback_converter = dspy.Predict(ConvertFeedbackToRequirement)

        self.requirement_suggester = dspy.ChainOfThought(SuggestRequirements)
        self.requirement_completer = dspy.Predict(CompleteRequirements)
        self.requirement_evaluator = dspy.ChainOfThought(EvaluateRequirement)

    def optimize_prompt(
        self,
        prompt: str,
        requirements: List[Requirement],
    ):
        """Optimize the prompt to satisfy the given requirements.
        Args:
            prompt (str): The prompt to optimize.
            requirements (List[Requirement]): The requirements that the prompt should satisfy.
        Returns:
            str: The optimized prompt.
        """
        self.task_program.__doc__ = prompt
        task_program_predictor = dspy.Predict(self.task_program)

        for requirement in requirements:
            examples = requirement.examples
            if len(examples) == 0:
                continue

            example = random.choice(examples)

            output = task_program_predictor(
                **{self.input_variable: example.input},
            ).output
            result = self.requirement_evaluator(
                model_input=example.input,
                model_output=output, 
                requirement=requirement2text(requirement),
                evaluation_method=requirement.evaluation_method,
            )

            max_rounds = 3
            rounds = 0
            while not result.meets_requirement and rounds < max_rounds:
                # Refine the prompt
                prompt = self.prompt_refiner(
                    task_description=self.task_description,
                    requirements=requirements2text(requirements),
                    previous_prompt=prompt,
                    past_input=example.input,
                    past_output=output,
                    feedback=result.reasoning
                ).prompt
                self.task_program.__doc__ = prompt
                task_program_predictor = dspy.Predict(task_program)
                
                # Evaluate the requirement again
                output = task_program_predictor(
                    **{self.input_variable: example.output},
                ).output
                result = self.requirement_evaluator(
                    model_input=example.input,
                    model_output=output, 
                    requirement=requirement2text(requirement),
                    evaluation_method=requirement.evaluation_method,
                )
                rounds += 1

        return prompt


    def compile_requirements(
        self, 
        requirements: List[Requirement],
        requirements_prev: Optional[List[Requirement]] = None,
    ) -> str:
        """Compile a prompt that satisfies the given requirements.
        Args:
            task_description (str): Description of the task.
            requirements (List[Requirement]): A list of requirements that the prompt should include.
        Returns:
            str: The compiled prompt.
        """
        hard_requirements = [req for req in requirements if req.priority == "hard"]
        examples = []
        for req in requirements:
            if len(req.examples) > 0:
                examples.extend(req.examples)
        
        examples_prev = []
        if requirements_prev is not None:
            for req in requirements_prev:
                if len(req.examples) > 0:
                    examples_prev.extend(req.examples)

        diff_requirements = []
        for req in requirements:
            if requirements_prev is not None:
                if req not in requirements_prev:
                    diff_requirements.append(req)
            else:
                diff_requirements.append(req)
        
        diff_examples = []
        for example in examples:
            if example not in examples_prev:
                diff_examples.append(example)

        # print("Requirements: ", requirements)

        if len(examples) > 0 or len(hard_requirements) > 0:
            prompt = self.compiler(
                task_description=self.task_description,
                requirements=requirements2text(requirements),
                hard_requirements=requirements2text(hard_requirements),
                new_requirements=requirements2text(diff_requirements),
                # good_examples=examples2text([example for example in examples if example.is_positive]),
                # bad_examples=examples2text([example for example in examples if not example.is_positive]),
                input_variable=self.input_variable,
            ).prompt
        else:
           prompt = self.basic_compiler(
                task_description=self.task_description,
                requirements=requirements2text(requirements),
                input_variable=self.input_variable,
            ).prompt

        prompt = self.optimize_prompt(
            prompt=prompt,
            requirements=requirements,
        )
        return prompt
    
    def complete_requirements(
        self, 
        requirement: Requirement,
    ) -> Requirement:
        """Complete the requirements with additional fields.
        Args:
            requirement (Requirement): The requirement to complete.
        Returns:
            Requirement: The completed requirement.
        """
        requirement_description = requirement.description
        with dspy.context(lm=self.mini):
            result = self.requirement_completer(requirement_description=requirement_description)
        requirement.name = result.requirement_name
        requirement.evaluation_method = result.evaluation_method
        requirement.priority = result.priority
        requirement.category = result.category
        
        return requirement

    def suggest_requirements(
        self,
        requirements: List[Requirement],
        examples: List[Example],
    ):
        """Suggest new requirements.
        Args:
            requirements (List[Requirement]): The current requirements for the prompt.
        Returns:
            List[Requirement]: The suggested new requirements.
        """
        with dspy.context(lm=self.mini):
            requirement_texts = self.requirement_suggester(
                current_requirements=requirements2text(requirements),
                current_output=examples2text(examples),
            ).new_requirements
        requirements = text2requirements(requirement_texts)
        return requirements

    def evaluate_requirements(
        self,
        requirements: List[Requirement],
        examples: List[Example],
    ):
        """Evaluate the requirements.
        Args:
            requirements (List[Requirement]): The requirements to evaluate.
            examples (List[Example]): The examples to evaluate.
        Returns:
            List[bool]: The evaluation results.
        """
        completions = []
        results = []

        with dspy.context(lm=self.mini):
            with ThreadPoolExecutor(max_workers=100) as executor:
                for example in examples:
                    for requirement in requirements:
                        future = executor.submit(
                            self.requirement_evaluator,
                            model_input=example.input,
                            model_output=example.output, 
                            requirement=requirement2text(requirement),
                            evaluation_method=requirement.evaluation_method,
                        )
                        completions.append((requirement.id, example.id, future))

        for (requirement.id, example.id, future) in completions:
            try:
                result = future.result()
                results.append(
                    {
                        "requirement_id": requirement.id,
                        "example_id": example.id,
                        "score": result.meets_requirement,
                        "rationale": result.reasoning,
                    }
                )
            except Exception as exc:
                results.append(exc)
        return results


if __name__ == '__main__':
    turbo = dspy.LM(model='openai/gpt-4o-2024-08-06')
    dspy.settings.configure(lm=turbo)

    task_description = "Classify the sentiment of a tweet"
    input_variable = "tweet"
    requirements=[
        Requirement(
            id="0", 
            name="classification-result", 
            description="The classification result must be one of 'positive', 'negative', or 'neutral", 
            prompt_snippet="", 
            evaluation_method="", 
            examples=[Example(id="0", input="I'm feeling great 😊", output="positive", is_positive=True), Example(id="1", input="I'm feeling terrible 😭", output="negative", is_positive=True)]),
        Requirement(
            id="1", 
            name="sarcasm-sentiment", 
            description="The model should be able to detect sentiment in sarcasm", 
            prompt_snippet="", 
            evaluation_method="",
            examples=[Example(id="2", input="Feeling great lol", output="negative", is_positive=False)]),
        Requirement(
            id="2",
            name="emoji-sentiment", 
            description="The model should be able to detect sentiment in emojis", 
            prompt_snippet="", 
            evaluation_method="",
            examples=[Example(id="3", input="I'm feeling great 😭", output="negative", is_positive=False)]),
    ]

    optimizer = PromptAgent(task_description=task_description, input_variable=input_variable)
    result = optimizer.suggest_requirements(
        requirements,
        [requirements[1].examples[0]],
    )
    dspy.inspect_history(n=1)
    result = optimizer.complete_requirements(
        requirements[1],
    )
    dspy.inspect_history(n=1)
    prompt = optimizer.compile_requirements(
        requirements=requirements,
    )

    print(prompt)

    all_examples = [
        Example(id="0", input="I'm feeling great 😊", output="positive", is_positive=True),
        Example(id="1", input="I'm feeling terrible 😭", output="negative", is_positive=True),
        Example(id="2", input="Feeling great lol", output="negative", is_positive=False),
        Example(id="3", input="I'm feeling great 😭", output="negative", is_positive=False),
    ]
    results = optimizer.evaluate_requirements(
        requirements=requirements,
        examples=all_examples,
    )
    print(results)

    dspy.inspect_history(n=10)
