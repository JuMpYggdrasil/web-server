from flask import Flask
from flask_apscheduler import APScheduler


class Config(object):
    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()


# interval examples
@scheduler.task('interval', id='do_job_1', seconds=5, misfire_grace_time=900)
def job1():
	print('Job 1 executed')
	# print(scheduler)


# cron examples
@scheduler.task('cron', id='do_job_2', minute='*')
def job2():
	print('Job 2 executed')
	for job in scheduler.get_jobs():
		if 'do_job_1' in job.id:
			print('yes')
			scheduler.delete_job('do_job_1')
		else:
			print('no')
		#print("name: %s, trigger: %s, next run: %s, handler: %s" % (job.name, job.trigger, job.next_run_time, job.func))
		#scheduler.delete_job('do_job_4')


@scheduler.task('cron', id='do_job_3', week='*', day_of_week='sun')
def job3():
    print('Job 3 executed')


if __name__ == '__main__':
	app = Flask(__name__)
	app.config.from_object(Config())

	# it is also possible to enable the API directly
	# scheduler.api_enabled = True
	scheduler.init_app(app)
	scheduler.start()

	app.run()

