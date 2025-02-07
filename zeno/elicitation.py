import dspy
import os
import copy
import dspy.predict
import litellm
import json
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import pickle
import tqdm
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .textgrad_optimizer import TextGradOptimizer

class JustifyResponseAndExtractRequirements(dspy.Signature):
    """You are an LLM working on a user-given task. First, provide justification for the model output you produce. The justification should explain why the model output is appropriate for the given task. 
Then extract task-level requirements for the task based on the justification. Make sure the requirements are task-level and not specific to the given example."""

    task_description = dspy.InputField(desc="Description of the task")
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    justification: str = dspy.OutputField(desc="Justification for producing the model output")
    requirements: List[str] = dspy.OutputField(desc="Task-level requirements.")

class CritiqueResponseAndSuggestRequirements(dspy.Signature):
    """You are an experienced requirement engineer for an LLM application. Given the task description, model input, model output, first critique the model output, then suggest additional requirements for the task.
The suggested requirements should be applicable beyond the specific example provided."""

    task_description = dspy.InputField(desc="Description of the task")
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    critique: str = dspy.OutputField(desc="Critique of the model output")
    suggested_requirements: List[str] = dspy.OutputField(desc="Suggested additional requirement for the LLM")

class ClassifyRequirement(dspy.Signature):
    """Classify whether the requirement contains example-specific information. Example-specific information is information that is specific to the given example and not generalizable to other examples. This is in contrast to task-level requirements, which are generalizable to other examples."""

    task_description = dspy.InputField(desc="Description of the task")
    model_input = dspy.InputField(desc="The model input")
    requirement = dspy.InputField(desc="The requirement")
    input_specific: bool = dspy.OutputField(desc="Whether the requirement contains example-specific information.")

class GroupRequirements(dspy.Signature):
    """Group requirements into different clusters. Make sure that all provided requirements are put into one of the clusters."""

    task_description = dspy.InputField(desc="Description of the task")
    requirements = dspy.InputField(desc="List of requirements")
    groups: Dict[str, List[str]] = dspy.OutputField(desc="Grouped requirements")

# class GenerateEvaluationPlan(dspy.Signature):
#     """You are a reviewer who is evaluating a model output. Given a task description and a requirement, generate a step-by-step evaluation plan."""

#     task_description = dspy.InputField(desc="Description of the task")
#     requirement = dspy.InputField(desc="The requirement")
#     evaluation_plan = dspy.OutputField(desc="Evaluation plan for the requirement")

class EvaluateRequirement(dspy.Signature):
    """You are a reviewer who is evaluating whether a model output satisfies the given requirement. 
    Given a task description, model input, model output, and requirement, first generate a step-by-step evaluation plan for the requirement, then execute the evaluation plan to evaluate if the model output meets the requirement."""
    
    task_description = dspy.InputField(desc="Description of the task")
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    requirement = dspy.InputField(desc="The requirement to evaluate")
    evaluation_plan: str = dspy.OutputField(desc="The evaluation plan for the requirement")
    plan_execution: str = dspy.OutputField(desc="The execution of the evaluation plan")
    meets_requirement: bool = dspy.OutputField(desc="Whether the model output meets the requirement, True or False")

class EvaluateGuideline(dspy.Signature):
    """You are a reviewer who is evaluating whether a model output satisfies the given guideline.
Given a task description, model input, model output, and guideline, first evaluate the model output using the requirements in the guideline one by one. For each requirement in the guideline, do the evaluation step-by-step. 
Then, calculate an overall score for how many requirements the model output satisfies."""

    task_description: str = dspy.InputField(desc="Description of the task")
    model_input: str = dspy.InputField(desc="The model input")
    model_output: str = dspy.InputField(desc="The model output")
    guideline: List[str] = dspy.InputField(desc="The guideline for evaluation")
    evaluation_execution: str = dspy.OutputField(desc="The execution of the evaluation guideline")
    score: int = dspy.OutputField(desc="A score indicating how many requirements in the guideline the model output satisfies")

