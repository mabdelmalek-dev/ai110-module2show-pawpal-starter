# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

This project includes a lightweight scheduling engine with a few practical
features to make daily planning useful and explainable:

- Scoring-based greedy selection: tasks are scored by a small heuristic that
	combines priority, recency (how recently a task was performed), duration,
	and whether a candidate time fits the task's earliest/latest constraints.
- One-step lookahead: when choosing the next task for a time window the
	scheduler briefly considers the best immediate follow-up to avoid locally
	poor choices.
- Sorting & filtering helpers: utilities to present schedule entries by start
	time and to filter tasks by pet name and completion state.
- Lightweight conflict detection: the scheduler detects overlapping entries
	and reports warnings (same-pet overlap, walker conflicts, or generic time
	overlaps) instead of raising exceptions so the UI can surface warnings to
	the user and allow manual resolution.

These choices favor clarity, speed, and explainability over perfect
optimality. The code is structured so the heuristic can be replaced with a
solver-backed approach for larger or more constrained cases.
