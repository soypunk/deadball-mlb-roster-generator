#!/usr/bin/env python3
#
# scorecard - creates a Deadball III roster from MLB data
#
# Requires: https://pypi.org/project/MLB-StatsAPI/

from datetime import datetime
from decimal import Decimal, InvalidOperation
from pprint import pprint
import argparse
import math
import random
import statsapi

# ========================================================================================
# Deadball Objects
# ========================================================================================
class Dice():
    """A Dice object with a variable number of sides
    
    Attributes
    ----------
    sides : int
        the number of sides our dice should have (default 6)

    Methods
    -------
    roll(times=1)
        returns a list of dice rolls
    
    Example
    -------    
    d = Dice(6)
    rolls = d.roll(2)    
    """
        
    def __init__(self, sides=6):
        self.sides = int(sides)
    
    def roll(self, times=1):
        """ Rolls a die with x sides """
        rng = random.Random()        
        rolls = []
        while len(rolls) < times:
            roll = rng.randint(1, self.sides)
            rolls.append(roll)            
        return rolls
        
    def __str__(self):
        return "A {self.sides} sided die".format(self=self)


class Team():
    """A Team object"""
    def __init__(self, name, mlb_id):
        self.name = str(name)
        self.mlb_id = int(mlb_id)
        self.batters = []
        self.pitchers = []        

    def __str__(self):
        return self.name
    

class Manager():
    """A Manager object"""
    def __init__(self, name, daring=None):
        self.name = str(name)
        if daring == None:
            d = Dice(20)
            rolls = d.roll()
            daring = rolls[0]
        self.daring = int(daring)

    def __str__(self):
        return self.name


class Player(object):
    """A Manager object"""  
    def __init__(self, name, mlb_id, pos, bt=0, obt=0):
        self.name = str(name)
        self.mlb_id = int(mlb_id)
        self.pos = str(pos).upper()
        self.bt = bt
        self.obt = obt

    def __str__(self):
        return self.name


class Batter(Player):
    def __init__(self, name, mlb_id, pos, bt=0, obt=0, bats='R', p=0, s=0, c=0, d=0):
        super().__init__(name, mlb_id, pos, bt, obt)
        self.bats = bats
        self._p = p
        self._s = s
        self._c = c
        self._d = d
        
    def __str__(self):
        return super().__str__()
    
    @property
    def p(self):
        if self._p == -2:
            return 'P--'
        elif self._p == -1:
            return 'P-'
        elif self._p == 1:
            return 'P+'
        elif self._p == 2:
            return 'P++'
        else:
            return ''
            
    @property
    def s(self):
        if self._s == -1:
            return 'S-'
        elif self._s == 1:
            return 'S+'
        else:
            return ''
            
    @property
    def c(self):
        if self._c == -1:
            return 'C-'
        elif self._c == 1:
            return 'C+'
        else:
            return ''
            
    @property
    def d(self):
        if self._d == -1:
            return 'D-'
        elif self._d == 1:
            return 'D+'
        else:
            return ''
            
    @property
    def traits(self):
        return [self.p,self.s,self.c,self.d]


class Pitcher(Player):
    def __init__(self, name, mlb_id, pos, era, pd, bt=0, obt=0, bats='L', throws='R', k=0, gb=0, cn=0, st=0):
        super().__init__(name, mlb_id, pos, bt, obt)
        self.throws = throws
        self.pd = pd
        self.era = era
        self._k = k
        self._gb = gb
        self._cn = cn
        self._st = st
        
    def __str__(self):
        return super().__str__()

    @property
    def k(self):
        if self._k == 1:
            return 'K+'
        else:
            return ''
            
    @property
    def gb(self):
        if self._gb == 1:
            return 'GB+'
        else:
            return ''
            
    @property
    def cn(self):
        if self._cn == 1:
            return 'CN+'
        else:
            return ''
            
    @property
    def st(self):
        if self._st == 1:
            return 'ST+'
        else:
            return ''
            
    @property
    def traits(self):
        return [self.k,self.gb,self.cn,self.st]


# ========================================================================================
# Functions
# ========================================================================================

