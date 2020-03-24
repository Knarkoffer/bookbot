#!/usr/bin/env python3
# !python3
# coding: utf-8

import os
import time
import sys


def remove_nonascii_characters(input_string):
    output_string = str(input_string).encode('utf-8', 'ignore').decode().encode('ascii', 'ignore').decode()
    return output_string


def write_log(information_string):
    output_file = open('botlog.log', mode='a', encoding='utf-8')
    output_file.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' - ' + str(information_string) + '\n')
    output_file.close()


def fix_windows_filenames(input_string):
    output_string = input_string
    
    output_string = output_string.replace('\\', '')
    output_string = output_string.replace('/', '')
    output_string = output_string.replace(':', '_')
    output_string = output_string.replace('*', '')
    output_string = output_string.replace('?', '')
    output_string = output_string.replace('"', '')
    output_string = output_string.replace('<', '')
    output_string = output_string.replace('>', '')
    output_string = output_string.replace('|', '')
    
    return output_string


def remove_zalgo_from_string(input_string):
    output_string = ''.join(chr(x) for x in map(ord, input_string) if not (
                767 < x < 880 or 6831 < x < 6912 or 7615 < x < 7680 or 8399 < x < 8448 or 65055 < x < 65072))
    
    return output_string


def replace_unicodes(input_string):
    output_string = str(input_string)
    output_string = output_string.replace("\u2019", "'")
    return output_string


def string_to_list(input_data):
    input_data = str(input_data)
    
    output_list = []
    if os.path.isfile(input_data):
        with open(input_data, mode='r', encoding='utf-8') as f:
            output_list = f.read().splitlines()
    else:
        if ',' in str(input_data):
            output_list = input_data.split(',')
        else:
            output_list.append(input_data)
    
    # Trim all entries
    output_list = list(map(str.strip, output_list))
    
    # Removes empty entries
    output_list = list(filter(None, output_list))
    
    return output_list


def get_nextcloud_path():
    nextcloud_path = ''
    nextcloud_config_path = os.path.join(os.environ['LOCALAPPDATA'], r'Nextcloud\nextcloud.cfg')
    
    if os.path.isfile(nextcloud_config_path):
        
        with open(nextcloud_config_path, mode='r', encoding='utf-8') as ins:
            for line in ins:
                if 'localPath' in line:
                    nextcloud_path = str(line[line.find('=') + 1:]).strip().replace('/', '\\')
    
    else:
        sys.exit('Nextcloud not installed on machine or not where expected (' + nextcloud_config_path + ')')
    
    return nextcloud_path


def get_wordcount_approximation_string(wordcount_old, wordcount_new):
    wordcount_updated = wordcount_new - wordcount_old

    if wordcount_updated > 1000:
        # wordcount_updated = '~' + str(int(round(wordcount_updated / 1000))) + 'K'
        wordcount_updated = str(round(wordcount_updated / 1000, 1))

        # If it happens to be an even number, remove decimals, else approximate if it's above .5, then add a plus
        if wordcount_updated.endswith('.0'):
            wordcount_updated = wordcount_updated[:-len('.0')]
            wordcount_updated = wordcount_updated + 'K'  # WordCount in thousands, with one decimal
        else:
            wordcount_pri, wordcount_dec = wordcount_updated.split('.')
            wordcount_updated = wordcount_pri + 'K'

            if int(wordcount_dec) > 5:
                wordcount_updated = wordcount_updated + '+'
    else:
        wordcount_updated = str(wordcount_updated)

    return wordcount_updated


books_folder_path = os.path.join(get_nextcloud_path(), 'eBooks')
requests_file_path = os.path.join(books_folder_path, 'Requests')

fff_binary_path = r'C:\Python37\Scripts\fanficfare.exe'
fff_config_path = r'config_fanficfare.ini'
notified_books_file = r'config_notified_books.txt'
sites_supporting_chapter_dates = ['fsb', 'fsv']
supported_domains = r'config_supported_domains.yaml'
literature_channel_id = r'CBETU8AGH'  # dev (Change this variable when running tests)
# literature_channel_id = r'C947E0DHD'  # literature
slack_token = os.environ["SLACK_API_TOKEN"]
request_max_timeout = 90
