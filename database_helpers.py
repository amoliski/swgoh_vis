
import mysql.connector as msql
import random
from pyquery import PyQuery as pq

"""
Notes:

Get most recent activity for each active member:
select *, max(time) as mt
from unit
join member
    on member.id = unit.user_id
where member.active = 1
group by user_id
order by mt desc, user_id desc;

"""

def sql_connect():
    connection_props = json.load(open('../db_connection', 'r'));
    return msql.connect(
        user=connection_props['user']
        password=connection_props['password']
        database=connection_props['database']
        host=connection_props['host']
    )

romans = {
    'I':1,
    'II':2,
    'III':3,
    'IV':4,
    'V':5,
    'VI':6,
    'VII':7,
    'VIII':8,
    'IX':9,
    'X':10,
    'XI':11,
    'XII':12,
    'XIII':13,
    'XIV':14,
    'XV':15,
    'XVI':16,
    'XVII':17,
    'XVIII':18,
    'XIX':19,
    'XX':20,
}

def insert_unit_record(cnx, time,user_id, unit_name, level, gear_level, gp, stars):
    """
    Adds the specified unit to the database for a user
      It will check previous entries and skip it if it's a duplicate record
      'since only a handful of units change every day, this will save roughly a
      bazillionmilliontrillion redundant database entries
    """
    cursor = cnx.cursor()
    query = """
    insert into unit(time, user_id, unit_name, level, gear_level, gp, stars)
    select %s, %s, %s, %s, %s, %s, %s
    from unit
    where (user_id = %s and unit_name = %s and gp = %s) having count(*) = 0;""";
    cursor.execute(query, (time, user_id, unit_name, level, gear_level, gp, stars, user_id, unit_name, gp))
    cnx.commit()

def get_users(cnx):
    """
    Returns a list of all guild members and a randomly generated color so that
    every instance of that user's data throughout the databse will
    """
    cursor = cnx.cursor();
    cursor.execute("select id, username from member where active = true order by id asc")
    users = cursor.fetchall()
    return [user + (getRandomRgb(),) for user in users]


def insert_gp_record(cnx, user_id, gp, cs, ar, aa, timestamp):
    cursor = cnx.cursor()
    query = "insert into gp(user, gp, time, cs, arena_rank, arena_average) values (%s, %s, %s, %s, %s, %s)";
    cursor.execute(query, (user_id, gp, timestamp, cs, ar, aa))
    cnx.commit()

def insert_guild_gp(cnx, gp, timestamp):
    cursor = cnx.cursor()
    query = "insert into guild_gp(gp, capture_time) values (%s, %s)";
    cursor.execute(query, (gp, timestamp))
    cnx.commit()

def get_user_id(cnx, name, username):
    """
    Pulls the id of a user out of the database- if the user doesn't exist, we
    create it
    """
    cursor = cnx.cursor()
    query = 'select id from member where username = %s;'
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    if result:
        id,*_ = result
        return id

    query = 'insert into member(name, username) values (%s, %s);'
    cursor.execute(query, (name,username,))

    query = 'select LAST_INSERT_ID();'
    cursor.execute(query)
    result = cursor.fetchone()
    print(result)
    id,*_ = result
    cnx.commit()
    return id

