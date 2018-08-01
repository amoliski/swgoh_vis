
from datetime import datetime
import json
from pyquery import PyQuery as pq
import time
import random
from urllib.error import HTTPError

from database_helpers import (
  sql_connect,
  romans,
  insert_unit_record,
  get_users,
  insert_gp_record,
  insert_guild_gp,
  get_user_id,
  getRandomRgb,
  get_users_gp,
  get_guild_gp,
  gapfill,
  patch_guild_gp,
  patch_user_min
  )


def userlist(cnx=None):
    if not cnx:
        cnx = sql_connect()
    cursor = cnx.cursor()
    cursor.execute("select * from member where active=true")
    res = cursor.fetchall()
    return res

def cache_user_list():
    result = userlist()
    with open('/home/amoliski/swgoh/static/user_list.json', 'w') as f:
        f.write(json.dumps(result))

def units_changed_this_week():
    cnx = sql_connect()
    cur = cnx.cursor()
    changed_units = "select * from unit join member on unit.user_id = member.id and week(time) = week(now()) where member.active = true order by unit_name;"
    cur.execute(changed_units)
    r = cur.fetchall()
    return r

def unit_list():
    """
    Handy for figuring out what the different squad units are called
    """
    cnx = sql_connect()
    cur = cnx.cursor()
    sql = "select distinct(unit_name) from unit;"
    cur.execute(sql)
    result = [x[0] for x in cur.fetchall()]
    return result

def cache_unit_list():
    # Saves a list of all of the units that live in our DB
    result = unit_list()
    with open('/home/amoliski/swgoh/static/unit_list.json', 'w') as f:
        f.write(json.dumps(result))

def capture():
    """
    Load up the swgoh guild page and parse through it to get everyone's GP and such
    """
    d = pq(url="https://swgoh.gg/g/33234/coalition-of-the-damned/")
    cnx = sql_connect()

    # Save a single timestamp here rather than on database insert to make it
    # easier to select a specific date for anaysis or deletion
    timestamp = datetime.now()

    gp_total = 0

    table = d("tbody")
    rows = table.find('tr')
    for row in rows:
        tds = d(row).children()
        username = tds.eq(0).find('a').attr('href').replace('/u/', '').replace('/', '')
        name = tds.eq(0).text()

        try:
            gp = int(tds.eq(1).text())
        except:
            print("Error converting {}'s gp".format(username))
            gp = None

        try:
            cs = float(tds.eq(2).text())
        except:
            print("Error converting {}'s cs".format(username))
            cs = None

        try:
            ar = int(tds.eq(3).text())
        except:
            print("Error converting {}'s ar".format(username))
            ar = None

        try:
            aa = float(tds.eq(4).text())
        except:
            print("Error converting {}'s aa".format(username))
            aa = 0

        gp_total += gp

        user_id = get_user_id(cnx, name, username)

        insert_gp_record(cnx, user_id, gp, cs, ar, aa, timestamp)
    insert_guild_gp(cnx, gp_total, timestamp)
    # Update all of the charts
    save_cache()


