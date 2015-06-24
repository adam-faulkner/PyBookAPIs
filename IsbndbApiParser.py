#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
# ISBNdbApiParser
#
# Author: Adam Faulkner <adamflkr@gmail.com>
#
########################################################

import pycurl
import cStringIO
import xml.etree.cElementTree as ET
import string
"""
This class connects to the ISBNdb and Goodreads APIs and extracts category information
for books and authors. Title categories are extracted in the following way.  Since search results
on Goodreads are ranked by popularity, we first extract the top-ranked ISBN returned by the Goodreads
API given a title.  The Goodreads API tolerates keyword-in-title searches--searches for "Jonathan 
Strange" or  "Mr. Norrell" will return the correct ISBN for the title "Jonathan Strange and Mr. Norrell."
Goodreads does not provide category information for either titles or authors. So, the ISBN extracted from 
Goodreads is passed to the ISBNdb API and categories associated with the title are returned.

Author categories are extracted by first querying Goodreads for the top-ranked response given an
author's name.  The categories of that author's 3 top-ranked books are extracted and serve as the 
genre categories associated with that author.  




Exampe usage:

>>> from getGenres import IsbndbApiParser as parse
>>> instance = parse.ISBNdbApiParser(isbn_key, goodreads_key)
>>> print instance.getTitleGenre("The Big Sleep")
['Fiction', 'Los Angeles (Calif.)', 'Private investigators', 'Detective and mystery stories', 
'Los Angeles', 'Mystery', 'Mystery & Thrillers', 'World Literature', 'Hard-Boiled', 'General', 
'United States', 'California', 'Marlowe, Philip (Fictitious character)', 'Classics', 'Short Stories', 'Literature & Fiction']
>>> print instance.getAuthorGenre("Raymond Chandler")
['Fiction', 'Private Investigators', 'Detective And Mystery Stories', 'Los Angeles', 'Mystery', 
'World Literature', 'Hard-Boiled', 'General', 'United States', 'Detectives', 'Marlowe, Philip', 
'California', 'Novela', 'Crime Fiction', 'Mystery Fiction', 'Classics', 'Short Stories']


"""


class IsbndbApiParser(object):
    
    def __init__(self, IsbnDbKey, GrKey):
        """
        :param IsbnDbKey: the developer key for the ISBNdb API
        :param GrKey: the developer key for the Goodreads API
        """
        self.IsbnDbkey = IsbnDbKey
        self.GrKey = GrKey
        
        
    def connectToAPI(self, base_url, *args):
        """
        :param base_url: the base url used to connect to ISBNdb API  
        :param args: the parameters for the ISBNdb API methods
        """
        response = cStringIO.StringIO()    
        c = pycurl.Curl()
        values = [("access_key", self.IsbnDbkey)]
        
        if args:
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
   
  
    def _pairwiseArgs(self,iterable):
        
        from itertools import izip
        a = iter(iterable)
        return izip(a, a)
        
    
    def getISBN(self,title):
        """
        :param: book title
        Given a book title, call the Goodreads parser and get the ISBN 
        of the top-ranked result. Goodreads will tolerate keyword searches
        for titles.  
        
        """
        from goodReadsApiParser import goodReadsApiParser as gr
        gr_instance = gr(self.GrKey)
        return str(gr_instance.getISBN(title))
    
     
    
    
    
    def _getTitleCategory(self,title=None, isbn = None):
        import re
        """
        :param title: book title
        :param isbn: ISBN of a particular books
        
        Helper function for getTitleGenre.
        Parameter title is passed to getISBN() which connects
        to the Goodreads API to get the top-ranked ISBN
        for that title.
        """
        final_title_categories = []
        if not isbn:
            isbn = self.getISBN(title)
       
        xml = self.connectToAPI("http://isbndb.com/api/books.xml", "results","subjects", 
                                "index1", "isbn","value1",isbn)
        
        
        #return self.getISBN(title)
        tree = ET.fromstring(xml)
        categories = [category for category in tree.getiterator("Subject")]
        
        #return xml
        for i in categories:
            category = i.text
            category =re.sub(r"Amazon.com -- ", " ", category)
            if "Authors, A-Z" in category: #no genre information, so don't return this
                continue
            final_title_categories.append(category)
        return final_title_categories
           
             
        
    def _getAuthorCategory(self, author):
        """
        :param author: author
        
        Since ISBNdb does not provide author info
        """
        category_set = []
        from goodReadsApiParser import goodReadsApiParser as gr
        import itertools
        gr_instance = gr(self.GrKey)
        author_id = str(gr_instance.getAuthorId(author)) #get the gr id
        xml = gr_instance.connectToGoodreads("http://www.goodreads.com/author/list/"+author_id+".xml")#paginate the author's books
        #get the isbn of the first book returnedl ex, for the shining it's 0450040186
        tree = ET.fromstring(xml)
        categories = [category for category in tree.getiterator("isbn")]
        isbns= [i.text for i in categories]
        
        #return a list of isbns
        

        for i in isbns[:5]:
            for returned_genre in self._getTitleCategory(isbn = i):
                category_set.append(returned_genre.title())
                continue  #don't break on a returned value of None
        #category_set = set(category_set)
            
        
        return category_set
     
    
    
    def getBookAuthor(self, title):
        """
        :param title: title
        
        Given a book title, returns the  author of that book 
        using the getAuthor() method of goodReadsApiParser.py
        
        """
        from goodReadsApiParser import goodReadsApiParser as gr
        gr_instance = gr(self.GrKey)
        return str(gr_instance.getAuthor(title))
    

    def getAuthorGenre(self, author):
        
        
        """
        :param author: author
        
        Given an author name, returns the categories of the first 3 top-ranked
        books written by the author. 
        """
        excluded = string.digits+'()&'
        try:
            
            if self._getAuthorCategory(author): 
                
                genres = list(set([item.strip(" ") for sublist in [i.split("--") for i in list(self._getAuthorCategory(author))] for item in sublist]))
                for genre in genres:
                    if 1 in [ch in genre for ch in excluded]:
                        genres.remove(genre)
                return genres
            else:
                return "None found"
        except:
            return "None found"

    def getTitleGenre(self, title):
        
        """
        :param title: book title
        
        Given a book title or ISBN, get that book's set of categories.  
        ISBNdb provides categories extracted from Amazon.com's book
        information.  
        """
        excluded = string.digits+'()-'
        try:
            if self._getTitleCategory(title): 
                genres= list(set([item.strip(" ") for sublist 
                                 in [i.split("--") for i in self._getTitleCategory(title)] for item in sublist]))
                for genre in genres:
                    if 1 in [ch in genre for ch in excluded]:
                        genres.remove(genre)
                
                return genres
            else:
                return "None found"
        except:
            return "None found"
        


def demo(): 
    print "#"*70, '\n'
    obj = IsbndbApiParser(isbn_key, goodreads_key)
    print 'Genres for title "Jonathan Strange and Mr. Norrell" :', obj.getTitleGenre("Jonathan Strange and Mr. Norrell"), '\n'
    #print "#"*70, '\n' 
    #print 'Genres for author "Raymond Chandler" :', obj.getAuthorGenre("Raymond Chandler"), '\n'
    print "#"*70, '\n'
    print 'Author of "The Big Sleep": ', obj.getBookAuthor("The Big Sleep") 

if __name__ == '__main__': 
    demo() 

