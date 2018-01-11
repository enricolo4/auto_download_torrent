#!/usr/bin/python
# -*- coding: utf-8 -*-

import feedparser
import hashlib
import json
import libtorrent as lt
import os
import time
from datetime import date
from datetime import datetime
from time import mktime

'''
    No site showrss.info
    self.__feed_rss = url da sua showrss
    O endereço se encontra em myfeed/show Na parte inferior do site possue um
    endereço 'Your custom feed address'

    self.__save_path = Diretório que você deseja salvar as séries
'''


class TorrentDownloader:
    def __init__(self):
        self.__feed_rss = 'add_sua_showrss_aqui'
        self.__save_path = 'diretório_para_salvar_sua_série'
        self.__session = lt.session()
        self.__session.listen_on(6881, 6891)

    # Parser feed
    def get_feed_items(self, feed_rss):
        return(feedparser.parse(feed_rss))

    def generate_hash(self, link, title):
        return(hashlib.md5((link + title).encode('utf-8')).hexdigest())

    def download_torrent(self, link, title):
        params = {
            'auto_managed': True,
            'duplicate_is_error': True,
            'paused': False,
            'save_path': self.__save_path,
            'sequential_download': False,
            'seed_mode': False,
            'storage_mode': lt.storage_mode_t(2),
            'url': link
        }

        handle = self.__session.add_torrent(params)
        s = handle.status()
        self.__session.start_dht()

        while(not handle.has_metadata()):
            s = handle.status()
            time.sleep(1)

        print(s.state)
        while(not s.is_seeding and (s.state != 'checking_files')):
            s = handle.status()
            res = [s.state, title, s.progress*100]
            print(
                  'State: {0} ' 'Title: {1} Progresso: {2:.1f}%'.format(res[0],
                                                                        res[1],
                                                                        res[2])
                )
            time.sleep(0.5)
            os.system('cls' if os.name == 'nt' else 'clear')

    def remove_key(self, hash_dict, keys):
        for key in keys:
            day = datetime.strptime(key, '%d/%m/%Y')
            delta_time = (date.today() - day.date()).days
            if delta_time >= 25:
                hash_dict.pop(key)
        return hash_dict, list(hash_dict.keys())
    
    def checknew(self):
        series_dict = {}
        series_keys = []
        has_change = False

        today = str(date.today().strftime('%d/%m/%Y'))

        if os.path.isfile('series.json') and os.path.getsize('series.json'):
            with open('series.json', 'r') as series_file:
                series_dict = json.load(series_file)
                series_keys = list(series_dict.keys())
        else:
            with open('series.json', 'w') as series_file:
                    pass

        feeds = self.get_feed_items(self.__feed_rss)

        list_hash = []

        if len(series_keys) > 0:
            # for sk in series_keys:
            #     list_aux.append(series_dict[sk]['hash_code'])
            list_hash = [str(series_dict[x]['hash_code']) for x in series_dict]

        for i in range(len(feeds.entries)):
            new_hash = self.generate_hash(
                feeds.entries[i].link,
                feeds.entries[i].title
            )

            if new_hash not in list_hash:
                has_change = True
                print('Não existe esse hash na Lista')

                self.download_torrent(
                    feeds.entries[i].link,
                    feeds.entries[i].title
                )

                pub_date = datetime.fromtimestamp(
                    mktime(
                        feeds.entries[i].published_parsed
                    )
                ).strftime('%d/%m/%Y')

                series_dict.update(
                    {
                        feeds.entries[i].title: {
                            'hash_code': new_hash,
                            'magnet_link': feeds.entries[i].link,
                            'description': feeds.entries[i].description,
                            'pub_date': pub_date,
                            'download_date': today,
                            'watched': False
                        }
                    }
                )
                print('Add New TV Show: ', feeds.entries[i].title)
                print('Add New Hash: ', new_hash)
        if has_change:
            with open('series.json', 'w') as series_file:
                json.dump(series_dict, series_file, indent=4)


if __name__ == "__main__":
    TorrentDownloader().checknew()
