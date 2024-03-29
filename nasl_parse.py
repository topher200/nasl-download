# Importing as fix for requests bug, see:
# https://github.com/kennethreitz/requests/issues/858
import chardet

import bs4
import json
import os
import re
import requests

NASL_URL_ROOT = "http://www.nasl.tv"
JUSTINTV_API_URL_TEMPLATE = "http://api.justin.tv/api/clip/show/%s.xml"

class Vod:
  def __init__(self, matchup_string, url):
    self.matchup_string = matchup_string
    self.nasl_url = url
    self.week, self.division, self.match, self.game = \
        map(int, re.search('videos/w(\d)/d(\d)/m(\d)g(\d).html', url).groups())
    self.flv_url = None

  def underscored_matchup_string(self):
    return re.sub(' ', '_', self.matchup_string)

def get_all_vods():
  matches_page = requests.get(''.join([NASL_URL_ROOT, '/p/s4videos']))
  soup = bs4.BeautifulSoup(matches_page.content)
  possible_match_rows = soup.tbody.find_all('tr')
  match_rows = []
  for row in possible_match_rows:
    if (row.td.string == None):
      continue
    if re.search(' vs ', row.td.string):
      match_rows.append(row)
  vods = []
  for row in match_rows:
    matchup_string = row.td.string
    # we only want 3 games
    num_games = 0
    for link in row.find_all('a'):
      if (num_games >= 3):
        break
      url = str(link['href'])
      if (re.search('videos/w(\d)/d(\d)/m(\d)g(\d).html', url) == None):
        continue
      vods.append(Vod(matchup_string, url))
      num_games += 1
    if (num_games == 0):
      print("couldn't find any vod links for %s" % matchup_string)
  return vods

def get_justintv_archive_id(nasl_url):
  page = requests.get(nasl_url)
  soup = bs4.BeautifulSoup(page.content)
  flashvar_param = [param for param in soup.find_all('param')
                    if param['name'] == 'flashvars'][0]
  flashvar_string = str(flashvar_param['value'])
  twitch_id = int(re.search('archive_id=(\d+)&', flashvar_string).group(1))
  return(twitch_id)

def get_flv_url(archive_id):
  page = requests.get(JUSTINTV_API_URL_TEMPLATE % archive_id)
  soup = bs4.BeautifulSoup(page.content)
  video_file_url = soup.find('video_file_url').text
  return video_file_url

def set_flv_url(vods):
  for vod in vods:
    try:
      vod.flv_url = get_flv_url(get_justintv_archive_id(vod.nasl_url))
    except:
      # some Vods don't have flvs
      print('could not find flv file. skipping')
      pass

def download_vod(vod):
  dirname = \
      "/media/data/Dropbox/NASL Season 4/week_%d/NASL4W%dD%dM%d_%s/game %d" % \
      (vod.week, vod.week, vod.division, vod.match,
       vod.underscored_matchup_string(), vod.game)
  if os.path.exists(dirname):
    print('%s directory already exists. skipping' % dirname)
    return
  # make the folder even if there is no game
  os.makedirs(dirname)
  if (vod.flv_url == None):
    return
  binary_file = requests.get(vod.flv_url)
  filename = "NASL4W%dD%dM%d %s Game %d.flv" % \
      (vod.week, vod.division, vod.match, vod.underscored_matchup_string(),
       vod.game)
  with open(os.path.join(dirname, filename), 'wb') as output_file:
    output_file.write(binary_file.content)

def main():
  vods = get_all_vods()
  matches_with_no_vods = []
  for vod in vods:
    if (vod.week == 9):
      set_flv_url([vod])
      if (vod.game == 1) and (vod.flv_url == None):
        print('no link to game 1 of %s' % vod.matchup_string)
        matches_with_no_vods.append(vod.matchup_string)
      print('starting %s game %s' % (vod.matchup_string, vod.game))
      if (vod.matchup_string in matches_with_no_vods):
        print('skipping game due to no vods')
        continue
      download_vod(vod)
      print('completed %s game %s' % (vod.matchup_string, vod.game))

main()
