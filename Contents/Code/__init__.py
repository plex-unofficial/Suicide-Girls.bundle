from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

import mimetypes
import os.path
from urlparse import urlparse, urljoin
import re

CHIMERA = True
PLUGIN_PREFIX = '/photos/suicidegirls'
BASE = 'http://suicidegirls.com'
USER_INFO = 'http://suicidegirls.com/xml/user/getInfo/'

VIDEO_SECTIONS = [
  ['Recent', '/videos/girls/sort=added/', 1],
  ['Members', '/videos/members/', 1]
]

GIRL_SORTS = [
  ['Name', 'alpha'],
  ['First Set', 'first_set'],
  ['Latest Set', 'last_set'],
  ['Last Updated', 'last_updated'],
  ['Most Sets', 'set_count'],
  #['With Videos', 'has_video'],
  #['Set Winner', 'set_winner']
  #['Random', 'random']
]

PIC_SORTS = [
  ['Recent', 'added'],
  ['Comments 24 hours', '24hr'],
  ['Comments 7 days', '7day'],
  ['Comments 30 days', '30day'],
  ['Comments 3 months', '3month'],
  ['Comments 6 months', '6month'],
  ['Comments 1 year', '1yr'],
  ['Comments all time', 'total'],
  ['Loved 7 days', 'loved&filter=7day'],
  ['Loved 30 days', 'loved&filter=30day'],
  ['Loved 3 months', 'loved&filter=3month'],
  ['Loved 6 months', 'loved&filter=6month'],
  ['Loved 1 year', 'loved&filter=1yr'],
  ['Loved 2 years', 'loved&filter=2yr'],
  ['Loved all time', 'loved&filter=all'],
]

UNFILTERED_PIC_SORTS = [
  ['Recent', 'added'],
  ['Comments 24 hours', '24hr'],
  ['Comments 7 days', '7day'],
  ['Comments 30 days', '30day'],
  ['Comments 3 months', '3month'],
  ['Comments 6 months', '6month'],
  ['Comments 1 year', '1yr'],
  ['Comments all time', 'total'],
  ['Loved all time', 'loved']
]

PLUGIN_SUMMARY = '''SuicideGirls is a community that celebrates ALTERNATIVE BEAUTY and alternative culture from all over the world.

Since 2001, tens of thousands of models have submitted MILLIONS OF PHOTOS to this website hoping to become SuicideGirls.
BECOME A MEMBER of our community and you can join the discussion, meet new people and help us select the SuicideGirls for 2010.'''

CACHE_TIME = 0
CACHE_1YEAR = 365 * CACHE_1DAY
####################################################################################################

def xmlSections(sender):
  sections = [['Sets of the Day', 'girls', ''], ['Staff Picks', 'girls', 'staff'], ['Sets in Review', 'hopefuls', ''], ['Remixes', 'remix', ''], ['Multi-Girl Sets', 'girls', 'multi'],  ["SG Sets in Review", 'hopefuls', 'girls'], ["Hopefuls' Sets", 'hopefuls', 'hopefuls']]
  #['Misc', 'misc', ''], ['Candid Sets', 'girls', 'candid'], ['Celebrity Sets', 'girls','celeb'],
  dir = MediaContainer(viewGroup='_List', title2='Pics')
  for title, section, filter in sections:
    dir.Append(Function(DirectoryItem(xmlSorts, title=title), section=section, filter=filter))
  return dir
  
def xmlSorts(sender, section, filter):
  dir = MediaContainer(viewGroup='_List', title2='Sort By')
  if filter != '':
    sorts = UNFILTERED_PIC_SORTS
  else:
    sorts = PIC_SORTS
  for title, sort in sorts:
    dir.Append(Function(DirectoryItem(xmlAlbums, title=title), section=section, sort=sort, filter=filter))
  return dir
  
