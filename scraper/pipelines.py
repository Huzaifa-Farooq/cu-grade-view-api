# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html



# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from database import DataBase
from task import Task

from scraper.items import (
    StudentProfileItem, 
    CourseScoreItem, 
    ErrorItem
    )


class PortalPipeline:
    def __init__(self, session_id):
        self.task_id = session_id
        self.db = DataBase()

        self.items = []

        # update task status to IN_PROGRESS
        self.db.update_task_status(self.task_id, Task.IN_PROGRESS)

    def process_item(self, item):
        if isinstance(item, ErrorItem):
            # update task status to FAILED
            self.db.update_task_status(self.task_id, Task.FAILED, item['error'])
        elif isinstance(item, StudentProfileItem):
            self.db.add_student_profile_data(self.task_id, item)
        elif isinstance(item, CourseScoreItem):
            self.items.append(item)
            if len(self.items) >= 100:
                self.add_data_to_db()

    def close_pipeline(self):
        self.add_data_to_db()
        # update task status
        task = self.db.get_task(self.task_id)
        if task.status != Task.FAILED:
            self.db.update_task_status(self.task_id, Task.SUCCESS)

    def add_data_to_db(self):
        self.db.add_course_score_data(self.task_id, self.items)
        self.items = []
