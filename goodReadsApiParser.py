#!/usr/bin/env python
# -*- coding: utf-8 -*-
# goodReadsApiParser
#
# Author: Adam Faulkner <adamflkr@gmail.com>
# 

"""
Extract info from the Goodreads API (http://www.goodreads.com/api).  
Initialized with user's key (provided by Goodreads after signing up
as a developer.)

getTitleId(book_title): Given a book title, returns that title's Goodreads ID.
getAuthorId(author): Given an author name, returns that author's Goodreads ID.
getAuthor(title_id): Given the Goodreads ID of a book title, returns that book's author.



"""
import pycurl
import cStringIO
import xml.etree.cElementTree as ET

class goodReadsApiParser(object):
    
    def __init__(self, key):
        """Initialize with developer key"""
        self.key = key

    def connectToGoodreads(self, base_url, *args):
        """
        :param base url: the base url used to connect to Goodreads API  
        :param args: the parameters for the Goodreads API methods
        """
        response = cStringIO.StringIO()    
        c = pycurl.Curl()
        values = [("key", self.key)]
        
        for tup in self._pairwiseArgs(args):
            values.append(tup)
        
        c.setopt(c.URL, base_url)
        #set API parameters with their values, e.g., "title","The Big Sleep" 
        c.setopt(c.HTTPPOST, values)
        #keep server response
        c.setopt(c.WRITEFUNCTION, response.write)   
        c.perform()
        c.close()
        #returns raw xml 
        return response.getvalue()
        
    
    def _searchBaseXML(self,arg):
    
        return self.connectToGoodreads( "http://www.goodreads.com/search.xml","q", arg)
        
    
    def _pairwiseArgs(self,iterable):
    
        from itertools import izip
        a = iter(iterable)
        return izip(a, a)
        
    def getTitleId(self,book_title):
        """
        Given a book title, returns that title's Goodreads ID.
        """
        xml = self._searchBaseXML(book_title)
        tree = ET.fromstring(xml)
        try:
            child=tree.getiterator("best_book").next()
            return child[0].text
        except StopIteration:
            return "None found"
        
    def getAuthorId(self, author):
        """
        Given an author name, returns that author's Goodreads ID.
        """
    
        xml = self._searchBaseXML(author)
        tree = ET.fromstring(xml)
        try:
            child=tree.getiterator("author").next()
            return child[0].text
        except StopIteration:
            return "None found"
        
        
    def getAuthor(self, title):
        """
        Given a book title, returns that book's author.
        example url: http://www.goodreads.com/search.xml?key=wMPH5Ryoo2LRL0YBj2uTCg&q=Ender%27s+Game
        """
        
        xml = self.connectToGoodreads( "http://www.goodreads.com/book/title.xml", "title", title)
        tree = ET.fromstring(xml)
        
        try:
            child=tree.getiterator("author").next()
            return child[1].text
        except StopIteration:
            return "None found"

    def getISBN(self, title):
        """given a title, get the ISBN"""
        #http://www.goodreads.com/book/title.xml?&key=wMPH5Ryoo2LRL0YBj2uTCg&title=%20the%20davinci%20code
        xml = self.connectToGoodreads("http://www.goodreads.com/book/title.xml", "title", title)
        tree = ET.fromstring(xml)
        nodes = [node for node in tree.getiterator("isbn")]
        for i in nodes:
            return str(i.text)

        
def demo(): 
    obj = goodReadsApiParser(my_developer_ley)
    print "#"*70, '\n'
    print 'Author of "The Big Sleep" is: ', obj.getAuthor("The Big Sleep") 
    print 'Goodreads title ID for "The Big Sleep" is: ', obj.getTitleId("The Big Sleep"), '\n'
    print "#"*70, '\n'
    print 'Goodreads author ID for "Raymond Chandler" is: ', obj.getAuthorId("Raymond Chandler"), '\n'
    print "#"*70, '\n'
    print 'The author of the title with the Goodreads title ID "2052" is:', obj.getAuthor("2052"), '\n'
    print "#"*70, '\n'

if __name__ == '__main__': 
    demo() 