def update_rosters(add_delay, part=None, member=None):
    """
    Scrapes each member's unit list page on swgoh and updates the units database
    """
    swgoh_member_url = "https://swgoh.gg/u/{}/collection/"


    cnx = sql_connect()
    timestamp = datetime.now()
    if member:
        users = [member]
    else:
        users = get_users(cnx)
        if part == 1:
            users = users[:int(len(users)/2)+1]
        if part == 2:
            users = users[int(len(users)/2)-1:]
        random.shuffle(users)

    for user in users:
        user_id = user[0]
        username = user[1]
        # If an exception happens, this print'll tell us on which user it failed
        print(username, datetime.now())

        # Sleep for a random number of seconds to make it look less like a scraper bot
        # This makes the process take a while, but it only runs once a day anyway
        time.sleep(random.randint(10,25))

        # Load each user's page and parse through it
        url = swgoh_member_url.format(username)
        user_page = None
        try:
            user_page = pq(url=url)
        except HTTPError as e:
            print(e)
            break
        # Parses the HTML to get a list of all character elements that don't have the
        #    class given to chars that aren't yet unlocked
        chars = user_page('.collection-char')
        for char in chars:
            # Parse each character with pyquery
            c = pq(char)

            # Search the character element for the various bits of info it offers
            unit_name = c.find('a').eq(0).attr('href').split('/')[-2]
            char_gp_text = c.find('.collection-char-gp').attr('title').split(' ')[1]
            char_gp = int(char_gp_text.replace(',',''))
            char_gear_roman = c.find('.char-portrait-full-gear-level').text()
            char_gear = romans.get(char_gear_roman)
            char_level = c.find('.char-portrait-full-level').text()
            stars = len(c.find('.star:not(.star-inactive)'))

            # Dump the gathered character data into the database
            insert_unit_record(cnx, timestamp, user_id, unit_name, char_level, char_gear, char_gp, stars)
        print(username, datetime.now())



def split(a, n):
    """
    Splits an array into n arrays with an as-equal-as-possible distribution
    ex. an array with 42 elements split into 4 groups will
    """
    k, m = divmod(len(a), n)
    return [x for x in (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))]



def get_member_gp_chart(guild_gp, users, segment, segments=4):

    target_count = 100
    entries = len(guild_gp)
    step = int(entries / target_count)

    trimmed = guild_gp[::step]
    data = split(users, segments)[segments-segment]
    type = "line"


    datasets = []
    for user in data:
        name = user[0]
        gp = [int(x) for x in user[1].split(',')][::step]
        if len(gp) < len(trimmed):
            gp = [None] * (len(trimmed) - len(gp)) + gp
        color = user[2]
        dataset = {
            'label': name,
            'fill': False,
            'backgroundColor': color[0],
            'backupColor': color[0],
            'borderColor': color[0],
            'transColor': color[1],
            'data': gp
        }
        datasets.append(dataset)

    labels = [x[0].strftime('%m/%d/%Y %H:%M') for x in trimmed]
    options = {
        'responsive': True,
        'maintainAspectRatio': False,
        'title':{'display':True, 'text':'Member GP Totals (Group {})'.format(segment)},
        'hover': {'mode': 'nearest', 'intersect': True},
        'scales': {
            'xAxes': [{'type':'time', 'time':{'unit':'week','unitStepSize': 1,'displayFormats': {'day': 'MM/DD/YY'}}, 'display': True, 'scaleLabel': {'display': 'true','labelString': 'Date'}}],
            'yAxes': [{'display': True,'scaleLabel': {'display': True,'labelString': 'GP'}}]

        },
    }
    user_gp = {
        'name':'Member GP Totals (Group {})'.format(segment),
        'icon': 'users',
        'hash': 'users_segment_{}'.format(segment),
        'charts': [{
            'options': options,
            'type': type,
            'data': {'labels': labels,'datasets':datasets,'options':options,},
        }],
    }
    return user_gp

def get_guild_growth_all(guild_gp):
    #Take every tenth data point until the last 14, then take every datapoint
    # this keeps the chart from being too cluttered, but you'll always be able to
    # see the latest 14 datapoints
    trimmed = guild_gp[:-14:10] + guild_gp[-14:]

    type = "line"
    labels = [x[0].strftime('%m/%d/%Y %H:%M') for x in trimmed]
    datasets = [{
        'data': [x[1] for x in trimmed],
        'backgroundColor': "rgb(0, 153, 255)",
        'backupColor': "rgb(0, 153, 255)",
        'borderColor': "rgb(0, 133, 245)",
        'fill': True,
        'label': "Guild GP",

    }]
    options = {
        'responsive': True,
        'maintainAspectRatio': False,
        'title':{'display':True, 'text':'Guild GP Growth'},
        'hover': {'mode': 'nearest', 'intersect': True},
        'scales': {
            'xAxes': [{'type':'time', 'time':{'unit':'week','unitStepSize': 1,'displayFormats': {'day': 'MM/DD/YY'}}, 'display': True, 'scaleLabel': {'display': 'true','labelString': 'Date'}}],
            'yAxes': [{'display': True,'scaleLabel': {'display': True,'labelString': 'Value'}}]
        },
    }
    guild_growth = {
        'name':'Guild Growth',
        'icon': 'globe',
        'hash': 'guild_growth',
        'charts': [{
            'options': options,
            'type': type,
            'data': {'labels': labels,'datasets':datasets,'options':options,},
        }],
    }
    return guild_growth

