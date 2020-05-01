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
from api.utils import fetch_or_create_profile
from api.tasks import get_or_create_team
from django.db import transaction
import random


def pickle_in(fn='obj.pickle') -> typing.List[typing.Dict['str', typing.Any]]:
    with open(fn, 'rb') as f:
        return pickle.load(f)

#players = pickle_in('players.pickle')
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

def get_season(num, league: models.League) -> typing.Optional[models.Season]:
    try:
        season = league.seasons.get(name=f'Season {num}')
        return season
    except league.DoesNotExist:
        return

def get_league(num) -> typing.Optional[models.League]:
    if num == 1:
        return models.League.objects.get(name='Professional League')
    elif num == 2:
        return models.League.objects.get(name='Intermediate League')
    elif num == 3:
        return models.League.objects.get(name='Up and Coming League')
    else:
        return

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

def import_game():
    obj, _ = models.Game.objects.get_or_create(
        id='1-S2-1-4632373',
        name='Zone Control CE'
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
@transaction.atomic()
def import_leaderboards(cache=None):
    cache = cache if cache is not None else {}
    for l in leaderboards:

        toon = fetch_or_create_profile(l.get('player_handle'), cache)

        print(f'Importing {toon.name}')
        wins = l.get('wins', 0)
        games = l.get('games', 0)
        losses = games - wins
        models.Leaderboard.objects.update_or_create(
            profile=toon,
            mode='2v2v2v2',
            defaults={
                'created': l.get('created'),
                'wins': wins,
                'games': games,
                'losses':  losses,
                'elo': l.get('elo'),

            }
        )


def get_lane(pos, rosters):
    LANE_POSITION_MAP = {
        0: 7,
        1: 2,
        2: 1,
        3: 4,
        4: 3,
        5: 6,
        6: 5,
        7: 0,

    }
    for r in rosters:
        if LANE_POSITION_MAP[pos] == r['position_number']:
            return r
def get_team_position(num):
    POSITIONS = {
        0: 0,
        1: 0,
        2: 1,
        3: 1,
        4: 2,
        5: 2,
        6: 3,
        7: 3,
    }
    return POSITIONS[num]

def get_profile(handle, handle_map, cache={}) -> typing.Optional[models.SC2Profile]:
    handle_string = handle_map[handle['handle_id']]
    return fetch_or_create_profile(handle_string, cache)

def update_team_outcome(obj, profile, outcome):
    for team_num, team_details in obj.items():
        if profile in team_details['players']:
            team_details['outcome'] = outcome

@transaction.atomic()
def import_matches(match_set=matches):
    cache = {}
    handle_map = {h['id']:h['handle'] for h in handles}
    arcade_map = models.Game.objects.all().first()
    guild = import_guild()
    game = import_game()
    for m in match_set:

        try:
            guild, season, league = None, None, None
            print(f"Importing Match{m.get('id')}")
            related_rosters = [r for r in rosters if r['match_id'] == m['id']]
            related_events = [me for me in match_events if me['match_id'] == m['id']]


            season = None
            league = None
            if m['league_id'] is not None:
                league = get_league(m['league_id'])

            if m['season_id'] is not None and league is not None:
                season = get_season(m['season_id'], league)

            if m['game_id'] is None:
                # No game Id. This match will never be able to get imported.
                # Make a very long fake one.
                m['game_id'] = ''.join(str(random.randint(0, 9)) for _ in range(30))
                print(f"Using Game ID {m['game_id']}")
            match, created = models.Match.objects.get_or_create(
                id=m['game_id'],
                defaults={
                    'created': m['created'],
                    'guild': guild,
                    'arcade_map': arcade_map,
                    'league': league,
                    'season': season,
                    'legacy': True,
                    'ranked': True,
                }
            )
            team_map = {0: {'players': []}, 1: {'players': []}, 2: {'players': []}, 3: {'players': []}}
            for r in related_rosters:
                roster_handle_string = None
                roster_handle_string = handle_map[r['handle_id']]
                #for h in handles:
                #    if h['id'] == r['handle_id']:
                #        roster_handle_string = h['handle']
                print(f"Importing Roster Match {match.id}")
                print(f"Handle {roster_handle_string}")

                handle = fetch_or_create_profile(roster_handle_string, cache)

                team_map[r['team_number']]['players'].append(handle)
                team_map[r['team_number']]['position'] = get_team_position(r['position_number'])
                lane = get_lane(r['position_number'], related_rosters)
                if lane is not None:
                    lane = get_profile(lane, handle_map, cache)
                roster, _ = models.Roster.objects.get_or_create(
                    match=match,
                    sc2_profile=handle,
                    team_number=r['team_number'],
                    position_number=r['position_number'],
                    defaults={
                        'created': r['created'],
                        'color': r['color'],
                        'lane': lane,
                    }
                )



            for me in [r for r in related_events]:

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
                    sc2handle = fetch_or_create_profile(handle_string, cache)
                if opposing_handle_string is not None:
                    opposing_handle = fetch_or_create_profile(opposing_handle_string, cache)
                print(f"Importing Match {match.id} Event {me['key']}")

                if me['key'] == 'WIN':
                    models.MatchWinner.objects.update_or_create(
                        match=match,
                        profile=sc2handle
                    )
                    update_team_outcome(team_map, sc2handle, 'win')

                elif me['key'] == 'LOSS':
                    models.MatchLoser.objects.update_or_create(
                        match=match,
                        profile=sc2handle,
                        defaults={
                            'killer': None,
                            'left_game': False,
                            'game_time': me.get('game_time', 0) or 0,
                            'victim_number': 0,
                        }
                    )
                    update_team_outcome(team_map, sc2handle, 'loss')
                elif me['key'] == 'DRAW':
                    match.draw = True
                    match.save()
                    update_team_outcome(team_map, sc2handle, 'draw')
                else:
                    game_event_name, created = models.GameEventName.objects.get_or_create(
                        id=me['key'],
                        defaults={'title': f"New Game Event {me['key']}"}
                    )
                    obj, _ = models.GameEvent.objects.get_or_create(
                        key=game_event_name,
                        match=match,
                        profile=sc2handle,
                        opposing_profile=opposing_handle,
                        game_time=me['game_time'],
                        defaults= {
                            'value': me['value'],
                            'description': me['description'],
                            'total_score': 0,
                            'minerals_on_hand': 0,
                        }
                    )
                    print(obj.key)
            updated_rosters = models.Roster.objects.filter(match=match)
            for team_num, team_details in team_map.items():
                team_obj = get_or_create_team(team_details['players'])
                print(f"Mapping {team_details}")
                print(team_obj)
                match_team, created = models.MatchTeam.objects.get_or_create(
                    match=match,
                    team=team_obj,
                    defaults={
                        'position': team_details.get('position', -1),
                        'outcome': team_details.get('outcome', "unknown"),
                    }

                )
                for ros in updated_rosters:
                    if ros.sc2_profile in team_details['players']:
                        ros.team = match_team
                        ros.save()

        except models.SC2Profile.DoesNotExist:
            continue
    return cache