class IdentifyMistakes(dspy.Signature):
    """You are a reviewer who is evaluating whether a model output satisfies the given guideline.
Given a task description, model input, model output, and guideline, first evaluate the model output using the requirements in the guideline one by one to identify mistakes. For each requirement in the guideline, do the evaluation step-by-step. 
Then, list all requirements that the model output does not satisfy."""

    task_description: str = dspy.InputField(desc="Description of the task")
    model_input: str = dspy.InputField(desc="The model input")
    model_output: str = dspy.InputField(desc="The model output")
    guideline: List[str] = dspy.InputField(desc="The guideline for evaluation")
    evaluation_execution: str = dspy.OutputField(desc="The execution of the evaluation guideline")
    unsatisfied_requirements: List[str] = dspy.OutputField(desc="A list of requirements that the model output does not satisfy")

class CompareModelOutputsWithGuideline(dspy.Signature):
    """You are a reviewer who is comparing two model outputs to determine which one better satisfies the given guideline.
Given a task description, two model outputs, and a guideline, evaluate each model output using the requirements in the guideline one by one. For each requirement in the guideline, do the evaluation step-by-step.
Then, compare the two model outputs based on how many requirements each output satisfies."""

    task_description: str = dspy.InputField(desc="Description of the task")
    model_input: str = dspy.InputField(desc="The model input")
    model_output_a: str = dspy.InputField(desc="The first model output")
    model_output_b: str = dspy.InputField(desc="The second model output")
    guideline: List[str] = dspy.InputField(desc="The guideline for evaluation")
    execution_a: str = dspy.OutputField(desc="The execution of the evaluation of the first model output")
    execution_b: str = dspy.OutputField(desc="The execution of the evaluation of the second model output")
    reasoning: str = dspy.OutputField(desc="The reasoning for the comparison")
    better_output: str = dspy.OutputField(desc="The model output that better satisfies the guideline, either 'A' or 'B', or 'tie' if they are equal")

class RefineResponseWithFeedback(dspy.Signature):
    """Given the task description, model input, model output, and feedback, refine the model output based on the feedback."""

    task_description = dspy.InputField(desc="Description of the task")
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    feedback = dspy.InputField(desc="Feedback on the model output")
    refined_output: str = dspy.OutputField(desc="Refined model output based on the feedback")


class RefinePromptWithFeedback(dspy.Signature):
    """You are a prompt re-writer for large language models. I will give you a task description, and a prompt that is used to generate the model output. 
Your task is to refine the prompt based on the feedback provided. The refined prompt should lead a good language model to perform the task well and meet the requirement. Don't be afraid to be creative."""

    task_description = dspy.InputField(desc="Description of the task")
    previous_prompt = dspy.InputField(desc="The previous prompt")
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    requirement = dspy.InputField(desc="The requirement")
    feedback = dspy.InputField(desc="Feedback on the model output")
    prompt = dspy.OutputField(desc="The proposed prompt")

class BrainstormRequirements(dspy.Signature):
    """Given a task description, brainstorm a list of requirements that a model output should satisfy when performing the task."""

    task_description: str = dspy.InputField(desc="Description of the task")
    n: int = dspy.InputField(desc="Number of requirements to brainstorm")
    requirements: List[str] = dspy.OutputField(desc="A list of requirements")

class SuggestDesignDecisions(dspy.Signature):
    """You are a developer working on LLM application. Given a task description, suggest potential design choices to make for model's outputs."""

    task_description: str = dspy.InputField(desc="Description of the task")
    n: int = dspy.InputField(desc="Number of design chocies to suggest")
    design_choices: List[str] = dspy.OutputField(desc="A list of suggested design chocies")

# class AnalyzeDesignDecision(dspy.Signature):
#     """Given a task description, design choice, and model input and output, analyze the implicit design decision in the model's output."""

#     task_description = dspy.InputField(desc="Description of the task")
#     design_choice = dspy.InputField(desc="The design choice to analyze")
#     input: str = dspy.InputField(desc="The input to the model")
#     output: str = dspy.InputField(desc="The output of the model")
#     design_decision = dspy.OutputField(desc="The implicit design decision in the model's output")

# class CompareDesignDecision(dspy.Signature):
#     """Given a task description, design choice, and model input and output, compare two design decisions to determine if they are different."""

#     task_description = dspy.InputField(desc="Description of the task")
#     design_choice = dspy.InputField(desc="The design choice to compare")
#     design_decision_a = dspy.InputField(desc="The first design decision to compare")
#     design_decision_b = dspy.InputField(desc="The second design decision to compare")
#     is_different: bool = dspy.OutputField(desc="Whether the two design decisions are different")

