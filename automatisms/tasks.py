from celery import task


@task
def test_task():
    print("CELERY TEST TASK RUNNING >>>>>>>>>>>>>>>>>>> OK")
