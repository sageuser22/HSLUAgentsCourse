"""
Module 4: Agent Orchestration

This module demonstrates orchestration patterns for coordinating
multiple agents or agent capabilities.

Key Concepts:
- Agent coordination patterns
- Task decomposition and delegation
- Sequential and parallel execution
- Agent communication protocols
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from src.utils import get_openai_client, get_model_name, setup_logger

logger = setup_logger(__name__)


class AgentRole(Enum):
    """Roles that agents can play in the orchestration."""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"


@dataclass
class Task:
    """Represents a task to be executed by an agent."""
    id: str
    description: str
    assigned_to: AgentRole
    dependencies: List[str] = None
    result: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class Agent:
    """Base agent class with specific role and capabilities."""
    
    def __init__(self, role: AgentRole, model: str = None):
        """
        Initialize an agent with a specific role.
        
        Args:
            role: The role this agent plays
            model: OpenAI model to use
        """
        self.role = role
        self.client = get_openai_client()
        self.model = model or get_model_name()
        self.system_prompts = {
            AgentRole.COORDINATOR: "You are a coordinator agent. Your job is to plan tasks, delegate work, and synthesize results from other agents.",
            AgentRole.RESEARCHER: "You are a researcher agent. Your job is to gather information, search for relevant data, and provide detailed findings.",
            AgentRole.ANALYST: "You are an analyst agent. Your job is to analyze data, identify patterns, and draw conclusions.",
            AgentRole.WRITER: "You are a writer agent. Your job is to create clear, well-structured content based on provided information.",
            AgentRole.REVIEWER: "You are a reviewer agent. Your job is to review content, identify issues, and suggest improvements."
        }
        logger.info(f"Initialized {role.value} agent")
    
    def execute(self, task_description: str, context: str = "") -> str:
        """
        Execute a task according to the agent's role.
        
        Args:
            task_description: Description of the task
            context: Additional context from previous tasks
        
        Returns:
            str: Result of the task execution
        """
        logger.info(f"{self.role.value} agent executing task: {task_description[:50]}...")
        
        messages = [
            {"role": "system", "content": self.system_prompts[self.role]},
            {"role": "user", "content": f"Task: {task_description}"}
        ]
        
        if context:
            messages.append({"role": "user", "content": f"Context from previous tasks:\n{context}"})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        logger.info(f"{self.role.value} agent completed task")
        return result


class Orchestrator:
    """
    Orchestrates multiple agents to complete complex tasks.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the orchestrator.
        
        Args:
            model: OpenAI model to use for agents
        """
        self.model = model or get_model_name()
        self.agents = {
            role: Agent(role, self.model) for role in AgentRole
        }
        self.tasks: List[Task] = []
        logger.info("Initialized Orchestrator")
    
    def plan_tasks(self, objective: str) -> List[Task]:
        """
        Use the coordinator agent to plan tasks for an objective.
        
        Args:
            objective: The high-level objective to achieve
        
        Returns:
            List[Task]: Planned tasks
        """
        logger.info(f"Planning tasks for objective: {objective}")
        
        planning_prompt = f"""Given this objective, break it down into 3-5 specific tasks.
For each task, specify:
1. A unique task ID (task_1, task_2, etc.)
2. A clear description
3. Which role should handle it: {', '.join([r.value for r in AgentRole if r != AgentRole.COORDINATOR])}
4. Dependencies (which tasks must be completed first, if any)

Objective: {objective}

Format your response as:
TASK_ID: task_1
DESCRIPTION: [description]
ROLE: [role]
DEPENDENCIES: [comma-separated task IDs or 'none']

