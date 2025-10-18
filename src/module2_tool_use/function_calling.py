"""
Module 2: Tool Use and Function Calling

This module demonstrates how to use OpenAI's function calling capabilities
to enable agents to use external tools and APIs.

Key Concepts:
- Function definitions and schemas
- Tool calling with OpenAI API
- Handling function execution
- Multi-turn conversations with tools
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from src.utils import get_openai_client, get_model_name, setup_logger

logger = setup_logger(__name__)


# Example tool functions
def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time in a specified timezone.
    
    Args:
        timezone: Timezone name (currently only UTC is supported)
    
    Returns:
        str: Current time in ISO format
    """
    logger.info(f"Getting current time for timezone: {timezone}")
    return datetime.utcnow().isoformat() + "Z"


def calculate(operation: str, a: float, b: float) -> float:
    """
    Perform a mathematical operation.
    
    Args:
        operation: Operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
    
    Returns:
        float: Result of the operation
    """
    logger.info(f"Calculating: {a} {operation} {b}")
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero"
    }
    
    if operation not in operations:
        return f"Error: Unknown operation {operation}"
    
    return operations[operation](a, b)


def search_database(query: str, category: str = "all") -> List[Dict[str, str]]:
    """
    Search a mock database.
    
    Args:
        query: Search query
        category: Category to search in
    
    Returns:
        List[Dict]: Search results
    """
    logger.info(f"Searching database: query='{query}', category='{category}'")
    
    # Mock database
    mock_data = [
        {"id": "1", "category": "products", "title": "AI Course", "description": "Learn AI fundamentals"},
        {"id": "2", "category": "products", "title": "Agent Workshop", "description": "Build AI agents"},
        {"id": "3", "category": "users", "title": "John Doe", "description": "Senior Developer"},
        {"id": "4", "category": "users", "title": "Jane Smith", "description": "AI Researcher"},
    ]
    
    # Filter by category
    if category != "all":
        results = [item for item in mock_data if item["category"] == category]
    else:
        results = mock_data
    
    # Filter by query
    if query:
        query_lower = query.lower()
        results = [
            item for item in results 
            if query_lower in item["title"].lower() or query_lower in item["description"].lower()
        ]
    
    return results


class ToolAgent:
    """
    An agent that can use external tools via function calling.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the tool agent.
        
        Args:
            model: OpenAI model to use
        """
        self.client = get_openai_client()
        self.model = model or get_model_name()
        
        # Define available tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current time in UTC timezone",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "The timezone (currently only UTC supported)",
                                "enum": ["UTC"]
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Perform a mathematical calculation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "The operation to perform",
                                "enum": ["add", "subtract", "multiply", "divide"]
                            },
                            "a": {
                                "type": "number",
                                "description": "The first number"
                            },
                            "b": {
                                "type": "number",
                                "description": "The second number"
                            }
                        },
                        "required": ["operation", "a", "b"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_database",
                    "description": "Search a database for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "category": {
                                "type": "string",
                                "description": "The category to search in",
                                "enum": ["all", "products", "users"]
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Map function names to actual functions
        self.available_functions = {
            "get_current_time": get_current_time,
            "calculate": calculate,
            "search_database": search_database
        }
        
        logger.info(f"Initialized ToolAgent with {len(self.tools)} tools")
    
    def execute_function(self, function_name: str, arguments: dict) -> Any:
        """
        Execute a function by name with given arguments.
        
        Args:
            function_name: Name of the function to execute
            arguments: Arguments to pass to the function
        
        Returns:
            Any: Result of the function execution
        """
        if function_name not in self.available_functions:
            raise ValueError(f"Unknown function: {function_name}")
        
        function = self.available_functions[function_name]
        return function(**arguments)
    
    def run(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Run the agent with tool use capability.
        
        Args:
            user_message: The user's message/query
            max_iterations: Maximum number of iterations to prevent infinite loops
        
        Returns:
            str: The agent's final response
        """
        logger.info(f"Running agent with message: {user_message}")
        
        messages = [{"role": "user", "content": user_message}]
        
        for iteration in range(max_iterations):
            logger.info(f"Iteration {iteration + 1}/{max_iterations}")
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            messages.append(response_message)
            
            # Check if the model wants to use tools
            if not response_message.tool_calls:
                # No more tool calls, return the final response
                logger.info("Agent finished - no more tool calls")
                return response_message.content
            
            # Process each tool call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                
                # Execute the function
                function_response = self.execute_function(function_name, function_args)
                
                # Convert response to string
                if isinstance(function_response, (list, dict)):
                    function_response_str = json.dumps(function_response)
                else:
                    function_response_str = str(function_response)
                
                logger.info(f"Tool response: {function_response_str[:100]}...")
                
                # Add function response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response_str
                })
        
        logger.warning(f"Max iterations ({max_iterations}) reached")
        return "Max iterations reached. Please try rephrasing your query."


def main():
    """Example usage of the ToolAgent class."""
    agent = ToolAgent()
    
    print("\n" + "="*60)
    print("Tool Use and Function Calling Examples")
    print("="*60)
    
    # Example 1: Simple tool use
    print("\nExample 1: Getting current time")
    print("-" * 60)
    result = agent.run("What time is it right now in UTC?")
    print(f"Response: {result}")
    
    # Example 2: Mathematical calculation
    print("\n\nExample 2: Mathematical calculation")
    print("-" * 60)
    result = agent.run("What is 234 multiplied by 567?")
    print(f"Response: {result}")
    
    # Example 3: Database search
    print("\n\nExample 3: Database search")
    print("-" * 60)
    result = agent.run("Search for AI courses in the products category")
    print(f"Response: {result}")
    
    # Example 4: Multiple tool calls
    print("\n\nExample 4: Multiple tool calls")
    print("-" * 60)
    result = agent.run(
        "First, calculate 100 divided by 4, then search for users with that result in their description"
    )
    print(f"Response: {result}")


if __name__ == "__main__":
    main()
