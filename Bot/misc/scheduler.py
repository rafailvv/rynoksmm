from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore



jobstores = {
    'default': RedisJobStore(jobs_key='scheduler.jobs', run_times_key='scheduler.run_times', host='localhost', port=6379, db=0)
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

