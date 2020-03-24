#!/usr/bin/env python3
# !python3
# coding: utf-8

import os
import json
import shutil
import zipfile
import re
import datetime
import yaml
import subprocess

from bs4 import BeautifulSoup

import bot_general

monitored_stories = 'config_monitored_stories.yml'


def copy_fanfic_to_destination(story_item):
    # Figures out the filename using story_author_fixed and story_title_fixed
    
    story_author_fixed = bot_general.remove_zalgo_from_string(story_item['Author'])
    story_author_fixed = bot_general.remove_nonascii_characters(story_author_fixed)
    story_author_fixed = bot_general.fix_windows_filenames(story_author_fixed)
    
    story_title_fixed = bot_general.remove_zalgo_from_string(story_item['Title'])
    story_title_fixed = bot_general.remove_nonascii_characters(story_title_fixed)
    story_title_fixed = bot_general.fix_windows_filenames(story_title_fixed)
    
    base_folder_path = os.path.join(bot_general.books_folder_path, story_item['storyPath'])
    destination_folder_path = os.path.join(base_folder_path, story_author_fixed + ' - ' + story_title_fixed)
    
    # Checks if the folder exists, otherwise cleans it
    if not os.path.isdir(destination_folder_path):
        os.makedirs(destination_folder_path, exist_ok=True)
    else:
        # cleans target folder first
        for file in os.listdir(destination_folder_path):
            
            file_extension = file[file.rfind('.') + 1:].upper()
            extensions_to_keep = ['JPG', 'OPF']
            
            if file_extension not in extensions_to_keep:
                os.remove(os.path.join(destination_folder_path, file))
    
    # copied the newly updated file to nextcloud
    shutil.copyfile(story_item['File'],
                    os.path.join(destination_folder_path, story_author_fixed + ' - ' + story_title_fixed + '.epub'))


def update_monitored_stories():
    
    print('Updating monitored stories')
    
    # Needs to be global to be accessible by the add_update_story function
    global list_fics
    global list_fics_updated
    
    list_fics = []
    list_fics_updated = []
    
    with open(monitored_stories, mode='r', encoding='utf-8') as f:
        list_fics = yaml.load(f, Loader=yaml.SafeLoader)
    
    for fic_item in list_fics:
        add_update_story(fic_item['storyUrl'], existing_fic_item=fic_item)
        pass

    if list_fics_updated != list_fics:
        with open(monitored_stories, mode='w', encoding='utf-8') as f:
            yaml.dump(list_fics_updated, f, default_flow_style=False)


def get_epub_wordcount(epub_file):
    word_counter = 0
    unwanted_html_tags = ['title', 'h1', 'h2', 'h3']
    
    with zipfile.ZipFile(epub_file, mode='r') as bookEntity:
        
        # Grabs only the chapters, ignoring things like images and stylesheets,
        # but also false matches like cover.xhtml and title_page.xhtml etc...
        chapter_files = [file for file in bookEntity.namelist() if re.match(r'^OEBPS/file(\d+).xhtml$', file)]
        
        for chapter_file in chapter_files:
            
            # Reads the content to a binary string
            book_chapter = bookEntity.read(chapter_file)
            
            # Converts it into a normal string, and renders it into a soup
            chapter_content = book_chapter.decode('utf-8')
            content_soup = BeautifulSoup(chapter_content, features='html.parser')
            
            # Cleans unwanted tags
            for unwanted_tag in content_soup.find_all(unwanted_html_tags):
                unwanted_tag.decompose()
            #

            # Gets the text from all things not in tags
            chapter_text = content_soup.get_text()
            
            # Adds this chapters wc to the whole books
            word_counter = word_counter + len(re.findall(r'\w+', chapter_text))
        
        #
    
    #
    
    return word_counter


def json_to_selected_dict(json_object):
    
    # Don't add zchapters, as they'll get written to file then
    wanted_attributes = ['storyUrl', 'title', 'author', 'datePublished',
                         'dateUpdated', 'numChapters', 'numWords', 'siteabbrev', 'output_filename']
    return_dict = {}
    
    for attribute in wanted_attributes:
        if attribute == 'numChapters':
            return_dict[attribute] = int(json_object[attribute].replace(',', ''))
        elif attribute == 'numWords':
            return_dict[attribute] = json_object[attribute].replace(',', '')
        elif attribute.startswith('date'):
            return_dict[attribute] = datetime.datetime.strptime(json_object[attribute].split(' ')[0], '%Y-%m-%d').date()
        elif type(json_object[attribute]) == str:
            return_dict[attribute] = bot_general.replace_unicodes(json_object[attribute])
        else:
            return_dict[attribute] = json_object[attribute]
    
    return return_dict