def get_player_data(player_id, season, groups=['hitting','pitching','fielding'], type='season'):
    hydrate_group_string = '[' + ','.join(groups) + ']'
    params = {
        'personId':player_id,
        'hydrate':'stats(group='+hydrate_group_string+',type='+type+',season='+str(season)+'),currentTeam'
        }
    r = statsapi.get('person',params)
    pprint(r)
    bio =   {
                'id' : r['people'][0]['id'],
                'first_name' : r['people'][0]['useName'],
                'last_name' : r['people'][0]['lastName'],
                'active' : r['people'][0]['active'],
                'current_team' : r['people'][0]['currentTeam']['name'],
                'position' : r['people'][0]['primaryPosition']['abbreviation'],
                'nickname' : r['people'][0].get('nickName'),
                'active' : r['people'][0]['active'],
                'last_played' : r['people'][0].get('lastPlayedDate'),
                'bat_side' : r['people'][0]['batSide']['description'],
                'pitch_hand' : r['people'][0]['pitchHand']['description'],
                'stats': {
                    'hitting': {},
                    'pitching': {},
                    'fielding': {}                  
                }
            }

    for s in r['people'][0].get('stats',[]):
        for i in range(0,len(s['splits'])):
            stat_group =    {
                                'type' : s['type']['displayName'],
                                'group' : s['group']['displayName'],
                                'stats' : s['splits'][i]['stat']
                            }
            bio['stats'][s['group']['displayName']] = s['splits'][i]['stat']

    if len(bio['stats'])==0:
        raise ValueError('No stats found for given player, type, and group.')
    
    return bio

def get_team_data(team_name):
    return statsapi.lookup_team(team_name)[0]


def get_team_roster(team_id, season, type='active'):
    team_roster_params = {
        'rosterType':type,
        'season':season,
        'teamId':team_id
        }   
    return statsapi.get('team_roster',team_roster_params)


