#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to import paintings from the National Galleries of Scotland to Wikidata.

Just loop over pages like https://art.nationalgalleries.org/search?object_types[29864]=29864&page=0

This bot does use artdatabot to upload it to Wikidata and just asks the API for all it's paintings.

"""
import artdatabot
import pywikibot
import requests
import re
import html

def get_national_galleries_scotland_generator():
    """
    Generator to return National Galleries of Scotland paintings
    """
    basesearchurl = u'https://art.nationalgalleries.org/search?object_types[29864]=29864&page=%s'

    # Number per page seems to have changed, but that doesn't crash the bot
    for i in range(0, 125):
        urls = []
        searchurl = basesearchurl % (i,)
        print(searchurl)
        searchPage = requests.get(searchurl)
        urlregex = u'\<a href\=\"\/art-and-artists\/(\d+)\?object_types%5B29864%5D=2986[^\"]+\"' # ?
        matches = re.finditer(urlregex, searchPage.text)
        for match in matches:
            # To remove duplicates
            url = 'https://www.nationalgalleries.org/art-and-artists/%s' % (match.group(1))
            if url not in urls:
                urls.append(url)

        for url in urls:
            metadata = {}

            print (url)

            itempage = requests.get(url)
            metadata['url'] = url

            metadata['artworkidpid'] = 'P8946'
            metadata['artworkid'] = url.replace('https://www.nationalgalleries.org/art-and-artists/', '')

            metadata['collectionqid'] = u'Q2051997'
            metadata['collectionshort'] = u'NGoS'

            #No need to check, I'm actually searching for paintings.
            metadata['instanceofqid'] = u'Q3305213'

            invregex = u'<li class\="ngs-mimsy-data__item"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>accession number\:\<\/div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*([^\<]+)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            invregex = '<li class="ngs-mimsy-data__item">[\r\n\t\s]*<div class="ngs-mimsy-data__item-label">accession number:</div>[\r\n\t\s]*<div class="ngs-mimsy-data__item-values">[\r\n\t\s]*<div class="ngs-mimsy-data__item-value">([^\<]+)</div>'
            invmatch = re.search(invregex, itempage.text)

            if not invmatch:
                pywikibot.output(u'Something went wrong, skipping this one')
                continue

            metadata['id'] = invmatch.group(1).strip()
            metadata['idpid'] = u'P217'

            # They have three locations, using inventory to guess the location
            if metadata['id'].startswith(u'NG ') or metadata['id'].startswith(u'NGL '):
                metadata['locationqid'] = u'Q942713'  # Scottish National Gallery (Q942713)
            elif metadata['id'].startswith(u'PG '):
                metadata['locationqid'] = u'Q2441562'  # Scottish National Portrait Gallery (Q2441562)
            elif metadata['id'].startswith(u'GMA '):
                metadata['locationqid'] = u'Q1889944'  # Scottish National Gallery of Modern Art (Q1889944)
            else:
                metadata['locationqid'] = u'Q2051997'

            titleregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>title\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*([^\<]+)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            titlematch = re.search(titleregex, itempage.text)
            title = html.unescape(titlematch.group(1).strip())
            #if not titlematch:
            #    pywikibot.output(u'No title match, something went wrong on %s' % (url,))
            #    continue
            ## Chop chop, several very long titles
            if len(title) > 220:
                title = title[0:200]
            metadata['title'] = { u'en' : title,
                                  }

            creatorregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>artists?\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*(\<a href\=\"[^\"]+\" title=\"[^\>]+\"\>)?(?P<creator>[^\<]+)\<\/'
            creatormatch = re.search(creatorregex, itempage.text)
            name = html.unescape(creatormatch.group(u'creator').strip())
            if u',' in name:
                (surname, sep, firstname) = name.partition(u',')
                name = u'%s %s' % (firstname.strip(), surname.strip(),)
            if name==u'Unknown':
                metadata['creatorname'] = u'anonymous'
                metadata['description'] = { u'nl' : u'schilderij van anonieme schilder',
                                            u'en' : u'painting by anonymous painter',
                                            }
                metadata['creatorqid'] = u'Q4233718'
            else:
                metadata['creatorname'] = name
                metadata['description'] = { u'nl' : u'%s van %s' % (u'schilderij', name,),
                                            u'en' : u'%s by %s' % (u'painting', name,),
                                            }

            acquisitiondateregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>credit line\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*[^\<]+(\d\d\d\d)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            acquisitiondatematch = re.search(acquisitiondateregex, itempage.text)
            if acquisitiondatematch:
                metadata['acquisitiondate'] = acquisitiondatematch.group(1)

            dateregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>date created\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*(\d\d\d\d)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            datedregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>date created\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*Dated\s*(\d\d\d\d)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            datecircaregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>date created\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*[aA]bout\s*(\d\d\d\d)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            periodregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>date created\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*(\d\d\d\d)\s*-\s*(\d\d\d\d)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            shortperiodregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>date created\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*(\d\d)(\d\d)\s*-\s*(\d\d)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            circaperiodregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>date created\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*[aA]bout\s*(\d\d\d\d)\s*-\s*(\d\d\d\d)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            otherdateregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>date created\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*([^\<]+)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'

            datematch = re.search(dateregex, itempage.text)
            datedmatch = re.search(datedregex, itempage.text)
            datecircamatch = re.search(datecircaregex, itempage.text)
            periodmatch = re.search(periodregex, itempage.text)
            shortperiodmatch = re.search(shortperiodregex, itempage.text)
            circaperiodmatch = re.search(circaperiodregex, itempage.text)
            otherdatematch = re.search(otherdateregex, itempage.text)

            if datematch:
                metadata['inception'] = int(datematch.group(1))
            elif datedmatch:
                metadata['inception'] = int(datedmatch.group(1))
            elif datecircamatch:
                metadata['inception'] = int(datecircamatch.group(1))
                metadata['inceptioncirca'] = True
            elif periodmatch:
                metadata['inceptionstart'] = int(periodmatch.group(1),)
                metadata['inceptionend'] = int(periodmatch.group(2),)
            elif shortperiodmatch:
                metadata['inceptionstart'] = int(u'%s%s' % (shortperiodmatch.group(1), shortperiodmatch.group(2)))
                metadata['inceptionend'] = int(u'%s%s' % (shortperiodmatch.group(1), shortperiodmatch.group(3)))
            elif circaperiodmatch:
                metadata['inceptionstart'] = int(circaperiodmatch.group(1),)
                metadata['inceptionend'] = int(circaperiodmatch.group(2),)
                metadata['inceptioncirca'] = True
            elif otherdatematch:
                print('Could not parse date: "%s"' % (otherdatematch.group(1).strip(),))

            mediumregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>materials\:\<\/div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-value\"\>([^\<]+)\<\/div\>[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'

            mediummatch = re.search(mediumregex, itempage.text)
            if mediummatch:
                metadata['medium'] = html.unescape(mediummatch.group(1)).lower()

            measurementsregex = u'\<li class\=\"ngs-mimsy-data__item\"\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-label\"\>measurements\:</div\>[\r\n\t\s]*\<div class\=\"ngs-mimsy-data__item-values\"\>[\r\n\t\s]*([^\<]+)[\r\n\t\s]*\<\/div\>[\r\n\t\s]*\<\/li\>'
            measurementsmatch = re.search(measurementsregex, itempage.text)
            if measurementsmatch:
                measurementstext = measurementsmatch.group(1).strip()
                regex_2d = u'(?P<height>\d+(\.\d+)?) x (?P<width>\d+(\.\d+)?) cm.*'
                regex_3d = u'(?P<height>\d+(\.\d+)?) x (?P<width>\d+(\.\d+)?) x (?P<depth>\d+(\.\d+)?) cm.*'
                match_2d = re.match(regex_2d, measurementstext)
                match_3d = re.match(regex_3d, measurementstext)
                if match_2d:
                    metadata['heightcm'] = match_2d.group(u'height').replace(u',', u'.')
                    metadata['widthcm'] = match_2d.group(u'width').replace(u',', u'.')
                elif match_3d:
                    metadata['heightcm'] = match_3d.group(u'height').replace(u',', u'.')
                    metadata['widthcm'] = match_3d.group(u'width').replace(u',', u'.')
                    metadata['depthcm'] = match_3d.group(u'depth').replace(u',', u'.')

            # They seem to provide images "<span class="ngs-slider__slide-copyright">Creative Commons CC by NC</span>"

            image_url_regex = '<meta property\="og:image" content="(https://www\.nationalgalleries\.org/sites/default/files/styles/thumbnail/public/externals/\d+\.jpg)\?itok\=[^"]+" />'
            image_url_match = re.search(image_url_regex, itempage.text)

            if image_url_match and '<span class="ngs-slider__slide-copyright">Creative Commons CC by NC</span>' in itempage.text:
                recentinception = False
                if metadata.get('inception') and metadata.get('inception') > 1924:
                    recentinception = True
                if metadata.get('inceptionend') and metadata.get('inceptionend') > 1924:
                    recentinception = True
                if not recentinception:
                    metadata['imageurl'] = image_url_match.group(1)
                    metadata['imageurlformat'] = 'Q2195'  # JPEG
                    metadata['imageoperatedby'] = 'Q2051997'  # National Galleries Scotland
                    metadata['imageurlforce'] = True  # Add all images

            yield metadata


def main(*args):
    dictGen = get_national_galleries_scotland_generator()
    dryrun = False
    create = False

    for arg in pywikibot.handle_args(args):
        if arg.startswith('-dry'):
            dryrun = True
        elif arg.startswith('-create'):
            create = True

    if dryrun:
        for painting in dictGen:
            print(painting)
    else:
        artDataBot = artdatabot.ArtDataBot(dictGen, create=create)
        artDataBot.run()

if __name__ == "__main__":
    main()