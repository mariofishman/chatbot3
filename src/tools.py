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


# Mock search result
search_result = """The Model Context Protocol (MCP) is an open standard protocol developed 
by Anthropic to enable seamless integration between AI models and external systems like 
tools, databases, and other services. It acts as a standardized communication layer, 
allowing AI models to access and utilize data from various sources in a consistent and 
efficient manner. Essentially, MCP simplifies the process of connecting AI assistants 
to external services by providing a unified language for data exchange. """


# Mock search tool
@tool(parse_docstring=True)
def web_search(
    query: str,
):
    """Search the web for information on a specific topic.

    This tool performs web searches and returns relevant results
    for the given query. Use this when you need to gather information from
    the internet about any topic.

    Args:
        query: The search query string. Be specific and clear about what
               information you're looking for.

    Returns:
        Search results from the search engine.

    Example:
        web_search("machine learning applications in healthcare")
    """
    return search_result