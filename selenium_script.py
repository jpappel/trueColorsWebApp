from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time

def main():

    url = 'https://webapps.cs.moravian.edu/'

    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(1)

    Select(driver.find_element(By.ID, 'quiz_location')).select_by_value('Home')
    time.sleep(1)

    def get_gold():
        driver.find_element(By.ID, 'start_button').click()
        time.sleep(1)

        for i in range(1, 6):
            print("Block: ", i)
            driver.find_element("css selector", "input[name='answer'][id='4']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerB'][id='3']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerC'][id='2']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerD'][id='1']").click()
            time.sleep(1)
            driver.find_element(By.ID, 'submit_button').click()

        time.sleep(3)

        print(driver.find_element(By.ID, 'user_result').text)

    def get_green():
        driver.find_element(By.ID, 'start_button').click()
        time.sleep(1)

        for i in range(1, 6):
            print("Block: ", i)
            driver.find_element("css selector", "input[name='answer'][id='1']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerB'][id='2']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerC'][id='3']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerD'][id='4']").click()
            time.sleep(1)
            driver.find_element(By.ID, 'submit_button').click()

        time.sleep(3)

        print(driver.find_element(By.ID, 'user_result').text)

    def get_orange():
        driver.find_element(By.ID, 'start_button').click()
        time.sleep(1)

        for i in range(1, 6):
            print("Block: ", i)
            driver.find_element("css selector", "input[name='answer'][id='2']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerB'][id='1']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerC'][id='4']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerD'][id='3']").click()
            time.sleep(1)
            driver.find_element(By.ID, 'submit_button').click()

        time.sleep(3)

        print(driver.find_element(By.ID, 'user_result').text)

    def get_blue():
        driver.find_element(By.ID, 'start_button').click()
        time.sleep(1)

        for i in range(1, 6):
            print("Block: ", i)
            driver.find_element("css selector", "input[name='answer'][id='3']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerB'][id='4']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerC'][id='1']").click()
            time.sleep(0.5)
            driver.find_element("css selector", "input[name='answerD'][id='2']").click()
            time.sleep(1)
            driver.find_element(By.ID, 'submit_button').click()

        time.sleep(3)

        print(driver.find_element(By.ID, 'user_result').text)


    get_orange()
    
    driver.quit()


if __name__ == '__main__':
    main()



