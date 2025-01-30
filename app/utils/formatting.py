import re

def format_ai_message(message):
    """
    Formats AI messages by converting markdown-style syntax to HTML.
    Supports:
    - **text** for bold
    - *text* for italic
    - __text__ for underline
    - `text` for inline code
    - ```text``` for code blocks
    """
    formatting_rules = [
        (r'\*\*(.*?)\*\*', '<b>\\1</b>'),       # Bold
        (r'\*(.*?)\*', '<i>\\1</i>'),           # Italic
        (r'__(.*?)__', '<u>\\1</u>'),           # Underline
        (r'```(.*?)```', '<pre>\\1</pre>'),     # Code block
        (r'`(.*?)`', '<code>\\1</code>')        # Inline code
    ]
    
    formatted_message = message
    for pattern, replacement in formatting_rules:
        formatted_message = re.sub(pattern, replacement, formatted_message, flags=re.DOTALL)
    
    return formatted_message
