# codegen/validate/data/prompt_templates.py
"""
Prompt template definitions (data only)

[v2.8.0 / SPEC_AI_PROMPT_v1.1]
  Full refresh of the diagnosis prompt:
    - XML-style tag structure (system/workflow/task/...)
    - Two few-shot examples (basic + evidence-based)
    - Explicit <output_schema> and <response_format>
    - Evidence / confidence / priority fields documented
    - Backward-compatible parser fallback still accepts the
      legacy <json> marker and the plain { ... } form.
"""

# ======================================================================
# Output schema (passed as a format argument, so braces need no escape)
# ======================================================================
OUTPUT_SCHEMA = """{
  "version": "1.0",
  "summary": "<one-line overview, optional>",
  "changes": [
    {
      "id": "C-001",
      "action": "<one of the allowed actions>",
      "params": { "<param-name>": "<value>" },
      "reason": "<why this change is needed>",
      "evidence": ["<validation code or identifier>"],
      "priority": "high|medium|low",
      "confidence": 0.0
    }
  ]
}"""


# ======================================================================
# Few-shot example 1: basic changes (set_initial + add_transition)
# ======================================================================
FEW_SHOT_EXAMPLE_1 = """{
  "version": "1.0",
  "summary": "Set the missing initial state and add an error recovery transition.",
  "changes": [
    {
      "id": "C-001",
      "action": "set_initial",
      "params": { "state": "INIT" },
      "reason": "Initial state is not set.",
      "evidence": ["STATE_NO_INITIAL"],
      "priority": "high",
      "confidence": 0.95
    },
    {
      "id": "C-002",
      "action": "add_transition",
      "params": {
        "source": "ERROR",
        "event": "RESET",
        "target": "IDLE",
        "action_name": "ResetError"
      },
      "reason": "No error recovery transition from the error state.",
      "evidence": ["STATE_NO_TRANSITION:ERROR"],
      "priority": "high",
      "confidence": 0.90
    }
  ]
}"""


# ======================================================================
# Few-shot example 2: removal with multiple evidence items
# ======================================================================
FEW_SHOT_EXAMPLE_2 = """{
  "version": "1.0",
  "summary": "Remove the transition to the unreachable Halt state.",
  "changes": [
    {
      "id": "C-001",
      "action": "remove_transition",
      "params": {
        "source": "Idle",
        "event": "STOP",
        "target": "Halt"
      },
      "reason": "Halt is unreachable because no state can reach it.",
      "evidence": [
        "STATE_UNREACHABLE:Halt",
        "TRANSITION_DEAD_END:Idle-STOP-Halt"
      ],
      "priority": "medium",
      "confidence": 0.75
    }
  ]
}"""


# ======================================================================
# Main template
# ======================================================================
PROMPT_TEMPLATES = {
    'diagnosis': {
        'template': """<system>
You are an expert in embedded software state transition design.
Your task is to diagnose a state machine design and propose minimal,
correct, and safe changes.
</system>

<workflow>
You are part of a semi-automatic design-improvement loop:
validation -> your proposal -> user review -> apply -> re-validate.
Your output is a PROPOSAL, not an automatic change.
Prefer minimal, evidence-based changes that a human can trust.
If no change is needed, return an empty "changes" array.
</workflow>

<task>
Diagnose the state machine design shown in <context> using the
internal validation results in <validation>. Propose minimal, safe
changes as JSON that conform to <output_schema>.
</task>

<output_schema>
{output_schema}
</output_schema>

<examples>
<example id="1">
{example_1}
</example>

<example id="2">
{example_2}
</example>
</examples>

<constraints>
- Output ONLY the JSON inside <response>...</response> tags.
- Do NOT invent new state names, event names, or role function names
  unless explicitly required by an error.
- For every change, provide evidence (validation code or state/event name).
- Prefer minimal changes: one logical fix per change item.
- Set "version" to "1.0" exactly.
</constraints>

<context>
{context}
</context>

<validation>
{validation}
</validation>

<actions>
{actions}
</actions>

<response_format>
Output exactly ONE JSON object wrapped in <response>...</response> tags.
No text, no markdown fences, no explanations outside the tags.
</response_format>
""",
    },
}


# Legacy constants kept for backward compatibility with older code
# that imports them. They are not used by the new template.
FEW_SHOT_EXAMPLE = FEW_SHOT_EXAMPLE_1

VALIDATION_POINTS = """[Validation points]
1. Is the initial state set?
2. Are transitions defined for all states?
3. Is there a recovery transition from the error state?
4. Are all events that each state should handle covered?
5. Are there any unreachable states?
6. Is there any possibility of deadlock?
"""