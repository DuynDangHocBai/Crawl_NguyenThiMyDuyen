import json
import time
import os
import requests
from datetime import datetime  # Thêm thư viện để lấy thời gian thực
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1. Khởi tạo thư mục
SAVE_DIR = "reuters_legal_final_data"
IMG_DIR = os.path.join(SAVE_DIR, "images")
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Đường dẫn chuyên mục Legal
target_url = "https://www.reuters.com/legal/" 
all_results = []

try:
    print(f"Truy cập: {target_url}")
    driver.get(target_url)
    time.sleep(20) # Đợi giải Verify

    articles = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="Title"]')
    links = list(dict.fromkeys([a.get_attribute('href') for a in articles if a.get_attribute('href')]))
    
    # Thử nghiệm với 10 bài
    test_links = links[:10]

    for i, link in enumerate(test_links):
        try:
            # Lấy thời gian hiện tại lúc bắt đầu cào bài này
            scraped_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"--- [{scraped_time}] Đang cào bài {i+1}: {link}")
            driver.get(link)
            
            wait = WebDriverWait(driver, 15)
            title_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
            title = title_el.text

            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(3)

            # Lấy nội dung
            content_selectors = [
                'div[class*="article-body-module__content"] p', 
                'div[data-testid="ArticleBody"] p',
                'div[class*="ArticleBody"] p',
                'div[class*="text-module__text"]'
            ]

            content_text = ""
            for selector in content_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    content_text = " ".join([el.text for el in elements if len(el.text.strip()) > 10])
                    if content_text: break 

            # lấy ảnh
            img_path = "None"
            try:
                img_el = driver.find_element(By.CSS_SELECTOR, 'img[data-testid="EagerImage"], div[data-testid="Image"] img')
                img_url = img_el.get_attribute('srcset')
                if img_url:
                    img_url = img_url.split(' ')[0]
                else:
                    img_url = img_el.get_attribute('src')

                if img_url and "http" in img_url:
                    img_name = f"legal_{i}.jpg"
                    img_data = requests.get(img_url, timeout=10).content
                    with open(os.path.join(IMG_DIR, img_name), 'wb') as f:
                        f.write(img_data)
                    img_path = img_name
            except:
                pass

            if title and content_text:
                all_results.append({
                    "title": title,
                    "url": link,
                    "content": content_text,
                    "image": img_path,
                    "scraped_at": scraped_time # Thêm thời gian vào file JSON
                })
                print(f"Thành công! {title[:40]}... ")
            else:
                print("Lỗi: Không lấy được nội dung.")

        except Exception as e:
            continue

finally:
    with open(os.path.join(SAVE_DIR, 'legal_final.json'), 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
    driver.quit()
    print("Kết thúc. Kiểm tra file trong thư mục legal_data!")