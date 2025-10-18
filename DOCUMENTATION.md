# Course Documentation

## Architecture Overview

This course follows a modular architecture where each module builds on previous concepts while introducing new capabilities. The progression is designed to take you from basic prompt chaining to sophisticated multi-agent systems.

### Design Principles

1. **Modularity**: Each module is self-contained and can be studied independently
2. **Progressive Complexity**: Concepts build from simple to complex
3. **Practical Focus**: All examples are runnable and demonstrate real patterns
4. **Production-Ready**: Patterns can be adapted for real-world applications

## Module Breakdown

### Module 1: Basic Prompt Chaining

**File:** `src/module1_prompt_chaining/basic_chain.py`

**Core Concept:** Sequential processing where output from one LLM call feeds into the next.

**Key Classes:**
- `PromptChain`: Main class for executing prompt chains

**Key Methods:**
- `simple_chain()`: 3-step chain (summarize → extract → generate)
- `conditional_chain()`: Chain with branching logic based on analysis

**When to Use:**
- Processing text through multiple transformation steps
- Building context progressively
- Implementing decision trees based on LLM outputs

**Example Use Cases:**
- Document summarization pipeline
- Content analysis and recommendation
- Multi-step reasoning tasks

### Module 2: Tool Use and Function Calling

**File:** `src/module2_tool_use/function_calling.py`

**Core Concept:** Enabling agents to use external tools via OpenAI's function calling API.

**Key Classes:**
- `ToolAgent`: Agent that can call external functions

**Built-in Tools:**
- `get_current_time()`: Get current UTC time
- `calculate()`: Perform mathematical operations
- `search_database()`: Query a mock database

**Key Methods:**
- `run()`: Execute agent with automatic tool selection
- `execute_function()`: Execute a specific tool

**When to Use:**
- Agents need access to real-time data
- Calculations or data transformations required
- Integration with external APIs or databases

**Example Use Cases:**
- Calendar and scheduling assistants
- Data analysis agents
- API integration bots

**Adding Custom Tools:**

```python
# 1. Define your tool function
def my_tool(param1: str, param2: int) -> str:
    """Your tool implementation"""
    return result

# 2. Add tool schema
tool_schema = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "What this tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of param1"
                },
                "param2": {
                    "type": "number",
                    "description": "Description of param2"
                }
            },
            "required": ["param1", "param2"]
        }
    }
}

# 3. Register in ToolAgent
agent.tools.append(tool_schema)
agent.available_functions["my_tool"] = my_tool
```

### Module 3: Web Search Integration

**File:** `src/module3_web_search/web_agent.py`

**Core Concept:** Agents that can search the web and synthesize information from multiple sources.

**Key Classes:**
- `WebSearchAgent`: Agent with web search capabilities

**Key Methods:**
- `search_web()`: Perform web search (currently mock, replace with real API)
- `fetch_page_content()`: Extract text from webpages
- `summarize_content()`: Summarize web content with LLM
- `research_topic()`: Multi-source research and synthesis
- `answer_with_search()`: Answer questions using web search

**When to Use:**
- Need real-time or current information
- Research across multiple sources
- Fact-checking and verification

**Example Use Cases:**
- Research assistants
- News aggregation and summarization
- Competitive intelligence gathering

**Production Integration:**

Replace the mock `search_web()` with real APIs:
- Google Custom Search API
- Bing Search API
- SerpAPI
- DuckDuckGo API

```python
import requests

def search_web_real(query: str, num_results: int = 3):
    # Example with SerpAPI
    api_key = os.getenv("SERPAPI_KEY")
    params = {
        "q": query,
        "num": num_results,
        "api_key": api_key
    }
    response = requests.get("https://serpapi.com/search", params=params)
    return response.json()["organic_results"]
```

### Module 4: Agent Orchestration

**File:** `src/module4_agent_orchestration/orchestrator.py`

**Core Concept:** Coordinating multiple specialized agents to complete complex tasks.

**Key Classes:**
- `Agent`: Base agent with specific role
- `Orchestrator`: Coordinates multiple agents
- `Task`: Represents a task with dependencies
- `AgentRole`: Enum of available roles

**Agent Roles:**
- `COORDINATOR`: Plans and synthesizes
- `RESEARCHER`: Gathers information
- `ANALYST`: Analyzes data
- `WRITER`: Creates content
- `REVIEWER`: Reviews and critiques

**Key Methods:**
- `plan_tasks()`: Break down objective into tasks
- `execute_tasks()`: Execute tasks respecting dependencies
- `execute_objective()`: End-to-end planning and execution

**When to Use:**
- Complex multi-step tasks
- Need for specialized expertise
- Tasks with dependencies

**Example Use Cases:**
- Content creation pipelines
- Research and analysis workflows
- Project planning and execution

**Task Dependencies:**

