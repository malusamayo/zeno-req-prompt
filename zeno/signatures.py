import dspy
import dsp
class CompleteRequirements(dspy.Signature):
    """You are given a user-written requirement description. Your task is to generate additional fields: 'name', 'evaluation_method', 'priority', and 'category'. """
    requirement_description = dspy.InputField(desc="A user-written requirement descriotion")
    requirement_name = dspy.OutputField(desc="The name of the requirement, formatted as lowercase with hyphens, e.g., 'answer-length'")
    evaluation_method = dspy.OutputField(desc="A specific, objective, and measurable method for evaluating whether the requirement is met")
    priority = dspy.OutputField(desc="Whether the requirement is a soft or hard requirement")
    category = dspy.OutputField(desc="The focus area of the requirement, classified as structure, content, or presentation")

class SuggestRequirements(dspy.Signature):
    """You are an experienced requirement engineer for an LLM application. Given the prompt, current requirements, and example inputs and outputs, suggest three new requirements."""

    current_requirements = dspy.InputField(desc="The current requirements for the LLM")
    current_output = dspy.InputField(desc="Sampled current model inputs and outputs")
    new_requirements = dspy.OutputField(desc="Suggested additional requirements for the LLM")

class EvaluateRequirement(dspy.Signature):
    """Given the requirement and evaluation criteria, determine if the model output meets the requirement. Answer yes or no."""
    
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    requirement = dspy.InputField(desc="The requirement")
    evaluation_method = dspy.InputField(desc="The evaluation method")
    meets_requirement: bool = dspy.OutputField(desc="Whether the model output meets the requirement")

class UpdateEvaluationMethod(dspy.Signature):
    """Given an example, update the evaluation method to produce the expected evaluation result."""
    
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    expected_evaluation_result = dspy.InputField(desc="The expected evaluation result")
    previous_evaluation_method = dspy.InputField(desc="The previous evaluation method")
    updated_evaluation_method = dspy.OutputField(desc="The updated evaluation method")

class BasicCompilePrompt(dspy.Signature):
    """You are a prompt writer for large language models. I will give you a task description, and a list of requirements that the large language model must satisfy when performing the task. 
    
Your task is to propose a prompt will lead a good language model to perform the task well and meet all the requirements. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(desc="A list of requirements that the prompt should include")
    input_variable = dspy.InputField(desc="The name of the input variable")
    prompt = dspy.OutputField(desc="The proposed prompt")

class CompilePrompt(dspy.Signature):
    """You are a prompt writer for large language models. I will give you a task description, and a list of requirements that the large language model must satisfy when performing the task.
There are some hard requirements that the model must satisfy, and some soft requirements that the model should satisfy if possible. Make sure to include these requirements in your prompt.\
Some new requirements may also provided, which you should prioritize in your prompt.

Your task is to propose a prompt will lead a good language model to perform the task well and meet all the requirements. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(desc="A list of requirements that the prompt should include")
    hard_requirements = dspy.InputField(desc="A list of hard requirements that the prompt must include")
    new_requirements = dspy.InputField(desc="A list of new requirements that the prompt should prioritize")
    # good_examples = dspy.InputField(desc="A list of good examples")
    # bad_examples = dspy.InputField(desc="A list of bad examples")
    input_variable = dspy.InputField(desc="The name of the input variable")
    previous_prompt = dspy.InputField(desc="The previous prompt")
    prompt = dspy.OutputField(desc="The proposed prompt")

class BasicCompilePromptWithExamples(dspy.Signature):
    """You are a prompt writer for large language models. I will give you a task description, and a list of requirements that the large language model must satisfy when performing the task.
I will also provide you with some positive ``examples`` of the expected inputs and outputs for this task, as well as some negative ``examples`` that the model should avoid. You can incorporate these examples in your prompt.

Your task is to propose a prompt will lead a good language model to perform the task well and meet all the requirements. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(desc="A list of requirements that the prompt should include")
    incorrect_examples = dspy.InputField(desc="A list of incorrect examples")
    prompt = dspy.OutputField(desc="The proposed prompt")

class RefinePromptWithFeedback(dspy.Signature):
    """You are a prompt re-writer for large language models. I will give you a task description, a list of requirements that the large language model must satisfy when performing the task, and a prompt that was previously used for the task. I will also provide you with some feedback on the previous prompt.

Your task is to propose a new prompt will lead a good language model to perform the task well, meet all the requirements, and incorporate the feedback. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(desc="A list of requirements that the prompt should include")
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

class ConvertFeedbackToRequirement(dspy.Signature):
    """Convert user feedback to a new requirement that an LLM should satisfy."""

    task_description = dspy.InputField(desc="Description of the task")
    existing_requirements = dspy.InputField(format=dsp.passages2text, desc="A list of existing requirements")
    feedback = dspy.InputField(desc="User feedback on concrete model observations")
    requirement = dspy.OutputField(desc="A new requirement for the prompt.")