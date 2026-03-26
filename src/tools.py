from langchain.tools import tool

@tool
def add(a: float, b: float) -> float:
    """
    This function should be used to add two numbers
    """
    return a + b

@tool
def multiply(a: float, b: float) -> float:
    """
    This function should be used to multiply two numbers
    """
    return a * b

@tool
def divide(a: float, b: float) -> float:
    """
    This function should be used to divide two numbers
    """
    return a / b

@tool
def subtract(a: float, b: float) -> float:
    """
    This function should be used to subtract two numbers
    """
    return a - b