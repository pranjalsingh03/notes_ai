import json
import re

def parse_json_response(response):
    if not isinstance(response, str):
        return response
    
    if not response:
        return None
    
    # Function to extract content between triple backticks
    def extract_content_between_triple_backquotes(text):
        pattern = r'```(.*?)```'
        return re.findall(pattern, text, re.DOTALL)
    
    # Function for safe JSON parsing
    def safe_json_parse(json_string, default_value):
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            return default_value
    
    # Remove 'json' prefix if present
    response = response.replace('json', '', 1)
    
    # Try to extract JSON from triple backticks
    extracted_json = extract_content_between_triple_backquotes(response)
    if extracted_json:
        return safe_json_parse(extracted_json[0], None)
    
    # If response starts with 'json', parse the trimmed string
    if response.lstrip().startswith('json'):
        return safe_json_parse(response.replace('json', '', 1).strip(), None)
    
    # Otherwise, try to parse the entire response as JSON
    return safe_json_parse(response, None)