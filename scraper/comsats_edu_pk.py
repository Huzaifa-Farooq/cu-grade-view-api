import re
from scrapy.http import HtmlResponse
import requests

from scraper.items import (
    StudentProfileItem, 
    CourseScoreItem, 
    ErrorItem
    )


class ComsatsEduPkCrawler:
    def __init__(self, settings):
        self.settings = settings
        headers = {
            'authority': 'atk-cms.comsats.edu.pk:8090',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50',
        }
        self.session = requests.Session()
        self.session.headers.update(headers)
        cookies = {"ASP.NET_SessionId": self.settings.get("SESSION_ID")}
        self.session.cookies.update(cookies)

    def start_crawling(self):
        response = self.session.get(url="https://atk-cms.comsats.edu.pk:8090/")
        response = self.prepare_html_response(response)
        if "COURSEREGISTRATION" not in response.url:
            yield ErrorItem(
                error="Invalid Session ID"
            )
            return

        else:
            # for profile
            yield from self.get_profile()

            yield from self.get_courses_scores()

    def prepare_html_response(self, response):
        return HtmlResponse(
            url=response.url,
            body=response.content,
            headers=response.headers,
            status=response.status_code,
            encoding=response.encoding
        )


    def get_profile(self):
        response = self.session.get(url="https://atk-cms.comsats.edu.pk:8090/Profile/Index")
        response = self.prepare_html_response(response)
        name = response.xpath("//*[contains(text(), 'Full Name')]/parent::div/text()[2]").get().strip()
        registration_number = response.xpath("//*[contains(text(), 'Registration Number')]/parent::div/text()[2]").get().strip()
        yield StudentProfileItem(
            name=name,
            registration_number=registration_number
        )

    def set_course(self, course_url):
        r = self.session.get(url="https://atk-cms.comsats.edu.pk:8090" + course_url)
        return r

    def get_courses(self):
        response = self.session.get(url="https://atk-cms.comsats.edu.pk:8090/Courses/Index")
        response = self.prepare_html_response(response)
        courses = []

        for course in response.css("#RegisteredCourses table tbody > tr"):
            course_id = course.css("td:nth-child(1)::text").get().strip()
            course_name = course.css("td:nth-child(2)::text").get().strip()
            credit_hours = course.css("td:nth-child(3)::text").get().strip()
            teacher = course.css("td:nth-child(4)::text").get().strip()

            url = course.attrib['onclick']
            url = re.search(r"window.location='(.*)'", url).group(1)

            courses.append({
                "course_id": course_id,
                "course_name": course_name,
                "credit_hours": credit_hours,
                "teacher": teacher,
                "url": url
            })

        return courses

    def get_courses_scores(self):
        for course in self.get_courses():
            url = course["url"]
            # settings course
            self.set_course(url)
            yield from self.get_course_score(course)

    def get_course_score(self, course_metadata):
        # mrkas summary page
        r = self.session.get(url="https://atk-cms.comsats.edu.pk:8090/MarksSummary/Index")
        # course scores page
        response = self.prepare_html_response(r)
        quizes_elems = response.css("div.quiz_listing")

        # zipping adjacent div and table
        quizes = zip(quizes_elems.xpath("./div"), quizes_elems.xpath("./table"))
        for section_title_elem, quiz_table in quizes:
            section_title = section_title_elem.css("::text").get().strip()
            quiz_rows = quiz_table.css("tbody > tr")
            for quiz_row in quiz_rows:
                title = quiz_row.css("td:nth-child(1)::text").get().strip()
                marks = quiz_row.css("td:nth-child(2)::text").get().strip()
                total_marks = quiz_row.css("td:nth-child(3)::text").get().strip()
                datetime = quiz_row.css("td:nth-child(4)::text").get().strip()
                yield CourseScoreItem(
                    course_id=course_metadata["course_id"],
                    course_name=course_metadata["course_name"],
                    credit_hours=course_metadata["credit_hours"],
                    teacher=course_metadata["teacher"],
                    section_title=section_title,
                    title=title,
                    marks=marks,
                    total_marks=total_marks,
                    datetime=datetime
                )


        # attendance
        # for course in self.courses:
        #     course_id = course.css("td:nth-child(1)::text").get().strip()
        #     if course.css(".only_class_attendance"):
        #         class_attendance = course.css("div.only_class_attendance").attrib['aria-valuenow']
        #         lab_attendance = 0
