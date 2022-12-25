import os
from django.http import HttpResponse
from django.shortcuts import render
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import multiprocessing

import pymongo, gridfs

def count():
    # count the number of files in the static directory
    dir = "./static"
    lst = os.listdir(dir)
    required_files = []
    for fname in lst:
        if fname.startswith("editorial") and fname.endswith(".txt"):
            required_files.append(fname)
    number_of_files = len(required_files)
    return number_of_files

def index(request):
    number_of_files = count()
    editorials = []
    for i in range(1, number_of_files+1):
        with open(f"./static/editorial_{i}.txt", "r", encoding="utf-8") as file:
            title = file.readline()
            sub_title = file.readline()
            content = file.readline()
            file.close()
        name = "\"{% static 'editorial_audio_" + str(i) +".wav' %}\""
        editorial = {'title':title, 'sub_title':sub_title, 'content':content, 'audio': name}  
        editorials.append(editorial)
    return render(request, 'index.html', {'editorials':editorials})

def specific_editorial_fetch(request):
    def correct(text):
        text = text.replace("�", " " )
        return text
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches",["enable-automation"])
    options.add_argument('disable-infobars')
    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    # service=Service(ChromeDriverManager().install()), 

    driver.get("https://www.thehindu.com/opinion/editorial")
    driver.maximize_window()

    # connect to database
    client = pymongo.MongoClient("mongodb+srv://gurvindersinghmaan33:MaanBai$$22@cluster0.i60bgne.mongodb.net/?retryWrites=true&w=majority")
    database = client["thehindueditorialaudio"]


    driver.implicitly_wait(10)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    driver.implicitly_wait(10)
    editorial_links = driver.find_elements(by=By.XPATH, value="//div[@class='row editorial-section equal-height']/div/descendant::strong/parent::a")

    editorial_titles = []
    for editorial_link in editorial_links:
        editorial_titles.append(editorial_link.get_attribute("href"))

    editorial_titles = editorial_titles[2::]
    i = 1 
    for editorial_title in editorial_titles:
        content = ""
        driver.get(editorial_title)
        driver.implicitly_wait(10)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.implicitly_wait(10)
        title = driver.find_element(by=By.XPATH, value="//h1[@class='title']").text
        sub_title = driver.find_element(by=By.XPATH, value="//h3[@class='sub-title']").text
        content_box = driver.find_elements(by=By.XPATH, value=" //div[starts-with(@id, 'content-body')]/p")
        for content_item in content_box:
            content = (content.replace('\r', '').replace('\n', '')).strip() + (str(content_item.text).replace('\r', '').replace('\n', '')).strip()

        content = content.replace("To read this editorial in Tamil, click here.", "")
        content = content.replace("To read this editorial in Hindi, click here.", "")
        content.replace('\r', '').replace('\n', '')
        content = content.strip()
        
        if os.path.exists(f"./static/editorial_{i}.txt"):
            print(os.path.exists(f"./static/editorial_{i}.txt"))
            os.remove(f"./static/editorial_{i}.txt")

        with open(os.path.abspath(f"./static/editorial_{i}.txt"), "a", encoding="utf-8") as f:
            f.write(correct(text=title) + "\n")
            f.write(correct(text=sub_title) + "\n") 
            f.write(correct(text=content))
            f.close()
        
        files = []
        files_list = database.fs.files.find()
        for file in files_list:
            if file['filename'].endswith(".txt"):
                files.append(file['_id'])
        for id in files:
            database.fs.files.delete_one({'_id': id})
            
        file_path = f"./static/editorial_{i}.txt"
        name = f"editorial_{i}.txt"
        filedata = open(file_path, "rb")
        data = filedata.read()
        filedata.close()
        fs = gridfs.GridFS(database=database)
        fs.put(data, filename = name)
        i = i + 1
    client.close()
    driver.quit()
    return render(request, 'done.html')


def flag_check(collection, driver, flag_process):
    flag = False
    # check for the flag
    response = collection.find_one({'key':'audio_flag'})
    flag = response['value']
    if flag():
        driver.quit()
        flag_process.terminate()
        return True
    time.sleep(60)

def specific_audio_fetch(request):
    # colab code here
    options = webdriver.ChromeOptions() 
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(options=options)
    driver.get('https://accounts.google.com/ServiceLogin')
    driver.maximize_window()
    email_id = "gurvindersinghmaan33@gmail.com"
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//input[@type='email']"))).send_keys(f"{email_id}\n")
    password = "MaanBai$$22"
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']"))).send_keys(f"{password}\n")
    time.sleep(10)
    driver.get("https://colab.research.google.com/github/gurvindersinghmaan33/tts/blob/main/tortoise_tts.ipynb")
    time.sleep(30)
    driver.find_element(by=By.TAG_NAME, value="html").send_keys(Keys.CONTROL, Keys.F10)
    print("Shortcut")
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//paper-button[text()='Run anyway']"))).click()

    #   connect to database
    client = pymongo.MongoClient("mongodb+srv://gurvindersinghmaan33:MaanBai$$22@cluster0.i60bgne.mongodb.net/?retryWrites=true&w=majority")
    database = client["thehindueditorialaudio"]
    collection = database["thea"]
    flag_process = multiprocessing.Process(target=flag_check, args=(collection,))
    flag_process.start()
    return render(request, 'done.html')

def download_audio(request):
    #   connect to database
    client = pymongo.MongoClient("mongodb+srv://gurvindersinghmaan33:MaanBai$$22@cluster0.i60bgne.mongodb.net/?retryWrites=true&w=majority")
    database = client["thehindueditorialaudio"]
    collection = database['thea']
    num_files = count()
    for i in range(1, num_files + 1):
        fs = gridfs.GridFS(database=database)
        audio_name = f"editorial_audio_{i}.wav"
        data = database.fs.files.find_one({"filename":audio_name}) 
        id = data["_id"]
        outputdata = fs.get(id).read()
        output = open(f"editorial_audio_{i}.wav", "wb")
        output.write(outputdata)
        output.close()
    collection.update_one({'key':'audio_flag'},{'$set':{'value':False}})
    client.close()
    return render(request, 'done.html')

def about(request):
    return render(request, 'about.html')
