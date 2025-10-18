"""
Module 5: Advanced Multi-Agent Systems

This module demonstrates advanced patterns for building sophisticated
multi-agent systems with complex interactions.

Key Concepts:
- Collaborative problem-solving
- Debate and consensus mechanisms
- Hierarchical agent structures
- Memory and state management
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from src.utils import get_openai_client, get_model_name, setup_logger

logger = setup_logger(__name__)


@dataclass
class Message:
    """Represents a message in agent communication."""
    sender: str
    recipient: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "direct"  # direct, broadcast, reply


class CollaborativeAgent:
    """
    An agent that can collaborate with other agents through discussion.
    """
    
    def __init__(self, name: str, expertise: str, model: str = None):
        """
        Initialize a collaborative agent.
        
        Args:
            name: Agent's name
            expertise: Agent's area of expertise
            model: OpenAI model to use
        """
        self.name = name
        self.expertise = expertise
        self.client = get_openai_client()
        self.model = model or get_model_name()
        self.memory: List[Message] = []
        logger.info(f"Initialized agent '{name}' with expertise in {expertise}")
    
    def respond(self, prompt: str, context: List[Message] = None) -> str:
        """
        Generate a response based on prompt and conversation context.
        
        Args:
            prompt: The prompt or question
            context: Previous messages for context
        
        Returns:
            str: Agent's response
        """
        logger.info(f"Agent {self.name} responding to prompt")
        
        system_msg = f"You are {self.name}, an expert in {self.expertise}. Provide insights from your expertise perspective."
        
        messages = [{"role": "system", "content": system_msg}]
        
        # Add context from previous messages
        if context:
            context_str = "\n".join([
                f"{msg.sender}: {msg.content}" 
                for msg in context[-5:]  # Last 5 messages
            ])
            messages.append({
                "role": "user", 
                "content": f"Previous conversation:\n{context_str}\n\n"
            })
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def add_to_memory(self, message: Message):
        """Add a message to the agent's memory."""
        self.memory.append(message)