def create_player(player_data, type='batter', midpoint_era=Decimal('3.50')):
    #
    # player_data attributes:
    # 'id', 'first_name', 'last_name', 'active', 'current_team', 'position', 'nickname', 
    # 'last_played', 'mlb_debut', 'bat_side', 'pitch_hand', 'stats'
    #
    # player_data['stats']['splits']
    # 'gamesPlayed', 'groundOuts', 'runs', 'doubles', 'triples', 'homeRuns', 'strikeOuts',
    # 'baseOnBalls', 'intentionalWalks', 'hits', 'hitByPitch', 'avg', 'atBats', 'obp', 
    # 'slg', 'ops', 'caughtStealing', 'stolenBases', 'stolenBasePercentage', 
    # 'groundIntoDoublePlay', 'numberOfPitches', 'plateAppearances', 'totalBases', 'rbi',
    # 'leftOnBase', 'sacBunts', 'sacFlies', 'babip', 'groundOutsToAirouts'
    # 
    # player_data['stats']['pitching']
    # 'gamesPlayed', 'gamesStarted', 'groundOuts', 'runs', 'homeRuns', 'strikeOuts', 
    # 'baseOnBalls', 'intentionalWalks', 'hits', 'avg', 'atBats', 'obp', 'slg', 'ops', 
    # 'caughtStealing', 'stolenBases', 'stolenBasePercentage', 'groundIntoDoublePlay', 
    # 'numberOfPitches', 'era', 'inningsPitched', 'wins', 'losses', 'saves', 
    # 'saveOpportunities', 'holds', 'earnedRuns', 'whip', 'battersFaced', 'gamesPitched',
    # 'completeGames', 'shutouts', 'strikes', 'strikePercentage', 'hitBatsmen', 'balks',
    # 'wildPitches', 'pickoffs', 'airOuts', 'groundOutsToAirouts', 'winPercentage', 
    # 'pitchesPerInning', 'gamesFinished', 'strikeoutWalkRatio', 'strikeoutsPer9Inn', 
    # 'walksPer9Inn', 'hitsPer9Inn', 'runsScoredPer9', 'homeRunsPer9', 'inheritedRunners',
    # 'inheritedRunnersScored'
    #
    # player_data['stats']['fielding']
    # 
    # 'assists', 'putOuts', 'errors', 'chances', 'fielding', 'position', 
    # 'rangeFactorPerGame', 'innings', 'games', 'gamesStarted', 'doublePlays'
    #    
    type = type.lower()
    player_name = player_data['first_name']

    if player_data['nickname']:
        player_name += ' "{nickname}"'.format(**player_data)       
    player_name += ' ' + player_data['last_name']

    #
    # P hitting trait
    #
    p = 0
    if 'homeRuns' in player_data['stats']['hitting']:
        hr = int(player_data['stats']['hitting']['homeRuns'])
        if hr >=35:
            p = 2
        elif hr >= 20 and hr < 35:
            p = 1
        elif hr > 5 and hr < 10:
            p = -1            
        elif hr <= 5:
            p = -2
    
    if 'slg' in player_data['stats']['hitting']:
        try:
            slg = Decimal(player_data['stats']['hitting']['slg'])
        except:
            slg = False
        
        if p < 2:
            if slg >= Decimal('.540'):          
                p = 2
            elif slg >= Decimal('.450') and slg < Decimal('.540'):
                p = 1

    if 'avg' in player_data['stats']['hitting']:
        try:
            ba = Decimal(player_data['stats']['hitting']['avg'])
            
            try:
                slg
            except NameError:
                slg = False
            
            if slg:
                iso = slg - ba
                if iso <= Decimal('.120') and iso > Decimal('.090'):
                    p = -1
                elif iso <= Decimal('.090'):
                    p = -2                
            
            bt = str(round(ba,2))[2:4]
        except (InvalidOperation, ValueError):
            bt = 0
    else:
        bt = 0

    if 'obp' in player_data['stats']['hitting']:        
        try:
            obp = Decimal(player_data['stats']['hitting']['obp'])
            obt = str(round(obp,2))[2:4]
        except (InvalidOperation, ValueError):
            obt = 0        
    else:
        obt = 0
    
    #
    # contact trait
    # 
    c = 0
    if 'doubles' in player_data['stats']['hitting']:
        if player_data['stats']['hitting']['doubles'] >= 35:
            c = 1
    
    if c == 0:
        if 'strikeOuts' in player_data['stats']['hitting'] and 'plateAppearances' in player_data['stats']['hitting']:
            so = player_data['stats']['hitting']['strikeOuts']
            pa = player_data['stats']['hitting']['plateAppearances']
            
            if pa != 0:            
                k00 = int(round(so / pa, 2) * 100)
            
                if k00 > 25:
                    c = -1
                elif k00 <= 10:
                    c = 1

    #
    # speed trait
    # 
    s = 0
    if 'stolenBases' in player_data['stats']['hitting']:
        sb = player_data['stats']['hitting']['stolenBases']
        if sb >= 20:
            s = 1
        elif sb == 0:
            s = -1

    if type == 'pitcher':    
        k = 0
        try:
            if Decimal(player_data['stats']['pitching']['strikeoutsPer9Inn']) > Decimal('9.0'):
                k = 1
        except:
            k = 0
            
        gb = 0
        try:
            if (player_data['stats']['pitching']['groundIntoDoublePlay']/9) > 1:
                gb = 1
        except:
            gb = 0
        
        cn = 0
        try:
            if Decimal(player_data['stats']['pitching']['walksPer9Inn']) < Decimal('2.0'):
                cn = 1
        except:
            cn = 0
        
        st = 0
        try:
            if Decimal(player_data['stats']['pitching']['inningsPitched']) > 200:
                st = 1
        except:
            st = 0
        
        try:
            era = Decimal(player_data['stats']['pitching']['era'])
        except KeyError:
            era = Decimal(0.00)
        
        era_table = get_era_table(midpoint_era)
        pitch_dice = {k:v for (k,v) in era_table.items() if v < era}
        sorted_pitch_dice = sorted(list(pitch_dice.values()),reverse=True)
        
        try:
            pd = list(pitch_dice.keys())[list(pitch_dice.values()).index(sorted_pitch_dice[0])]            
        except:
            pd = '-d20'
    
        player = Pitcher(
            name = player_name,
            mlb_id = player_data['id'],
            pos = player_data['position'],
            pd = pd,
            bt = bt,
            obt = obt,
            bats = player_data['bat_side'][0],
            throws = player_data['pitch_hand'][0],
            era = era,
            k = k,
            gb = gb,
            cn = cn,
            st = st
        )
    else:
        player = Batter(
            name = player_name,
            mlb_id = player_data['id'],
            pos = player_data['position'],
            bt = bt,
            obt = obt,
            bats = player_data['bat_side'][0],
            p = p,
            c = c,
            s = s
        )
    
    return player
    

