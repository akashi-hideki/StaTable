# codegen/validate/data/prompt_templates.py
"""
Prompt template definitions (data only)

[v1.8 section 11.2 #7]
  - Removed unused 'review' key
    (removed together with prompt_generator.generate_review_prompt)
"""

PROMPT_TEMPLATES = {
    'diagnosis': {
        'template': """You are an expert in embedded software state transition design.

[Task]
Validate state transition design data and output necessary changes in JSON format.

[Output format]
Output pure JSON only.
No greetings, descriptions, supplements, markers, or code block symbols.

[Output example]
{example}

[Actual data]
{data}

[Instructions]
Propose changes to the actual data using the same JSON format as the example.
Do not output anything other than JSON.

{action_definitions}

{validation_points}
""",
    },
}

FEW_SHOT_EXAMPLE = """{
  "changes": [
    {
      "action": "set_initial",
      "params": {"state": "INIT"},
      "reason": "Initial state is not set"
    },
    {
      "action": "add_transition",
      "params": {
        "source": "ERROR",
        "event": "RESET",
        "target": "IDLE",
        "action_name": "ResetError"
      },
      "reason": "No error recovery transition from the error state"
    }
  ]
}"""

VALIDATION_POINTS = """[Validation points]
1. Is the initial state set?
2. Are transitions defined for all states?
3. Is there a recovery transition from the error state?
4. Are all events that each state should handle covered?
5. Are there any unreachable states?
6. Is there any possibility of deadlock?
"""