def get_guild_growth_week(guild_gp):

    trimmed = guild_gp[-14:]

    type = "line"
    labels = [x[0].strftime('%m/%d/%Y %H:%M') for x in trimmed]
    datasets = [{
        'data': [x[1] for x in trimmed],
        'backgroundColor': "rgb(0, 153, 255)",
        'backupColor': "rgb(0, 153, 255)",
        'borderColor': "rgb(0, 133, 245)",
        'fill': True,
        'label': "Guild GP",

    }]
    options = {
        'responsive': True,
        'maintainAspectRatio': False,
        'title':{'display':True, 'text':'Guild GP Growth (Last Week)'},
        'hover': {'mode': 'nearest', 'intersect': True},
        'scales': {
            'xAxes': [{'type':'time', 'time':{'unit':'day','unitStepSize': 1,'displayFormats': {'day': 'MM/DD/YY'}}, 'display': True, 'scaleLabel': {'display': 'true','labelString': 'Date'}}],
            'yAxes': [{'display': True,'scaleLabel': {'display': True,'labelString': 'Value'}}]
        },
    }
    guild_growth = {
        'name':'Guild Growth (week)',
        'icon': 'globe',
        'hash': 'guild_growth_week',
        'charts': [{
            'options': options,
            'type': type,
            'data': {'labels': labels,'datasets':datasets,'options':options,},
        }],
    }
    return guild_growth

def get_player_deltas_all(guild_gp, users):
    trimmed = guild_gp[:-10:10]+guild_gp[-10::2]
    type = "line"

    datasets = []
    for user in users:
        name = user[0]
        gp = [int(x) for x in user[1].split(',')]
        gp = gp[:-10:10]+gp[-10::2]
        if len(gp) < len(trimmed):
            gp = [gp[0]] * (len(trimmed) - len(gp)) + gp
        color = user[2]
        dataset = {
            'label': name,
            'fill': False,
            'backgroundColor': color[0],
            'backupColor': color[0],
            'borderColor': color[0],
            'transColor': color[1],
            'data': [x-gp[0] for x in gp],
        }
        datasets.append(dataset)

    labels = [x[0].strftime('%m/%d/%Y %H:%M') for x in trimmed]
    options = {
        'responsive': True,
        'maintainAspectRatio': False,
        'title':{'display':True, 'text':'Member GP Growth (All)'},
        'hover': {'mode': 'nearest', 'intersect': True},
        'scales': {
            'xAxes': [{'type':'time', 'time':{'unit':'week','unitStepSize': 1,'displayFormats': {'day': 'MM/DD/YY'}}, 'display': True, 'scaleLabel': {'display': 'true','labelString': 'Date'}}],
            'yAxes': [{'ticks':{'min':0, 'max':200000, 'stepSize': 50000},'display': True,'scaleLabel': {'display': True,'labelString': 'GP Change'}}]
        },
    }
    user_growth = {
        'name':'Member Growth (all)',
        'icon': 'trending-up',
        'hash': 'member_gp_growth_all',
        'charts': [{
            'options': options,
            'type': type,
            'data': {'labels': labels,'datasets':datasets,'options':options,},
        }],
    }
    return user_growth

