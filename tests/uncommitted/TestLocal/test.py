import logging
import os

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from applitools.selenium import logger, Eyes, Target, ClassicRunner

runner = ClassicRunner()

eyes = Eyes(runner)

eyes.save_debug_screenshots = True

driver = webdriver.Chrome(ChromeDriverManager().install())

logger.set_logger(logger.StdoutLogger(level=logging.DEBUG))

try:
    driver.get(
        "file:///Users/serhii/Projects/WORK/APPLITOOLS/eyes.sdk.python/tests/uncommitted/TestLocal/Webpage/MobileView For Alon.html"
    )

    driver = eyes.open(driver, "Stanley", "#34367", {"width": 1200, "height": 700})

    frame1 = driver.find_element_by_css_selector("#mainFrame")
    driver.switch_to.frame(frame1)
    frame2 = driver.find_element_by_css_selector("#angularContainerIframe")
    driver.switch_to.frame(frame2)

    checked_element = driver.find_element_by_css_selector("#highcharts-04fphv9-0")
    eyes.check("Step 1", Target.region(checked_element))

    eyes.close_async()
except Exception as e:
    print(str(e))
    eyes.abort_async()
finally:
    driver.quit()
    results = runner.get_all_test_results()
    print(results)