def xmlAlbums(sender, sort, model='', filter='', section='girls', page=1):
  dir = MediaContainer(viewGroup='Plugin', replaceParent=(page!=1), title2='Albums')
  url = BASE + '/albums/xml/%s/sort=%s&page=%i&filter=%s&model=%s/' % (section, sort, page, filter, model)
  xml = str(unicode(HTTP.Request(url), errors='ignore'))
  items = XML.ElementFromString(xml).xpath('/sets/item')
  for item in items:
    itemURL = item.xpath('./imageBase')[0].text.replace(' ', '%20')
    summary = item.xpath('./description')[0].text
    albumID = itemURL.split('/')[-2]
    modelName = item.xpath('./modelName')[0].text
    albumName = item.xpath('./name')[0].text
    if re.match(r'.*/\d+/$', itemURL):
      title = item.xpath('./name')[0].text
      thumb = item.xpath('./thumb')[0].text
      dir.Append(Function(DirectoryItem(jsAlbum, title=title, summary=summary, thumb=thumb), albumID=albumID))
    else:
      title = '%s: %s' % (modelName, albumName)
      thumb = itemURL + 'setpreview_large.jpg'
      #imageCount = int(item.xpath('./imageCount')[0].text)
      itemURL = BASE + '/xml/girls/%s/galleries/%s/' % (modelName, String.Quote(albumName))
      dir.Append(Function(DirectoryItem(xmlAlbum, title=title, summary=summary, thumb=thumb), url=itemURL))
  if len(items) == 24:
    dir.Append(Function(DirectoryItem(xmlAlbums, title='Next', thumb=R('next.png')), section=section, sort=sort, model=model, filter=filter, page=page+1))
  return dir
  
def xmlAlbum(sender, url):
  dir = MediaContainer(viewGroup='Plugin', title2=sender.itemTitle)
  for item in XML.ElementFromURL(url).xpath('/gallery/photo'):
    thumb = BASE + item.get('src').replace(' ', '%20')
    dir.Append(Function(PhotoItem(getThumb, title='', thumb=Function(getThumb, thumb=thumb)), thumb=thumb))
  return dir

def jsAlbum(sender, albumID):
  dir = MediaContainer(viewGroup='Plugin', title2=sender.itemTitle)
  js = XML.ElementFromURL(BASE + '/xml/albums/jsimagelist/site/%s/' % albumID).xpath('/albums/jsimagelist/js')[0].text
  for line in js.split('\n'):
    line = line.strip()
    if line.startswith('list['):
      thumb = line.split('ImageHolder("')[1].split('"')[0]
      dir.Append(Function(PhotoItem(getThumb, title='', thumb=Function(getThumb, thumb=thumb)), thumb=thumb))
  return dir
####################################################################################################
def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, L('Suicide Girls'), 'icon-default.png', 'art-default.png')
  Plugin.AddPrefixHandler('/video/suicidegirls', VideoMenu, L('Suicide Girls'), 'icon-default.png', 'art-default.png')
  
  Plugin.AddViewGroup('_List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('_InfoList', viewMode='InfoList', mediaType='items')
  if CHIMERA:
    Plugin.__viewGroups['Plugin'] = {"ViewMode": '131131', "MediaType": 'items'}
  else:
    Plugin.AddViewGroup('Plugin', viewMode='Pictures', mediaType='items')
  
  MediaContainer.title1 = L('Suicide Girls')
  MediaContainer.viewGroup = '_List'
  MediaContainer.art = R('art-default.png')
  DirectoryItem.thumb = R('icon-default.png')
  HTTP.SetCacheTime(CACHE_TIME)

def CreatePrefs():
  Prefs.Add(id='username', type='text', default='', label='Username')  
  Prefs.Add(id='password', type='text', default='', label='Password', option='hidden')
####################################################################################################

def MainMenu():
  dir = MediaContainer(viewGroup='_List')
  currentlyLoggedIn = Login()
  if not currentlyLoggedIn:
    dir.Append(Function(DirectoryItem(FreePicsMenu, title='Free Pics')))
    dir.viewGroup = '_InfoList'
    dir.noCache = True
    dir.Append(PrefsItem(title='Log In', thumb=R('icon-default.png'), summary=PLUGIN_SUMMARY))
    dir.Append(Function(DirectoryItem(Join, title='Join', settings=True)))
  else:
    dir.Append(Function(DirectoryItem(GirlSortMenu, title='Girls', thumb=R('icon-default.png'))))
    dir.Append(Function(DirectoryItem(xmlSections, title='Pics', thumb=R('icon-default.png'))))
  return dir
####################################################################################################

def Join(sender):
  #import objc
  from AppKit import NSWorkspace
  from Foundation import NSURL
  NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_('http://suicidegirls.com/join/'))

####################################################################################################
def GirlSortMenu(sender):
  dir = MediaContainer(viewGroup='_List', title2='Sort by')
  for title, sort in GIRL_SORTS:
    dir.Append(Function(DirectoryItem(getGirlsXML, title=title), sort=sort))
  return dir

def AlbumSortMenu(sender, model):
  dir = MediaContainer(viewGroup='_List', title2='Sort By')
  if model.endswith('s'):
    pos = "'"
  else:
    pos = "'s"
  sorts = [["%s%s Choice" % (model, pos), 'sequence']] + PIC_SORTS
  for title, sort in sorts:
    dir.Append(Function(DirectoryItem(xmlAlbums, title=title), model=model, sort=sort))
  return dir