# Stealing fun colors from google
rgbs = ["#F44336","#EF9A9A","#E57373","#EF5350","#F44336",
        "#E53935","#D32F2F","#C62828","#B71C1C","#FF8A80","#FF5252","#FF1744",
        "#D50000","#E91E63","#F8BBD0","#F48FB1","#F06292","#EC407A",
        "#E91E63","#D81B60","#C2185B","#AD1457","#880E4F","#FF80AB","#FF4081",
        "#F50057","#C51162","#9C27B0","#E1BEE7","#CE93D8","#BA68C8",
        "#AB47BC","#9C27B0","#8E24AA","#7B1FA2","#6A1B9A","#4A148C","#EA80FC",
        "#E040FB","#D500F9","#AA00FF","#673AB7","#D1C4E9","#B39DDB",
        "#9575CD","#7E57C2","#673AB7","#5E35B1","#512DA8","#4527A0","#311B92",
        "#B388FF","#7C4DFF","#651FFF","#6200EA","#3F51B5","#C5CAE9",
        "#9FA8DA","#7986CB","#5C6BC0","#3F51B5","#3949AB","#303F9F","#283593",
        "#1A237E","#8C9EFF","#536DFE","#3D5AFE","#304FFE","#2196F3",
        "#BBDEFB","#90CAF9","#64B5F6","#42A5F5","#2196F3","#1E88E5","#1976D2",
        "#1565C0","#0D47A1","#82B1FF","#448AFF","#2979FF","#2962FF","#03A9F4",
        "#B3E5FC","#81D4FA","#4FC3F7","#29B6F6","#03A9F4","#039BE5",
        "#0288D1","#0277BD","#01579B","#80D8FF","#40C4FF","#00B0FF","#0091EA",
        "#00BCD4","#B2EBF2","#80DEEA","#4DD0E1","#26C6DA","#00BCD4",
        "#00ACC1","#0097A7","#00838F","#006064","#84FFFF","#18FFFF","#00E5FF",
        "#00B8D4","#009688","#B2DFDB","#80CBC4","#4DB6AC","#26A69A",
        "#009688","#00897B","#00796B","#00695C","#004D40","#A7FFEB","#64FFDA",
        "#1DE9B6","#00BFA5","#4CAF50","#C8E6C9","#A5D6A7","#81C784",
        "#66BB6A","#4CAF50","#43A047","#388E3C","#2E7D32","#1B5E20","#B9F6CA",
        "#69F0AE","#00E676","#00C853","#8BC34A","#C5E1A5",
        "#AED581","#9CCC65","#8BC34A","#7CB342","#689F38","#558B2F","#33691E",
        "#CCFF90","#B2FF59","#76FF03","#64DD17","#CDDC39",
        "#E6EE9C","#DCE775","#D4E157","#CDDC39","#C0CA33","#AFB42B","#9E9D24",
        "#827717","#F4FF81","#CE851C","#C6FF00","#AEEA00","#FFEB3B",
        "#FFF59D","#FFF176","#FFEE58","#FFEB3B","#FDD835","#FBC02D",
        "#F9A825","#F57F17","#FFFF8D","#d6d66e","#FFEA00","#FFD600","#FFC107",
        "#FFE082","#FFD54F","#FFCA28","#FFC107","#FFB300",
        "#FFA000","#FF8F00","#FF6F00","#FFE57F","#FFD740","#FFC400","#FFAB00",
        "#FF9800","#FFCC80","#FFB74D","#FFA726","#FF9800",
        "#FB8C00","#F57C00","#EF6C00","#E65100","#FFD180","#FFAB40","#FF9100",
        "#FF6D00","#FF5722","#FFCCBC","#FFAB91","#FF8A65","#FF7043",
        "#FF5722","#F4511E","#E64A19","#D84315","#BF360C","#FF9E80","#FF6E40",
        "#FF3D00","#DD2C00","#795548","#BCAAA4","#A1887F",
        "#8D6E63","#795548","#6D4C41","#5D4037","#4E342E","#3E2723","#9E9E9E",
        "#9E9E9E","#757575",
        "#616161","#424242","#212121","#607D8B","#B0BEC5",
        "#90A4AE","#78909C","#607D8B","#546E7A","#455A64","#37474F","#263238"]

def getRandomRgb():
    #def color():
    #    return random.randint(0, 255)

    #c1 = color()
    #c2 = color()
    #c3 = color()
    color = random.choice(rgbs)[1:]
    r,g,b = tuple(int(color[i:i+2], 16) for i in (0, 2 ,4))

    return ['rgb({},{},{})'.format(r, g, b),'rgba({},{},{},.1)'.format(r, g, b)]


def get_users_gp(cnx):
    cursor = cnx.cursor()
    cursor.execute("""
    SET SESSION group_concat_max_len = 1000000;
    """)
    cursor.execute("""
    select member.name, GROUP_CONCAT(gp.gp order by gp.gp asc), max(gp) as max
    from member join gp on member.id=gp.user
    where member.active = true
    group by member.id
    order by max asc;
    """)
    users = cursor.fetchall()
    userlist = [user[:-1] + (getRandomRgb(),) for user in users]
    return userlist


