from functions.write_file_content import write_file
from functions.run_python import run_python_file


def test():
    # Test write_file function
    print("=== Testing write_file function ===")
    result = write_file("calculator", "lorem.txt", "wait, this isn't lorem ipsum")
    print(result)

    result = write_file("calculator", "pkg/morelorem.txt", "lorem ipsum dolor sit amet")
    print(result)

    result = write_file("calculator", "/tmp/temp.txt", "this should not be allowed")
    print(result)
    
    # Test run_python_file function
    print("\n=== Testing run_python_file function ===")
    
    print("1. Running calculator main.py (should print usage instructions):")
    result = run_python_file("calculator", "main.py")
    print(result)
    print()
    
    print("2. Running calculator main.py with args ['3 + 5']:")
    result = run_python_file("calculator", "main.py", ["3 + 5"])
    print(result)
    print()
    
    print("3. Running calculator tests.py:")
    result = run_python_file("calculator", "tests.py")
    print(result)
    print()
    
    print("4. Attempting to run ../main.py (should return error):")
    result = run_python_file("calculator", "../main.py")
    print(result)
    print()
    
    print("5. Attempting to run nonexistent.py (should return error):")
    result = run_python_file("calculator", "nonexistent.py")
    print(result)
    print()


if __name__ == "__main__":
    test()