def create_team(team_name, season, dh, midpoint_era):
    team_data = get_team_data(team_name)
    # team is a dictionary with the following keys    
    # 'id', 'name', 'teamCode', 'fileCode', 'teamName', 'locationName', 'shortName'
    
    team_roster_data = get_team_roster(team_data['id'], season)
    
    team = Team(
        name = team_data['name'],
        mlb_id = team_data['id']
    )
    
    for player in team_roster_data['roster']:            
        if player['position']['abbreviation'] == 'P':
            groups = ['hitting','pitching']
        else:
            groups = ['hitting','fielding']
        
        player_data = get_player_data(player['person']['id'], season, groups)        
        
        if player['position']['abbreviation'] == 'P':
            p = create_player(player_data, type='pitcher', midpoint_era=midpoint_era)
            team.pitchers.append(p)        
            if dh == False:
                p = create_player(player_data, type='batter')
                team.batters.append(p)
        else:
            p = create_player(player_data, type='batter')
            team.batters.append(p)
    
    return team

def get_era_table(era):
    BASE_ERA = Decimal(str(era)[0:2]+'9'+str(era)[3:4])
    ERA_D20 = BASE_ERA-3
    ERA_D12 = BASE_ERA-2
    ERA_D8 = BASE_ERA-1
    ERA_D4 = era
    ERA_ND4 = BASE_ERA
    ERA_ND8 = BASE_ERA+1
    ERA_ND12 = BASE_ERA+2
    ERA_ND20 = BASE_ERA+3
    ERA_N20 = BASE_ERA+4
    ERA_N25 = BASE_ERA+5
    ERA_N30 = BASE_ERA+6
    ERA_DIE_CODE_TABLE = {
        'd20' :     ERA_D20,
        'd12' :     ERA_D12,
        'd8'  :     ERA_D8,
        'd4'  :     ERA_D4,
        '-d4' :     ERA_ND4,
        '-d8' :     ERA_ND8,
        '-d12':     ERA_ND12,
        '-d20':     ERA_ND20,
        '-20' :     ERA_N20,
        '-25' :     ERA_N25,
        '-30' :     ERA_N30
    }
    return ERA_DIE_CODE_TABLE