# class SynthesizeInput(dspy.Signature):
#     """Given a task description, synthesize a list of inputs."""

#     task_description = dspy.InputField(desc="Description of the task")
#     input: str = dspy.InputField(desc="The input to the model")
#     output: str = dspy.InputField(desc="The output of the model")
#     n: int = dspy.InputField(desc="Number of input examples to synthesize")
#     input_examples: List[str] = dspy.OutputField(desc="A list of synthesized input examples")

def use_lm(lm):
    def decorator(program):
        def wrapper(*args, **kwargs):
            with dspy.context(lm=lm):
                return program(*args, **kwargs)
        return wrapper
    return decorator

def batch_inference(program, args_list) -> List[Any]:
    futures = {}
    results = [None] * len(args_list)
    
    with ThreadPoolExecutor(max_workers=64) as executor:
        for i, args in enumerate(args_list):
            future = executor.submit(
                program,
                **args
            )
            futures[future] = i

        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            index = futures[future]
            results[index] = result
    return results

def run_model(program, examples):
    examples = copy.deepcopy(examples)
    results = batch_inference(
        program,
        [example.inputs().toDict() for example in examples]
    )
    for example, result in zip(examples, results):
        example.output = result.output
    return examples

class InferRequirementsFromTask(dspy.Module):

    def __init__(self, task_description):
        self.lm = dspy.LM('openai/gpt-4o-2024-08-06')
        self.task_description = task_description
        self.suggest = use_lm(self.lm)(dspy.Predict(BrainstormRequirements))
    
    def forward(self, n=10):
        return self.suggest(task_description=self.task_description, n=n).requirements
    

class InferRequirementsFromData(dspy.Module):

    def __init__(self, task_description):
        self.lm = dspy.LM('openai/gpt-4o-2024-08-06')
        self.judge_lm = dspy.LM('openai/gpt-4o-mini-2024-07-18')
        self.task_description = task_description
        self.extract = use_lm(self.lm)(dspy.Predict(JustifyResponseAndExtractRequirements))
        self.suggest = use_lm(self.lm)(dspy.Predict(CritiqueResponseAndSuggestRequirements))
        self.classify = use_lm(self.judge_lm)(dspy.ChainOfThought(ClassifyRequirement))
        self.group = use_lm(self.lm)(dspy.Predict(GroupRequirements))


    def forward(self, examples, n=10):
        
        results = batch_inference(self.suggest, [
            {"task_description": self.task_description, 
             "model_input": example.inputs().toDict(), 
             "model_output": example.output} for example in examples
        ])

        for example, result in zip(examples, results):
            example.critique, example.requirements = result.critique, result.suggested_requirements
            
        all_requirements = [req for example in examples for req in example.requirements]

        # arg_list = [{
        #     "task_description": self.task_description, 
        #     "model_input": getattr(example, self.input_variable),
        #     "requirement": requirement
        # } for example in examples for requirement in example.requirements]

        # results = batch_inference(self.classify, arg_list)
        # # filter out example-specific requirements
        # filtered_requirements = []
        # accum = 0
        # for i, example in enumerate(examples):
        #     example.requirements = [req for j, req in enumerate(example.requirements) if not results[accum + j].input_specific]
        #     accum += len(example.requirements)
        #     filtered_requirements.extend(example.requirements)

        # grouped_requirements = self.group(task_description=self.task_description, requirements=all_requirements).groups
        
        return all_requirements
        
class InferRequirements(dspy.Module):

    def __init__(self, task_description):
        self.lm = dspy.LM('openai/gpt-4o-2024-08-06')
        self.task_description = task_description
        self.suggest = use_lm(self.lm)(dspy.Predict(BrainstormRequirements))
        self.identify = use_lm(self.lm)(dspy.Predict(IdentifyMistakes))
    
    def forward(self, examples, n=10):
        requirements = self.suggest(task_description=self.task_description, n=n).requirements
        requirements_unsat_result = {
            requirement: [] for requirement in requirements
        }
        arg_list = [{
            "task_description": self.task_description, 
            "model_input": example.inputs().toDict(),
            "model_output": example.output,
            "guideline": requirements
        } for example in examples]
        results = batch_inference(self.identify, arg_list)
        for example, result in zip(examples, results):
            for requirement in result.unsatisfied_requirements:
                if requirement not in requirements_unsat_result:
                    requirements_unsat_result[requirement] = []
                requirements_unsat_result[requirement].append({
                    "input": example.inputs().toDict(),
                    "output": example.output,
                    "execution": result.evaluation_execution,
                })
        # sort the requirements by the number of examples that don't meet them
        requirements_unsat_result = {k: v for k, v in sorted(requirements_unsat_result.items(), key=lambda item: len(item[1]), reverse=True)}
        return requirements_unsat_result
    

