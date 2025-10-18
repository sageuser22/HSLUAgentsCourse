"""
Example: Customer Support Agent

This example demonstrates building a customer support agent that:
1. Understands customer queries
2. Searches a knowledge base
3. Provides helpful responses
4. Escalates when necessary
"""

from typing import List, Dict
from src.module1_prompt_chaining import PromptChain
from src.module2_tool_use import search_database
from src.utils import get_openai_client, get_model_name, setup_logger

logger = setup_logger(__name__)


class CustomerSupportAgent:
    """
    A customer support agent that can handle inquiries using various strategies.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the customer support agent.
        
        Args:
            model: OpenAI model to use
        """
        self.client = get_openai_client()
        self.model = model or get_model_name()
        self.chain = PromptChain(model)
        logger.info("Initialized CustomerSupportAgent")
    
    def handle_query(self, customer_query: str) -> dict:
        """
        Handle a customer support query.
        
        Args:
            customer_query: The customer's question or issue
        
        Returns:
            dict: Support response with analysis and solution
        """
        logger.info(f"Handling query: {customer_query[:50]}...")
        
        # Step 1: Classify the query
        classification_prompt = f"""Classify this customer query into one of these categories:
- product_info: Questions about products or services
- technical_support: Technical issues or problems
- billing: Billing, payments, or account issues
- general: General inquiries

Respond with only the category name.

Query: {customer_query}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": classification_prompt}],
            temperature=0.1
        )
        
        category = response.choices[0].message.content.strip().lower()
        logger.info(f"Query classified as: {category}")
        
        # Step 2: Search knowledge base
        kb_results = self._search_knowledge_base(customer_query, category)
        
        # Step 3: Generate response
        response_prompt = f"""You are a helpful customer support agent. 
Based on the customer query and knowledge base information, provide a helpful response.

Customer Query: {customer_query}

Knowledge Base Information:
{kb_results}

Provide a clear, professional, and helpful response:"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": response_prompt}],
            temperature=0.7
        )
        
        support_response = response.choices[0].message.content
        
        # Step 4: Determine if escalation is needed
        escalation_check = f"""Based on this customer query and response, should this be escalated to a human agent?
Escalate if: the issue is complex, requires account access, or the customer is frustrated.
Respond with only "yes" or "no".

Query: {customer_query}
Response: {support_response}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": escalation_check}],
            temperature=0.1
        )
        
        should_escalate = "yes" in response.choices[0].message.content.lower()
        
        return {
            "query": customer_query,
            "category": category,
            "knowledge_base_results": kb_results,
            "response": support_response,
            "escalate": should_escalate
        }
    
    def _search_knowledge_base(self, query: str, category: str) -> str:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query
            category: Query category
        
        Returns:
            str: Formatted knowledge base results
        """
        # In a real system, this would search a proper knowledge base
        # Here we use the mock database from module 2
        results = search_database(query, "all")
        
        if not results:
            return "No relevant information found in knowledge base."
        
        formatted = "Relevant knowledge base articles:\n"
        for result in results[:3]:
            formatted += f"- {result['title']}: {result['description']}\n"
        
        return formatted


def main():
    """Run customer support examples."""
    agent = CustomerSupportAgent()
    
    print("\n" + "="*70)
    print("CUSTOMER SUPPORT AGENT EXAMPLES")
    print("="*70)
    
    # Example queries
    queries = [
        "I can't log in to my account. I keep getting an error message.",
        "What AI courses do you offer?",
        "I was charged twice for the same workshop. Please help!"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"QUERY {i}")
        print("="*70)
        print(f"\nCustomer: {query}")
        
        result = agent.handle_query(query)
        
        print(f"\nCategory: {result['category']}")
        print(f"\nKnowledge Base Results:\n{result['knowledge_base_results']}")
        print(f"\nAgent Response:\n{result['response']}")
        print(f"\nEscalate to Human: {'Yes' if result['escalate'] else 'No'}")


if __name__ == "__main__":
    main()
