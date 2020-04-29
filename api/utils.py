import gzip
import io
import json
import re
import typing

import boto3
import requests
import zclreplay
from django.conf import settings



from .models import SC2Profile

def serialize_drf_serializers(obj):
    if hasattr(obj, 'data'):
        return obj.data
    return obj

def get_player_name(profile: SC2Profile) -> str:
    base_url = "https://starcraft2.com/en-us/profile"
    url = "{0}/{1.region}/{1.realm}/{1.profile_id}".format(base_url, profile)
    r = requests.get(url, allow_redirects=True)
    pattern = re.compile("<title>(.+?)</title>")
    matches = re.findall(pattern, r.content.decode('utf-8'))
    name = matches[0].split('-')
    name = name[1].strip()
    if name == "StarCraft II Official Game Site":
        return "Unknown"
    return name

def gzip_chart_to_s3(obj: typing.Any, match_id: int, name: str, bucket: str = 'zcleagues'):
    key = 'charts/{0}/{0}_{1}.json.gz'.format(match_id, name)
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    tmp = io.BytesIO()
    with gzip.GzipFile(fileobj=tmp, mode='wb') as fout:
        fout.write(json.dumps(obj).encode('utf-8'))
    tmp.seek(0)
    s3.upload_fileobj(tmp, bucket, key)

def get_chart_from_s3(match_id: int, name: str, bucket: str = 'zcleagues'):
    key = 'charts/{0}/{0}_{1}.json.gz'.format(match_id, name)
    s3 = boto3.client('s3',
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    b_stream = io.BytesIO(s3.get_object(Bucket=bucket, Key=key)['Body'].read())
    with gzip.GzipFile(fileobj=b_stream, mode='rb') as gz:
        data = gz.read().decode()
        data = json.loads(data)
    return data


def fetch_or_create_profile(profile: typing.Union[str, zclreplay.Player], cache: typing.Dict[str, typing.Any]) -> typing.Optional[SC2Profile]:
    """
    Commonly we need to fetch profiles from the replay parser. This helps optimize it by storing the results of a
    query in a cache that the caller passes in. Python passes in dicts by reference so this will mutate from the caller.

    If no profile is found, we create it and update the cache with the new instance.
    Parameters
    ----------
    profile: either the profile string, or a replay Player instance
    cache: A dict container that is indexed by profile_id and has the resulting SC2Profile object

    Returns
    -------
    Optional[SC2Profile]. This will return None if the profile attribute is None
    """
    from api.tasks import get_profile_details
    profile_id = profile # Default to string

    if profile_id is None:
        return

    if isinstance(profile, zclreplay.Player):
        profile_id = profile.profile_id

    if cache.get(profile_id) is not None:
        return cache[profile_id]

    # Cache Miss
    obj, created = SC2Profile.objects.get_or_create(
        id=profile_id,
        defaults={'name': 'FOO'}
    )
    if created:
        get_profile_details.delay(obj.id)
    cache[profile_id] = obj
    return obj

def get_or_create_profile(player: typing.Union[str, zclreplay.Player]) -> typing.Optional[SC2Profile]:
    profile_id = player

    if isinstance(player, zclreplay.Player) and player is not None:
        profile_id = player.profile_id

    if profile_id is None:
        return

    obj, created = SC2Profile.objects.get_or_create(
        id=profile_id,
        defaults={'name': 'FOO'}
    )
    if created:
        obj.name = get_player_name(obj)
        obj.save()
    return obj

def position_number_to_team_string(n: int):
    if n == 0 or n == 1:
        return "Top left"
    if n == 2 or n == 3:
        return "Top Right"
    if n == 4 or n == 5:
        return "Bottom Right"
    if n == 6 or n == 7:
        return "Bottom Left"
    return "Unknown"

def make_filter_params(params):
    result = {}
    for key in params:
        val = params.get(key)
        result[key] = val if val else None
    return result
