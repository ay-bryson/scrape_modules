import json
import re

FILE_PREFIX = 'all_modules_ws1819'
FILE_SUFFIX = '.json'
FILENAME = FILE_PREFIX + FILE_SUFFIX

# 1 : get_strings
# 2 : clean
# 3 : read 'strings.txt'
SELECTOR = 3


def main():
    with open(FILENAME, 'r') as f:
        modules = json.load(f)

    if SELECTOR == 1:
        get_strings(modules)
    elif SELECTOR == 2:
        clean(modules)
    elif SELECTOR == 3:
        read_strings()


def read_strings():
    with open('strings.txt', 'r') as f:
        strings = f.readlines()
    strings = [string[:-1] for string in strings[:10]]


def get_strings(modules):
    words_used = []

    for module_no in modules:
        module = modules[module_no]
        module_name = module['name']
        words = module_name.split(' ')
        for word in words:
            word = re.sub(r'[^\w\s]', '', word)
            if len(word) > 2 and len(word) <= 20:
                if word not in words_used:
                    words_used.append(word)

    with open('strings.txt', 'a') as f:
        for word in words_used:
            f.write(word.lower() + '\n')

def clean(modules):
    for module_no in modules:
        module = modules[module_no]
        for key in module:
            if 'module_' in key:
                key_split = key.split('_')
                module[key_split[1]] = module[key]
                del module[key]
        # if len(module.keys()) == 6:
        #     module['pruefungsform'] = filter_pform(module['pruefungsform'])
        # else:
        #     continue
        # modules[module_no] = module
    with open(FILENAME, 'w') as f:
        f.write(json.dumps(modules, indent=4))

def filter_pform(pform_raw):
    if 'ndliche Pr' in pform_raw:
        return 'Mündliche Prüfung'
    elif 'Portfoliop' in pform_raw:
        return 'Portfolioprüfung'
    elif 'Schriftliche P' in pform_raw:
        return 'Schriftliche Prüfung'
    elif 'Keine P' in pform_raw:
        return 'Keine Prüfung'
    elif pform_raw in ['Praktikum',
                       'Abschlussarbeit',
                       'Oral exam',
                       'Portfolio examination',
                       'Written exam',
                       'Referat',
                       'Hausarbeit',
                       'Homework',
                       'No exam',
                       'Internes Praktikum',
                       '']:
        return pform_raw
    else:
        print('Unrecognised: ' + pform_raw)
        return pform_raw

if __name__ == '__main__':
    main()