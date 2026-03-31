from datetime import date, time, datetime, timezone
from typing import Optional
import json
import os

from pawpal_system import Owner, Pet, Task, Scheduler, TaskInstance
from prettytable import PrettyTable


def build_demo_owner_from_dict(data: dict) -> Owner:
    owner = Owner(id=data.get("id", 1), name=data.get("name", "Demo Owner"), email=data.get("email"))
    owner.set_availability(data.get("availability", [{"start": time(8, 0), "end": time(18, 0)}]))

    pets = {}
    for p in data.get("pets", []):
        pet = Pet(id=p.get("id"), name=p.get("name"), species=p.get("species"), age=p.get("age"))
        owner.add_pet(pet)
        pets[pet.id] = pet

    # create tasks and attach to pets
    for t in data.get("tasks", []):
        pet_id = t.get("pet_id")
        task = Task(id=t.get("id"), pet_id=pet_id, title=t.get("title"), type=t.get("type", ""), duration_minutes=t.get("duration_minutes", 0), priority=t.get("priority", 1), earliest_time=t.get("earliest_time"), latest_time=t.get("latest_time"))
        pet = next((pp for pp in owner.pets if pp.id == pet_id), None)
        if pet:
            pet.add_task(task)

    return owner


def load_demo_fixture(path: str = "demo_fixture.json") -> Optional[Owner]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return build_demo_owner_from_dict(data)


def print_schedule_table(owner: Owner, schedule):
    tasks = {t.id: t for t in owner.get_all_tasks()}
    rows = []
    for entry in schedule.get_today_tasks():
        start = entry.scheduled_start.strftime("%H:%M") if entry.scheduled_start else "--:--"
        end = entry.scheduled_end.strftime("%H:%M") if entry.scheduled_end else "--:--"
        task = tasks.get(entry.task_id)
        title = task.title if task else f"Task {entry.task_id}"
        pet_name = None
        if task:
            pid = task.pet_id
            pet = next((p for p in owner.pets if p.id == pid), None)
            pet_name = pet.name if pet else "Unknown"
        rows.append((start, end, title, pet_name, entry.status))

    # simple table print
    print(f"Today's Schedule for {owner.name} ({schedule.date}):\n")
    print(f"{'Start':<6} {'End':<6} {'Task':<30} {'Pet':<15} {'Status':<10}")
    print("-" * 75)
    for r in rows:
        print(f"{r[0]:<6} {r[1]:<6} {r[2]:<30} {r[3]:<15} {r[4]:<10}")
    print("\n", schedule.summarize())