TASK_ID: task_2
...
"""
        
        coordinator = self.agents[AgentRole.COORDINATOR]
        plan = coordinator.execute(planning_prompt)
        
        # Parse the plan (simplified parsing)
        tasks = []
        current_task = {}
        
        for line in plan.split('\n'):
            line = line.strip()
            if line.startswith('TASK_ID:'):
                if current_task:
                    tasks.append(self._create_task_from_dict(current_task))
                current_task = {'id': line.split(':', 1)[1].strip()}
            elif line.startswith('DESCRIPTION:'):
                current_task['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('ROLE:'):
                role_name = line.split(':', 1)[1].strip()
                current_task['role'] = role_name
            elif line.startswith('DEPENDENCIES:'):
                deps = line.split(':', 1)[1].strip()
                current_task['dependencies'] = [] if deps.lower() == 'none' else [d.strip() for d in deps.split(',')]
        
        if current_task:
            tasks.append(self._create_task_from_dict(current_task))
        
        self.tasks = tasks
        logger.info(f"Planned {len(tasks)} tasks")
        return tasks
    
    def _create_task_from_dict(self, task_dict: dict) -> Task:
        """Create a Task object from a dictionary."""
        role_name = task_dict.get('role', 'researcher')
        try:
            role = AgentRole(role_name)
        except ValueError:
            logger.warning(f"Unknown role '{role_name}', defaulting to RESEARCHER")
            role = AgentRole.RESEARCHER
        
        return Task(
            id=task_dict.get('id', 'task_unknown'),
            description=task_dict.get('description', ''),
            assigned_to=role,
            dependencies=task_dict.get('dependencies', [])
        )
    
    def execute_tasks(self, tasks: List[Task] = None) -> Dict[str, Any]:
        """
        Execute tasks in order, respecting dependencies.
        
        Args:
            tasks: Tasks to execute (uses self.tasks if None)
        
        Returns:
            Dict: Results including task outcomes and synthesis
        """
        if tasks is None:
            tasks = self.tasks
        
        logger.info(f"Executing {len(tasks)} tasks")
        
        # Build context from completed tasks
        context = {}
        
        # Execute tasks
        for task in tasks:
            # Wait for dependencies
            if task.dependencies:
                dep_context = []
                for dep_id in task.dependencies:
                    if dep_id in context:
                        dep_context.append(f"{dep_id}: {context[dep_id][:200]}...")
                context_str = "\n".join(dep_context)
            else:
                context_str = ""
            
            # Execute task
            task.status = "in_progress"
            logger.info(f"Executing {task.id}: {task.description}")
            
            agent = self.agents[task.assigned_to]
            result = agent.execute(task.description, context_str)
            
            task.result = result
            task.status = "completed"
            context[task.id] = result
        
        # Synthesize results
        logger.info("Synthesizing results")
        synthesis_prompt = "Synthesize the results from all tasks into a coherent final output.\n\n"
        for task in tasks:
            synthesis_prompt += f"{task.id} ({task.assigned_to.value}):\n{task.result}\n\n"
        
        coordinator = self.agents[AgentRole.COORDINATOR]
        synthesis = coordinator.execute(synthesis_prompt)
        
        return {
            "tasks": tasks,
            "synthesis": synthesis
        }
    
    def execute_objective(self, objective: str) -> Dict[str, Any]:
        """
        Complete end-to-end execution: plan and execute tasks for an objective.
        
        Args:
            objective: The objective to achieve
        
        Returns:
            Dict: Complete results
        """
        logger.info(f"Executing objective: {objective}")
        
        # Plan tasks
        tasks = self.plan_tasks(objective)
        
        # Execute tasks
        results = self.execute_tasks(tasks)
        
        return {
            "objective": objective,
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "role": t.assigned_to.value,
                    "status": t.status,
                    "result": t.result
                }
                for t in results["tasks"]
            ],
            "synthesis": results["synthesis"]
        }


def main():
    """Example usage of the Orchestrator class."""
    orchestrator = Orchestrator()
    
    print("\n" + "="*60)
    print("Agent Orchestration Example")
    print("="*60)
    
    objective = "Create a comprehensive blog post about the benefits and challenges of remote work"
    
    result = orchestrator.execute_objective(objective)
    
    print(f"\nObjective: {result['objective']}")
    print(f"\nTasks executed:")
    for task in result['tasks']:
        print(f"\n{task['id']} - {task['role']}:")
        print(f"  Description: {task['description']}")
        print(f"  Status: {task['status']}")
        print(f"  Result: {task['result'][:150]}...")
    
    print(f"\n{'='*60}")
    print("Final Synthesis:")
    print("="*60)
    print(result['synthesis'])


if __name__ == "__main__":
    main()
