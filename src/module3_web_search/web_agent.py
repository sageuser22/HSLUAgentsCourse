"""
Module 3: Web Search Integration

This module demonstrates how to integrate web search capabilities
into AI agents for retrieving real-time information.

Key Concepts:
- Web scraping basics
- Integrating search into agent workflows
- Processing and summarizing web content
- Combining multiple sources
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from src.utils import get_openai_client, get_model_name, setup_logger

logger = setup_logger(__name__)


class WebSearchAgent:
    """
    An agent that can search the web and process results.
    
    Note: This is a simplified implementation. For production use,
    consider using APIs like Google Custom Search, Bing Search API,
    or SerpAPI for better results and reliability.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the web search agent.
        
        Args:
            model: OpenAI model to use
        """
        self.client = get_openai_client()
        self.model = model or get_model_name()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logger.info("Initialized WebSearchAgent")
    
    def search_web(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        """
        Perform a web search (mock implementation).
        
        In production, replace this with actual search API calls.
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            List[Dict]: Search results with title, url, and snippet
        """
        logger.info(f"Searching web for: {query}")
        
        # Mock search results for demonstration
        # In production, use actual search APIs
        mock_results = [
            {
                "title": f"Result 1 for '{query}'",
                "url": "https://example.com/page1",
                "snippet": f"This page contains information about {query}. It discusses the key concepts and applications in detail, providing insights and examples."
            },
            {
                "title": f"Latest developments in {query}",
                "url": "https://example.com/page2",
                "snippet": f"Recent advancements in {query} have shown promising results. This article explores the current state and future directions."
            },
            {
                "title": f"Understanding {query}: A comprehensive guide",
                "url": "https://example.com/page3",
                "snippet": f"A comprehensive guide covering all aspects of {query}, including practical examples and best practices for implementation."
            }
        ]
        
        results = mock_results[:num_results]
        logger.info(f"Found {len(results)} results")
        return results
    
    def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a webpage.
        
        Args:
            url: URL to fetch
        
        Returns:
            Optional[str]: Extracted text content or None if failed
        """
        try:
            logger.info(f"Fetching content from: {url}")
            
            # For mock URLs, return mock content
            if "example.com" in url:
                return f"This is mock content from {url}. In production, this would contain the actual webpage text extracted using BeautifulSoup."
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            max_length = 2000
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            logger.info(f"Fetched {len(text)} characters")
            return text
        
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def summarize_content(self, content: str, focus: str = "") -> str:
        """
        Summarize web content using LLM.
        
        Args:
            content: Content to summarize
            focus: Optional focus area for the summary
        
        Returns:
            str: Summary of the content
        """
        logger.info("Summarizing content")
        
        focus_text = f" with focus on {focus}" if focus else ""
        prompt = f"""Summarize the following content{focus_text} in 2-3 clear sentences:

{content}

Summary:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def research_topic(self, topic: str, num_sources: int = 3) -> Dict[str, any]:
        """
        Research a topic by searching and summarizing multiple sources.
        
        Args:
            topic: Topic to research
            num_sources: Number of sources to consult
        
        Returns:
            Dict: Research results with sources and synthesis
        """
        logger.info(f"Researching topic: {topic}")
        
        # Step 1: Search for sources
        search_results = self.search_web(topic, num_sources)
        
        # Step 2: Fetch and summarize each source
        summaries = []
        for result in search_results:
            content = self.fetch_page_content(result['url'])
            if content:
                summary = self.summarize_content(content, focus=topic)
                summaries.append({
                    "title": result['title'],
                    "url": result['url'],
                    "summary": summary
                })
        
        # Step 3: Synthesize information
        logger.info("Synthesizing information from sources")
        
        synthesis_prompt = f"""Based on the following summaries from different sources about '{topic}', 
provide a comprehensive synthesis that:
1. Identifies common themes
2. Highlights key insights
3. Notes any contradictions or different perspectives

Sources:
"""
        for i, source in enumerate(summaries, 1):
            synthesis_prompt += f"\n{i}. {source['title']}\n   {source['summary']}\n"
        
        synthesis_prompt += "\nComprehensive synthesis:"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.5
        )
        
        synthesis = response.choices[0].message.content
        
        return {
            "topic": topic,
            "sources": summaries,
            "synthesis": synthesis
        }
    
    def answer_with_search(self, question: str) -> str:
        """
        Answer a question using web search.
        
        Args:
            question: Question to answer
        
        Returns:
            str: Answer based on web search
        """
        logger.info(f"Answering question with search: {question}")
        
        # Step 1: Determine search query
        query_prompt = f"""Convert this question into an optimal search query (just return the query):

Question: {question}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query_prompt}],
            temperature=0.3
        )
        
        search_query = response.choices[0].message.content.strip()
        logger.info(f"Search query: {search_query}")
        
        # Step 2: Search and gather information
        results = self.search_web(search_query, num_results=2)
        
        context = ""
        for i, result in enumerate(results, 1):
            content = self.fetch_page_content(result['url'])
            if content:
                context += f"\nSource {i} ({result['title']}):\n{content}\n"
        
        # Step 3: Answer based on context
        answer_prompt = f"""Answer the following question based on the provided context.
If the context doesn't contain enough information, say so.

Question: {question}

Context:
{context}

Answer:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": answer_prompt}],
            temperature=0.5
        )
        
        return response.choices[0].message.content


def main():
    """Example usage of the WebSearchAgent class."""
    agent = WebSearchAgent()
    
    print("\n" + "="*60)
    print("Web Search Integration Examples")
    print("="*60)
    
    # Example 1: Research a topic
    print("\nExample 1: Research a topic")
    print("-" * 60)
    result = agent.research_topic("artificial intelligence ethics", num_sources=2)
    print(f"Topic: {result['topic']}")
    print(f"\nSources:")
    for i, source in enumerate(result['sources'], 1):
        print(f"\n{i}. {source['title']}")
        print(f"   URL: {source['url']}")
        print(f"   Summary: {source['summary']}")
    print(f"\nSynthesis:\n{result['synthesis']}")
    
    # Example 2: Answer a question with search
    print("\n\n" + "="*60)
    print("Example 2: Answer a question using web search")
    print("-" * 60)
    answer = agent.answer_with_search("What are the latest developments in quantum computing?")
    print(f"\nAnswer:\n{answer}")


if __name__ == "__main__":
    main()