Tasks can depend on other tasks:
```python
task1 = Task(id="task_1", description="Research topic", assigned_to=AgentRole.RESEARCHER)
task2 = Task(id="task_2", description="Analyze findings", assigned_to=AgentRole.ANALYST, dependencies=["task_1"])
task3 = Task(id="task_3", description="Write report", assigned_to=AgentRole.WRITER, dependencies=["task_2"])
```

### Module 5: Advanced Multi-Agent Systems

**File:** `src/module5_advanced_agents/multi_agent.py`

**Core Concept:** Sophisticated patterns for agent collaboration, debate, and hierarchy.

**Key Classes:**
- `CollaborativeAgent`: Agent that collaborates through discussion
- `DebateSystem`: Agents debate and reach consensus
- `HierarchicalAgentSystem`: Manager-worker hierarchy
- `Message`: Communication between agents

**Key Methods:**

**DebateSystem:**
- `add_agent()`: Add agent to debate
- `conduct_debate()`: Run multi-round debate
- `_synthesize_consensus()`: Create consensus from positions

**HierarchicalAgentSystem:**
- `set_manager()`: Set the manager agent
- `add_worker()`: Add worker agents
- `solve_problem()`: Manager delegates to workers

**When to Use:**
- Need multiple perspectives
- Complex problem-solving
- Quality through debate/review
- Hierarchical task delegation

**Example Use Cases:**
- Decision support systems
- Creative brainstorming
- Quality assurance workflows
- Strategic planning

## Utility Modules

### Configuration (`src/utils/config.py`)

**Functions:**
- `get_openai_client()`: Get configured OpenAI client
- `get_model_name()`: Get model from environment
- `get_temperature()`: Get temperature setting

### Logging (`src/utils/logger.py`)

**Functions:**
- `setup_logger()`: Create configured logger

**Usage:**
```python
from src.utils import setup_logger

logger = setup_logger(__name__)
logger.info("Information message")
logger.error("Error message")
```

## Examples

### Research Assistant (`examples/research_assistant.py`)

**Combines:**
- Module 2 (Tool Use)
- Module 3 (Web Search)
- Module 4 (Orchestration)

**Demonstrates:**
- Multi-module integration
- Complex workflow orchestration
- Research pipeline

### Customer Support (`examples/customer_support.py`)

**Combines:**
- Module 1 (Prompt Chaining)
- Module 2 (Tool Use)

**Demonstrates:**
- Query classification
- Knowledge base search
- Response generation
- Escalation logic

## Best Practices

### 1. Error Handling

Always wrap API calls in try-except:
```python
try:
    response = client.chat.completions.create(...)
except Exception as e:
    logger.error(f"Error: {e}")
    # Handle appropriately
```

### 2. Cost Management

- Use `gpt-4o-mini` for development
- Monitor token usage
- Cache results when possible
- Set max_tokens to limit costs

### 3. Temperature Settings

- **0.0-0.3**: Focused, deterministic (classifications, extraction)
- **0.4-0.7**: Balanced (general use)
- **0.8-1.0**: Creative (brainstorming, varied output)

### 4. Prompt Design

- Be specific and clear
- Provide examples when helpful
- Use structured output formats
- Include role/persona for context

### 5. Testing

- Test with mock data first
- Validate outputs
- Handle edge cases
- Monitor rate limits

## Performance Optimization

### Parallel Execution

For independent tasks, execute in parallel:
```python
import asyncio

async def parallel_execution(tasks):
    results = await asyncio.gather(*[
        execute_task(task) for task in tasks
    ])
    return results
```

### Caching

Cache repeated queries:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_llm_call(prompt: str) -> str:
    # LLM call here
    pass
```

### Batching

Batch similar operations:
```python
# Instead of multiple calls
for item in items:
    result = process(item)

# Batch process
batch_prompt = f"Process these items:\n{items}"
results = process_batch(batch_prompt)
```

## Security Considerations

1. **API Keys**: Never commit `.env` to version control
2. **Input Validation**: Validate user inputs before processing
3. **Output Filtering**: Filter sensitive information from outputs
4. **Rate Limiting**: Implement rate limiting for user-facing applications
5. **Error Messages**: Don't expose internal errors to users

## Deployment

### Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `OPENAI_MODEL`: Model to use (default: gpt-4o-mini)
- `TEMPERATURE`: Generation temperature (default: 0.7)

### Docker Deployment

Example `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "your_module"]
```

## Troubleshooting

### Common Issues

**Import Errors:**
- Ensure you're in the repository root
- Activate virtual environment
- Install requirements

**API Errors:**
- Check API key is set correctly
- Verify internet connection
- Check rate limits

**Unexpected Outputs:**
- Adjust temperature
- Refine prompts
- Check model version

## Contributing

To contribute new modules or examples:

1. Follow existing code structure
2. Include docstrings
3. Add examples
4. Update documentation
5. Test thoroughly

## Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [Best Practices](https://platform.openai.com/docs/guides/production-best-practices)

## License

MIT License - See LICENSE file for details.