class DebateSystem:
    """
    A system where agents debate and reach consensus on a topic.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the debate system.
        
        Args:
            model: OpenAI model to use
        """
        self.model = model or get_model_name()
        self.agents: List[CollaborativeAgent] = []
        self.conversation_history: List[Message] = []
        logger.info("Initialized DebateSystem")
    
    def add_agent(self, name: str, expertise: str):
        """
        Add an agent to the debate.
        
        Args:
            name: Agent's name
            expertise: Agent's expertise
        """
        agent = CollaborativeAgent(name, expertise, self.model)
        self.agents.append(agent)
        logger.info(f"Added agent {name} to debate")
    
    def conduct_debate(self, topic: str, rounds: int = 3) -> Dict[str, Any]:
        """
        Conduct a debate among agents on a topic.
        
        Args:
            topic: Topic to debate
            rounds: Number of debate rounds
        
        Returns:
            Dict: Debate results including all positions and consensus
        """
        logger.info(f"Starting debate on: {topic}")
        
        # Initial positions
        print(f"\n{'='*60}")
        print(f"DEBATE TOPIC: {topic}")
        print(f"{'='*60}\n")
        
        for agent in self.agents:
            position_prompt = f"State your position on this topic based on your expertise:\n{topic}"
            position = agent.respond(position_prompt)
            
            msg = Message(
                sender=agent.name,
                recipient="all",
                content=position,
                message_type="broadcast"
            )
            self.conversation_history.append(msg)
            agent.add_to_memory(msg)
            
            print(f"{agent.name} ({agent.expertise}):")
            print(f"{position}\n")
        
        # Debate rounds
        for round_num in range(1, rounds + 1):
            print(f"{'='*60}")
            print(f"ROUND {round_num}")
            print(f"{'='*60}\n")
            
            for agent in self.agents:
                debate_prompt = f"""Based on the other agents' positions, provide your response.
You may:
- Agree with certain points
- Raise counterarguments
- Propose compromises
- Add new perspectives from your expertise

Topic: {topic}"""
                
                response = agent.respond(debate_prompt, self.conversation_history)
                
                msg = Message(
                    sender=agent.name,
                    recipient="all",
                    content=response,
                    message_type="broadcast"
                )
                self.conversation_history.append(msg)
                agent.add_to_memory(msg)
                
                print(f"{agent.name}:")
                print(f"{response}\n")
        
        # Synthesize consensus
        logger.info("Synthesizing consensus")
        consensus = self._synthesize_consensus(topic)
        
        print(f"{'='*60}")
        print("CONSENSUS")
        print(f"{'='*60}")
        print(consensus)
        
        return {
            "topic": topic,
            "agents": [{"name": a.name, "expertise": a.expertise} for a in self.agents],
            "conversation": [
                {
                    "sender": msg.sender,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in self.conversation_history
            ],
            "consensus": consensus
        }
    
    def _synthesize_consensus(self, topic: str) -> str:
        """Synthesize a consensus from the debate."""
        client = get_openai_client()
        
        conversation_text = "\n\n".join([
            f"{msg.sender}: {msg.content}"
            for msg in self.conversation_history
        ])
        
        prompt = f"""Based on the following debate, synthesize a consensus that:
1. Identifies areas of agreement
2. Acknowledges remaining disagreements
3. Proposes a balanced conclusion

Topic: {topic}

Debate:
{conversation_text}

Consensus:"""
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        return response.choices[0].message.content


class HierarchicalAgentSystem:
    """
    A hierarchical system with manager and worker agents.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the hierarchical system.
        
        Args:
            model: OpenAI model to use
        """
        self.model = model or get_model_name()
        self.manager = None
        self.workers: List[CollaborativeAgent] = []
        logger.info("Initialized HierarchicalAgentSystem")
    
    def set_manager(self, name: str, expertise: str):
        """Set the manager agent."""
        self.manager = CollaborativeAgent(name, expertise, self.model)
        logger.info(f"Set {name} as manager")
    
    def add_worker(self, name: str, expertise: str):
        """Add a worker agent."""
        worker = CollaborativeAgent(name, expertise, self.model)
        self.workers.append(worker)
        logger.info(f"Added worker {name}")
    
    def solve_problem(self, problem: str) -> Dict[str, Any]:
        """
        Solve a problem using hierarchical collaboration.
        
        Args:
            problem: Problem to solve
        
        Returns:
            Dict: Solution with breakdown and synthesis
        """
        logger.info(f"Solving problem: {problem}")
        
        if not self.manager:
            raise ValueError("Manager not set")
        
        if not self.workers:
            raise ValueError("No workers available")
        
        # Manager breaks down the problem
        breakdown_prompt = f"""As a manager, break down this problem into {len(self.workers)} subtasks,
one for each of your team members with these expertises: {', '.join([w.expertise for w in self.workers])}.

Problem: {problem}

For each subtask, specify:
1. Subtask description
2. Which team member (by expertise) should handle it

Format as:
SUBTASK 1: [description]
ASSIGNED TO: [expertise]

SUBTASK 2: ...
"""
        
        breakdown = self.manager.respond(breakdown_prompt)
        logger.info("Manager broke down the problem")
        
        # Parse and assign subtasks
        subtasks = []
        lines = breakdown.split('\n')
        current_subtask = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('SUBTASK'):
                if current_subtask:
                    subtasks.append(current_subtask)
                current_subtask = {'description': line.split(':', 1)[1].strip() if ':' in line else ''}
            elif line.startswith('ASSIGNED TO:'):
                current_subtask['assigned_to'] = line.split(':', 1)[1].strip()
        
        if current_subtask:
            subtasks.append(current_subtask)
        
        # Workers complete subtasks
        worker_results = []
        for i, (subtask, worker) in enumerate(zip(subtasks[:len(self.workers)], self.workers)):
            logger.info(f"Worker {worker.name} working on subtask {i+1}")
            result = worker.respond(f"Complete this subtask: {subtask.get('description', 'Unknown task')}")
            worker_results.append({
                "worker": worker.name,
                "expertise": worker.expertise,
                "subtask": subtask.get('description', ''),
                "result": result
            })
        
        # Manager synthesizes results
        synthesis_prompt = f"""As a manager, synthesize the results from your team into a final solution.

Problem: {problem}

Team results:
"""
        for wr in worker_results:
            synthesis_prompt += f"\n{wr['worker']} ({wr['expertise']}):\n{wr['result']}\n"
        
        synthesis_prompt += "\nFinal solution:"
        
        final_solution = self.manager.respond(synthesis_prompt)
        logger.info("Manager synthesized final solution")
        
        return {
            "problem": problem,
            "breakdown": breakdown,
            "subtasks": worker_results,
            "solution": final_solution
        }


def main():
    """Example usage of advanced multi-agent systems."""
    
    # Example 1: Debate System
    print("\n" + "="*60)
    print("EXAMPLE 1: Debate System")
    print("="*60)
    
    debate = DebateSystem()
    debate.add_agent("Alice", "environmental science")
    debate.add_agent("Bob", "economics")
    debate.add_agent("Charlie", "technology")
    
    result = debate.conduct_debate(
        "Should companies be required to achieve carbon neutrality by 2030?",
        rounds=2
    )
    
    # Example 2: Hierarchical System
    print("\n\n" + "="*60)
    print("EXAMPLE 2: Hierarchical Agent System")
    print("="*60)
    
    hierarchy = HierarchicalAgentSystem()
    hierarchy.set_manager("Manager", "project management")
    hierarchy.add_worker("Developer", "software development")
    hierarchy.add_worker("Designer", "user experience design")
    hierarchy.add_worker("Analyst", "data analysis")
    
    solution = hierarchy.solve_problem(
        "Design and implement a mobile app for tracking personal carbon footprint"
    )
    
    print(f"\nProblem: {solution['problem']}")
    print(f"\nManager's Breakdown:\n{solution['breakdown']}")
    print(f"\nSubtask Results:")
    for st in solution['subtasks']:
        print(f"\n{st['worker']} ({st['expertise']}):")
        print(f"Subtask: {st['subtask']}")
        print(f"Result: {st['result'][:200]}...")
    print(f"\nFinal Solution:\n{solution['solution']}")


if __name__ == "__main__":
    main()