def get_player_deltas_week(guild_gp, users):
    trimmed = guild_gp[-14:]
    type = "line"

    datasets = []
    for user in users:
        name = user[0]
        gp = [int(x) for x in user[1].split(',')][-14:]
        if len(gp) < len(trimmed):
            gp = [gp[0]] * (len(trimmed) - len(gp)) + gp
        color = user[2]
        dataset = {
            'label': name,
            'fill': False,
            'backgroundColor': color[0],
            'backupColor': color[0],
            'borderColor': color[0],
            'transColor': color[1],
            'data': [x-gp[0] for x in gp]
        }
        datasets.append(dataset)

    labels = [x[0].strftime('%m/%d/%Y %H:%M') for x in trimmed]
    options = {
        'responsive': True,
        'maintainAspectRatio': False,
        'title':{'display':True, 'text':'Member GP Growth (Last Week)'},
        'hover': {'mode': 'nearest', 'intersect': True},
        'scales': {
            'xAxes': [{'type':'time', 'time':{'unit':'day','unitStepSize': 1,'displayFormats': {'day': 'MM/DD/YY'}}, 'display': True, 'scaleLabel': {'display': 'true','labelString': 'Date'}}],
            'yAxes': [{'display': True,'scaleLabel': {'display': True,'labelString': 'Value'}}]
        },
    }
    user_growth = {
        'name':'Member Growth (week)',
        'icon': 'trending-up',
        'hash': 'member_gp_growth_week',
        'charts': [{
            'options': options,
            'type': type,
            'data': {'labels': labels,'datasets':datasets,'options':options,},
        }],
    }
    return user_growth

