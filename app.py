from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app)
counter = 0

url = "https://www.wired.com/search/?q=&sort=publishdate+desc"

def scrape_with_selenium(url):
    options = webdriver.ChromeOptions()  # Options for headless browser
    options.add_argument("--headless")    # Run Chrome in the background

    driver = webdriver.Chrome(options=options)  # Initialize the Chrome driver
    driver.get(url)

    articles = {}
    sent_articles = set()
    for _ in range(30): # loop through clicks
        try:
            # Wait for the "More Stories" button to be clickable (adjust timeout as needed)
            more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.BaseButton-bLlsy.ButtonWrapper-xCepQ.fhIjxp.gHDKrI.button.button--primary.SummaryListButton-hvPLNp.FZeiZ")) #inspect element on the webpage to get CSS Selector
            )
            more_button.click()
            time.sleep(5) # wait for the content to load, adjust as needed

        except Exception as e: # when the button is no longer found, break the loop
            print("No more 'More Stories' button found or error: ", e)
            break

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        articles = get_headlines(soup, articles)
        
        new_articles = {title: articles[title] for title in articles if title not in sent_articles}
        if new_articles:
            socketio.emit('new_articles', new_articles)
            sent_articles.update(new_articles.keys())

    driver.quit()  # Close the browser
    return articles

def get_headlines(soup, articles_dict):
    summary_div = soup.find_all("div", class_="SummaryItemContent-eiDYMl dogWHS summary-item__content")
    for article_element in summary_div:  # Find the 'a' tag
            h3_tag = article_element.find("h3")
            a_tag = article_element.find("a")  # Find the h3 tag inside the 'a' tag
            time_tag = article_element.find("time")
            if h3_tag:
                title = h3_tag.text.strip()
                link ="https://www.wired.com" + a_tag["href"]  
                if time_tag:
                    time = time_tag.text.strip()
                    articles_dict[title] = (link, time)
    return articles_dict
    
def write_to_csv(articles):
    with open("articles.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "link", "date"]  # Column headers
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader() 
        for title, (link, date) in articles.items():
             writer.writerow({"title": title, "link": link, "date": date})

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on('start_scraping')
def handle_start_scraping():
    def scrape():
        articles = scrape_with_selenium(url)
        write_to_csv(articles)
        print(len(articles))
    thread = threading.Thread(target=scrape)
    thread.start()

if __name__ == "__main__":
    socketio.run(app, debug=True)  # Set debug=False for production