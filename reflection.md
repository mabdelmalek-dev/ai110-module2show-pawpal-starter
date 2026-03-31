# PawPal+ Project Reflection

## 1. System Design

Three core user actions in PawPal+ are:

-Add and manage pet care tasks with duration and priority.

-Generate a daily schedule based on available time and task importance.

-View today's planned tasks with explanations for scheduling decisions.

**a. Initial design**

- Briefly describe your initial UML design.
I started with a simple design based on the owner, the pet, and the tasks that need to be done each day.

The Owner stores basic information like contact details, available time, and preferences, because these affect scheduling.

The Pet keeps simple pet information such as name, routines, and medical notes that may affect care needs.

A Task represents a care activity like feeding, walking, or medication, with details such as duration and priority.

A TaskInstance is one scheduled version of a task for a specific day and tracks whether it was completed.

Constraints are used to apply rules like available time or preferred task times.

The Scheduler / Planner is the main part that decides which tasks fit into the day and creates a DailySchedule, which is the final ordered list of tasks.

Notification and Explanation support the system by sending reminders and showing why certain tasks were chosen or skipped.

Finally, Storage is used to save tasks and schedules so the information can be reused later.
- What classes did you include, and what responsibilities did you assign to each?

Owner: Keeps basic information about the pet owner, like name, daily free time, and preferences. This helps decide when tasks can be scheduled.

Pet: Stores simple pet details such as name, type of animal, age, and any special care notes.

Task: Describes a care activity like feeding, walking, or giving medicine, including how long it takes and how important it is.

TaskInstance: Represents one specific time a task is planned for a day and whether it is completed or not.

Constraints / Preferences: Holds rules such as available time, preferred hours, or limits on how many tasks fit in one day.

Scheduler / Planner: Chooses which tasks should go into the daily plan based on priority and available time.

DailySchedule: Stores the final list of tasks for the day in order.

Notification / Reminder: Used for reminders so the owner knows when a task should happen.

Explanation: Gives a short reason for why a task was selected or skipped.

Storage / Repository: Saves tasks and schedules so the data can be used later.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. While moving from the initial UML to code I made a focused change to keep responsibilities clear:

- **Added a `Scheduler` class** to `pawpal_system.py`. Originally the plan described a scheduler conceptually, but I hadn't created a concrete class for it in the codebase. I added a `Scheduler` skeleton that will own the plan-generation flow (task scoring, fitting tasks into owner availability, applying `Constraints`, and producing a `DailySchedule`).

Why: without a dedicated `Scheduler` the planning logic tends to drift into UI code, task objects, or storage code which makes the algorithm hard to test and evolve. Centralizing planning in `Scheduler` keeps the system modular, makes it easier to unit-test scheduling decisions, and reduces coupling between persistence/UI and the core algorithm.

(If I make further refactors — for example moving `Notification` scheduling to a small `Notifier` service or adding an ID/locking helper for concurrent updates — I'll document them here.)

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff the current scheduler makes is using a fast greedy selection with a tiny (one-step) lookahead instead of solving a global optimization (for example, an integer linear program) that would guarantee an optimal ordering.

- **Tradeoff:** Greedy + 1-step lookahead vs. global optimal planning.

- **Implication:** The greedy approach is much faster and easier to reason about and test, and it keeps the code simple and interactive for a UI-driven workflow. However, it can miss globally optimal schedules — particularly in edge cases where a lower-priority short task should be deferred to make room for a later high-value task whose placement depends on the first decision.

- **Why this is reasonable:** For a consumer-facing pet-care helper the task set per day is typically small (a handful of tasks), and responsiveness and explainability matter: owners expect quick results and clear reasoning. The greedy heuristic produces useful schedules quickly and lets us expose simple, human-understandable scoring rules (priority, recency, duration, time-window fit). When stronger guarantees are required, the codebase is structured so a future ILP/CP solver can be added as an optional backend for harder cases.

Decision about a code simplification suggestion:

I reviewed a possible simplification of `score_task_for_slot()` that an AI suggested: condensing the scoring logic into shorter, more "Pythonic" expressions (e.g., single-line computations, more compact recency math, and chained ternaries). While those changes would reduce LOC, they would also make the scoring function harder for future readers (students and maintainers) to inspect and tune. Because the scoring weights are intentionally simple and expected to be tuned by hand, I decided to keep the more explicit, step-by-step implementation — it trades a bit of conciseness for clarity and easier manual tuning.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