def main():
    # Try to load demo fixture first
    owner = load_demo_fixture()
    if owner is None:
        # fallback: create a simple seeded demo
        owner = Owner(id=1, name="Alice", email="alice@example.com")
        owner.set_availability([
            {"start": time(8, 0), "end": time(12, 0)},
            {"start": time(14, 0), "end": time(18, 0)},
        ])

        pet1 = Pet(id=1, name="Buddy", species="Dog", age=4)
        pet2 = Pet(id=2, name="Milo", species="Cat", age=2)
        owner.add_pet(pet1)
        owner.add_pet(pet2)

        # Add tasks intentionally out of chronological order to test sorting
        t1 = Task(id=1, pet_id=pet1.id, title="Morning Walk", type="walk", duration_minutes=30, priority=5,
              earliest_time=time(9, 15), latest_time=time(10, 0), requires_walker=True)
        t2 = Task(id=2, pet_id=pet1.id, title="Feed Breakfast", type="feed", duration_minutes=10, priority=10,
              earliest_time=time(7, 30), latest_time=time(9, 0))
        t3 = Task(id=3, pet_id=pet2.id, title="Give Medication", type="med", duration_minutes=5, priority=9,
              earliest_time=time(12, 0), latest_time=time(20, 0))

        # out-of-order additions
        t4 = Task(id=4, pet_id=pet1.id, title="Evening Walk", type="walk", duration_minutes=20, priority=4,
              earliest_time=time(18, 0), latest_time=time(19, 0))
        t5 = Task(id=5, pet_id=pet2.id, title="Noon Play", type="play", duration_minutes=15, priority=3,
              earliest_time=time(11, 30), latest_time=time(12, 30))

        # add to pets in a non-chronological order
        pet1.add_task(t1)
        pet1.add_task(t4)
        pet1.add_task(t2)
        pet2.add_task(t3)
        pet2.add_task(t5)

        # mark one task as completed to test filtering
        t2.last_performed = datetime.now(timezone.utc)

    # Run scheduler
    sched = Scheduler(date=date.today())
    sched.run_metadata["owner"] = owner
    try:
        schedule = sched.generate_plan()
    except Exception as e:
        print(f"Scheduling failed: {e}")
        return

    # --- simulate/introduce an overlapping pair to demonstrate conflict detection ---
    # create two TaskInstance objects scheduled at the same time (09:00-09:30)
    from datetime import datetime as _dt, timedelta as _td
    overlap_start = _dt.combine(schedule.date, time(9, 0)).replace(tzinfo=timezone.utc)
    overlap_end = overlap_start + (schedule.entries[0].scheduled_end - schedule.entries[0].scheduled_start if schedule.entries and schedule.entries[0].scheduled_start and schedule.entries[0].scheduled_end else _td(minutes=30))
    # pick two tasks (if available) to overlap; otherwise skip
    all_tasks = owner.get_all_tasks()
    if len(all_tasks) >= 2:
        # build TaskInstance directly
        ti_a = TaskInstance(task_id=all_tasks[0].id, date=schedule.date, scheduled_start=overlap_start, scheduled_end=overlap_end)
        ti_b = TaskInstance(task_id=all_tasks[1].id, date=schedule.date, scheduled_start=overlap_start, scheduled_end=overlap_end)
        schedule.add_entry(ti_a)
        schedule.add_entry(ti_b)

    # detect conflicts and print warnings (lightweight)
    conflicts = sched.detect_conflicts(schedule)
    if conflicts:
        print('\n-- Schedule warnings:')
        for a, b, reason in conflicts:
            print(f"WARNING: {reason} between task_id={a.task_id} and task_id={b.task_id} (start {a.scheduled_start} - {b.scheduled_start})")

    # Demonstrate sorting and filtering
    print("\n-- Raw schedule entries (unsorted):")
    for e in schedule.entries:
        print(repr((e.task_id, e.scheduled_start, e.scheduled_end)))

    print("\n-- Sorted entries by start time using scheduler.sort_by_time:")
    sorted_entries = sched.sort_by_time(schedule.get_today_tasks(), "scheduled_start")
    for e in sorted_entries:
        print(f"{e.scheduled_start.strftime('%H:%M') if e.scheduled_start else '--:--'} - {e.scheduled_end.strftime('%H:%M') if e.scheduled_end else '--:--'} : task {e.task_id}")

    print("\n-- Tasks filtered for pet 'Buddy' (incomplete):")
    filtered = owner.filter_tasks(pet_name="Buddy", completed=False)
    for t in filtered:
        print(f"- {t.title} (id={t.id}) earliest={t.earliest_time}")

    print("\n-- Tasks filtered for completed tasks:")
    completed = owner.filter_tasks(completed=True)
    for t in completed:
        print(f"- {t.title} (id={t.id}) last_performed={t.last_performed}")

    print_schedule_table(owner, schedule)


    # also print a prettier table using PrettyTable
    table = PrettyTable()
    table.field_names = ["Start", "End", "Task", "Pet", "Status"]
    id_to_title = {t.id: t.title for t in owner.get_all_tasks()}
    id_to_pet = {t.id: t.pet_id for t in owner.get_all_tasks()}
    for e in schedule.get_today_tasks():
        start = e.scheduled_start.strftime('%H:%M') if e.scheduled_start else '--:--'
        end = e.scheduled_end.strftime('%H:%M') if e.scheduled_end else '--:--'
        title = id_to_title.get(e.task_id, f"Task {e.task_id}")
        pet_id = id_to_pet.get(e.task_id)
        pet = next((p for p in owner.pets if p.id == pet_id), None)
        pet_name = pet.name if pet else ''
        table.add_row([start, end, title, pet_name, e.status])
    print("\nPretty schedule table:")
    print(table)


if __name__ == "__main__":
    main()
