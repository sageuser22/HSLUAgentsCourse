# HSLU Agents Course

A comprehensive repository for learning Agentic AI workflows, from basic prompt chaining to advanced multi-agent systems. This course provides hands-on examples using Python and the OpenAI API, building from fundamental concepts to sophisticated agent architectures.

## 🎯 Course Overview

This course teaches you how to build intelligent AI agents through progressively complex modules:

1. **Module 1: Basic Prompt Chaining** - Sequential LLM calls with context building
2. **Module 2: Tool Use and Function Calling** - Agents that can use external tools and APIs
3. **Module 3: Web Search Integration** - Agents with internet search capabilities
4. **Module 4: Agent Orchestration** - Coordinating multiple agents for complex tasks
5. **Module 5: Advanced Multi-Agent Systems** - Collaborative agents, debates, and hierarchies

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sageuser22/HSLUAgentsCourse.git
cd HSLUAgentsCourse
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Your `.env` file should contain:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
TEMPERATURE=0.7
```

## 📚 Module Details

### Module 1: Basic Prompt Chaining

Learn the fundamentals of chaining LLM calls together, where the output of one call becomes the input for the next.

**Key Concepts:**
- Sequential processing
- Building context across steps
- Conditional branching in chains
- Error handling

**Run the example:**
```bash
python -m src.module1_prompt_chaining.basic_chain
```

**What you'll build:**
- Simple 3-step chain (summarize → extract key points → generate actions)
- Conditional chain with branching logic
- Context management across multiple LLM calls

### Module 2: Tool Use and Function Calling

Learn how to give agents access to external tools using OpenAI's function calling capabilities.

**Key Concepts:**
- Function definitions and JSON schemas
- Tool calling with OpenAI API
- Multi-turn conversations with tools
- Function execution and result handling

**Run the example:**
```bash
python -m src.module2_tool_use.function_calling
```

**What you'll build:**
- Agents that can use multiple tools (calculator, time, database search)
- Automatic tool selection based on user queries
- Sequential tool use for complex queries

### Module 3: Web Search Integration

Build agents that can search the web and synthesize information from multiple sources.

**Key Concepts:**
- Web scraping basics with BeautifulSoup
- Integrating search into agent workflows
- Processing and summarizing web content
- Research synthesis from multiple sources

**Run the example:**
```bash
python -m src.module3_web_search.web_agent
```

**What you'll build:**
- Topic research agent (multi-source synthesis)
- Question-answering with web search
- Content extraction and summarization

**Note:** The example uses mock search results. For production, integrate with real search APIs (Google Custom Search, Bing, SerpAPI).

### Module 4: Agent Orchestration

Learn patterns for coordinating multiple agents or agent capabilities to solve complex tasks.

**Key Concepts:**
- Agent role specialization
- Task decomposition and delegation
- Dependency management
- Result synthesis

**Run the example:**
```bash
python -m src.module4_agent_orchestration.orchestrator
```

**What you'll build:**
- Multi-role agent system (researcher, analyst, writer, reviewer)
- Automatic task planning and delegation
- Dependency-aware task execution
- Coordinated synthesis of results

### Module 5: Advanced Multi-Agent Systems

Explore sophisticated patterns for building collaborative multi-agent systems.

**Key Concepts:**
- Agent-to-agent communication
- Debate and consensus mechanisms
- Hierarchical agent structures
- Shared memory and state management

**Run the example:**
```bash
python -m src.module5_advanced_agents.multi_agent
```

**What you'll build:**
- Debate system (agents discuss and reach consensus)
- Hierarchical system (manager delegates to specialized workers)
- Collaborative problem-solving
- Multi-perspective synthesis

## 🏗️ Project Structure

```
HSLUAgentsCourse/
├── src/
│   ├── utils/                    # Shared utilities
│   │   ├── config.py            # OpenAI client setup
│   │   └── logger.py            # Logging configuration
│   ├── module1_prompt_chaining/ # Module 1: Prompt chains
│   │   └── basic_chain.py
│   ├── module2_tool_use/        # Module 2: Function calling
│   │   └── function_calling.py
│   ├── module3_web_search/      # Module 3: Web integration
│   │   └── web_agent.py
│   ├── module4_agent_orchestration/  # Module 4: Orchestration
│   │   └── orchestrator.py
│   └── module5_advanced_agents/ # Module 5: Multi-agent systems
│       └── multi_agent.py
├── examples/                     # Additional examples (coming soon)
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore file
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
└── README.md                    # This file
```

## 💡 Learning Path

We recommend following the modules in order:

1. **Start with Module 1** to understand the basics of prompt chaining
2. **Progress to Module 2** to learn about tool integration
3. **Move to Module 3** to add web search capabilities
4. **Study Module 4** to coordinate multiple agents
5. **Master Module 5** for advanced multi-agent patterns

Each module builds on concepts from previous modules while introducing new patterns and capabilities.

## 🔧 Customization

### Using Different Models

Change the model in your `.env` file:
```
OPENAI_MODEL=gpt-4  # Use GPT-4 for better quality
OPENAI_MODEL=gpt-3.5-turbo  # Use GPT-3.5 for lower cost
```

### Adjusting Temperature

Control creativity/randomness in your `.env`:
```
TEMPERATURE=0.1  # More focused and deterministic
TEMPERATURE=0.9  # More creative and varied
```

### Adding Custom Tools

To add your own tools in Module 2:

1. Define your tool function:
```python
def my_custom_tool(param1: str, param2: int) -> str:
    """Your tool implementation"""
    return result
```

2. Add the tool schema to the `tools` list in `ToolAgent`
3. Register the function in `available_functions`

## 📖 Additional Resources

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [LangChain Documentation](https://python.langchain.com/) (alternative framework)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This course was created to teach practical agentic AI workflows using modern LLM capabilities. It emphasizes:

- **Hands-on learning** with working code examples
- **Progressive complexity** from basic to advanced
- **Production-ready patterns** that can be adapted for real applications
- **Modular design** for easy understanding and extension

## 📧 Support

If you have questions or run into issues:

1. Check the module examples and comments
2. Review the OpenAI API documentation
3. Open an issue on GitHub with details about your problem

## 🗺️ Roadmap

Future additions planned:

- [ ] More advanced examples for each module
- [ ] Jupyter notebooks for interactive learning
- [ ] Integration with popular search APIs
- [ ] Vector database integration for RAG patterns
- [ ] Streaming responses and real-time updates
- [ ] Cost optimization techniques
- [ ] Testing and evaluation frameworks
- [ ] Deployment examples

---

**Happy Learning! 🎓**