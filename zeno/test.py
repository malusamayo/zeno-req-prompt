import re

# Regex pattern to find text not within <req name="{requirement_name}">...</req> tags
pattern = re.compile(r'(<req name=".*?">.*?</req>)|([^<]+)')

# Function to wrap non-<req> text with <text> tags
def wrap_non_req_text(match):
    if match.group(2):  # This is the text outside <req> tags
        return f'<text>{match.group(2).strip()}</text>'
    return match.group(1)  # This is a <req> tag, return it unchanged

# Apply the wrapping
wrapped_prompt = pattern.sub(wrap_non_req_text, 'aanjnxakacoddsfvsv<req name="sdncujisd">HIHIHIHIHIH</req>aanjnxakacoddsfvsv<req name="sdncujisd">HIHIHIHIHIH</req>aanjnxakacoddsfvsv')

print("Wrapped prompt with <text> tags:", wrapped_prompt)