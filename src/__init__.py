"""
HSLU Agents Course - Teaching Agentic AI Workflows

This package provides modular examples of building AI agents using OpenAI API,
progressing from basic prompt chaining to advanced multi-agent systems.

Modules:
- module1_prompt_chaining: Basic sequential LLM processing
- module2_tool_use: Function calling and tool integration
- module3_web_search: Web search and information gathering
- module4_agent_orchestration: Multi-agent coordination
- module5_advanced_agents: Advanced collaboration patterns
"""

__version__ = "1.0.0"
__author__ = "HSLU Agents Course"

from . import utils
from . import module1_prompt_chaining
from . import module2_tool_use
from . import module3_web_search
from . import module4_agent_orchestration
from . import module5_advanced_agents

__all__ = [
    "utils",
    "module1_prompt_chaining",
    "module2_tool_use",
    "module3_web_search",
    "module4_agent_orchestration",
    "module5_advanced_agents"
]