def get_guild_data():
    cnx = sql_connect()
    guild_gp = get_guild_gp(cnx)
    users = get_users_gp(cnx)

    result = {
        'charts': [
            get_guild_growth_all(guild_gp),
            get_guild_growth_week(guild_gp),
            get_player_deltas_all(guild_gp, users),
            get_player_deltas_week(guild_gp, users),
            get_member_gp_chart(guild_gp, users, 1),
            get_member_gp_chart(guild_gp, users, 2),
            get_member_gp_chart(guild_gp, users, 3),
            get_member_gp_chart(guild_gp, users, 4),
            ],
        'unit_counts':
            [
                {'group_name':'CLS', 'hash':'uon_cls', 'icon':'anchor', 'units':{
                    'Commander Luke Skywalker':get_unit_counts('commander-luke-skywalker', cnx),
                    'R2D2':get_unit_counts('r2-d2', cnx),
                    'Princess Leia':get_unit_counts('princess-leia', cnx),
                    'Old Ben':get_unit_counts('obi-wan-kenobi-old-ben', cnx),
                    'Farmboy Luke':get_unit_counts('luke-skywalker-farmboy', cnx),
                    'Stormtrooper Han':get_unit_counts('stormtrooper-han', cnx),
                }},
                {'group_name':'JTR', 'hash':'uon_jtr', 'icon':'award', 'units':{
                    'Jedi Training Rey':get_unit_counts('rey-jedi-training', cnx),
                    'BB-8':get_unit_counts('bb-8', cnx),
                    'Veteran Chewie':get_unit_counts('veteran-smuggler-chewbacca', cnx),
                    'Veteran Han':get_unit_counts('veteran-smuggler-han-solo', cnx),
                    'Scavenger Rey':get_unit_counts('rey-scavenger', cnx),
                    'Finn':get_unit_counts('finn', cnx)
                }},
                {'group_name':'Raids and TB Rewards', 'icon':'gift', 'hash':'uon_rtb', 'units':{
                    'Rebel Officer Leia Organa':get_unit_counts('rebel-officer-leia-organa', cnx),
                    'General Kenobi':get_unit_counts('general-kenobi', cnx),
                    'Captain Han Solo':get_unit_counts('captain-han-solo', cnx),
                    'IPD':get_unit_counts('imperial-probe-droid', cnx),
                    'Hermit Yoda':get_unit_counts('hermit-yoda', cnx),
                    'Wampa':get_unit_counts('wampa', cnx),
                    'Darth Traya':get_unit_counts('darth-traya',cnx),
                }},
                {'group_name':'Hard Nodes', 'hash':'uon_hard', 'icon':'minimize', 'units':{
                    'Sabine Wren':get_unit_counts('sabine-wren', cnx),
                    'Holdo':get_unit_counts('amilyn-holdo', cnx),
                    'Rose':get_unit_counts('rose-tico', cnx),
                    'Baze':get_unit_counts('baze-malbus', cnx),
                    'Shoretrooper':get_unit_counts('shoretrooper', cnx),
                    'Nightsister Zombie':get_unit_counts('nightsister-zombie', cnx),
                    'Mother Talzin':get_unit_counts('mother-talzin', cnx),
                }},
                {'group_name':'Hard Nodes II', 'hash':'uon_hard2', 'icon':'minimize', 'units':{
                    'Darth Nihilus':get_unit_counts('darth-nihilus', cnx),
                    'FO Stormtrooper':get_unit_counts('first-order-stormtrooper', cnx),
                    'Lobot':get_unit_counts('lobot', cnx),
                    'Visas Marr':get_unit_counts('visas-marr', cnx),
                    'Sion':get_unit_counts('darth-sion', cnx),
                }},
                {'group_name':'Hard Nodes III', 'hash':'uon_hard3', 'icon':'minimize', 'units':{
                    'Bossk':get_unit_counts('bossk', cnx),
                    'Wicket':get_unit_counts('wicket', cnx),
                    'Vandor Chewie':get_unit_counts('vandor-chewbacca', cnx),
                    'Young Han':get_unit_counts('young-han-solo', cnx),
                }},
                {'group_name':'Marquee', 'hash':'uon_marq', 'icon':'dollar-sign', 'units':{
                    'Enfys':get_unit_counts('enfys-nest', cnx),
                    'Jolee':get_unit_counts('jolee-bindo', cnx),
                    'L337':get_unit_counts('l3-37', cnx),
                    'Qi\'ra':get_unit_counts('qira', cnx),
                    'Range Trooper':get_unit_counts('range-trooper', cnx),
                    'Young Lando':get_unit_counts('young-lando-calrissian', cnx),
                    'T3-M4':get_unit_counts('t3-m4', cnx),
                    'Mission':get_unit_counts('mission-vao', cnx),
                    'Zaalbar':get_unit_counts('zaalbar', cnx),
                }},
            ]
    }

    return json.dumps(result)


def save_cache():
    analyze = get_guild_data()
    with open('/home/amoliski/swgoh/static/cache.json', 'w') as f:
        f.write(analyze)



colors = {'black':'\u001b[30m','red':'\u001b[31m','green':'\u001b[32m','yellow':'\u001b[33m','blue':'\u001b[34m','magenta':'\u001b[35m','cyan':'\u001b[36m','white':'\u001b[37m','reset':'\u001b[0m'}

def color_text(s, color):
    code=colors.get(color, colors.get('white'))
    rst = colors.get('reset')
    return(code+str(s)+rst)


def get_roster(user_id, cnx = None, gp=False):
    if not cnx:
        cnx = sql_connect()
    cur = cnx.cursor()
    if gp:
        cur.execute("select unit_name, max(stars), max(level), max(gear_level), max(gp) from unit where user_id = %s group by unit_name", (user_id, ))
        return {field[0]:[field[1],field[2],field[3],field[4]] for field in cur.fetchall()}

    else:
        cur.execute("select unit_name, max(stars), max(level), max(gear_level) from unit where user_id = %s group by unit_name", (user_id, ))
        return {field[0]:[field[1],field[2],field[3]] for field in cur.fetchall()}

