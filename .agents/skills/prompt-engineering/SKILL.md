---
name: prompt-engineering
description: Write effective prompts for LLMs — structure, few-shot examples, chain-of-thought, system prompts, and output parsing.
user-invocable: true
---

# Prompt Engineering

Write prompts that get reliable, high-quality output from LLMs.

## Core Principles

1. **Be specific** — vague prompts get vague results
2. **Show, don't tell** — examples beat instructions
3. **Structure the output** — tell the model exactly what format you want
4. **Iterate** — prompts are code; test and refine them

## Techniques

### System Prompts

Always assign the model's role and constraints:

```
You are a senior code reviewer. Review the provided code for:
1. Security vulnerabilities
2. Performance issues
3. Readability problems

For each issue found, provide:
- Severity (critical/warning/info)
- Line number
- Description
- Suggested fix

If no issues are found, respond with "No issues found."
```

### Few-Shot Examples

Provide 2-3 examples of input → output:

```
Convert the user's natural language query to a SQL query.

Example 1:
Input: "How many users signed up last month?"
Output: SELECT COUNT(*) FROM users WHERE created_at >= DATE_TRUNC('month', NOW() - INTERVAL '1 month') AND created_at < DATE_TRUNC('month', NOW());

Example 2:
Input: "Show me the top 5 products by revenue"
Output: SELECT p.name, SUM(o.amount) as revenue FROM products p JOIN orders o ON o.product_id = p.id GROUP BY p.name ORDER BY revenue DESC LIMIT 5;

Now convert this query:
Input: "{user_query}"
Output:
```

### Chain-of-Thought

Ask the model to reason step by step:

```
Analyze this error and suggest a fix. Think step by step:
1. What does the error message mean?
2. What could cause this error?
3. What is the most likely root cause given the code context?
4. What is the fix?
```

### Constraints and Guardrails

Always include constraints to ensure the model completes the task in the most efficient way.

```
Rules:
- Only use information from the provided context
- If you don't know the answer, say "I don't know" — do not guess
- Keep responses under 200 words
- Do not include any PII in your response
```

### Structure

Always structure the prompt sections using using the following XML-style delimiters:

```
<role>
[who the model is]
</role>

<context>
[background information]
</context>

<task>
[exact task]
</task>

<constraints>
[hard requirements]
</constraints>

<reasoning_process>
[how the model should think]
</reasoning_process>

<examples>
[input/output examples]
</examples>

<output_format>
[expected structure]
</output_format>
```

## Anti-Patterns

- **Too vague**: "Make this better" → Be specific about what "better" means
- **Too long**: Giant prompts with everything → Split into focused prompts
- **Contradictory**: "Be concise but thorough" → Pick one or define the tradeoff
- **No examples**: Complex formatting without showing what you want → Add 1-2 examples
- **Prompt injection risk**: Including raw user input without delimiting → Use clear delimiters like `<user_input>...</user_input>`

## Tips

- Temperature 0 for deterministic tasks (code, classification), 0.7+ for creative tasks
- Test prompts with edge cases, not just the happy path
- Version control your prompts — they're as important as code
- Use structured output (JSON) when parsing the response programmatically
- Shorter prompts often outperform longer ones if they're precise enough