class LLMJudge(dspy.Module):
    def __init__(self, task_description, input_variable, judge_lm=None):
        if judge_lm is None:
            self.judge_lm = dspy.LM('openai/o3-mini', temperature=1.0, max_tokens=10000)
            self.judge_lm.kwargs['max_completion_tokens'] = self.judge_lm.kwargs.pop('max_tokens')
        else:
            self.judge_lm = judge_lm
        self.task_description = task_description
        self.input_variable = input_variable
        self.evaluator = use_lm(self.judge_lm)(dspy.Predict(EvaluateRequirement))
        self.aggregate_evaluator = use_lm(self.judge_lm)(dspy.Predict(EvaluateGuideline))
        self.compare_evaluator = use_lm(self.judge_lm)(dspy.Predict(CompareModelOutputsWithGuideline))

    def evaluate_requirement(self, example, requirement):
        return self.evaluator(task_description=self.task_description, 
                            model_input=getattr(example, self.input_variable), 
                            model_output=example.output, 
                            requirement=requirement)
    
    def evaluate_guideline(self, example, guideline):
        return self.aggregate_evaluator(task_description=self.task_description, 
                            model_input=getattr(example, self.input_variable), 
                            model_output=example.output, 
                            guideline=guideline)
    
    def compare_outputs(self, example_a, example_b, guideline):
        return self.compare_evaluator(task_description=self.task_description, 
                            model_input=getattr(example_a, self.input_variable), 
                            model_output_a=example_a.output, 
                            model_output_b=example_b.output, 
                            guideline=guideline)
    
    def compare(self, examples_a, examples_b, requirements):
        def random_permute(example_a, example_b):
            if np.random.rand() > 0.5:
                return example_a, example_b, 0
            else:
                return example_b, example_a, 1
        
        np.random.seed(42)
        permuations = [random_permute(example_a, example_b) for example_a, example_b in zip(examples_a, examples_b)]

        results = batch_inference(
            self.compare_outputs,
            [{"example_a": example_a, "example_b": example_b, "guideline": requirements} for example_a, example_b, _ in permuations]
        )
        # calculate win rate, mapping permutations back
        win_rate_A = sum([(result.better_output == 'A' and not is_permutated) or (result.better_output == 'B' and is_permutated) 
                            for result, (_, _, is_permutated) in zip(results, permuations)]) / len(results)
        win_rate_B = sum([(result.better_output == 'B' and not is_permutated) or (result.better_output == 'A' and is_permutated)
                            for result, (_, _, is_permutated) in zip(results, permuations)]) / len(results)
        print(f"Win rate for A: {win_rate_A}")
        print(f"Win rate for B: {win_rate_B}")

        eval_results = []
        for result, (example_a, example_b, is_permutated) in zip(results, permuations):
            eval_results.append({
                "input": getattr(example_a, self.input_variable),
                "output_a": example_a.output,
                "output_b": example_b.output,
                "permutated": is_permutated,
                "execution_a": result.execution_a,
                "execution_b": result.execution_b,
                "reasoning": result.reasoning,
                "better_output": result.better_output,
            }) 

        return eval_results

    def forward(self, examples, requirements, aggregate=False):
        if aggregate:        
            results = batch_inference(
                self.evaluate_guideline,
                [{"example": example, "guideline": requirements} for example in examples]
            )
            for example, result in zip(examples, results):
                example.evaluation_result = {
                    # "evaluation_plan": result.evaluation_plan,
                    # "plan_execution": result.plan_execution,
                    "evaluation_execution": result.evaluation_execution,
                    "score": result.score
                }
        
        else:
            results = batch_inference(
                self.evaluate_requirement,
                [{"example": example, "requirement": requirement} for requirement in requirements for example in examples]
            )
            
            for i, result in enumerate(results):
                requirement_id = i // len(examples)
                example_id = i % len(examples)
                # create the requirements field if it doesn't exist
                if not hasattr(examples[example_id], "requirements"):
                    examples[example_id].requirements = []
                examples[example_id].requirements.append({
                    "requirement": requirements[requirement_id],
                    "evaluation_plan": result.evaluation_plan,
                    "plan_execution": result.plan_execution,
                    "meets_requirement": result.meets_requirement
                })

        return examples

    def evaluate(self, examples, requirements, program=None, aggregate=False):
        examples = copy.deepcopy(examples)

        # run the program to generate the output if provided
        if program is not None:
            results = batch_inference(
                program,
                [example.inputs().toDict() for example in examples]
            )
            for example, result in zip(examples, results):
                example.output = result.output

        if aggregate:
            evaluate_examples = self.forward(examples, requirements, aggregate=aggregate)
            print(f"Average score: {sum([example.evaluation_result['score'] for example in evaluate_examples]) / len(evaluate_examples)}")
        else:
            evaluate_examples = self.forward(examples, requirements)
            pass_rates = []
            for i, requirement in enumerate(requirements):
                print(f"Requirement: {requirement}")
                pass_rate = sum([example.requirements[i]['meets_requirement'] for example in evaluate_examples]) / len(evaluate_examples)
                print(f"Pass rate for requirement: {pass_rate}")
                pass_rates.append(pass_rate)
            print(f"Average pass rate: {sum(pass_rates) / len(pass_rates)}")
        return evaluate_examples



