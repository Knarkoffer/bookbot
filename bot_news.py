# !/usr/bin/env python3
# !python3
# coding: utf-8

import glob
import json
import os
import sys
import datetime
import bot_general

from bs4 import BeautifulSoup


def get_file_age_minutes(file_path):
    
    if os.path.isfile(file_path):
        
        datetime_now = datetime.datetime.now()
        datetime_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
    
        diff = (datetime_now - datetime_modified)
        diff_minutes = (diff.days * 24 * 60) + (diff.seconds / 60)
        
        return diff_minutes
    else:
        return 0  # Returns a zero, to ignore the file if it doesn't exist


def scan_for_new_books(force_update=False):
    print('Checking NextCloud for new books')
    
    new_books = []
    notified_books = bot_general.string_to_list(bot_general.notified_books_file)
    
    for file in glob.glob(bot_general.books_folder_path + r'\**\*.opf', recursive=True):
        
        if (get_file_age_minutes(file) > 5) or force_update:
            
            book_data = get_data_from_opf(file)
            
            # Translates book path to a nice output format
            base_folder = os.path.dirname(os.path.dirname(file))
            book_path = base_folder[len(bot_general.books_folder_path) + 1:]
            book_path = book_path.replace('\\', ' > ')
            book_data['Path'] = book_path
            
            if not book_data.get('UUID'):
                sys.exit(f"Book {book_data['Title']} located from {file} does not have UUID, weird?!'")
            
            if book_data['UUID'] not in notified_books:
                
                new_books.append(book_data)
               
                output_file = open(bot_general.notified_books_file, mode='a', encoding='utf-8')
                output_file.write(book_data['UUID'] + '\n')
                output_file.close()

        else:
            print(f"{file} is too new, and force_update was not toggled")
            pass

    return new_books


def get_data_from_opf(input_file):
    
    data_successfully_read = False
    file_soup = None
    book_data = {}
    book_subjects = []
    children = None
    
    if os.path.isfile(input_file):
        try:
            with open(input_file, mode='r', encoding='utf-8') as file:
                file_soup = BeautifulSoup(file, features="html.parser")
            children = file_soup.find('metadata').findChildren()
            data_successfully_read = True
        finally:
            pass

    if data_successfully_read:
        for child in children:
            child_soup = BeautifulSoup(str(child), features="html.parser")
            if 'id="uuid_id"'.lower() in str(child).lower():
                book_data['UUID'] = str(child_soup.text).lower().strip()
            elif 'opf:scheme="ISBN"'.lower() in str(child).lower():
                book_data['ISBN'] = str(child_soup.text).upper().strip().replace('-', '')
            elif '<dc:subject>'.lower() in str(child).lower():
                book_subjects.append(child_soup.get_text())

        book_data['Title'] = file_soup.find('metadata').find('dc:title').get_text().strip()
        book_data['Author'] = file_soup.find('metadata').find('dc:creator').get_text().strip()

        # Gets the series name and index
        metas = file_soup.find('metadata').findAll('meta')
        series_name = ''
        series_index = ''

        for meta in metas:
            if meta.get('name') == 'calibre:series':
                series_name = str(meta.get('content').strip())
            elif meta.get('name') == 'calibre:series_index':
                series_index = str(meta.get('content').strip())
            elif meta.get('name', None) == 'calibre:user_metadata:#wordcount':
                wc_dict = json.loads(str(meta.get('content').strip()))
                if wc_dict.get('#value#', None):
                    book_data['WordCount'] = bot_general.get_wordcount_approximation_string(0, wc_dict['#value#'])

        if series_name and series_index:
            book_data['Series'] = series_name + ' #' + series_index
        
        if len(book_subjects) > 0:
            book_data['Subjects'] = ', '.join(book_subjects)
        
        return book_data
    
    else:
        print(f"Problems reading from OPF-file: {input_file}")
        return None
