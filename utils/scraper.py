from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
import praw
import datetime
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, \
    ElementClickInterceptedException, NoSuchWindowException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from praw.exceptions import InvalidURL
import pandas as pd
from pathlib import Path
from selenium.webdriver.chrome.options import Options



output_path = str(Path(__file__).parent.parent.resolve()) + '/output'



def search_keywords_in_reddit(keywords):
    result = {}

    reddit = praw.Reddit(client_id='8y1pAV6ILIGM-qFHoDpwyA',
                         client_secret='x5ggjG-_hKk9kjdH9H-RpKpakWdhAw',
                         user_agent='bootcamp_review')

    # # open a new window and open reddit
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--start-maximized')
    # chrome_options.add_argument('--no-proxy-server')
    # chrome_options.add_argument("--proxy-server='direct://'")
    # chrome_options.add_argument("--proxy-bypass-list=*")
    # chrome_options.binary_location = "/Users/raolu/airflow/utils/chromedriver"
    # chrome_options.add_argument('--no-sandbox')
    # driver = webdriver.Chrome(chrome_options=chrome_options)

    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--start-fullscreen")
    chrome_options.add_argument("--no-proxy-server")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    time.sleep(3)
    driver.get("https://www.reddit.com/?feed=home")
    time.sleep(3)

    driver.get("https://www.reddit.com/search/?q={0}".format(str(keywords)))
    idx = 1

    while True:
        try:
            post = driver.find_element('xpath','//*[@id="AppRouter-main-content"]/div/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div/div[{0}]'.format(str(idx)))
            actions = ActionChains(driver)
            actions.move_to_element(post).perform()
            time.sleep(1)
            post.click()

            post_url = driver.current_url
            if post_url is not None:
                url_list = post_url.split('/')
                if "comments" not in url_list:
                    driver.execute_script("window.history.go(-1)")
                    driver.get("https://www.reddit.com/search/?q={0}".format(str(keywords)))
                    idx += 1
                    continue

            submission = reddit.submission(url=post_url)

            print(idx, " -- ", submission.title, " -- ", submission.subreddit)

            result[submission.id] = [keywords,
                                     submission.title,
                                     str(submission.subreddit),
                                     str(submission.author),
                                     str(datetime.datetime.fromtimestamp(submission.created_utc)),
                                     submission.score, submission.selftext,
                                     {}]

            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list():
                author = str(comment.author)
                created_at = str(datetime.datetime.fromtimestamp(comment.created_utc))
                upvotes = comment.score
                body = comment.body
                result[submission.id][7][comment.id] = {'author': author,
                                                        'date': created_at,
                                                        'upvotes': upvotes,
                                                        'content': body}

            cross = driver.find_element('xpath', '//*[@id="overlayScrollContainer"]/div[1]/div/div[2]/button')
            cross.click()
            cross.click()

            current_url = driver.current_url
            print(current_url)
            url_list = current_url.split('/')

            if "comments" in url_list:
                driver.execute_script("window.history.go(-1)")

            time.sleep(0.5)
            idx += 1

        except (ElementNotInteractableException, ElementClickInterceptedException, NoSuchWindowException):
            print("Element is Not Interactable!")
            idx += 1
            continue
        except InvalidURL:
            print("Invalid URL! This post is either removed or is an AD.")
            idx += 1
            continue
        except NoSuchElementException:
            print("Reached to the end, no more post!")
            idx += 1
            driver.quit()
            break
        except TimeoutException:
            print("Element is not visible")
            idx += 1
            continue
        except StaleElementReferenceException:
            idx += 1
            continue
    return result


def scrape_keyword_from_reddit(key_list):
    post_list = []
    comment_list = []

    for cmp in key_list:
        result = search_keywords_in_reddit(cmp)
        print(" -------------------- {} --------------------".format(cmp))
        comment = {}

        for k, v in result.items():
            comment[k] = v[7]

        for post_id, detail in result.items():
            post_list.append([post_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5], detail[6]])

        for post_id, dict in comment.items():
            for comment_id, cmt in dict.items():
                comment_list.append(
                    [post_id, comment_id, cmt['author'], cmt['date'], cmt['upvotes'], cmt['content']])

    df_post = pd.DataFrame(post_list,
                            columns=['id', 'post_query', 'title', 'subreddit', 'author', 'date', 'upvotes', 'content'])
    df_comment = pd.DataFrame(comment_list, columns=['id', 'post_id', 'author', 'date', 'upvotes', 'content'])
    df_post.to_csv(output_path + "/all_posts.csv", index=False)
    df_comment.to_csv(output_path + "/all_comments.csv", index=False)
