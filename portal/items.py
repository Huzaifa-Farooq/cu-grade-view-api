# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


# item as a dict
class CourseScoreItem(scrapy.Item):
    course_id = scrapy.Field()
    course_name = scrapy.Field()
    credit_hours = scrapy.Field()
    teacher = scrapy.Field()
    section_title = scrapy.Field()
    title = scrapy.Field()
    marks = scrapy.Field()
    total_marks = scrapy.Field()
    datetime = scrapy.Field()


class StudentProfileItem(scrapy.Item):
    name = scrapy.Field()
    registration_number = scrapy.Field()


class AttendanceItem(scrapy.Item):
    course_id = scrapy.Field()
    attendance_type = scrapy.Field()
    topic = scrapy.Field()
    attended = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()


class ErrorItem(scrapy.Item):
    url = scrapy.Field()
    error = scrapy.Field()
