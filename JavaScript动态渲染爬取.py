# 导入Selenium库相关模块
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
import logging
from os import makedirs
from os.path import exists
import json
import re
import time
import random
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urljoin

# 创建结果目录（如果不存在）
RESULTS_DIR = 'results'
exists(RESULTS_DIR) or makedirs(RESULTS_DIR)

# 配置日志记录
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 网站URL配置
index_url = 'https://www.maoyan.com/films?showType=3&offset={page}'
time_out = 15  # 增加超时时间
index_page = 10

# 初始化WebDriver
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_experimental_option('useAutomationExtension', False)
# 添加防检测选项
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")

service = Service('chromedriver.exe')
driver = webdriver.Chrome(service=service, options=options)

# 隐藏自动化痕迹
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.navigator.chrome = { runtime: {} };
    '''
})

wait = WebDriverWait(driver, time_out)



def human_like_action():
    """模拟人类交互行为"""
    try:
        # 随机移动鼠标
        action = ActionChains(driver)
        for _ in range(random.randint(1, 3)):
            x = random.randint(0, driver.get_window_size()['width'])
            y = random.randint(0, driver.get_window_size()['height'])
            action.move_to_element_with_offset(driver.find_element(By.TAG_NAME, 'body'), x, y)
            action.pause(0.1)
            action.perform()

        # 随机滚动页面
        scroll_amount = random.randint(200, 800)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
        time.sleep(random.uniform(0.5, 1.5))
    except:
        pass


def scrape_page(url, condition, locator):
    """
    通用页面爬取函数（添加人类行为模拟）
    """
    logging.info('开始爬取 %s', url)
    try:
        # 随机延迟
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)

        driver.get(url)

        # 人类行为模拟
        human_like_action()

        wait.until(condition(locator))

        # 再次模拟人类行为
        human_like_action()

        # 增加页面停留时间
        time.sleep(random.uniform(1.0, 3.0))
    except TimeoutException:
        logging.error('爬取有问题 %s', url, exc_info=True)


def scrape_index(page):
    url = index_url.format(page=page * 30)
    scrape_page(url, condition=EC.visibility_of_element_located,
                locator=(By.CSS_SELECTOR, '.channel-detail.movie-item-title'))


def parse_index():
    elements = driver.find_elements(By.CSS_SELECTOR, '.channel-detail.movie-item-title > a')
    for element in elements:
        href = element.get_attribute('href')
        yield urljoin(index_url, href)


def scrape_detail(url):
    scrape_page(url, condition=EC.visibility_of_element_located,
                locator=(By.TAG_NAME, 'h1'))


def parse_detail():
    url = driver.current_url
    names = driver.find_element(By.TAG_NAME, 'h1').text
    categories = [element.text for element in driver.find_elements(
        By.CSS_SELECTOR, '.text-link')]
    cover = driver.find_element(By.CSS_SELECTOR, '.avatar').get_attribute('src')
    drama = driver.find_element(By.CSS_SELECTOR, '.mod-content > .dra').text

    return {
        'url': url,
        'name': names,
        'categories': categories,
        'cover': cover,
        'drama': drama
    }


def save_data(data):
    name = data.get('name')
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    data_path = f'{RESULTS_DIR}/{name}.json'
    json.dump(data, open(data_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)


# 添加会话重置函数
def reset_session():
    """重置会话状态以减少被检测风险"""
    try:
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        logging.info("已重置会话状态")
    except:
        pass


def main():
    try:
        # 遍历每一页索引页
        for page in range(0, index_page):
            # 每处理2页重置一次会话
            if page > 0 and page % 2 == 0:
                reset_session()
                time.sleep(random.uniform(2, 5))  # 重置后休息

            scrape_index(page)
            detail_urls = parse_index()
            for i, detail_url in enumerate(list(detail_urls)):
                logging.info('正在爬取 %s', detail_url)
                scrape_detail(detail_url)
                detail_data = parse_detail()
                logging.info('爬取内容 %s', detail_data)
                save_data(detail_data)

                # 每处理5个详情页休息一次
                if (i + 1) % 5 == 0:
                    rest_time = random.uniform(3, 8)
                    logging.info('休息 %.1f 秒...', rest_time)
                    time.sleep(rest_time)

    finally:
        driver.close()


if __name__ == '__main__':
    main()