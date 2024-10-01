REQUIREMENT_OPTIMIZER_PROMPT = """You are given a requirement with the following fields: 'name', 'description', and 'evaluation_method'. 

1. If any field has an empty string ("" or ''), you MUST generate an appropriate value for that field based on the content of the 'description' or available context.
2. For fields that already have a value (i.e., they are not an empty string), DO NOT MODIFY them. Keep their content exactly as it is.
3. For the 'name' field, if it is an empty string, generate a name based on the 'description' that is concise and descriptive of the requirement. The name should be in lowercase and contain hyphens (-) instead of spaces.
4. For the 'evaluation_method', if it is an empty string, generate a clear, step-by-step method based on the 'description' that explains how to evaluate whether the requirement is met. The evaluation method should include specific, measurable steps.
5. The evaluation method must be actionable, clearly stating how the model output should be evaluated, and use yes/no questions where possible. For example, "Check if X is present in the output. If yes, return 'Yes'. If no, return 'No'."
6. Make sure the evaluation method uses simple language that GPT can follow directly.
7.Ensure each evaluation method is objective and based on measurable aspects of the output (e.g., "The answer includes the word 'X'", "The response correctly explains Y concept").
### Examples:
{{ 
    "name": "answer-length", 
    "description": "All answers must be concise, not exceeding 50 words.",
    "evaluation_method": "1.Review the answers and ensure none exceed 50 words.\n2. Flag any answers exceeding the word limit for revision.\n3. Verify that all flagged answers are revised to meet the word count requirement."
}}
{{
    "name": "factuality-check",
    "description": "Ensure all responses are factually accurate and based on reliable sources.",
    "evaluation_method": "1. Review answers for factual correctness.\n2. Flag any responses with inaccuracies or unsupported claims for revision.\n3. Verify that flagged responses have been corrected with accurate and well-supported information."
}}

Your task is to fill in **any** missing fields with appropriate content. If all fields have content, return them as is. If any field is an empty string (""), generate its value based on the requirement's description or context.

The current requirement is: 
{{ 
    "name": "{name}", 
    "description": "{description}",
    "evaluation_method": "{evaluation_method}"
}}
"""

REQUIREMENT_CREATOR_PROMPT = """You are given a user-written requirement. Based on the user's input, you need to generate a requirement with the following fields: 'name' and 'evaluation_method'.

1. For the 'name' field, generate a name based on the user input that is concise and descriptive of the requirement. The name should be in lowercase and contain hyphens (-) instead of spaces.
2. For the 'description' field, generate a description based on the 'name' that clearly explains the requirement in detail.
3. For the 'evaluation_method' field, generate a clear, step-by-step method based on the 'description' that explains how to evaluate whether the requirement is met. The evaluation method should include specific, measurable steps. (i.e., how GPT should verify if the requirement is fulfilled, step-by-step)
4. Make sure the evaluation method uses simple language that GPT can follow directly and evaluation method does not mention steps GPT cannot execute.
5. Ensure each evaluation method is objective and based on measurable aspects of the output (e.g., "The answer includes the word 'X'", "The response correctly explains Y concept").
### Examples:
Input: Answer should be concise
Output: {{ 
    "name": "answer-length", 
    "evaluation_method": "Review the answers and ensure none exceed 50 words."
}}

Input: Responses should be factually accurate
Output: {{
    "name": "factuality-check",
    "evaluation_method": "Review answers and flag any responses with inaccuracies or unsupported claims for revision."
}}

Your task is to fill in **any** missing fields with appropriate content. If all fields have content, return them as is. If any field is an empty string (""), generate its value based on the requirement's description or context.

When you create the requirement, make sure the requirement is atomic, i.e., we can not be further break it down to multiple smaller requirements.

The user input requirement is: {user_input}
"""

PROMPT_COMPILER_PROMPT = """Given the following requirements, generate a prompt that satisfies all the requirements listed. For each requirement:
1. If the requirement's prompt_snippet field is empty, generate a prompt snippet that corresponds to the requirement within the generated prompt. Use the exact wording from the generated prompt for the Prompt Snippet. The format should be (requirement_id, prompt snippet), and include it in the output array of all generated prompt snippets for requirements without existing content in the prompt_snippet field.
2. If the requirement has content in the prompt_snippet field, use the exact words from this field in the generated prompt.
3. Ensure the generated prompt addresses all the requirements.
4. The output format should be: 
    {{ 
        "prompt": generated_prompt, 
        "requirements_prompt_snippets": 
            [
                {{ 
                    "requirement_id": requirement_id, 
                    "prompt_snippet": prompt_snippet
                }}
            ] 
    }}
Requirements: {requirements}
"""


