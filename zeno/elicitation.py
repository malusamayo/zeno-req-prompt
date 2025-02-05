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

from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
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
    Given a task description, model input, model output, and guideline, first generate a step-by-step evaluation plan for the guideline, then execute the evaluation plan to evaluate if the model output meets the guideline."""

    task_description = dspy.InputField(desc="Description of the task")
    model_input = dspy.InputField(desc="The model input")
    model_output = dspy.InputField(desc="The model output")
    guideline = dspy.InputField(desc="The guideline for evaluation")
    evaluation_plan: str = dspy.OutputField(desc="The evaluation plan for the guideline")
    plan_execution: str = dspy.OutputField(desc="The execution of the evaluation plan")
    score: float = dspy.OutputField(desc="A score indicating how well the model output meets the guideline from 0 to 10")


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

class SuggestDesignDecisions(dspy.Signature):
    """You are a developer working on LLM application. Given a task description, suggest potential design choices to make for model's outputs."""

    task_description = dspy.InputField(desc="Description of the task")
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

def batch_inference(program, args_list):
    completions = []
    results = []
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        for args in args_list:
            future = executor.submit(
                program,
                **args
            )
            completions.append(future)

    for completion in completions:
        result = completion.result()
        results.append(result)
    return results

class InferRequirements(dspy.Module):

    def __init__(self, task_description):
        self.lm = dspy.LM('openai/gpt-4o-2024-08-06')
        self.task_description = task_description
        self.suggest = use_lm(self.lm)(dspy.Predict(SuggestDesignDecisions))
    
    def forward(self, n=10):
        return self.suggest(task_description=self.task_description, n=n).design_choices
    

class InferRequirementsFromData(dspy.Module):

    def __init__(self, task_description, input_variable):
        self.lm = dspy.LM('openai/gpt-4o-2024-08-06')
        self.judge_lm = dspy.LM('openai/gpt-4o-mini-2024-07-18')
        self.task_description = task_description
        self.input_variable = input_variable
        self.extract = use_lm(self.lm)(dspy.Predict(JustifyResponseAndExtractRequirements))
        self.suggest = use_lm(self.lm)(dspy.Predict(CritiqueResponseAndSuggestRequirements))
        self.classify = use_lm(self.judge_lm)(dspy.ChainOfThought(ClassifyRequirement))
        self.group = use_lm(self.lm)(dspy.Predict(GroupRequirements))


    def forward(self, examples, n=10):
        
        results = batch_inference(self.suggest, [
            {"task_description": self.task_description, 
             "model_input": getattr(example, self.input_variable), 
             "model_output": example.output} for example in examples
        ])

        for example, result in zip(examples, results):
            # example.justification, example.requirements = result.justification, result.requirements
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

    def evaluate_requirement(self, example, requirement):
        return self.evaluator(task_description=self.task_description, 
                            model_input=getattr(example, self.input_variable), 
                            model_output=example.output, 
                            requirement=requirement)

    def forward(self, examples, requirements):        
        results = batch_inference(
            self.evaluate_requirement,
            [{"example": example, "requirement": requirement} for example in examples for requirement in requirements]
        )
        
        for i, result in enumerate(results):
            example_id = i // len(requirements)
            requirement_id = i % len(requirements)
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

    def evaluate(self, examples, requirements):
        evaluate_examples = self.forward(examples, requirements)
        pass_rates = []
        for i, requirement in enumerate(requirements):
            print(f"Requirement: {requirement}")
            pass_rate = sum([example.requirements[i]['meets_requirement'] for example in evaluate_examples]) / len(evaluate_examples)
            print(f"Pass rate for requirement: {pass_rate}")
            pass_rates.append(pass_rate)
        print(f"Average pass rate: {sum(pass_rates) / len(pass_rates)}")
        return pass_rates



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
