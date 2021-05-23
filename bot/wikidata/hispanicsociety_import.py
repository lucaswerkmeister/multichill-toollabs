#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to import paintings from the Hispanic Society of America to Wikidata.

Just loop over pages http://hispanicsociety.emuseum.com/advancedsearch/objects/classifications%3APainting/images?page=2


This bot does uses artdatabot to upload it to Wikidata.

"""
import artdatabot
import pywikibot
import requests
import re
import time
from html.parser import HTMLParser

def getHispanicSocietyGenerator():
    """
    Generator to return Munch Museum paintings
    """
    basesearchurl = 'http://hispanicsociety.emuseum.com/advancedsearch/objects/classifications%%3APainting/images?page=%s'
    htmlparser = HTMLParser()

    # Not sure if this needed for thie Emuseum instance
    session = requests.Session()
    session.get('http://hispanicsociety.emuseum.com/advancedsearch/objects')

    # 397 hits, 12 per page.
    for i in range(1, 35):
        searchurl = basesearchurl % (i,)

        print (searchurl)
        searchPage = session.get(searchurl)

        workurlregex = '\<div class\=\"title text-wrap\s*first-field\s*\"\>\<a title\=\"([^\"]+)\" href=\"(\/objects\/\d+\/[^\?]+)\?[^\"]+\"\>'
        matches = re.finditer(workurlregex, searchPage.text)

        for match in matches:
            metadata = {}
            title = htmlparser.unescape(match.group(1)).strip()
            url = 'http://hispanicsociety.emuseum.com%s' % (match.group(2),)

            itempage = session.get(url)
            pywikibot.output(url)
            metadata['url'] = url

            metadata['collectionqid'] = 'Q2420849'
            metadata['collectionshort'] = 'Hispanic Society'
            metadata['locationqid'] = 'Q2420849'

            #No need to check, I'm actually searching for paintings.
            metadata['instanceofqid'] = 'Q3305213'
            metadata['idpid'] = 'P217'


            # The website also contains paintings outside of the collection.
            invregex = '\<div class\=\"detailField invnoField\"\>\<span class\=\"detailFieldLabel\"\>Accession Number\:\s*\<\/span\>\<span class\=\"detailFieldValue\"\>([^\<]+)\<\/span\>'
            invmatch = re.search(invregex, itempage.text)

            if not invmatch:
                # Painting from a different collection
                continue
            # Not sure if I need to replace space here
            metadata['id'] = htmlparser.unescape(invmatch.group(1).replace('&nbsp;', ' ')).strip()

            # Already got it
            #titleregex = '\<meta property\=\"og\:title\" content\=\"([^\"]+)\"\s*\/\>'
            #titlematch = re.search(titleregex, itempage.text)
            #title = htmlparser.unescape(titlematch.group(1)).strip()

            # Chop chop, several very long titles
            if len(title) > 220:
                title = title[0:200]
            title = title.replace('\t', '').replace('\n', '')
            metadata['title'] = { 'en' : title,
                                  }

            creatorregex = '\<meta content\=\"([^\"]+)\" property\=\"schema\:creator\" itemprop\=\"creator\"\>'
            creatormatch = re.search(creatorregex, itempage.text)

            # Some paintings don't have a creator, but are not anonymous
            if creatormatch:
                creatorname = htmlparser.unescape(creatormatch.group(1)).strip()

                metadata['creatorname'] = creatorname
                metadata['description'] = { 'nl' : '%s van %s' % ('schilderij', metadata.get('creatorname'),),
                                            'en' : '%s by %s' % ('painting', metadata.get('creatorname'),),
                                            'de' : '%s von %s' % ('Gemälde', metadata.get('creatorname'), ),
                                            'fr' : '%s de %s' % ('peinture', metadata.get('creatorname'), ),
                                            }

            # Let's see if we can extract some dates. Date in meta fields is provided. Didn't update, catches most
            dateregex = '\<meta content\=\"(\d\d\d\d)\" property\=\"schema\:dateCreated\" itemprop\=\"dateCreated\"\>'
            datecircaregex = '\<meta content\=\"[Cc]a?\.\s*(\d\d\d\d)\" property\=\"schema\:dateCreated\" itemprop\=\"dateCreated\"\>'
            periodregex = '\<meta content\=\"(\d\d\d\d)\s*[–-]\s*(\d\d\d\d)\" property\=\"schema\:dateCreated\" itemprop\=\"dateCreated\"\>'
            circaperiodregex = '\<meta content\=\"ca?\.\s*(\d\d\d\d)\s*[–-]\s*(\d\d\d\d)\" property\=\"schema\:dateCreated\" itemprop\=\"dateCreated\"\>'
            shortperiodregex = '\<meta content\=\"(\d\d)(\d\d)[–-](\d\d)\" property\=\"schema\:dateCreated\" itemprop\=\"dateCreated\"\>'
            circashortperiodregex = '\<meta content\=\"ca?\. (\d\d)(\d\d)-(\d\d)\" property\=\"schema\:dateCreated\" itemprop\=\"dateCreated\"\>'
            otherdateregex = '\<meta content\=\"([^\"]+)\" property\=\"schema\:dateCreated\" itemprop\=\"dateCreated\"\>'

            datematch = re.search(dateregex, itempage.text)
            datecircamatch = re.search(datecircaregex, itempage.text)
            periodmatch = re.search(periodregex, itempage.text)
            circaperiodmatch = re.search(circaperiodregex, itempage.text)
            shortperiodmatch = re.search(shortperiodregex, itempage.text)
            circashortperiodmatch = re.search(circashortperiodregex, itempage.text)
            otherdatematch = re.search(otherdateregex, itempage.text)

            if datematch:
                metadata['inception'] = int(datematch.group(1).strip())
            elif datecircamatch:
                metadata['inception'] = int(datecircamatch.group(1).strip())
                metadata['inceptioncirca'] = True
            elif periodmatch:
                metadata['inceptionstart'] = int(periodmatch.group(1))
                metadata['inceptionend'] = int(periodmatch.group(2))
            elif circaperiodmatch:
                metadata['inceptionstart'] = int(circaperiodmatch.group(1))
                metadata['inceptionend'] = int(circaperiodmatch.group(2))
                metadata['inceptioncirca'] = True
            elif shortperiodmatch:
                metadata['inceptionstart'] = int(u'%s%s' % (shortperiodmatch.group(1),shortperiodmatch.group(2),))
                metadata['inceptionend'] = int(u'%s%s' % (shortperiodmatch.group(1),shortperiodmatch.group(3),))
            elif circashortperiodmatch:
                metadata['inceptionstart'] = int(u'%s%s' % (circashortperiodmatch.group(1),circashortperiodmatch.group(2),))
                metadata['inceptionend'] = int(u'%s%s' % (circashortperiodmatch.group(1),circashortperiodmatch.group(3),))
                metadata['inceptioncirca'] = True
            elif otherdatematch:
                print ('Could not parse date: "%s"' % (otherdatematch.group(1),))

            ### Nothing useful here
            #acquisitiondateregex = '\<div class\=\"detailField creditlineField\"\>[^\<]+,\s*(\d\d\d\d)\<\/div\>'
            #acquisitiondatematch = re.search(acquisitiondateregex, itempage.text)
            #if acquisitiondatematch:
            #    metadata['acquisitiondate'] = int(acquisitiondatematch.group(1))


            mediumregex = '\<meta content\=\"([^\"]+)\" property\=\"schema\:artMedium\" itemprop\=\"artMedium\"\>'
            mediummatch = re.search(mediumregex, itempage.text)
            # Artdatabot will sort this out
            if mediummatch:
                metadata['medium'] = mediummatch.group(1)

            # Dimensions need to be extracted from the text (meta properties appear broken)
            measurementsregex = '\<span class\=\"detailFieldLabel\"\>Dimensions\:\<\/span\>\<span class\=\"detailFieldValue\"\>\<div\>[^\<]+\(([^\<]+cm)\)\<\/div\>'
            measurementsregex = '\<div class\=\"detailField dimensionsField\"\>\<span class\=\"detailFieldLabel\"\>Dimensions\:\<\/span\>\<span class\=\"detailFieldValue\"\>\<div\>([^\<]+cm)'
            measurementsmatch = re.search(measurementsregex, itempage.text)
            if measurementsmatch:
                measurementstext = measurementsmatch.group(1)
                regex_2d = '^(Unframed\s*)?H\s*(?P<height>\d+(\.\d+)?)\s*[×x]\s*W\s*(?P<width>\d+(\.\d+)?)\s*cm$'
                match_2d = re.match(regex_2d, measurementstext)
                if match_2d:
                    metadata['heightcm'] = match_2d.group('height').replace(',', '.')
                    metadata['widthcm'] = match_2d.group('width').replace(',', '.')

            # Image url is provided and it's a US collection. Just check the date
            imageregex = '\<meta content\=\"(http\:\/\/hispanicsociety\.emuseum\.com\/internal\/media\/dispatcher\/\d+\/resize%3Aformat%3Dfull)\" name\=\"og:image\"\>'
            imagematch = re.search(imageregex, itempage.text)
            if imagematch:
                recentinception = False
                if metadata.get('inception') and metadata.get('inception') > 1924:
                    recentinception = True
                if metadata.get('inceptionend') and metadata.get('inceptionend') > 1924:
                    recentinception = True
                if not recentinception:
                    metadata['imageurl'] = imagematch.group(1)
                    metadata['imageurlformat'] = 'Q2195' #JPEG
                #    metadata['imageurllicense'] = 'Q18199165' # cc-by-sa.40
                    metadata['imageoperatedby'] = 'Q2420849'
                #    # Used this to add suggestions everywhere
                #    metadata['imageurlforce'] = True
            yield metadata


def main(*args):
    dictGen = getHispanicSocietyGenerator()
    dryrun = False
    create = False

    for arg in pywikibot.handle_args(args):
        if arg.startswith('-dry'):
            dryrun = True
        elif arg.startswith('-create'):
            create = True

    if dryrun:
        for painting in dictGen:
            print (painting)
    else:
        artDataBot = artdatabot.ArtDataBot(dictGen, create=create)
        artDataBot.run()

if __name__ == "__main__":
    main()
