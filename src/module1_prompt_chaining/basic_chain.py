"""
Module 1: Basic Prompt Chaining

This module demonstrates the fundamental concept of prompt chaining,
where the output of one LLM call becomes the input for the next.

Key Concepts:
- Sequential processing
- Building context across multiple steps
- Error handling in chains
"""

from src.utils import get_openai_client, get_model_name, setup_logger

logger = setup_logger(__name__)


class PromptChain:
    """
    A basic prompt chain that processes information through multiple steps.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the prompt chain.
        
        Args:
            model: OpenAI model to use (defaults to config value)
        """
        self.client = get_openai_client()
        self.model = model or get_model_name()
        logger.info(f"Initialized PromptChain with model: {self.model}")
    
    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Make a call to the LLM.
        
        Args:
            prompt: The prompt to send
            temperature: Temperature for generation
        
        Returns:
            str: The LLM's response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
    
    def simple_chain(self, initial_input: str) -> dict:
        """
        Execute a simple 3-step chain:
        1. Summarize the input
        2. Extract key points from summary
        3. Generate action items from key points
        
        Args:
            initial_input: The text to process
        
        Returns:
            dict: Results from each step
        """
        logger.info("Starting simple chain execution")
        
        # Step 1: Summarize
        logger.info("Step 1: Summarizing input")
        summary_prompt = f"""Summarize the following text in 2-3 sentences:

{initial_input}"""
        summary = self._call_llm(summary_prompt, temperature=0.3)
        logger.info(f"Summary generated: {summary[:100]}...")
        
        # Step 2: Extract key points
        logger.info("Step 2: Extracting key points")
        keypoints_prompt = f"""Extract 3-5 key points from the following summary:

{summary}

Format as a bullet list."""
        key_points = self._call_llm(keypoints_prompt, temperature=0.3)
        logger.info(f"Key points extracted")
        
        # Step 3: Generate action items
        logger.info("Step 3: Generating action items")
        actions_prompt = f"""Based on these key points, suggest 2-3 actionable next steps:

{key_points}

Format as a numbered list."""
        action_items = self._call_llm(actions_prompt, temperature=0.5)
        logger.info(f"Action items generated")
        
        return {
            "original": initial_input,
            "summary": summary,
            "key_points": key_points,
            "action_items": action_items
        }
    
    def conditional_chain(self, text: str, analysis_type: str = "sentiment") -> dict:
        """
        Execute a chain with conditional branching based on analysis results.
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis ("sentiment" or "topic")
        
        Returns:
            dict: Analysis results and follow-up
        """
        logger.info(f"Starting conditional chain with analysis_type: {analysis_type}")
        
        # Step 1: Analyze text
        if analysis_type == "sentiment":
            analysis_prompt = f"""Analyze the sentiment of the following text. 
Respond with only one word: Positive, Negative, or Neutral.

{text}"""
        else:
            analysis_prompt = f"""Identify the main topic of the following text in 1-2 words.

{text}"""
        
        analysis = self._call_llm(analysis_prompt, temperature=0.1).strip()
        logger.info(f"Analysis result: {analysis}")
        
        # Step 2: Conditional follow-up
        if analysis_type == "sentiment":
            if "Positive" in analysis:
                followup_prompt = f"""The text has positive sentiment. Suggest how to leverage this positivity.

Original text: {text}"""
            elif "Negative" in analysis:
                followup_prompt = f"""The text has negative sentiment. Suggest how to address the concerns.

Original text: {text}"""
            else:
                followup_prompt = f"""The text has neutral sentiment. Suggest how to make it more engaging.

Original text: {text}"""
        else:
            followup_prompt = f"""The main topic is: {analysis}. 
Suggest 3 related topics to explore.

Original text: {text}"""
        
        followup = self._call_llm(followup_prompt, temperature=0.7)
        logger.info("Follow-up generated")
        
        return {
            "text": text,
            "analysis_type": analysis_type,
            "analysis": analysis,
            "followup": followup
        }


def main():
    """Example usage of the PromptChain class."""
    chain = PromptChain()
    
    # Example 1: Simple chain
    print("\n" + "="*60)
    print("Example 1: Simple Chain")
    print("="*60)
    
    sample_text = """
    Artificial intelligence is rapidly transforming industries across the globe.
    From healthcare to finance, AI systems are being deployed to automate tasks,
    provide insights, and enhance decision-making. However, this transformation
    also raises important questions about ethics, privacy, and the future of work.
    Organizations must carefully consider these implications while adopting AI technologies.
    """
    
    result = chain.simple_chain(sample_text)
    print(f"\nOriginal Text: {result['original'][:100]}...")
    print(f"\nSummary:\n{result['summary']}")
    print(f"\nKey Points:\n{result['key_points']}")
    print(f"\nAction Items:\n{result['action_items']}")
    
    # Example 2: Conditional chain
    print("\n" + "="*60)
    print("Example 2: Conditional Chain (Sentiment Analysis)")
    print("="*60)
    
    sentiment_text = "I'm absolutely thrilled with the progress we've made this quarter!"
    result = chain.conditional_chain(sentiment_text, "sentiment")
    print(f"\nText: {result['text']}")
    print(f"\nSentiment: {result['analysis']}")
    print(f"\nFollow-up:\n{result['followup']}")


if __name__ == "__main__":
    main()
