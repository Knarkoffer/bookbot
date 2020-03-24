# !/usr/bin/env python3
# !python3
# coding: utf-8

import sys
import json
import re
import requests
import time
import yaml
import re
import slack
import time
import asyncio
import sys
import os
import concurrent

# import bot_requests
import bot_stories
import bot_news
import bot_general

python_version_major = sys.version_info[0]
python_version_minor = sys.version_info[1]
if not python_version_major >= 3 and python_version_minor >= 7:
    print('Script only designed for Python 3.7+, use with others on your own risk')
    sys.exit()


def notify_about_new_books():
    new_books = bot_news.scan_for_new_books()
    if len(new_books) == 0:
        print('No new books in Nextcloud to inform channel about... :-(')
    else:
        print(f"Will now inform the the channel about {len(new_books)} books")
        
        for book in new_books:
            
            out_text = f"New book uploaded to *{book['Path']}* " + "\n" + f"_{book['Title']}_ by {book['Author']}"
            
            # Grabts either Series or ISBN
            if book.get('Series'):
                out_text = out_text + f" [{book['Series']}]"
            elif book.get('ISBN'):
                out_text = out_text + f" [{book['ISBN']}]"
            
            if book.get('Subjects'):
                out_text = out_text + '\n' + 'Subjects: ' + book['Subjects']
            
            print(f"Inform the channel about {book['Title']}")
            send_message(bot_general.literature_channel_id, out_text)


def get_userdata(user_id):
    
    payload = {'token': bot_general.slack_token, 'user': user_id}
    response = requests.get('https://slack.com/api/users.info', params=payload)
    
    response_code = int(str(response.status_code).strip())
    
    if response_code == 200:
        response.encoding = 'utf-8'
        response_json = json.loads(response.text)
        user_data = response_json['user']['profile']
    else:
        user_data = None
    
    return user_data


def send_normal_message(channel, message_text):
    slack_rtm_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=message_text,
        as_user=True,
        username='BookBot',
        icon_emoji=':books:'
    )


async def send_async_message(channel='#random', text=''):
    response = await slack_rtm_client.chat_postMessage(
            channel=channel,
            text=text
            )
    assert response["ok"]


def send_message3(channel='#dev', text=''):
    response = slack_rtm_client.chat_postMessage(
            channel=channel,
            text=text
            )
    assert response["ok"]


def send_msg(channel='#random', text=''):
    response = loop.run_until_complete(slack_rtm_client.chat_postMessage(
        channel=channel,
        text=text
    )
    )


def send_message(channel='#dev', message_text=''):
    client = slack.WebClient(token=bot_general.slack_token)

    response = client.chat_postMessage(
        channel=channel,
        text=message_text,
        as_user=True,
        username='BookBot',
        icon_emoji=':books:'
    )

    assert response["ok"]


@slack.RTMClient.run_on(event='message')
async def monitor_channel(**payload):
    data = payload['data']

    if data.get('client_msg_id'):
        print('Is message')
        if data.get('channel', '') == bot_general.literature_channel_id and data.get('text', '').startswith('!'):
            print('is in literature-channel and a command for bot')
            command = data['text'].split(' ')[0]

            if command == '!add':
                print('Add command')

            elif command == '!update':
                print('Update command')

            elif command == '!news':
                print('News command')
                send_normal_message(bot_general.literature_channel_id, "Yah!")

            elif command == '!help':
                print('Help command')

                message_block = list()
                message_block.append(r'*!add* - to add new story to monitor, use this command followed by a blank '
                                     r'space, and then the path of the library where you want them. Example:')
                message_block.append(r'!add https://www.fanfiction.net/s/11660663/ Fiction\FanFic\Harry Potter')
                # message_block.append(r'*!list* - Prints a list with the currently monitored stories')
                message_block.append(r'*!news* - Forces a recheck of new books (non-fanfics)')
                message_block.append(r'*!update* - Runs an update to make sure all monitored stories are up to date')
                # message_block.append(r'*!request* - Request a book by giving its ISBN number. Example:')
                # message_block.append(r'!request 9781786460806')
                message_text = '\n'.join(message_block)

                # bot_general.write_log(str(sender_id) + ' used the help function with command ' + command)
                # send_message(channel, message_text)

                pass


def sync_loop():
    global ticker_counter
    while True:
        # datetime_now = time.strftime('%Y-%m-%d %H:%M:%S')
        # print(f"Hi there, the time is {datetime_now} now, and the ticket counter is {ticker_counter}")

        # NEWS
        # 3600 = 1 hrs
        if (ticker_counter % 3600) == 1:
            #new_books = bot_news.scan_for_new_books()
            new_books = []

            if len(new_books) > 0:
                for new_book in new_books:
                    out_string = f"New book uploaded to _{new_book['Path']}_" + "\n" + \
                                f"_*{new_book['Title']}*_ by {new_book['Author']} "

                    if new_book.get('Series'):
                        out_string = out_string + f"[{new_book['Series']}]"
                    elif new_book.get('ISBN'):
                        out_string = out_string + f"[{new_book['ISBN']}]"

                    if new_book.get('WordCount'):
                        out_string = out_string + f"[{new_book['WordCount']}]"

                    if new_book.get('Subjects'):
                        out_string = out_string.strip() + '\n' + 'Subjects: ' + new_book['Subjects']

                    print(f"Notifying the channel about {new_book['Title']}")
                    #task = loop.create_task(send_async_message(bot_general.literature_channel_id, out_string))
                    #loop.run_until_complete(task)
                    send_message(bot_general.literature_channel_id, out_string)

        # STORIES
        # 43200 = 12 hrs
        # 86400 = 24 hrs
        if (ticker_counter % 43200) == 0:
            #bot_stories.update_monitored_stories()
            pass

        ticker_counter = ticker_counter + 1
        datetime_now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"{datetime_now} - Sleeping 1 second")
        time.sleep(1)


def say_hello(data, **kwargs):
    if 'Hello' in data['text']:
        channel_id = data['channel']
        thread_ts = data['ts']
        user = data['user']

        webclient = slack.WebClient(bot_general.slack_token)
        webclient.chat_postMessage(
            channel=channel_id,
            text="Hi <@{}>!".format(user),
            thread_ts=thread_ts
        )


async def slack_main():

    global slack_rtm_client
    global loop

    loop = asyncio.get_event_loop()
    slack_rtm_client = slack.RTMClient(token=bot_general.slack_token, run_async=True, loop=loop)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    await asyncio.gather(
        loop.run_in_executor(executor, sync_loop),
        slack_rtm_client.on(event='message', callback=say_hello),
        slack_rtm_client.start()
    )


slack_rtm_client = None
loop = None

# General Bot configs

ticker_counter = 0

if __name__ == "__main__":
    asyncio.run(slack_main())