####################################################################################################
def FreePicsMenu(sender):
  dir = MediaContainer(viewGroup='Plugin')
  for item in XML.ElementFromURL('http://suicidegirls.com/xml/join/gallery/').xpath('/gallery/photo'):
    url = BASE + item.get('src')
    dir.Append(Function(PhotoItem(getThumb, title=item.get('title'), subtitle=item.get('subtitle'), thumb=Function(getThumb, thumb=url)), thumb=url))
  return dir
  
####################################################################################################
def VideoMenu():
  dir = MediaContainer(viewGroup='_List')
  currentlyLogedIn = Login()
  if currentlyLogedIn:
    dir.Append(Function(DirectoryItem(getGirlsXML, title='Girls', thumb=R('icon-default.png')), sort='has_video', mediaType='videos'))
  
    for title, url, style in VIDEO_SECTIONS:
      absURL = BASE + url
      dir.Append(Function(DirectoryItem(getVideos2, title=title, thumb=R('icon-default.png')), url=absURL))
    dir.Append(Function(DirectoryItem(getVideosRSS, title='Free Videos', thumb=R('icon-default.png')), url=BASE+'/rss/video/boxee/'))
  else:
    dir.noCache = True
    dir.viewGroup = '_InfoList'
    dir.Append(Function(DirectoryItem(getVideosRSS, title='Free Videos', thumb=R('icon-default.png')), url=BASE+'/rss/video/boxee/'))
    dir.Append(PrefsItem(title='Log In', thumb=R('icon-default.png'), summary=PLUGIN_SUMMARY))
    dir.Append(Function(DirectoryItem(Join, title='Join', settings=True)))
  return dir
####################################################################################################

def getGirlsXML(sender, sort=None, mediaType='pics/all'):
  dir = MediaContainer(viewGroup='Plugin', title2=sender.itemTitle)
  if mediaType == 'videos':
    hnd = getVideos
  else:
    hnd = AlbumSortMenu
    
  url = BASE +'/media/generated/girlindex/%s/all.xml' % sort
  
  for alias in XML.ElementFromURL(url).xpath('/girls/girl/alias'):
    title = alias.text
    thumb = 'http://img.suicidegirls.com/media/girls/%s/girl_pic_large.jpg' % String.Quote(title)
    dir.Append(Function(DirectoryItem(hnd, title=title, thumb=thumb), model=title))
  if sort == 'has_video': dir.Sort('name')
  return dir
####################################################################################################
  
def getVideos(sender, model):
  cookies = HTTP.GetCookiesForURL(BASE)
  dir = MediaContainer(viewGroup='Plugin', title2=sender.itemTitle, httpCookies=cookies)
  url = BASE + '/girls/%s/videos/' % (String.Quote(model))
  for vid in XML.ElementFromURL(url, True).xpath('//div[@class="card videoCard"]'):
    title = vid.get('v_title')
    summary = vid.get('v_description')
    thumb = vid.xpath('./a/img')[0].get('src')
    url = BASE + vid.xpath('./h1/a')[0].get('href')
    dir.Append(Function(VideoItem(getVideo, title=title, summary=summary, thumb=thumb), url=url))
  return dir
  
def durationToInt(duration):
  components = duration.split(':')
  components.reverse()
  m = 1
  i = 0
  for component in components:
    i += int(component) * m
    m *= 60
  return i
  
def getVideos2(sender, url, pageNum=1):
  cookies = HTTP.GetCookiesForURL(BASE)
  dir = MediaContainer(viewGroup='Plugin', title2=sender.itemTitle, httpCookies=cookies, replaceParent=(pageNum!=1))
  page = XML.ElementFromURL(url + 'page%i/' % pageNum, True)
  for vid in page.xpath('//div[@class="preview"]'):
    img = vid.xpath('./a[@class="pngSpank"]/img')[0]
    
    videoName = vid.xpath('./a[@class="title"]')[0].text
    modelName = vid.xpath('./div[@class="info"]/span[@class="by"]/a')[0].text
    title = '%s: %s' % (modelName, videoName)
    
    durationStr = vid.xpath('./div[@class="info"]/span[@class="time"]')[0].text
    duration = durationToInt(durationStr)
    
    thumb = BASE + img.get('src')
    vidURL = BASE + vid.xpath('./a[@class="pngSpank"]')[0].get('href')
    dir.Append(Function(VideoItem(getVideo, title=title, thumb=thumb, duration=duration), url=vidURL))
  nextPage = page.xpath('//img[@class="arrow_next"]')
  if len(nextPage) != 0:
    dir.Append(Function(DirectoryItem(getVideos2, title='Next', thumb=R('next.png')), url=url, pageNum=pageNum+1))
  return dir

