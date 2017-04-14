#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import errno
import json
import logging.config
import os
import re
import time
import warnings

import concurrent.futures
import requests
import tqdm

from InstagramScrapper.constants import *
from TumblrDefs import INSTAGRAM_PASS, INSTAGRAM_USERNAME

warnings.filterwarnings('ignore')

#TODO find a way to scrap media with multiple images
class InstagramScraper(object):

    """InstagramScraper scrapes and downloads an instagram user's photos and videos"""

    def __init__(self, username, login_user=None, login_pass=None, quiet=False, max=0, retain_username=False):
        self.username = username
        self.login_user = INSTAGRAM_USERNAME
        self.login_pass = INSTAGRAM_PASS
        self.retain_username = retain_username

        # Controls the graphical output of tqdm
        self.quiet = quiet


        self.session = requests.Session()
        self.cookies = None
        self.logged_in = False

        if self.login_user and self.login_pass:
            self.login()

    def login(self):
        """Logs in to instagram"""
        self.session.headers.update({'Referer': BASE_URL})
        req = self.session.get(BASE_URL)

        self.session.headers.update({'X-CSRFToken': req.cookies['csrftoken']})

        login_data = {'username': self.login_user, 'password': self.login_pass}
        login = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        self.session.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        self.cookies = login.cookies

        if login.status_code == 200 and json.loads(login.text)['authenticated']:
            self.logged_in = True
        else:
            print('Login failed for ' + self.login_user)
            raise ValueError('Login failed for ' + self.login_user)

    def logout(self):
        """Logs out of instagram"""
        if self.logged_in:
            try:
                logout_data = {'csrfmiddlewaretoken': self.cookies['csrftoken']}
                self.session.post(LOGOUT_URL, data=logout_data)
                self.logged_in = False
            except requests.exceptions.RequestException:
                print('Failed to log out ' + self.login_user)


    def scrape(self):
        """Crawls through and downloads user's media"""
        scrapedItems = []
        # Get the user metadata.
        user = self.fetch_user(self.username)

        if user:
            if self.logged_in:
                # Get the user's stories.
                stories = self.fetch_stories(user['id'])
                # Downloads the user's stories and sends it to the executor.
                scrapedItems = [item for item in stories]
        # Crawls the media and sends it to the executor.
        scrapedMedia = [item for item in self.media_gen(self.username)]
        self.logout()
        return scrapedItems,scrapedMedia


    def fetch_user(self, username):
        """Fetches the user's metadata"""
        resp = self.session.get(BASE_URL + username)

        if resp.status_code == 200 and '_sharedData' in resp.text:
            try:
                shared_data = resp.text.split("window._sharedData = ")[1].split(";</script>")[0]
                return json.loads(shared_data)['entry_data']['ProfilePage'][0]['user']
            except (TypeError, KeyError, IndexError):
                pass

    def fetch_stories(self, user_id):
        """Fetches the user's stories"""
        resp = self.session.get(STORIES_URL.format(user_id), headers={
            'user-agent' : STORIES_UA,
            'cookie'     : STORIES_COOKIE.format(self.cookies['ds_user_id'], self.cookies['sessionid'])
        })

        retval = json.loads(resp.text)

        if resp.status_code == 200 and 'items' in retval and len(retval['items']) > 0:
            return [item for item in retval['items']]
        return []

    def getBatchOfPhotos(self,size):
        count = 0
        batch = []
        for item in self.media_gen(self.username):
            batch += [item]
            count += 1
            if count == size:
                yield batch
                batch = []
                count = 0
        yield batch

    def media_gen(self, username):
        """Generator of all user's media"""
        try:
            media = self.fetch_media_json(username, max_id=None)

            while True:
                for item in media['items']:
                    yield item
                if media.get('more_available'):
                    max_id = media['items'][-1]['id']
                    media = self.fetch_media_json(username, max_id)
                else:
                    return
        except ValueError:
            print('Failed to get media for ' + username)

    def fetch_media_json(self, username, max_id):
        """Fetches the user's media metadata"""
        url = MEDIA_URL.format(username)

        if max_id is not None:
            url += '?&max_id=' + max_id

        resp = self.session.get(url)

        if resp.status_code == 200:
            media = json.loads(resp.text)

            if not media['items']:
                raise ValueError('User {0} is private'.format(username))

            media['items'] = [item for item in media['items']]
            return media
        else:
            raise ValueError('User {0} does not exist'.format(username))

def main():
    max = 0
    parser = argparse.ArgumentParser(
        description="instagram-scraper scrapes and downloads an instagram user's photos and videos.")

    parser.add_argument('username', help='Instagram user(s) to scrape', nargs='*')
    parser.add_argument('--destination', '-d', help='Download destination')
    parser.add_argument('--login_user', '-u', help='Instagram login user')
    parser.add_argument('--login_pass', '-p', help='Instagram login password')
    parser.add_argument('--filename', '-f', help='Path to a file containing a list of users to scrape')
    parser.add_argument('--quiet', '-q', action='store_true', help='Be quiet while scraping')
    parser.add_argument('--maximum', '-m', type=int, default=0, help='Maximum number of items to scrape')
    parser.add_argument('--retain_username', '-n', action='store_true',
                        help='Creates username subdirectory when destination flag is set')

    args = parser.parse_args()

    if (args.login_user and args.login_pass is None) or (args.login_user is None and args.login_pass):
        parser.print_help()
        raise ValueError('Must provide login user AND password')

    if not args.username and args.filename is None:
        parser.print_help()
        raise ValueError('Must provide username(s) OR a file containing a list of username(s)')
    elif args.username and args.filename:
        parser.print_help()
        raise ValueError('Must provide only one of the following: username(s) OR a filename containing username(s)')
    usernames = []

    if args.filename:
        usernames = InstagramScraper.parse_file_usernames(args.filename)
    else:
        usernames = InstagramScraper.parse_str_usernames(','.join(args.username))

    scraper = InstagramScraper(usernames, args.login_user, args.login_pass, args.destination, args.quiet, args.maximum, args.retain_username)
    scraper.scrape()
    scraper.scrapeWithoutDownload()

if __name__ == '__main__':
    for item in InstagramScraper("fox_model_israel").getBatch(10):
        print(item)
        break

    #scrapedItems, scrapedMedia = InstagramScraper("fox_model_israel").scrape()
    #print(scrapedMedia["fox_model_israel"][2])
