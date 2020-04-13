from accounts.models import DiscordUser

import datetime
import pickle
import typing
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from api import models

def pickle_in(fn='obj.pickle') -> typing.List[typing.Dict['str', typing.Any]]:
    with open(fn, 'rb') as f:
        return pickle.load(f)

players = pickle_in('players.pickle')
handles = pickle_in('handles.pickle')
leagues = pickle_in('leagues.pickle')
seasons = pickle_in('seasons.pickle')
leaderboards = pickle_in('leaderboards.pickle')
matches = pickle_in('matches.pickle')
rosters = pickle_in('rosters.pickle')
match_events = pickle_in('match_events.pickle')


def player_id(n):
    for p in players:
        if p.get('id') == n:
            return p.get('discord_id')




def import_players():
    global players
    for i, p in enumerate(players):
        if p['discord_id'] is None:
            continue
        print(f"Loading {p}")

        DiscordUser.objects.get_or_create(
            id=p['discord_id'],
            defaults={
                'id': p['discord_id'],
                'username': p['username'],
                'discriminator': p['discord_discriminator'],
                'email': f'a{i}@a.com',
                'avatar': '',
            }
        )

def import_handles():

    for h in handles:
        print(f"Parsing: {h.get('handle')}" )
        try:
            region, game, realm, profile_id = h.get('handle').split('-')
        except ValueError:
            continue

        profile_url = f'https://starcraft2.com/en-us/profile/{region}/{realm}/{profile_id}'
        obj, created = models.SC2Profile.objects.get_or_create(
            id=h.get('handle'),
            defaults={
                'id': h.get('handle'),
                'created': h.get('created'),
                'profile_url': profile_url,
                'name': h.get('name')
            }
        )


        if h.get('player_id') is None:
            continue

        try:
            p = DiscordUser.objects.get(id=player_id(h.get('player_id')))
            obj.discord_users.add(p)
            obj.save()
        except DiscordUser.DoesNotExist:
            continue


def find_avatar():


        driver = os.path.normpath('c:/users/dfitz/chromedriver_win32/chromedriver.exe')
        browser = webdriver.Chrome(executable_path=driver)

        for p in models.SC2Profile.objects.all():
            try:
                print(p.profile_url)
                if p.avatar_url:
                    continue
                browser.implicitly_wait(30)

                browser.get(p.profile_url)
                search = browser.find_element_by_class_name('Portrait-image')
                pic_url = search.find_element(by=By.TAG_NAME, value='img').get_attribute('src')

                p.avatar_url = pic_url
                p.save()


            except:
                continue
        browser.quit()

def import_guild():
    obj, _ = models.Guild.objects.get_or_create(
        id=476518371320397834,
        defaults={
            'name': 'ZC LEAGUES',
        }
    )
    return obj

def import_leagues():
    guild = import_guild()
    for l in leagues:
        l_obj, _ = models.League.objects.get_or_create(
            guild=guild,
            name=l.get('name'),
            defaults={
                'description': l.get('description', ''),
            }
        )
        for s in seasons:
            s_obj, _ = models.Season.objects.get_or_create(
                league=l_obj,
                name=s.get('name'),
                defaults={
                    'description': s.get('description', ''),
                }
            )

def import_leaderboards():
    for l in leaderboards:
        print(f"Importing {l.get('player_name')}")
        try:
            toon = models.SC2Profile.objects.get(
                id=l.get('player_handle')
            )
        except models.SC2Profile.DoesNotExist:
            continue
        models.Leaderboard.objects.get_or_create(
            toon=toon,
            defaults={
                'created': l.get('created'),
                'wins': l.get('wins'),
                'games': l.get('games'),
                'elo': l.get('elo'),
            }
        )


def import_matches():
    for m in matches:
        try:
            guild, season, league = None, None, None
            print(f"Importing Match{m.get('id')}")
            related_rosters = [r for r in rosters if r['match_id'] == m['id']]
            related_events = [me for me in match_events if me['match_id'] == m['id']]

            guild = models.Guild.objects.first()
            season = None
            league = None
            if m['season_id'] is not None:
                season = models.Season.objects.get(id=m['season_id'])
            if m['league_id'] is not None:
                league = models.League.objects.get(id=m['league_id'])

            match, created = models.Match.objects.get_or_create(
                game_id=m['game_id'],
                defaults={
                    'created': m['created'],
                    'guild': guild,
                    'league': league,
                    'season': season,
                }
            )
            for r in related_rosters:
                roster_handle_string = None
                for h in handles:
                    if h['id'] == r['handle_id']:
                        roster_handle_string = h['handle']
                print(f"Importing Roster Match {match.id}")
                print(f"Handle {roster_handle_string}")

                handle = models.SC2Profile.objects.get(id=roster_handle_string)

                roster, _ = models.Roster.objects.get_or_create(
                    match=match,
                    sc2_profile=handle,
                    team_number=r['team_number'],
                    position_number=r['position_number'],
                    defaults={
                        'created': r['created'],
                        'color': r['color']
                    }
                )
            for me in related_events:
                # Need to get the original handle profile string
                handle_string = None
                opposing_handle_string = None
                for h in handles:
                    if h['id'] == me['opposing_handle_id']:
                        opposing_handle_string = h['handle']
                    if h['id'] == me['handle_id']:
                        handle_string = h['handle']
                sc2handle, opposing_handle = None, None
                if handle_string is not None:
                    sc2handle = models.SC2Profile.objects.get(id=handle_string)
                if opposing_handle_string is not None:
                    opposing_handle = models.SC2Profile.objects.get(id=opposing_handle_string)
                print(f"Importing Match {match.id} Event {me['key']}")
                obj, _ = models.MatchEvent.objects.get_or_create(
                    match=match,
                    handle=sc2handle,
                    opposing_handle=opposing_handle,
                    game_time=me['game_time'],
                    defaults= {
                        'value': me['value'],
                        'raw': me['raw'],
                        'description': me['description'],
                        'points': me['points'],
                        'key': me['key'],
                    }
                )
                print(obj.key)
        except models.SC2Profile.DoesNotExist:
            continue

from django.db.models import Q, F, Avg, Count
from api.annotations.leaderboards import qs_with_ranking
from api.models import *
from accounts.models import *

o = (
    DiscordUser
    .objects
    .annotate(avg_elo=Avg(
        'profiles__leaderboard__elo'
    ))
    .all()
)
