

import subprocess
import os
from google.genai import types


def run_python_file(working_directory, file_path, args=[]):
    """
    Execute a Python file in the specified working directory with security checks.

    Args:
        working_directory (str): The permitted working directory
        file_path (str): Path to the Python file to execute
        args (list): Additional arguments to pass to the Python script

    Returns:
        str: Output from the execution or error message
    """
    try:
        # Resolve absolute paths for comparison
        abs_working_dir = os.path.abspath(working_directory)
        abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))

        # Security check: ensure file is within working directory
        if not abs_file_path.startswith(abs_working_dir):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        # Check if file exists
        if not os.path.exists(abs_file_path):
            return f'Error: File "{file_path}" not found.'

        # Check if file is a Python file
        if not file_path.endswith('.py'):
            return f'Error: "{file_path}" is not a Python file.'

        # Prepare command
        cmd = ['python', file_path] + args

        # Execute the Python file
        completed_process = subprocess.run(
            cmd,
            cwd=abs_working_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Format output
        output_parts = []

        if completed_process.stdout:
            output_parts.append(f"STDOUT:\n{completed_process.stdout}")

        if completed_process.stderr:
            output_parts.append(f"STDERR:\n{completed_process.stderr}")

        if completed_process.returncode != 0:
            output_parts.append(f"Process exited with code {completed_process.returncode}")

        if not output_parts:
            return "No output produced."

        return "\n".join(output_parts)

    except Exception as e:
        return f"Error executing Python file: {e}"


# Schema declaration for the run_python_file function
schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file with optional arguments, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the Python file to execute, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                description="Optional arguments to pass to the Python script.",
                items=types.Schema(type=types.Type.STRING),
            ),
        },
        required=["file_path"],
    ),
)
