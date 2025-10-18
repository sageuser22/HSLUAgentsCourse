"""
Complete Example: Building a Research Assistant Agent

This example demonstrates how to combine multiple modules to create
a sophisticated research assistant that can:
1. Search the web for information
2. Use tools to perform calculations or get data
3. Orchestrate multiple specialized agents
4. Provide comprehensive research reports
"""

from src.module2_tool_use import ToolAgent
from src.module3_web_search import WebSearchAgent
from src.module4_agent_orchestration import Orchestrator
from src.utils import setup_logger

logger = setup_logger(__name__)


class ResearchAssistant:
    """
    A comprehensive research assistant combining multiple agent capabilities.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the research assistant.
        
        Args:
            model: OpenAI model to use
        """
        self.tool_agent = ToolAgent(model)
        self.web_agent = WebSearchAgent(model)
        self.orchestrator = Orchestrator(model)
        logger.info("Initialized ResearchAssistant")
    
    def research_and_analyze(self, topic: str) -> dict:
        """
        Perform comprehensive research on a topic.
        
        Args:
            topic: Topic to research
        
        Returns:
            dict: Complete research report
        """
        logger.info(f"Researching topic: {topic}")
        
        # Use web search to gather information
        logger.info("Step 1: Gathering information from web")
        web_results = self.web_agent.research_topic(topic, num_sources=2)
        
        # Use orchestrator to create comprehensive analysis
        logger.info("Step 2: Orchestrating detailed analysis")
        objective = f"""Create a detailed analysis of '{topic}' using this research:

Sources:
{chr(10).join([f"- {s['title']}: {s['summary']}" for s in web_results['sources']])}

Synthesis:
{web_results['synthesis']}

The analysis should include:
1. Key findings and insights
2. Practical implications
3. Recommendations for further exploration
"""
        
        analysis = self.orchestrator.execute_objective(objective)
        
        return {
            "topic": topic,
            "web_research": web_results,
            "detailed_analysis": analysis
        }


def main():
    """Run the research assistant example."""
    print("\n" + "="*70)
    print("RESEARCH ASSISTANT EXAMPLE")
    print("="*70)
    
    assistant = ResearchAssistant()
    
    # Example research task
    topic = "The impact of AI on healthcare diagnostics"
    
    print(f"\nResearching: {topic}")
    print("-" * 70)
    
    result = assistant.research_and_analyze(topic)
    
    # Display results
    print("\n" + "="*70)
    print("WEB RESEARCH RESULTS")
    print("="*70)
    
    for i, source in enumerate(result['web_research']['sources'], 1):
        print(f"\nSource {i}: {source['title']}")
        print(f"URL: {source['url']}")
        print(f"Summary: {source['summary']}")
    
    print("\n" + "="*70)
    print("SYNTHESIS FROM WEB RESEARCH")
    print("="*70)
    print(result['web_research']['synthesis'])
    
    print("\n" + "="*70)
    print("DETAILED ANALYSIS")
    print("="*70)
    print(f"\nTasks Executed:")
    for task in result['detailed_analysis']['tasks']:
        print(f"\n- {task['id']} ({task['role']}): {task['description']}")
    
    print("\n" + "="*70)
    print("FINAL SYNTHESIS")
    print("="*70)
    print(result['detailed_analysis']['synthesis'])


if __name__ == "__main__":
    main()