def main(team, season, dh, midpoint_era):
    # lookup_team returns a list of search results, so we take the first one [0]        
    team = create_team(team, season, dh, midpoint_era)
    die_codes = get_era_table(midpoint_era)
    era_list = list(die_codes.values())    
    html = """<!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://unpkg.com/tachyons/css/tachyons.min.css">
        <title>{team.name}</title>
    </head>
    <body class="sans-serif ma0 pa1">
        <h1 class="lh-solid f3">{team.name}</h1>
        <h2 class="lh-solid f5">Batters</h2>
        <table class="f6 w-100 mb0 collapse ba br2 b--black-20 pv2 ph2 mt4">
            <thead>
                <tr class="bg-moon-gray">
                    <th class="pv2 ph2 tl f6 fw6 ttu">Pos</th>
                    <th class="pv2 ph2 tl f6 fw6 ttu">Bats</th>
                    <th class="pv2 ph2 tl f6 fw6 ttu">Name</th>
                    <th class="pv2 ph2 tl f6 fw6 ttu">BT</th>
                    <th class="pv2 ph2 tl f6 fw6 ttu">OBT</th>
                    <th class="pv2 ph2 tl f6 fw6 ttu">Traits</th>
                </tr>
            </thead>
            <tbody>
    """.format(team=team)
    for batter in team.batters:
        html += """
                <tr class="striped--light-gray">
                    <td class="pv2 ph2">{batter.pos}</dt>
                    <td class="pv2 ph2">{batter.bats}</dt>
                    <td class="pv2 ph2">{batter.name}</dt>
                    <td class="pv2 ph2">{batter.bt}</dt>
                    <td class="pv2 ph2">{batter.obt}</dt>
                    <td class="pv2 ph2">{traits}</dt>
                </tr>
        """.format(batter=batter, traits=', '.join(filter(None, batter.traits)))
    html += """
        </tbody>
        </table>
        <p class="mt0 mb3"><small>(Optional trait: D+ 8.0 Def or Golden Glove / D- -12 Def)</small></p>

        <section class="flex">
            <section class="w-75">
                <h2 class="lh-solid f5">Pitchers</h2>
                <table class="f6 w-100 collapse ba br2 b--black-20 pv2 ph2 mt4">
                    <thead>
                        <tr class="bg-moon-gray">
                            <th class="pv2 ph2 tl f6 fw6 ttu">Pos</th>
                            <th class="pv2 ph2 tl f6 fw6 ttu">Throws</th>
                            <th class="pv2 ph2 tl f6 fw6 ttu">Name</th>                
                            <th class="pv2 ph2 tl f6 fw6 ttu">PD</th>
                            <th class="pv2 ph2 tl f6 fw6 ttu">ERA</th>                    
                            <th class="pv2 ph2 tl f6 fw6 ttu">Traits</th>
                        </tr>
                    </thead>
                    <tbody>
    """.format(team=team)
    for pitcher in team.pitchers:
        html += """
                        <tr class="striped--light-gray">
                            <td class="pv2 ph2">{pitcher.pos}</dt>
                            <td class="pv2 ph2">{pitcher.throws}</dt>
                            <td class="pv2 ph2">{pitcher.name}</dt>
                            <td class="pv2 ph2">{pitcher.pd}</dt>
                            <td class="pv2 ph2">{pitcher.era}</dt>
                            <td class="pv2 ph2">{traits}</dt>
                        </tr>
        """.format(pitcher=pitcher, traits=', '.join(filter(None, pitcher.traits)))    
    html += """
                    </tbody> 
                </table>
            </section>
            <section class="w-25">
                <h2 class="lh-solid f5">Pitch Die Codes</h2>
                <table class="f7 collapse ba br2 b--black-20 pv2 ph2 mt4">
                    <thead>
                        <tr class="bg-moon-gray">
                            <th class="pv2 ph2 tl f6 fw6 ttu">ERA</th>
                            <th class="pv2 ph2 tl f6 fw6 ttu">D</th>                
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[0]}</td>
                            <td class="pv2 ph2">d20</td>     
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[1]}</td>
                            <td class="pv2 ph2">d12</td>                   
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[2]}</td>
                            <td class="pv2 ph2">d8</td>                   
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[3]}</td>
                            <td class="pv2 ph2">d4</td>                   
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[4]}</td>
                            <td class="pv2 ph2">-d4</td>                   
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[5]}</td>
                            <td class="pv2 ph2">-d8</td>                   
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[6]}</td>
                            <td class="pv2 ph2">-d12</td>                   
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[7]}</td>
                            <td class="pv2 ph2">-d20</td>
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[8]}</td>
                            <td class="pv2 ph2">-20</td>
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[9]}</td>
                            <td class="pv2 ph2">-25</td>
                        </tr>
                        <tr>
                            <td class="pv2 ph2">ERA &lt; {era[10]}</td>
                            <td class="pv2 ph2">-30</td>
                        </tr>                          
                    </tbody>
                </table>        
            </section>
        </section>
    </body>
    </html>
    """.format(team=team, era=era_list)
    print(html)


# ========================================================================================
# __main__
# ========================================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--team", help="an MLB team name", required=True)
    parser.add_argument("-s", "--season", help="What season (YYYY) to use? defaults to current", type=int, default=datetime.now().year)
    parser.add_argument("-e", "--era", help="Tweak the midpoint ERA", type=Decimal, default=Decimal('3.50'))
    parser.add_argument('--dh', action='store_true', default=False)
    args = parser.parse_args()
    main(team=args.team, season=args.season, dh=args.dh, midpoint_era=args.era)