def add_update_story(story_url, existing_fic_item='', story_path=''):
    
    global list_fics
    global list_fics_updated

    new_story = False

    story_item = {}
    
    if not existing_fic_item:
        story_item['dateChecked'] = datetime.datetime.strptime('1970-01-01', '%Y-%m-%d').date()
        new_story = True
    else:
        story_item['dateChecked'] = existing_fic_item['dateChecked']
    
    date_checked = story_item['dateChecked']
    date_today = datetime.date.today()
    days_since_check = (date_today - date_checked).days
    
    if days_since_check != 0:
        
        if new_story:
            print('Adding ' + str(story_url))
        else:
            print('Checking for update of ' + existing_fic_item['title'])
        
        subprocess_output = subprocess.check_output(
            [bot_general.fff_binary_path, '-u', story_url, '-j', '-c', bot_general.fff_config_path,
             '--non-interactive'], shell=True)
        
        subprocess_text = subprocess_output.decode()
        
        if subprocess_text.startswith('Failed to read epub for update:') and 'Continuing with update=false' in subprocess_text:
            new_story = True
        
        return_json = json.loads(subprocess_text[subprocess_text.find('{'):])
        story_item = json_to_selected_dict(return_json)
        
        #Configures some additional parameters not recieved from FFF
        story_item['dateChecked'] = datetime.date.today()
        
        if new_story:
            story_item['storyPath'] = story_path
        else:
            story_item['storyPath'] = existing_fic_item['storyPath']


        if story_item['numWords']:
            story_item['numWords'] = int(story_item['numWords'])
        else:
            story_item['numWords'] = get_epub_wordcount(story_item['output_filename'])
        
        if story_item['siteabbrev'] in bot_general.sites_supporting_chapter_dates:
           
            youngest_chapter = 999
            
            for chapter in return_json['zchapters']:
    
                chapter_date = datetime.datetime.strptime(chapter[-1]['date'], '%Y-%m-%d %H:%M:%S').date()
                chapter_age = (datetime.date.today() - chapter_date).days
                
                if chapter_age < youngest_chapter:
                    youngest_chapter = chapter_age
                    chapter_title = chapter[-1]['title']
                    
                    # Strips the chapter numbers from the name of the latest chapter
                    p = re.compile(r'^(\d+: ")')
                    result = p.search(chapter_title)

                    if result:
                        latest_chapter = chapter_title[len(result.group(1)):-1]
                    else:
                        latest_chapter = chapter_title

        else:
            latest_chapter = return_json['zchapters'][-1][-1]['title']
        
        if new_story:
    
            words_updated = bot_general.get_wordcount_approximation_string(0, story_item['numWords'])
            
            print('Story added: _*' + str(story_item['title']) + '*_ by ' + str(story_item['author']) +
                  ' [' + words_updated + '] added')
            
            append_new_fic_to_monitor(story_item)
            
        else:
            
            if existing_fic_item['numWords'] != story_item['numWords']:
                words_updated = bot_general.get_wordcount_approximation_string(existing_fic_item['numWords'], story_item['numWords'])
                
                print(f"_*{story_item['title']}*_ by  {story_item['author']} updated with a new chapter "
                      f"titled {latest_chapter} [{words_updated}]")
            
            else:
                print(f"{story_item['title']} has not been updated since last check")
            #

            list_fics_updated.append(story_item)
 
    else:
        print('Already checked for updates of "' + existing_fic_item['title'] + '" today')
        list_fics_updated.append(existing_fic_item)


def bot_command_add(command_line):
    
    with open(monitored_stories, mode='r', encoding='utf-8') as f:
        current_monitored_fics = yaml.load(f, Loader=yaml.SafeLoader)
        
    story_url = command_line
    story_path = ''

    if ' ' in command_line:
        story_url, story_path = command_line.split(' ')

    new_story = True
    story_title = None
    
    for fic_item in current_monitored_fics:
        if (story_url in fic_item['storyUrl']) or (fic_item['storyUrl'] in story_url):
            new_story = False
            story_title = fic_item['title']
    
    if new_story:
        if not story_path:
            if story_url.startswith('https://forums.sufficientvelocity.com'):
                story_path = r'Fiction\FanFic\Worm'
            elif story_url.startswith('https://forums.spacebattles.com/'):
                story_path = r'Fiction\FanFic\Worm'

        story_path = story_path.replace('\\\\', '\\')
        story_path = story_path.replace('/', '\\')

        if not story_path.lower().startswith('fiction'):
            story_path = 'Fiction\\' + story_path

        add_update_story(story_url, story_path=story_path)
       
    else:
        print(f"Already monitoring {story_title}")


def append_new_fic_to_monitor(story_item):
   
    with open(monitored_stories, mode='r', encoding='utf-8') as f:
        temporary_list_fics = yaml.load(f, Loader=yaml.SafeLoader)

    temporary_list_fics.append(story_item)
    
    with open(monitored_stories, mode='w', encoding='utf-8') as f:
        yaml.dump(temporary_list_fics, f, default_flow_style=False)
    
    pass
