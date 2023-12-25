from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from twilio.rest import Client
from dotenv import load_dotenv
import os
import random

load_dotenv()

class Course():
    def __init__(self, course_code, course_name, attendance_data) -> None:
        self.course_code = course_code
        self.course_name = course_name

        self.classes_attended = int(attendance_data.split(" ")[0].split("/")[0])
        self.total_classes = int(attendance_data.split(" ")[0].split("/")[1])
        self.attendance = round(float(attendance_data.split(" ")[1][1:-1]) - random.randint(0,40), 2)

allsubjects = set()

options = Options()
# options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

driver.get("https://s.amizone.net")

# Adding explicit wait for username_box
username_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "_UserName")))
password_box = driver.find_element(by=By.NAME, value="_Password")

username_box.send_keys(os.environ['AMIZONE_USERNAME'])
password_box.send_keys(os.environ['AMIZONE_PASSWORD'])

submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")

submit_button.click()

# Adding explicit wait for my_courses_button
my_courses_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'My Courses')))
my_courses_button.click()

# Adding explicit wait for table_element
table_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//table[.//th[text()="Open/Domain/FBL Courses "]]')))

rows = table_element.find_elements(By.TAG_NAME, "tr")  # get all of the rows in the table
for row in rows:
    # Get the columns (all the column 2)
    cols = row.find_elements(By.TAG_NAME, "td")  # note: index start from 0, 1 is col 2f
    if len(cols) == 7:
        course_code, course_name, course_data = cols[0].text, cols[1].text, cols[-2].text
        obj = Course(course_code, course_name, course_data)
        allsubjects.add(obj)

time.sleep(2)

driver.quit()

output_msg = "*TODAY'S ATTENDANCE REMINDER!*\n\n"
for sub in allsubjects:
    output_msg += f"*{sub.course_name}* - {round(sub.attendance, 2)} "
    if sub.attendance < 75:
        output_msg += "| *BELOW 75%*"
    output_msg += "\n\n"


twilio_client = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTHTOKEN'])

from openai import OpenAI
client = OpenAI()

context = """Use the given input to create a Funny, Witty very short summary of the attendance data, and motivate the student to attend classes if he/she has below 75 in any course. Keep it short (under 100 words)"""

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": context},
    {"role": "user", "content": output_msg}
  ]
)

message = twilio_client.messages.create(
    from_='whatsapp:+[FROM NUMBER]',
    body=output_msg + completion.choices[0].message.content,
    to='whatsapp:+[TO NUMBER]'
)
