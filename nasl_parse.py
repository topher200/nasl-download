import bs4
import re
import requests

NASL_URL_ROOT = "http://www.nasl.tv"
JUSTINTV_API_URL_TEMPLATE = "http://api.justin.tv/api/clip/show/%s.xml"

# Returns true if the passed url is of a video from that week
def from_week(url, week_number):
  return re.search('/videos/w%d' % week_number, url)

class Vod:
  def __init__(self, url):
    self.url = url
    self.week, self.division, self.match, self.game = \
        re.search('videos/w(\d)/d(\d)/m(\d)g(\d).html', url).groups()

def get_match_urls():
  matches_page = requests.get(''.join([NASL_URL_ROOT, '/p/s4videos']))
  soup = bs4.BeautifulSoup(matches_page.content)
  links = [link['href'] for link in soup.find_all('a')]
  vods = [link for link in links if re.search('videos/w', link)]
  return [''.join([NASL_URL_ROOT, vod_url]) for vod_url in vods]

def get_justintv_archive_id(vod_url):
  page = requests.get(vod_url)
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

def download_file(flv_url):
  binary_file = requests.get(flv_url)
  import random
  with open('/media/topher/Dropbox/%s.flv' % random.randint(0, 10000), 'wb') as \
        output_file:
    output_file.write(binary_file.content)

week_3_vods = [link for link in get_match_urls() if from_week(link, 3)]
vod_numbers = [5,6,7,8,9,10,11,12]
for vod_number in vod_numbers:
  try:
    download_file(get_flv_url(get_justintv_archive_id(week_3_vods[4])))
    print('download completed %d of %d', vod_number, vod_numbers)
  except:
    continue
