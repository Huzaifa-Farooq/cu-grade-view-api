
from scraper.pipelines import PortalPipeline
from scraper.comsats_edu_pk import ComsatsEduPkCrawler


def run_scraper(session_id):
    crawler = ComsatsEduPkCrawler(settings={
        "SESSION_ID": session_id
    })
    pipeline = PortalPipeline(session_id=session_id)
    for item in crawler.start_crawling():
        pipeline.process_item(item)
        print(item)

    pipeline.close_pipeline()
    pipeline.add_data_to_db()