class IterativeRefine(dspy.Module):

    def __init__(self, task_description, input_variable, lm, task_program):
        self.lm = lm
        self.judge_lm = dspy.LM('openai/o3-mini', temperature=1.0, max_tokens=10000)
        self.judge_lm.kwargs['max_completion_tokens'] = self.judge_lm.kwargs.pop('max_tokens')
        self.task_description = task_description
        self.input_variable = input_variable
        self.pred = use_lm(self.lm)(dspy.Predict(task_program))
        self.evaluator = use_lm(self.lm)(dspy.Predict(EvaluateRequirement))
        self.refine = use_lm(self.lm)(dspy.Predict(RefineResponseWithFeedback))
        self.prompt_refine = use_lm(self.lm)(dspy.Predict(RefinePromptWithFeedback))

    def generate_and_refine(self, example, requirement):
        # generate the response
        response = self.pred(**{self.input_variable: getattr(example, self.input_variable)}).output
        # get the feedback
        result = self.evaluator(task_description=self.task_description, model_input=getattr(example, self.input_variable), model_output=response, requirement=requirement)
        i = 0
        while not result.meets_requirement and i < 3:
            feedback = result.plan_execution
            # refine the response
            response = self.refine(task_description=self.task_description, model_input=getattr(example, self.input_variable), model_output=response, feedback=feedback).refined_output
            result = self.evaluator(task_description=self.task_description, model_input=getattr(example, self.input_variable), model_output=response, requirement=requirement)
            i += 1
        return response

    def forward(self, examples, requirement):
        results = batch_inference(
            self.generate_and_refine,
            [{"example": example, "requirement": requirement} for example in examples]
        )
        return results

def cluster_requirements(requirements, num_clusters=40):
    
    requirement_df = pd.DataFrame({"requirements": requirements})
    requirement_df['ada_embedding'] =  batch_inference(
        lambda requirement: litellm.embedding(model='openai/text-embedding-ada-002', input=[requirement]).data[0]['embedding'],
        [{"requirement": req} for req in requirements]
    )

    # cluster the requirements
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    labels = kmeans.fit_predict(np.vstack(requirement_df['ada_embedding'].to_list()))
    requirement_df['cluster'] = labels

    # remove clusters with only 1 requirements
    cluster_counts = requirement_df['cluster'].value_counts()
    clusters_to_remove = cluster_counts[cluster_counts < 2].index
    requirement_df = requirement_df[~requirement_df['cluster'].isin(clusters_to_remove)]

    # print the clusters
    for i in range(num_clusters):
        subset = requirement_df[requirement_df['cluster'] == i]['requirements']
        if len(subset) == 0:
            continue
        print(f"Cluster {i}:")
        for req in subset:
            print(f"  - {req}")
        print()
