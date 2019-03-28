from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from urllib import request

import json, time

SEMESTER = 'ss19' # format: ssXX or wsXXXX
FILE_PREFIX = 'data/all_modules_' + SEMESTER
FILE_SUFFIX = '.json'
FILENAME = FILE_PREFIX + FILE_SUFFIX


def main():
    do_backup = input('Backup now? [Y/n]:  ')

    if not do_backup in ['n', 'N']:
        backup()

    browser = webdriver.Chrome()
    browser.get('https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/suchen.html')

    ss19_element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, """//*[@id="j_idt103:headpanel"]/div[3]/div[1]/div/select/option[2]""")))
    ss19_element.click()

    search_element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, """//*[@id="j_idt103:headpanel"]/div[2]/div/div/div/input""")))

    check_characters(browser)
    check_words(browser)
    get_pform()
    print('All done!')


def check_characters(browser):
    all_chars = 'abcdefghijklmnopqrstuvwxyz'

    try:
        with open('data/checking_char.txt', 'r') as f:
            last_char = f.read()
        char_found = False
    except FileNotFoundError:
            char_found = True

    for char1 in all_chars:
        for char2 in all_chars:
            if (char1 == last_char) or (char1 + char2 == last_char):
                char_found = True
            try:
                if char_found and not last_char != 'z':
                    check_string(char1+char2, browser)
            except TimeoutException:
                continue
            except StaleElementReferenceException:
                browser.refresh()
                continue
        if char_found and not last_char != 'z':
            check_string(char1, browser)
            backup()


def check_words(browser):
    with open('data/words.txt', 'r') as f:
        words = f.readlines()
    words = [word[:-1] for word in words]

    try:
        with open('data/checking_word.txt', 'r') as f:
            last_word = f.read()
        word_found = False
    except FileNotFoundError:
        word_found = True

    i = 0
    for word in words:
        if not word_found:
            if word == last_word:
                word_found = True
        try:
            if word_found and not last_word == words[-1]:
                check_string(word, browser)
                i += 1
                if i % 50 == 0:
                    backup()
        except TimeoutException:
            continue
        except StaleElementReferenceException:
            browser.refresh()
            continue
        except HTTPError:
            break


def get_pform():
    try:
        with open(FILENAME, 'r') as f:
            all_modules = json.load(f)
    except FileNotFoundError:
        print('File not found! Are you sure there is data in the file specified?')
        input()
        raise FileNotFoundError

    modules_skipped = 0
    skipped_msg_printed = False

    i = 0
    for module_no in all_modules:
        module = all_modules[module_no]
        if len(module.keys()) == 6:
            modules_skipped += 1
            continue
        else:
            if not skipped_msg_printed:
                print('Skipped {} entries'.format(modules_skipped))
                skipped_msg_printed = True
            module["pruefungsform"] = get_pruefungsform(module["link"])
            module_id = module['id']
            all_modules[module_no] = module
            with open(FILENAME, 'w') as f:
                f.write(json.dumps(all_modules, indent=4))
            print('Saved {} to module {}.'.format(module["pruefungsform"], module_id))
            i += 1
            if i % 50 == 0:
                backup()


def check_string(string, browser):
    print('Checking: ', string)
    if len(string) < 3:
        with open('data/checking_char.txt', 'w') as f:
            f.write(string)
    elif len(string) >= 3:
        with open('data/checking_word.txt', 'w') as f:
            f.write(string)

    search_element = browser.find_element(By.XPATH, """//*[@id="j_idt103:headpanel"]/div[2]/div/div/div/input""")
    search_element.clear()
    search_element.send_keys(string)

    search_element.send_keys(Keys.RETURN)
    time.sleep(1)

    try:
        with open(FILENAME, 'r') as f:
            all_modules = json.load(f)
    except:
        all_modules = {}

    try:
        find_modules_element = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, """#j_idt103\\3a ergebnisliste_data""")))
    except TimeoutException:
        print('Some kind of connection issue... Skipping to Prüfungsform.')
        return

    i = 0
    while True:
        try:
            module_element = browser.find_element(By.XPATH, """//*[@id="j_idt103:ergebnisliste_data"]/tr[""" + str(i+1) + """]""")
            module_id = module_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            try:
                any(all_modules['module_no_' + str(module_id)])
                i += 1
                continue
            except KeyError:
                pass
            module_link = module_element.find_element(By.CSS_SELECTOR, 'a[href*="beschreibung/anzeigen"]').get_attribute('href')
            module_name = module_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            module_ects = module_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            module_verantwortliche_r = module_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            module_entry = {'name':module_name,
                            'link':module_link,
                            'ects':module_ects,
                            'verantwortliche_r':module_verantwortliche_r,
                            'id':module_id}

            all_modules['module_no_' + str(module_id)] = module_entry
            i += 1
        except NoSuchElementException:
            print('Modules found: ' + str(len(all_modules)))
            with open(FILENAME, 'w') as f:
                f.write(json.dumps(all_modules, indent=4))

            return


def get_pruefungsform(link):
    page_html = request.urlopen(link)
    page_html_str = str(page_html.read())
    pform_location = page_html_str.find('fa-legal')
    title_char = page_html_str[pform_location+26]
    offset = 51 if title_char == 'P' else 44
    pform_begin = pform_location + offset
    pform_end = page_html_str[pform_begin:].find('\\n')
    pform_raw = page_html_str[pform_begin:pform_begin+pform_end]
    return filter_pform(pform_raw)


def backup():
    print('Backing up...')
    with open(FILENAME, 'r') as f:
        all_data = json.load(f)
    with open(FILE_PREFIX + '_backup' + FILE_SUFFIX, 'w') as f:
        f.write(json.dumps(all_data, indent=4))
    print('Done!')


def filter_pform(pform_raw):
    if 'ndliche Pr' in pform_raw:
        return 'Mündliche Prüfung'
    elif 'Portfoliopr' in pform_raw:
        return 'Portfolioprüfung'
    elif 'Schriftliche P' in pform_raw:
        return 'Schriftliche Prüfung'
    elif 'Keine P' in pform_raw:
        return 'Keine Prüfung'
    elif pform_raw in ['Praktikum',
                       'Abschlussarbeit',
                       'Oral exam',
                       'Portfolio examination',
                       'Referat',
                       'Hausarbeit',
                       'Thesis',
                       'Written exam',
                       'Homework',
                       'No exam']:
        return pform_raw
    else:
        print('Unrecognised: ' + pform_raw)
        return pform_raw


if __name__ == '__main__':
    main()