# AI Chatbot

## Overview
This AI chatbot project allows you to quickly deploy your AI models through modular systems. Features include conversation logging, memory retention, file attachments, and a login system using local storage for secure authentication and data management. The application is built with Flask and is easy to configure allowing quick customization of any part of the system.

## Features
- **Login System**: Secure user authentication with local storage for lightweight account management. It is configured with an SMTP server allowing for email authentication and password resetting.
- **Conversation Logging**: Saves chat history for easy reference.
- **Memory Retention**: Stores user-specific details (e.g., name, preferences) to enhance responses. Memories are either stored locally to a conversation or can be accessed throughout the application based on their value.
- **File Attachments**: Enables file sharing directly in chat for collaboration.

## Model Setup
To add models, configure them in `models.json` for dropdown selection in the application and use `models.py` to manage the logic for accessing the model via their endpoint. Examples are left inside of those scripts for further instructions.

Here is an example of a model in the 'models.json' file.
```python
{
    "name": "GPT-4o",  # Display name of the model
    "system_prompt": "You are a helpful AI assistant.",  # System prompt for the model
    "env_endpoint": "AZURE_OPENAI_ENDPOINT",  # Optional: The name of the api environment variable in the '.env' file
    "env_api_key": "AZURE_OPENAI_API_KEY",  # Optional: The name of the endpoint environment variable in the '.env' file
    "handler": "send_message_to_openai",  # Required: the name of the method handeling the endpoint of the model
    "in_use": true  # Option to display the model in the dropdown menu or not
}
```

## Getting Started
To get started with the project, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/ice-forge/ai-chatbot.git
    ```

2. Install the necessary dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up the local configuration in the `.env` file with the required veriables.
    ```
    FLASK_SECRET_KEY=your_secret_key

    SMTP_SERVER=smtp.example.com
    SMTP_PORT=587

    SMTP_EMAIL=your@email.com
    SMTP_PASSWORD=your_password
    ```

## Usage
Run the application:
```bash
python run.py
```
## Issues
This project is a prototype and still contains bugs. The following issues will be resolved soon:
- Uploading files after already being uploaded can cause the AI to loose context of the file.

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
