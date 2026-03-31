from datetime import date, datetime, time, timedelta, timezone
import pytest

from pawpal_system import Task, TaskInstance, Owner, Pet, Scheduler, DailySchedule


def test_next_occurrence_daily():
    t = Task(id=1, pet_id=1, title="daily-task", recurrence_rule="daily")
    d = date(2026, 3, 31)
    assert t.next_occurrence(d) == d + timedelta(days=1)


def test_mark_done_creates_next_instance():
    t = Task(id=2, pet_id=1, title="daily-task", recurrence_rule="daily")
    performed = datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc)
    ti = t.mark_done(performed)
    assert isinstance(ti, TaskInstance)
    assert ti.date == date(2026, 4, 1)


def test_detect_conflicts_same_pet():
    owner = Owner(id=1, name="Owner A")
    pet = Pet(id=1, name="Buddy", species="dog")
    owner.add_pet(pet)

    # two tasks belonging to same pet
    t1 = Task(id=1, pet_id=pet.id, title="t1", duration_minutes=30)
    t2 = Task(id=2, pet_id=pet.id, title="t2", duration_minutes=20)
    pet.add_task(t1)
    pet.add_task(t2)

    sched = Scheduler(date=date(2026, 3, 31))
    sched.run_metadata["owner"] = owner

    # build a DailySchedule and add overlapping TaskInstances
    schedule = DailySchedule(date=date(2026, 3, 31), owner_id=owner.id)
    start = datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc)
    ti1 = TaskInstance(task_id=1, date=schedule.date, scheduled_start=start, scheduled_end=start + timedelta(minutes=30))
    ti2 = TaskInstance(task_id=2, date=schedule.date, scheduled_start=start + timedelta(minutes=10), scheduled_end=start + timedelta(minutes=40))
    schedule.add_entry(ti1)
    schedule.add_entry(ti2)

    conflicts = sched.detect_conflicts(schedule)
    assert any(r == "same-pet overlap" for (_, _, r) in conflicts)


def test_sort_by_time_mixed_types():
    sched = Scheduler()
    items = [
        {"scheduled_start": "09:00"},
        {"scheduled_start": time(8, 0)},
        {"scheduled_start": datetime(2026, 3, 31, 10, 0)},
        {"scheduled_start": datetime(2026, 3, 31, 7, 0, tzinfo=timezone.utc)},
    ]

    sorted_items = sched.sort_by_time(items, "scheduled_start")

    def to_hour(item):
        v = item["scheduled_start"]
        if isinstance(v, str):
            return int(v.split(":")[0])
        if isinstance(v, time):
            return v.hour
        if isinstance(v, datetime):
            return v.hour
        return None

    hours = [to_hour(i) for i in sorted_items]
    assert hours == [7, 8, 9, 10]


def test_get_today_tasks_ordering():
    # ensure get_today_tasks returns entries ordered by scheduled_start
    schedule = DailySchedule(date=date(2026, 3, 31), owner_id=1)
    # out of order entries: aware and naive datetimes
    a = datetime(2026, 3, 31, 10, 0, tzinfo=timezone.utc)
    b = datetime(2026, 3, 31, 8, 0)  # naive
    c = datetime(2026, 3, 31, 9, 30, tzinfo=timezone.utc)
    ti_a = TaskInstance(task_id=1, date=schedule.date, scheduled_start=a, scheduled_end=a + timedelta(minutes=10))
    ti_b = TaskInstance(task_id=2, date=schedule.date, scheduled_start=b, scheduled_end=b + timedelta(minutes=15))
    ti_c = TaskInstance(task_id=3, date=schedule.date, scheduled_start=c, scheduled_end=c + timedelta(minutes=20))
    # add in mixed order
    schedule.add_entry(ti_a)
    schedule.add_entry(ti_c)
    schedule.add_entry(ti_b)

    ordered = schedule.get_today_tasks()
    starts = [((e.scheduled_start.astimezone(timezone.utc) if e.scheduled_start.tzinfo else e.scheduled_start.replace(tzinfo=timezone.utc)).hour) for e in ordered]
    assert starts == [8, 9, 10]


def test_detect_conflicts_duplicate_times():
    owner = Owner(id=1, name="Owner B")
    pet1 = Pet(id=1, name="A", species="dog")
    pet2 = Pet(id=2, name="B", species="cat")
    owner.add_pet(pet1)
    owner.add_pet(pet2)
    t1 = Task(id=1, pet_id=pet1.id, title="t1", duration_minutes=10)
    t2 = Task(id=2, pet_id=pet2.id, title="t2", duration_minutes=10)
    pet1.add_task(t1)
    pet2.add_task(t2)

    sched = Scheduler(date=date(2026, 3, 31))
    sched.run_metadata["owner"] = owner

    schedule = DailySchedule(date=date(2026, 3, 31), owner_id=owner.id)
    start = datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc)
    ti1 = TaskInstance(task_id=1, date=schedule.date, scheduled_start=start, scheduled_end=start + timedelta(minutes=10))
    ti2 = TaskInstance(task_id=2, date=schedule.date, scheduled_start=start, scheduled_end=start + timedelta(minutes=10))
    schedule.add_entry(ti1)
    schedule.add_entry(ti2)

    conflicts = sched.detect_conflicts(schedule)
    # expect at least one time overlap warning
    assert any(r in ("time overlap", "walker conflict", "same-pet overlap") for (_, _, r) in conflicts)
