# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import sys

sys.path.append("..")

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from database import DataBase
from task import Task

from portal.items import (
    StudentProfileItem, 
    CourseScoreItem, 
    AttendanceItem,
    ErrorItem
    )

import json


class PortalPipeline:
    def open_spider(self, spider):
        self.task_id = spider.settings.get("SESSION_ID")
        self.db = DataBase()

        self.items = []

        # update task status to IN_PROGRESS
        self.db.create_task(self.task_id)
        self.db.update_task_status(self.task_id, Task.IN_PROGRESS)

    def process_item(self, item, spider):
        if isinstance(item, ErrorItem):
            # update task status to FAILED
            self.close_spider(spider)
            self.db.update_task_status(self.task_id, Task.FAILED, item['error'])
            return {}
        elif isinstance(item, StudentProfileItem):
            self.db.add_student_profile_data(self.task_id, item)
        elif isinstance(item, CourseScoreItem) or isinstance(item, AttendanceItem):
            self.items.append(item)
            if len(self.items) >= 100:
                self.add_data_to_db()
        return item

    def close_spider(self, spider):
        self.add_data_to_db()
        # update task status
        task = self.db.get_task(self.task_id)
        if task.status != Task.FAILED:
            self.db.update_task_status(self.task_id, Task.SUCCESS)

    def add_data_to_db(self):
        self.db.create_task(self.task_id)
        course_score_items = [i for i in self.items if isinstance(i, CourseScoreItem)]
        self.db.add_course_score_data(self.task_id, course_score_items)
        attendance_items = [i for i in self.items if isinstance(i, AttendanceItem)]
        self.db.add_attendance_data(self.task_id, attendance_items)
        self.items = []
