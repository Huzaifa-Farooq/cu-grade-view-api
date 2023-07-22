from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from portal.spiders.comsats_edu_pk import ComsatsEduPkSpider

from multiprocessing import Pool


def start_scraper(session_id):
    # Create a CrawlerProcess instance
    process = CrawlerProcess(settings={
        **get_project_settings(),
        "SESSION_ID": session_id,
        # "LOG_FILE": "Logs/{}.log".format(session_id),
    })
    process.crawl(ComsatsEduPkSpider)
    process.start()


# start_scraper("n0x0sfkmilu1xpibjdo4v4mb")
