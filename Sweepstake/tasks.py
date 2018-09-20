from celery.decorators import task
from Sweepstake.management.commands import update_scores
from wc2018 import celery


@task(name="update_scores")
def update_sweepstake_scores():
    updater = update_scores.Command()
    updater.handle()


# @task(name="test")
# def test_process(num1, num2):
#     return num1*num2
