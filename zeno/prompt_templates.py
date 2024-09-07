REQUIREMENT_OPTIMIZER_PROMPT = """You are given a requirement with the following fields: 'name', 'description', and 'evaluation_method'. 

1. If any field has an empty string ("" or ''), you MUST generate an appropriate value for that field based on the content of the 'description' or available context.
2. For fields that already have a value (i.e., they are not an empty string), DO NOT MODIFY them. Keep their content exactly as it is.
3. For the 'evaluation_method', if it is an empty string, generate a clear, step-by-step method based on the 'description' that explains how to evaluate whether the requirement is met. The evaluation method should include specific, measurable steps.

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
                    "prompt_snippet": prompt snippet
                }}
            ] 
    }}
Requirements: '''{requirements}'''
"""


REQUIREMENT_EXTRACTOR_PROMPT = """Given the following prompt, extract a series of success criteria used for evaluating the model outputs from the prompt. 
Requirements:
1. List requirements one by one in the format: 
    {{ 
        "name": "{name}", 
        "description": "{description}",
        "evaluation_method": "{evaluation_method}",
        "prompt_snippet": "{prompt_snippet}"
    }}
2. Use the exact wording from the prompt for the Prompt Snippet.
3. Only include unique criteria mentioned in the original prompt. Merge the ones that are similar. 
4. Try to make the evaluation method as clear and objective as possible and give specific steps. 
5. Be concise.
Prompt: '''{prompt}'''
Requirements:
"""