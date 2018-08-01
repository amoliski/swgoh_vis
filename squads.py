from database_helpers import (
  sql_connect,
  get_users,
  romans
)

from pyquery import PyQuery as pq


def get_squads(user):
    urls = get_squad_urls(user)
    for url in urls:
        page = pq(url)
        units = page('.collection-char').items()
        for unit in units:
            unit_name = unit.find('a.char-portrait-full-link').attr('href').split('/')[-2]
            unit_level = unit.find('.char-portrait-full-level').text()
            unit_gear = romans.get(unit.find('.char-portrait-full-gear-level').text())
            print(unit_name, unit_level, unit_gear)

    return page

def get_squad_urls(user):
    page = pq(url="https://swgoh.gg/u/{}/squads/".format(user))
    return ['https://swgoh.gg{}'.format(x.attr('href')) for x in page('a[href*="squads/"].panel-profile.panel-a').items()]