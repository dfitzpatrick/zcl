import json
from . import objects
from datetime import datetime

"""
{
UnitStat                                    Dict[str, Any]
    name:                                   str
    created:                                int
    lost:                                   int
    killed:                                 int
    feed_score                              int
    lost_score                              int

Profile
    id                                      str
    name                                    str
    lane_id                                 str
    position                                int
    color                                   str

Stats                                       List[Dict[str, Any]]
    [{
        ...profile
        stats                               Dict[str, UnitStat] name
            
            
Snapshot
    event                                   Event
    game_time                               int
    players                                 Stats
    

Main
    id:                                     int 
    match_date:                             str
    mode:                                   str
    variant:                                str
    game_length:                            int
    is_draw:                                boolean
    units_killed                            int
    tanks_made                              int
    nukes_used                              int
    snapshots                               List[Snapshot]
    observers                               List[Profile]
    rosters:                                List[Dict[str, Any]
        [{
            label:                          str
            team_id:                        int
            winner:                         boolean
            profiles:                        List[Profile]
        
    
                
                         
    
    
    
          

"""


class ReplayObjectEncoder(json.JSONEncoder):

    def default(self, o):
        if hasattr(o, 'to_dict'):
            return o.to_dict()

        if isinstance(o, datetime):
            return {'__datetime__': o.replace(microsecond=0).isoformat()}


        return {'__{}__'.format(o.__class__.__name__): o.__dict__}