REQUIREMENT_EXTRACTOR_PROMPT = """Given the following prompt, extract a series of success criteria used for evaluating the model outputs. The success criteria should be clear, concise, and usable for automatic evaluation by a GPT model. 

Requirements:
1. List the requirements one by one in the format: 
    {{ 
        "name": name, 
        "description": description,
        "evaluation_method": evaluation_method (i.e., how GPT should verify if the requirement is fulfilled, step-by-step),
        "prompt_snippet": prompt_snippet
    }}
    
2. The evaluation method must be actionable, clearly stating how the model output should be evaluated, and use yes/no questions where possible. For example, "Check if X is present in the output. If yes, return 'Yes'. If no, return 'No'."

3. Make sure the evaluation method uses simple language that GPT can follow directly.

4. Use the exact wording from the prompt for the Prompt Snippet. 

5. Only include unique criteria from the original prompt. Combine similar ones.

6. Ensure each evaluation method is objective and based on measurable aspects of the output (e.g., "The answer includes the word 'X'", "The response correctly explains Y concept").

7. Be concise in writing the criteria and methods.

8. Requirement name should be in this format: "answer-length", "factuality-check".

Prompt: '''{prompt}'''

Requirements:
"""

REQUIREMENT_EVALUATION_PROMPT = """
Answer 1 for yes and 0 for no. 
Given the prompt '''${prompt}''' and requirement '''${requirement}''', follow the evaluation method to determine if the model output fulfills the requirement: '''${evaluation_method}'''? Give a rationale to explain your answer.
Model Output: '''${modelOutput} '''
The output format should be:
    {{ 
        "modelOutput": evaluated_model_output, 
        "pass/fail": 0 or 1
        "rationale":
    }}
"""

REQUIREMENT_SUGGESTION_PROMPT = """You are an experienced requirement engineer for an LLM application. Given current requirements and example inputs / outputs, suggest new requirements.

---
Current requirements:
{current_requirements}

---
Example input:
{input_data}

Model output:
{model_output}

---

Given the user feedback, suggest new requirements. Each new requirement should be atomic and does not overlap with existing requirements. 

Your response should be in the following JSON format:
[ 
    {{
        "name": "new requirement name", 
        "description": "new requirement description", 
        "evaluation_method": "evaluation method of the new requirement which will be executed by GPT", 
        "prompt_snippet" : "prompt implementation of the new requirement"
    }}
] 
"""

REQUIREMENT_UPDATE_PROMPT = """You are an experienced requirement engineer for an LLM application. Given user feedback on an example, update the requirements.

---
Current requirements:
{current_requirements}

---
Example input:
{input_data}

Model output:
{model_output}

User feedback:
{feedback}

---

Given the user feedback, update the requirements:
- If a new requirement should be added, provide a description of the new requirement.
- The new requirement should be atomic does not overlap with existing requirements. 

Your response should be in the following JSON format:
{{
    "actions": [
        {{"action": "add", "new_requirement": {{"name": "new requirement name", "description": "new requirement description", "evaluation_method": "evaluation method of the new requirement which will be executed by GPT", "prompt_snippet" : "prompt implementation of the new requirement"}}}}
    ]
}}  
"""

REQUIREMENT_UPDATE_REQUEST_PROMPT =  """
You are an experienced requirements engineer for an LLM application. Your task is to determine whether the name, description, and evaluation method of a given requirement are mismatched with its prompt implementation (prompt snippet).

---
**Current requirement details:**
- Name: {requirement_name}
- Description: {requirement_description}
- Evaluation method: {requirement_evaluation_method}
- Prompt implementation (prompt snippet): {requirement_prompt_snippet}

---
If you find any mismatch, update the name, description, and evaluation method so that they align with the prompt snippet implementation.

Please provide your response in the following JSON format:

{{
  "need_update": 0 or 1,
  "updated_requirement": {{
    "name": "new requirement name", 
    "description": "new requirement description", 
    "evaluation_method": "evaluation method of the new requirement, which will be executed by GPT"
  }}
}}

"""