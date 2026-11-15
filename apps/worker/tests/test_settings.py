from f1_worker.settings import WorkerSettings, standings_task


def test_standings_scheduled_every_30_minutes_and_unique() -> None:
    job = next(j for j in WorkerSettings.cron_jobs if j.coroutine is standings_task)
    assert job.minute == {0, 30}
    assert job.unique is True


def test_standings_registered_as_function() -> None:
    assert standings_task in WorkerSettings.functions
