TITLE = 'Link TV'
ART   = 'art-default.jpg'
ICON  = 'icon-default.png'

PREFIX = '/video/linktv'
BASE_URL = 'http://www.linktv.org'
HTTP_USER_AGENT = "Mozilla/5.0 (iPad; CPU OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B176 Safari/7534.48.3"

RE_DURATION = Regex('([0-9]+):([0-9]+):([0-9]+)')

##########################################################################################
def Start():
	ObjectContainer.title1 = TITLE
	ObjectContainer.art    = R(ART)
	
	DirectoryObject.thumb = R(ICON)

	HTTP.CacheTime             = CACHE_1HOUR
	HTTP.Headers['User-agent'] = HTTP_USER_AGENT

##########################################################################################
@handler(PREFIX, TITLE, art = ART, thumb = ICON)
def MainMenu():
	oc = ObjectContainer()
	
	pageElement = HTML.ElementFromURL(BASE_URL + '/video/browse')
	for item in pageElement.xpath("//*[@id = 'strand']//option"):
		category   = item.xpath("./text()")[0].title()
		categoryID = item.xpath("./@value")
		
		if 'news' in category.lower():
			summary = u"Link TV delivers international news from diverse sources around the world, and presents a wide array of viewpoints not found in the mainstream media. By looking at the news the way the rest of the world sees it, we offer an inside-out perspective on global affairs and show how America is perceived in other countries."
		
		elif 'documentaries' in category.lower():
			summary = u"Link TV is your home for fascinating documentaries from around the world, both on air and online! These films will inspire, challenge, and entertain you. Reach across borders and check out this week's featured documentaries. And remember, there are tons of other great docs to watch free online, at any time!"
		
		elif 'cinema' in category.lower():
			summary = u"Link TV's CINEMONDO is a nationally broadcast, ground breaking world cinema series. CINEMONDO brings international cinema with great artistic, cultural and political value to the living rooms of Link TV's American audiences."
		
		elif 'music' in category.lower():
			summary = u"You may have heard world music, but on Link TV you can see it!  Link TV brings you the sights and sounds of the world every day with music videos, documentaries and concerts that are entertaining and insightful.  Whether it's familiar or far flung, come adventure with us, and hear the sound of the world, as it makes music. Link TV is your music connection to the world!"
		
		else:
			summary = u"Link TV broadcasts programs that engage, educate and activate viewers to become involved in the world. These programs provide a unique perspective on international news, current events, and diverse cultures, presenting issues not often covered in the US media."
		
		oc.add(
			DirectoryObject(
				key =
					Callback(
						SortChoice,
						title = category,
						categoryID = categoryID
					),
				title = category,
				summary = summary
			)
		)
		
	oc.add(
		InputDirectoryObject(
			key = 
				Callback(Search),
			title = "Search...", 
			prompt = "Search for", 
			thumb = R('search.png')
		)
	)
		
	return oc

##########################################################################################
@route(PREFIX + "/SortChoice")
def SortChoice(title, categoryID):
	oc = ObjectContainer(title1 = title)
	
	pageElement = HTML.ElementFromURL(BASE_URL + '/video/browse')
	for item in pageElement.xpath("//*[@id = 'sort_order']//option"):
		sortOrder   = item.xpath("./text()")[0].title()
		sortOrderID = item.xpath("./@value")[0]
		
		oc.add(
			DirectoryObject(
				key =
					Callback(
						LengthChoice,
						title = sortOrder,
						categoryID = categoryID,
						sortOrderID = sortOrderID
					),
				title = sortOrder
			)
		)
		
	return oc

##########################################################################################
@route(PREFIX + "/LengthChoice")
def LengthChoice(title, categoryID, sortOrderID):
	oc = ObjectContainer(title1 = title)
	
	pageElement = HTML.ElementFromURL(BASE_URL + '/video/browse')
	for item in pageElement.xpath("//*[@id = 'show_length']//option"):
		showLength   = item.xpath("./text()")[0].title()
		showLengthID = item.xpath("./@value")
		
		oc.add(
			DirectoryObject(
				key =
					Callback(
						Videos,
						name = showLength,
						categoryID = categoryID,
						sortOrderID = sortOrderID,
						showLengthID = showLengthID
					),
				title = showLength
			)
		)
		
	return oc
	