def getVideosRSS(sender, url):
  cookies = HTTP.GetCookiesForURL(BASE)
  dir = MediaContainer(viewGroup='Plugin', title2=sender.itemTitle, httpCookies=cookies)
  for item in RSS.FeedFromURL(url).entries:
    if 'author' in item:
      title = '%s: %s' % (item.author, item.title)
    else:
      title = item.title
    duration = int(item.media_content[0]['duration'])
    summary = String.StripTags(item.summary_detail.value)
    url = item.media_content[0]['url']
    thumb = item.media_thumbnail[0]['url']
    dir.Append(VideoItem(url, title=title, duration=duration, summary=summary, thumb=thumb))
  return dir
####################################################################################################

def getVideo(sender, url):
  vidURL = XML.ElementFromURL(url, True).xpath('//object[@class="vplayer"]/param[@name="flashvars"]')[0].get('value').split('=')[-1]
  return Redirect(vidURL)
####################################################################################################

def settingsContainer(settings, dialogTitle):
  container = MediaContainer(title=dialogTitle)
  for pref in settings:
    prefObj = XMLObject(tagName="Setting")
    Log(prefObj)
    for key in pref:
      prefObj.__dict__[key] = pref[key]
    Log(prefObj)
    # If dealing with an enum, deal with the keys differently
    if pref.has_key("values"):
      if isinstance(pref["values"], basestring):
        prefValues = pref["values"].split("|")
      else:
        prefValues = list(pref["values"])
      
      # Extract the default index
      if pref.has_key("default"):
        if pref["default"] in prefValues:
          prefObj.default = prefValues.index(pref["default"])

      # Set the default index
      if pref.has_key("value"):
        if pref["value"] in prefValues:
          prefObj.value = prefValues.index(pref["value"])
          
      # Localize values
      for i in range(len(prefValues)):
        prefValues[i] = str(L(prefValues[i]))
      prefObj.values = String.Join(prefValues, "|")

    if not pref.has_key("value") and pref.has_key("default"):
      prefObj.value = prefObj.default
    if pref.has_key("label"):
      prefObj.label = L(prefObj.label)
    container.Append(prefObj)
  return container

def Login():
  if isLoggedIn(): return True

  setCookies(getSafariCreds())
  if isLoggedIn():
    Log('Using Safari Credentials')
    return True
  
  setCookies(getFirefoxCreds())
  if isLoggedIn():
    Log('Using Firefox Credentials')
    return True
  
  values =  {'action': 'process_login', 'referer': '/', 'username': Prefs.Get('username'), 'password': Prefs.Get('password'), 'loginbutton': ''}
  HTTP.Request('http://suicidegirls.com/login/', cacheTime=0, values=values)
  return isLoggedIn()
  
def setCookies(sessionID):
  if sessionID != None:
    if 'Cookie' in HTTP.__headers:
      cookies = HTTP.__headers['Cookie']+ '; '
    else:
      cookies = ''
    cookies += 'PHPSESSID=%s' % sessionID
    HTTP.SetHeader('Cookie', cookies)
    
def getSafariCreds():
  Log('getSafariCreds')
  cookiePath = os.path.expanduser('~/Library/Cookies/Cookies.plist')
  f = open(cookiePath)
  cookies = f.read()
  f.close()

  for cookie in XML.ElementFromString(cookies).xpath('//key[text()="Domain"]/following-sibling::string[text()=".suicidegirls.com"]'):
    name = cookie.xpath('./following-sibling::key[text()="Name"]/following-sibling::*')[0].text
    if name == 'PHPSESSID':
      return cookie.xpath('./following-sibling::key[text()="Value"]/following-sibling::string')[0].text

def getFirefoxCreds():
  import sqlite3, shutil
  profilesPath = os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
  profileName = filter(lambda profile:profile.endswith('.default'), os.listdir(profilesPath))[0]
  cookiePath = os.path.join(profilesPath, profileName, 'cookies.sqlite')
  conn = sqlite3.connect(cookiePath)
  c = conn.cursor()
  try:
    c.execute('select value from moz_cookies where (name="PHPSESSID" and host=".suicidegirls.com");')
  except:
    pass # Firefox 3.5+ locks us out while running
  return c
  
def isLoggedIn():
  page = HTTP.Request(USER_INFO, cacheTime=0)
  err = XML.ElementFromString(page).xpath('//error')
  if len(err) == 0:
    return True
  else:
    return False

def getThumb(thumb, sender=None):
  return DataObject(HTTP.Request(thumb, cacheTime=0), mimetypes.guess_type(thumb))

  
