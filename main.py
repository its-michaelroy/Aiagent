import sys
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import schema_get_file_content, get_file_content
from functions.write_file_content import schema_write_file, write_file
from functions.run_python import schema_run_python_file, run_python_file

# System prompt that sets the behavior of the AI
system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

# Available functions for the LLM to use
available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file,
    ]
)

# Dictionary mapping function names to actual functions
function_map = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "write_file": write_file,
    "run_python_file": run_python_file,
}


def call_function(function_call_part, verbose=False):
    """
    Handle calling one of our four functions based on the LLM's request.

    Args:
        function_call_part: types.FunctionCall with .name and .args properties
        verbose: Whether to print detailed information

    Returns:
        types.Content with the function result
    """
    function_name = function_call_part.name
    function_args = dict(function_call_part.args)

    if verbose:
        print(f"Calling function: {function_name}({function_args})")
    else:
        print(f" - Calling function: {function_name}")

    # Check if function exists
    if function_name not in function_map:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    # Add the working directory to the arguments
    function_args["working_directory"] = "./calculator"

    # Call the function
    try:
        function_result = function_map[function_name](**function_args)
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"result": function_result},
                )
            ],
        )
    except Exception as e:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Error calling function: {e}"},
                )
            ],
        )


def main():
    load_dotenv()

    verbose = "--verbose" in sys.argv
    args = []
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            args.append(arg)

    if not args:
        print("AI Code Assistant")
        print('\nUsage: python main.py "your prompt here" [--verbose]')
        print('Example: python main.py "How do I build a calculator app?"')
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    user_prompt = " ".join(args)

    if verbose:
        print(f"User prompt: {user_prompt}\n")

    messages = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)]),
    ]

    generate_content(client, messages, verbose)


def generate_content(client, messages, verbose):
    """
    Agent loop that calls the LLM repeatedly until it provides a final response.
    """
    max_iterations = 20

    for iteration in range(max_iterations):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=messages,
                config=types.GenerateContentConfig(
                    tools=[available_functions],
                    system_instruction=system_prompt
                ),
            )

            if verbose:
                print(f"Iteration {iteration + 1}:")
                print("Prompt tokens:", response.usage_metadata.prompt_token_count)
                print("Response tokens:", response.usage_metadata.candidates_token_count)

            # Add the model's response to the conversation
            if response.candidates and response.candidates[0].content:
                messages.append(response.candidates[0].content)

            # Check if the response contains function calls or text
            has_function_calls = False
            has_text_response = False

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        function_call_part = part.function_call
                        function_call_result = call_function(function_call_part, verbose)

                        # Check if we got a valid function response
                        if not function_call_result.parts or not hasattr(function_call_result.parts[0], 'function_response'):
                            raise Exception("Invalid function call result format")

                        # Add the function result to the conversation
                        messages.append(function_call_result)

                        if verbose:
                            print(f"-> {function_call_result.parts[0].function_response.response}")

                    elif hasattr(part, 'text') and part.text:
                        has_text_response = True
                        if verbose:
                            print("Model response:")
                            print(part.text)

            # If there's a text response and no function calls, we're done
            if has_text_response and not has_function_calls:
                print("Final response:")
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(part.text)
                else:
                    print(response.text)
                break

            # If we only have function calls, continue the loop
            if has_function_calls and not has_text_response:
                continue

            # If we have both function calls and text, continue (the model might want to do more)
            if has_function_calls and has_text_response:
                continue

            # If we don't have any meaningful response, something went wrong
            if not has_function_calls and not has_text_response:
                print("No meaningful response from the model.")
                break

        except Exception as e:
            print(f"Error in iteration {iteration + 1}: {e}")
            break

    else:
        print("Reached maximum iterations (20). Agent may be stuck in a loop.")


if __name__ == "__main__":
    main()
