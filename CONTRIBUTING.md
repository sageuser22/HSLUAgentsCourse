# Contributing to HSLU Agents Course

Thank you for your interest in contributing! This document provides guidelines for contributing to the course.

## Ways to Contribute

1. **Add New Examples**: Create examples that demonstrate interesting use cases
2. **Improve Documentation**: Enhance existing docs or add new guides
3. **Fix Bugs**: Report or fix issues you encounter
4. **Add Features**: Propose and implement new modules or capabilities
5. **Share Feedback**: Provide feedback on the course structure and content

## Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/HSLUAgentsCourse.git
   cd HSLUAgentsCourse
   ```
3. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Set up development environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Code Guidelines

### Style

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### Documentation

- Add docstrings to all classes and functions
- Use Google-style docstrings
- Include type hints where appropriate
- Comment complex logic

Example:
```python
def process_data(input_text: str, temperature: float = 0.7) -> dict:
    """
    Process input text using LLM.
    
    Args:
        input_text: The text to process
        temperature: Temperature for generation (default: 0.7)
    
    Returns:
        dict: Processed results with keys 'output' and 'metadata'
    
    Raises:
        ValueError: If input_text is empty
    """
    # Implementation
```

### Module Structure

When adding a new module:

```
src/moduleN_name/
├── __init__.py          # Exports main classes
├── main_component.py    # Primary functionality
└── README.md           # Module-specific documentation (optional)
```

### Testing

Before submitting:

1. **Test imports:**
   ```python
   python -c "from src.your_module import YourClass"
   ```

2. **Run your module:**
   ```python
   python -m src.your_module.your_file
   ```

3. **Check for errors:**
   - Syntax errors
   - Import errors
   - Runtime errors

## Adding Examples

Examples should:

1. **Be practical**: Demonstrate real-world use cases
2. **Be documented**: Include comments explaining the logic
3. **Be runnable**: Work without modification (except API key)
4. **Be educational**: Teach a concept or pattern

Example structure:
```python
"""
Example: Brief Description

This example demonstrates:
1. Concept 1
2. Concept 2
3. Concept 3
"""

from src.module1 import Component1
from src.module2 import Component2

def main():
    """Run the example."""
    print("Example: Your Example Name")
    print("="*60)
    
    # Step 1: Setup
    component = Component1()
    
    # Step 2: Execute
    result = component.process("example input")
    
    # Step 3: Display
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

## Adding New Modules

For significant new modules:

1. **Propose first**: Open an issue describing the module
2. **Follow the pattern**: Look at existing modules for structure
3. **Include examples**: Add at least one runnable example
4. **Document thoroughly**: Add module documentation

Module checklist:
- [ ] `__init__.py` with exports
- [ ] Main implementation file
- [ ] Docstrings for all public methods
- [ ] At least one example
- [ ] Updated main README.md
- [ ] Module-specific README (if complex)

## Pull Request Process

1. **Update documentation**: Ensure docs reflect your changes
2. **Test thoroughly**: Verify everything works
3. **Write clear commit messages:**
   ```
   Add: Description of what was added
   Fix: Description of what was fixed
   Update: Description of what was updated
   ```
4. **Create pull request:**
   - Use a clear title
   - Describe what changed and why
   - Link to related issues
   - Include screenshots if UI changes

## Code Review

Pull requests will be reviewed for:

- **Functionality**: Does it work as intended?
- **Code quality**: Is it well-written and maintainable?
- **Documentation**: Is it properly documented?
- **Consistency**: Does it follow existing patterns?
- **Testing**: Has it been tested?

## Issue Guidelines

When reporting issues:

1. **Use a clear title**: Describe the problem concisely
2. **Provide context:**
   - What were you trying to do?
   - What did you expect to happen?
   - What actually happened?
3. **Include details:**
   - Python version
   - Operating system
   - Relevant code snippets
   - Error messages
4. **Minimal reproduction**: Provide minimal code to reproduce

## Feature Requests

When proposing features:

1. **Describe the use case**: Why is this needed?
2. **Explain the benefit**: How does this help learners?
3. **Suggest implementation**: How might it work?
4. **Consider alternatives**: What other approaches exist?

## Questions and Support

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Feature requests**: Open a GitHub Issue with "Feature Request" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- The README.md contributors section
- Release notes
- Commit history

## Getting Help

If you need help contributing:

1. Check existing documentation
2. Look at similar examples in the codebase
3. Open a Discussion for guidance
4. Reach out to maintainers

Thank you for contributing to HSLU Agents Course! 🎓
