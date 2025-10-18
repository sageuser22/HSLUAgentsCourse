# Quick Start Guide

Welcome to the HSLU Agents Course! This guide will help you get started in minutes.

## Step 1: Set Up Your Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sageuser22/HSLUAgentsCourse.git
   cd HSLUAgentsCourse
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Step 2: Configure Your API Key

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your OpenAI API key:**
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   TEMPERATURE=0.7
   ```

   Get your API key from: https://platform.openai.com/api-keys

## Step 3: Try Your First Module

Run the Module 1 example (Basic Prompt Chaining):

```bash
python -m src.module1_prompt_chaining.basic_chain
```

You should see the agent:
1. Summarize a text
2. Extract key points
3. Generate action items
4. Perform conditional analysis

## Step 4: Explore Other Modules

**Module 2 - Tool Use:**
```bash
python -m src.module2_tool_use.function_calling
```

**Module 3 - Web Search:**
```bash
python -m src.module3_web_search.web_agent
```

**Module 4 - Orchestration:**
```bash
python -m src.module4_agent_orchestration.orchestrator
```

**Module 5 - Advanced Agents:**
```bash
python -m src.module5_advanced_agents.multi_agent
```

## Step 5: Try the Examples

Run the complete examples that combine multiple modules:

**Research Assistant:**
```bash
python -m examples.research_assistant
```

**Customer Support Agent:**
```bash
python -m examples.customer_support
```

## Understanding the Output

Each module will print detailed logs showing:
- What the agent is doing at each step
- The prompts being sent to the LLM
- The responses received
- The final results

Look for patterns like:
- `INFO - Agent executing...` - Shows when an agent starts a task
- `Summary:` - Shows generated summaries
- `Tool response:` - Shows results from tool calls

## Customizing Your Experience

### Change the Model

Edit `.env`:
```
OPENAI_MODEL=gpt-4  # More capable but more expensive
OPENAI_MODEL=gpt-3.5-turbo  # Faster and cheaper
```

### Adjust Temperature

Edit `.env`:
```
TEMPERATURE=0.1  # More focused and deterministic
TEMPERATURE=0.9  # More creative and varied
```

### Modify the Examples

All source code is in the `src/` directory. Feel free to:
- Change prompts
- Add new tools
- Modify agent behaviors
- Create your own agents

## Troubleshooting

### ImportError: No module named 'openai'
**Solution:** Run `pip install -r requirements.txt`

### "OPENAI_API_KEY not found"
**Solution:** Make sure you created `.env` file with your API key

### Rate limit errors
**Solution:** You may be making too many API calls. Wait a moment or use a different API key tier.

### Module not found errors
**Solution:** Make sure you're running commands from the repository root directory

## Next Steps

1. **Read the full README.md** for detailed module explanations
2. **Experiment with the code** - modify examples to understand how they work
3. **Build your own agent** - combine concepts from different modules
4. **Share your creation** - contribute back to the repository!

## Getting Help

- Check the module docstrings in the source code
- Review the examples in the `examples/` directory
- Open an issue on GitHub if you encounter problems

**Happy Learning! 🚀**