def print_line(unit, data, minlevel=80):

    star = data[0]
    star = color_text(star, 'green' if star == 7 else 'yellow' if star == 6 else 'red')

    level = data[1]
    level = color_text(str(level).rjust(2), 'green' if level >= minlevel else 'yellow' if (level >= minlevel-10) else 'red')

    gear = data[2]
    gear = color_text(str(gear).rjust(2), 'green' if gear >= 8 else 'yellow' if gear > 7 else 'red')

    print(unit.replace('-', ' ').ljust(30),"{},{},{}".format(star, level, gear))

def print_roster(roster):
    for unit,data in roster.items():
        print_line(unit, data)

def check_readiness(unit, roster, minlevel):
    data = roster.get(unit, [0,0,0])
    return (data[1] >= minlevel and data[2] >= 8)

def check_stars(unit, roster):
    data = roster.get(unit, [0,0,0])
    return data[0] >= 7

def sort_key(a):
    """
    Function used in the player unit sorting that prioritizes stars, then levels, then gear
    """
    return 1000000*(10-a[1][0]) + 1000*(100-a[1][1]) + 15-(a[1][2])


def event_readiness(roster, event):
    event_units = event['units']
    event_level = event['min_level']
    reward = event['reward']
    player_units = []
    print(color_text(event['name'], 'cyan'))

    reward = roster.get(event['reward'], [0,0,0])


    for unit in event_units:
        data = roster.get(unit, [0,0,0])
        player_units.append([unit, data])

    player_units.sort(key=sort_key)

    done = reward[0] == 7

    stars = [check_stars(n, roster) for n in event_units].count(True) >= 5
    gear_and_levels = [check_readiness(n, roster, event_level) for n in event_units].count(True) >= 4

    ready = stars and gear_and_levels

    color = 'green' if done else 'yellow' if ready else 'red'
    readiness = 'Event Completed!' if done else 'Ready!' if ready else 'Not Ready'

    print(color_text(readiness,color))
    if not done:
        for player_unit in player_units:
            print_line(player_unit[0], player_unit[1])

    print('')


def get_unit_counts(unit_name, cnx):
    tally = [[],[],[],[],[],[],[],[],[]]
    tally_week = [[],[],[],[],[],[],[],[],[]]
    tally_month = [[],[],[],[],[],[],[],[],[]]
    cursor = cnx.cursor()
    "select name, r.stars from member left join (select user_id,  max(stars) as stars from unit where unit_name = %s group by user_id) as r on r.user_id = id order by stars;"
    query = """
        select name, r.stars, s.stars, t.stars, r.gear, s.gear, t.gear from member
        left join (select user_id,  max(stars) as stars, max(gear_level) as gear from unit where unit_name = %s group by user_id) as r on r.user_id = id
        left join (select user_id,  max(stars) as stars, max(gear_level) as gear from unit where unit_name = %s and time < now() - INTERVAL 7 DAY group by user_id) as s on s.user_id = id
        left join (select user_id,  max(stars) as stars, max(gear_level) as gear from unit where unit_name = %s and time < now() - INTERVAL 30 DAY group by user_id) as t on t.user_id = id
        where member.active = true
        order by r.stars desc, s.stars desc, t.stars desc, r.gear desc, s.gear desc, t.gear desc;"""
    cursor.execute(query, (unit_name,unit_name,unit_name,))
    results = cursor.fetchall()

    for result in results:
        stars = int(result[1]) if result[1] else 0
        if result[4] == 12:
            tally[0].append(result[0])
        else:
            tally[8-stars].append(result[0])

        stars = int(result[2]) if result[2] else 0
        if result[5] == 12:
            tally_week[0].append(result[0])
        else:
            tally_week[8-stars].append(result[0])

        stars = int(result[3]) if result[3] else 0
        if result[6] == 12:
            tally_month[0].append(result[0])
        else:
            tally_month[8-stars].append(result[0])

    return [tally, tally_week, tally_month]

def cache_roster():
    result = []
    users = userlist()
    for user in users:
        result.append([user, get_roster(user[0], gp=True)])

    with open('/home/amoliski/swgoh/static/rosters.json', 'w') as f:
        f.write(json.dumps(result))


    #save_cache()