##########################################################################################
@route(PREFIX + "/Videos")
def Videos(name, categoryID = None, sortOrderID = None, showLengthID = None, url = None):
	oc = ObjectContainer(title1 = name)

	if url is None:
		url = BASE_URL + '/video/browse'
		
		if categoryID is not None:
			url = url + '/s/' + categoryID
		
 		url = url + '/o/' + sortOrderID + '/l/' + showLengthID
 	
	pageElement = HTML.ElementFromURL(url)
	
	for item in pageElement.xpath("//*[@class = 'episodeDesc']"):
		link  = item.xpath(".//*[@class = 'episodeTitle']//a/@href")[0]
		
		if not link.startswith("/video/"):
			continue
			
		url     = BASE_URL + link
		title   = item.xpath(".//*[@class = 'episodeTitle']//a/text()")[0]
		
		try:
			thumb = GetThumbURL(item.xpath("//*[@href = '" + link + "']//img/@src")[0])
		except:
			thumb = None
			
		try:
			summary = item.xpath(".//div/text()")[0]
		except:
			summary = None
		
		try:
			searchString = HTML.StringFromElement(item)
			match        = RE_DURATION.search(searchString).groups()
			
			duration = int(match[0]) * 3600 + int(match[1]) * 60 + int(match[2])
			duration = duration * 1000 # milliseconds 
		except:
			duration = None		
		
		oc.add(
			VideoClipObject(
				url = url,
				title = title,
				thumb = thumb,
				summary = summary,
				duration = duration
			)
		)
		
	pagination = pageElement.xpath("//*[@class = 'pages']//a[text() = 'Next page']")
	
	if len(pagination) > 0:
		nextPageURL = BASE_URL + pagination[0].xpath("./@href")[0]
		
		oc.add(
			NextPageObject(
				key =
					Callback(
						Videos,
						name = name,
						url = nextPageURL
					),
				title = "More ..."
			)
		)
		
	return oc

##########################################################################################
@route(PREFIX + "/Search")
def Search(query, url = None):
	oc = ObjectContainer(title1 = "Results for: " + query)
	
	if url is None:
		url = BASE_URL + '/search/r/episodes/q/' + query
		
	pageElement = HTML.ElementFromURL(url)
	
	for item in pageElement.xpath("//*[@id = 'widget_3']//*"):
		try:
			link  = item.xpath(".//a/@href")[0]
			
			if not link.startswith("/video/"):
				continue
			
			url   = BASE_URL + link
			title = item.xpath(".//a//strong/text()")[0]
			
			try:
				summary = item.xpath(".//p/text()")[0]
			except:
				try:
					summary = item.xpath(".//br/text()")[0]
				except:
					summary = None
				
			try:
				thumb = GetThumbURL(pageElement.xpath("//*[@href = '" + link + "']//img/@src")[0])
			except:
				thumb = None
			
		
			oc.add(
				VideoClipObject(
					url = url,
					title = title,
					summary = summary,
					thumb = thumb
				)
			)
			
		except:
			pass
	
	pagination = pageElement.xpath("//*[@class = 'pages']//a[text() = 'Next page']")
	
	if len(pagination) > 0:
		nextPageURL = BASE_URL + pagination[0].xpath("./@href")[0]
		
		oc.add(
			NextPageObject(
				key =
					Callback(
						Search,
						query = query,
						url = nextPageURL
					),
				title = "More ..."
			)
		)
	
	if len(oc) < 1:
		oc.header  = "Sorry"
		oc.message = "No results found for: " + query
		
	return oc

##########################################################################################
def GetThumbURL(link):
	return BASE_URL + link.replace("jpg_90", "jpg_400")
