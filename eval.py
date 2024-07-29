from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import re
import numpy as np
import pandas as pd
import time
import random
from selenium_stealth import stealth

def random_sleep(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

def save_to_excel(language_counter, salary_counter, filename='data.xlsx'):
    languages_df = pd.DataFrame(language_counter.items(), columns=['Language', 'Mentions'])
    salary_df = pd.DataFrame(salary_counter.items(), columns=['Salary', 'Count'])
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        languages_df.to_excel(writer, sheet_name='Languages', index=False)
        salary_df.to_excel(writer, sheet_name='Salaries', index=False)

def htmlize(text: str):
    return text.replace(" ", "%20").replace(",", "%2C")

def clean_salary(salary: str) -> float:
    numbers = re.findall(r'\d+', salary.replace(",", ""))
    if len(numbers) == 2:
        low, high = map(int, numbers)
        return (low + high) / 2
    elif numbers:
        return float(numbers[0])
    return 0


def extract_languages(description: str, languages: set) -> list:
    mentioned_languages = []
    for language in languages:
        if ".NET" in description:
            mentioned_languages.append("C#")
        if "Springboot" in description:
            mentioned_languages.append("Java")
        else:
            if re.search(r'\b' + re.escape(language) + r'\b', description, re.IGNORECASE):
                mentioned_languages.append(language)
    return list(set(mentioned_languages))

def convert_to_dict(pages: int, job: str, location: str):
    all_languages = set(["JavaScript", "Java", "Python", "C#", "Go", "C++", "Rust", "Cobol"])
    language_counter = Counter()
    language_salary = defaultdict(list)
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    for page in range(pages):
        driver = webdriver.Chrome(options=options)
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        start = page * 10
        url = f"https://mx.indeed.com/jobs?q={job}&l={location}&sort=date&start={start}"
        driver.get(url)
        random_sleep()
        jobs_cards = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")

        for card in jobs_cards:
            print("Carding!")
            title = card.find_element(By.CLASS_NAME, "jcs-JobTitle").text
            try:
                salary_text = card.find_element(By.CLASS_NAME, "salary-snippet-container").text
                salary_value = clean_salary(salary_text)
            except Exception as e:
                salary_value = 0
            try:
                card.click()
                random_sleep()
            except Exception as e:
                print("Couldn't click")
                continue
            desc = driver.find_element(By.ID, "jobDescriptionText").text

            mentioned_languages = extract_languages(desc, all_languages)
            language_counter.update(mentioned_languages)

            for lang in mentioned_languages:
                if salary_value > 0:
                    language_salary[lang].append(salary_value)

        driver.quit()
    return language_counter, language_salary

job = htmlize("Desarrollador Jr") # Termino a buscar
location = htmlize("Ciudad de México, CDMX") # Lugar donde buscar
pages = 5
language_counter, language_salary = convert_to_dict(pages, job, location)

plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
colors = plt.get_cmap('tab10').colors
plt.bar(language_counter.keys(), language_counter.values(), color=colors)
plt.xlabel('Programming Languages')
plt.ylabel('Mentions')
plt.title('Mentions of Programming Languages in Job Descriptions')
plt.xticks(rotation=45)

plt.subplot(1, 2, 2)
language_avg_salary = {lang: np.mean(salaries) for lang, salaries in language_salary.items()}
plt.bar(language_avg_salary.keys(), language_avg_salary.values(), color=colors)
plt.xlabel('Programming Languages')
plt.ylabel('Average Salary')
plt.title('Average Salary for Programming Languages')
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

# Save to Excel (Updated)
language_salary_flattened = {lang: ','.join(map(str, salaries)) for lang, salaries in language_salary.items()}
languages_df = pd.DataFrame(list(language_salary_flattened.items()), columns=['Language', 'Salaries'])
with pd.ExcelWriter('data.xlsx', engine='openpyxl') as writer:
    languages_df.to_excel(writer, sheet_name='Languages_Salaries', index=False)