def get_guild_gp(cnx):
    cursor = cnx.cursor()
    cursor.execute("""
    select capture_time, gp from guild_gp order by capture_time asc;
    """)
    return cursor.fetchall()

def find_deleted_bois():
    """
    Load up the swgoh guild page and parse through it to get everyone's GP and such
    """
    cnx = sql_connect()
    d = pq(url="https://swgoh.gg/g/33234/coalition-of-the-damned/")
    table = d("tbody")
    rows = table.find('tr')
    users = []
    for row in rows:
        tds = d(row).children()
        username = tds.eq(0).find('a').attr('href').replace('/u/', '').replace('/', '')
        users.append(username)
    db_users = get_users(cnx)
    return [x for x in db_users if x[1] not in users]

def delete_user(id):
    """
    Warning!
    This will purge all data for the selected user from the database.
    Back up first!!
    """
    cnx = sql_connect()
    cursor = cnx.cursor()
    cursor.execute("delete from gp where user = %s;", (id,))
    cursor.execute("delete from member where id = %s;", (id,))
    cursor.execute("delete from unit where user_id = %s;", (id,))
    cnx.commit()

def deactivate_missing_bois():
    cnx = sql_connect()
    cursor = cnx.cursor()
    deleted = find_deleted_bois()
    print("Deactivating {}".format(", ".join([x[1] for x in deleted])))
    for boi in deleted:
        cursor.execute("update member set active = 0 where id = %s", (boi[0],))


def gapfill():
    """
    Goes through and finds missing entries (caused by new members) by setting
    the earlies timestamp to the inital GP and then sets the remaining missing
    slots to that lower value. Not recommended anymore after the changes to the
    charts to handle missing values
    """
    cnx = sql_connect()
    cursor = cnx.cursor()

    datepoints = []
    users = []

    cursor.execute("Select capture_time from guild_gp;")
    for datepoint in cursor.fetchall():
        datepoints.append(datepoint[0].strftime("%Y-%m-%d %H:%M:%S"))

    cursor.execute("Select id, name from member;")
    for user in cursor.fetchall():
        users.append(user)

    line = "          "
    for user in users:
        line+= user[1][:3].ljust(4)
    print(line)

    line = "          "
    for user in users:
        line+= str(user[0]).ljust(4)
    print(line)

    running_datepoint = None

    for i,datepoint in enumerate(datepoints):
        query = 'select user from gp where time=%s;'
        cursor.execute(query, (datepoint,))
        datepoint_users = [x[0] for x in cursor.fetchall()]
        print(datepoint_users)
        line = "datepoint:"
        for user in users:
            user_id = user[0]
            if user[0] in datepoint_users:
                line += "X   "
            elif running_datepoint is None:
                line += "*    "
                gp = None
                cs = None
                ar = None
                aa = None
                insert_gp_record(cnx, user_id, gp, cs, ar, aa, datepoint)

            else:
                query = "select user, gp, time, cs, arena_rank, arena_average from gp where user=%s and time=%s;"
                cursor.execute(query, (user_id, running_datepoint,))
                res = cursor.fetchone();

                gp = res[1]
                cs = res[3]
                ar = res[4]
                aa = res[5]

                insert_gp_record(cnx, user_id, gp, cs, ar, aa, datepoint)

        print(line)
        running_datepoint = datepoint

def patch_guild_gp():
    """
    Recalculates the GP table
    """
    cnx = sql_connect()
    cursor = cnx.cursor()
    query = "update gp as base join (select user, min(gp) as mgp from gp group by user) as gen on base.user=gen.user set base.gp = gen.mgp where gp is NULL;"
    cursor.execute(query)

def patch_user_min():
    cnx = sql_connect()
    cursor = cnx.cursor()
    query = "update gp join(select user, min(gp) as mgp from gp group by user) as abs on abs.user = gp.user set gp.gp = abs.mgp where gp.gp is null;"
    cursor.execute(query)
    return cursor.fetchall()
