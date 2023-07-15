import scrapy
import re


from portal.items import (
    StudentProfileItem, 
    CourseScoreItem, 
    ErrorItem
    )


class ComsatsEduPkSpider(scrapy.Spider):
    name = "comsats.edu.pk"
    allowed_domains = ["comsats.edu.pk"]
    start_urls = ["http://comsats.edu.pk/"]

    headers = {
        'authority': 'atk-cms.comsats.edu.pk:8090',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'referer': 'https://atk-cms.comsats.edu.pk:8090/Announcements',
        'sec-ch-ua': '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50',
    }

    courses = None

    def start_requests(self):
        session_id = self.settings.get("SESSION_ID")
        self.cookies = {"ASP.NET_SessionId": session_id}
        yield scrapy.Request(
            url="https://atk-cms.comsats.edu.pk:8090/",
            cookies=self.cookies,
            callback=self.parse,
            headers=self.headers
        )
    
    def parse(self, response):
        if "COURSEREGISTRATION" not in response.url:
            yield ErrorItem(
                error="Invalid Session ID"
            )
            return

        # for course scores
        yield scrapy.Request(
            url="https://atk-cms.comsats.edu.pk:8090/Courses/Index",
            cookies=self.cookies,
            callback=self.parse_index,
            headers=self.headers
        )

        # for student profile
        yield scrapy.Request(
            url="https://atk-cms.comsats.edu.pk:8090/Profile/Index",
            cookies=self.cookies,
            callback=self.parse_profile,
            headers=self.headers
        )

    def parse_profile(self, response):
        name = response.xpath("//*[contains(text(), 'Full Name')]/parent::div/text()[2]").get().strip()
        registration_number = response.xpath("//*[contains(text(), 'Registration Number')]/parent::div/text()[2]").get().strip()
        yield StudentProfileItem(
            name=name,
            registration_number=registration_number
        )

    def get_course_request(self):
        if self.courses:
            course = self.courses.pop(0)
            course_id = course.css("td:nth-child(1)::text").get().strip()
            course_name = course.css("td:nth-child(2)::text").get().strip()
            credit_hours = course.css("td:nth-child(3)::text").get().strip()
            teacher = course.css("td:nth-child(4)::text").get().strip()

            url = course.attrib['onclick']
            url = re.search(r"window.location='(.*)'", url).group(1)
            # settings course
            return scrapy.Request(
                url="https://atk-cms.comsats.edu.pk:8090" + url,
                callback=self.parse_course,
                headers=self.headers,
                cookies=self.cookies,
                meta={
                    "course_id": course_id,
                    "course_name": course_name,
                    "credit_hours": credit_hours,
                    "teacher": teacher,
                },
                dont_filter=True,
            )


    def parse_index(self, response):
        self.courses = response.css("#RegisteredCourses table tbody > tr")
        yield self.get_course_request()

        # attendance
        # for course in self.courses:
        #     course_id = course.css("td:nth-child(1)::text").get().strip()
        #     if course.css(".only_class_attendance"):
        #         class_attendance = course.css("div.only_class_attendance").attrib['aria-valuenow']
        #         lab_attendance = 0

    def parse_course(self, response):
        yield scrapy.Request(
            url=response.urljoin("/MarksSummary/Index"),
            callback=self.parse_marks,
            headers=self.headers,
            cookies=self.cookies,
            meta=response.meta,
            dont_filter=True,
        )
    
    def parse_marks(self, response):
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
                    course_id=response.meta["course_id"],
                    course_name=response.meta["course_name"],
                    credit_hours=response.meta["credit_hours"],
                    teacher=response.meta["teacher"],
                    section_title=section_title,
                    title=title,
                    marks=marks,
                    total_marks=total_marks,
                    datetime=datetime
                )

        if self.courses:
            yield self.get_course_request()
  