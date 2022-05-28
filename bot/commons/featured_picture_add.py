#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to add featured picture claim to SDC.

Just loop over the files in https://commons.wikimedia.org/wiki/Category:Featured_pictures_on_Wikimedia_Commons

"""

import pywikibot
import time
import json
from pywikibot import pagegenerators

class FeaturedPictureBot:
    """
    Bot to add structured data statements on Commons
    """
    def __init__(self, fullrun=False):
        """
        Grab generator based on search to work on.
        """
        self.site = pywikibot.Site(u'commons', u'commons')
        self.site.login()
        self.site.get_tokens('csrf')
        self.repo = self.site.data_repository()
        self.fullrun = fullrun

        self.generator = self.getGenerator(fullrun)

    def getGenerator(self, fullrun):
        """
        Get the generator to work on.
        """
        if fullrun:
            category = pywikibot.Category(self.site, title='Category:Featured_pictures_on_Wikimedia_Commons')
            gen = pagegenerators.CategorizedPageGenerator(category, namespaces=6)
        else:
            query = 'incategory:Featured_pictures_on_Wikimedia_Commons -haswbstatement:P6731=Q63348049'
            gen = pagegenerators.SearchPageGenerator(query, total=1000, namespaces=6, site=self.site)
        return pagegenerators.PageClassGenerator(gen)

    def run(self):
        """
        Run on the items
        """
        for filepage in self.generator:
            mediaid = u'M%s' % (filepage.pageid,)

            if not filepage.exists():
                continue

            currentdata = self.getCurrentMediaInfo(mediaid)
            self.handleFeaturedPicture(filepage, mediaid, currentdata)

    def getCurrentMediaInfo(self, mediaid):
        """
        Check if the media info exists. If that's the case, return that so we can expand it.
        Otherwise return an empty structure with just <s>claims</>statements in it to start
        :param mediaid: The entity ID (like M1234, pageid prefixed with M)
        :return: json
            """
        # https://commons.wikimedia.org/w/api.php?action=wbgetentities&format=json&ids=M52611909
        # https://commons.wikimedia.org/w/api.php?action=wbgetentities&format=json&ids=M10038
        request = self.site._simple_request(action='wbgetentities',ids=mediaid)
        data = request.submit()
        if data.get(u'entities').get(mediaid).get(u'pageid'):
            return data.get(u'entities').get(mediaid)
        return {}

    def handleFeaturedPicture(self, filepage, mediaid, currentdata):
        """
        Handle a single file.

        :return: Nothing, edit in place
        """
        pywikibot.output(u'Working on %s' % (filepage.title(),))
        if not filepage.exists():
            return
        if not filepage.has_permission():
            # Featured pictures are often protected
            return

        if currentdata.get('statements') and currentdata.get('statements').get('P6731'):
            for statement in currentdata.get('statements').get('P6731'):
                if statement.get('mainsnak').get('datavalue').get('value').get('id')=='Q63348049':
                    # Already on it. All done.
                    if not self.fullrun:
                        # Let's touch it to make sure the database is up to speed
                        filepage.touch()
                    return True

        toclaim = {'mainsnak': { 'snaktype':'value',
                                 'property': 'P6731',
                                 'datavalue': { 'value': { 'numeric-id': 63348049,
                                                           'id' : 'Q63348049',
                                                           },
                                                'type' : 'wikibase-entityid',
                                                }

                                 },
                   'type': 'statement',
                   'rank': 'normal',
                   }

        itemdata = {u'claims' : [toclaim,] }
        summary = 'Featured picture added to structured data based on membership of [[:Category:Featured pictures on Wikimedia Commons]]'
        #print (itemdata)
        pywikibot.output(summary)

        token = self.site.tokens['csrf']

        postdata = {u'action' : u'wbeditentity',
                    u'format' : u'json',
                    u'id' : mediaid,
                    u'data' : json.dumps(itemdata),
                    u'token' : token,
                    u'summary' : summary,
                    u'bot' : True,
                    }

        request = self.site._simple_request(**postdata)
        try:
            data = request.submit()
            filepage.touch()
        except pywikibot.exceptions.APIError:
            pywikibot.output('Got an API error while saving page. Sleeping and skipping')
            time.sleep(120)
            # Reload the tokens to be sure
            self.site.get_tokens('csrf')
        return


def main(*args):

    fullrun = False

    for arg in pywikibot.handle_args(args):
        if arg == '-fullrun':
            fullrun = True

    featuredPictureBot = FeaturedPictureBot(fullrun=fullrun)
    featuredPictureBot.run()

if __name__ == "__main__":
    main()
