import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import threading
import time
import random

def find_article_links(main_url):
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    article_links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and 'story' in href:
            full_link = main_url + href if 'http' not in href else href
            article_links.append(full_link)

    return article_links

def handle_cookie_banner(driver):
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
    except:
        pass

def has_comments(url):
    print(f"Checking for comments in article: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    with open('output.html', 'w', encoding='utf-8') as file:
        file.write(response.text)

    comment_section = soup.find('div', id='commentSection')
    if comment_section:
        print("Comment section found.")
        return True
    else:
        print("No comment section found.")
        return False

def scrape_comments(driver, url, vote_option_index):
    driver.get(url)
    print(url)

    if not has_comments(url):
        return
    handle_cookie_banner(driver)
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "commentSection"))
        )

        # Check if comments are present
        comments = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="CommentCard"]')
        if not comments:
            print("No comments found.")
            return

        WebDriverWait(driver, 4).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="CommentCard"]'))
        )
    except TimeoutError:
        print("Timeout waiting for comments to load.")
        return

    comments = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="CommentCard"]')
    counter = 0
    for comment in comments:
        counter += 1
        if counter < 2:
            continue



        delay_ms = random.randint(0, 250)
        time.sleep(delay_ms / 1000)  # we don't want to poke the bear
        author = comment.find_element(By.CSS_SELECTOR, 'p.authorNickname').text
        timestamp = comment.find_element(By.CSS_SELECTOR, 'p.createdAt').text
        comment_text = comment.find_element(By.CSS_SELECTOR, 'div.jPXCsY').text
        print(f"Author: {author}")
        print(f"Timestamp: {timestamp}")
        print(f"Comment: {comment_text}")
        print("-" * 40)

        # Find and hover over the commentReaction_container element before we can vote
        comment_reaction_container = comment.find_element(By.CSS_SELECTOR, '[class^="commentReaction_container"]')
        actions = ActionChains(driver)
        actions.move_to_element(comment_reaction_container).perform()
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[class^="commentReactionButton_button"]'))
        )

        # Find and click the specific voting option button based on the index
        voting_options = comment.find_elements(By.CSS_SELECTOR, '[class^="commentReactionButton_button"]')
        if vote_option_index < len(voting_options):
            voting_option = voting_options[vote_option_index]
            voting_option.click()

def thread_function(url, options, vote_option_index):
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    scrape_comments(driver, url, vote_option_index)
    driver.quit()

#main_url = 'https://www.20min.ch'
#article_links = find_article_links(main_url)
options = Options()
options.add_argument("incognito")
options.add_argument("headless")  # headless

number_of_iterations = 50
number_of_threads = 20
specific_article_url = ""
vote_option_index = 5 # Change this to the index of the voting option you want to select

threads = []
for _ in range(number_of_threads):
    for _ in range(number_of_iterations // number_of_threads):
        thread = threading.Thread(target=thread_function, args=(specific_article_url, options, vote_option_index))
        threads.append(thread)
        thread.start()

# Waiting for all threads to complete
for thread in threads:
    thread.join()
