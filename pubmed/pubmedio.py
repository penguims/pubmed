#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020,  Magic Fang, magicfang@gmail.com
#
# Distributed under terms of the GPL-3 license.

import re
import sys
import argparse
from xml.dom import minidom
from xml.dom import Node
import gzip

class Record(dict):
    """ Pubmed Article record class, inherit from dict class

    Original with below key, if the key value is missing in XML, it will be set to empty: "" or []
    PMID: Pubmed ID
    DateCompleted: Date completed, format: year-month-day
    DateRevised: Date revised, format: year-month-day
    ISSN: Journal ISSN number
    JournalTitle: Journal title
    ISOAbbreviation: ISO journal title abbreviation
    VolumeIssue:  Journal volume and issue, format: volume-issue
    PubDate: Journal published date, format: year-month
    Title: Article title
    Pagination: Article pagination
    Abstract: Article abstract
    Language: Language
    ELocationID: Eletronic Location ID
    AuthorList: Author list, 
      format: [[(collective name, '')|(full name, initial name), identifier|..., email|..., affiliation|...], ...]
    GrantList: Grant list, format: []
    MeshHeadingList: Mesh heading list: format: [uid:content, ...]
    ArticleIdList: Article ID list, format: [source:id, ...]
    PublicationStatus: Publication status
    ReferenceList: Reference list, format: [citation(articleid;id), ...]
    """
    # Some formats and key sets used in string or future
    FULL = False
    HEADER = False
    FULLCOLS = ('PMID', 'DateCompleted', 'DateRevised', 'ISSN', 'JournalTitle', 'ISOAbbreviation', 'VolumeIssue',
        'PubDate', 'Title', 'Pagination', 'Abstract', 'Language', 'ELocationID', 'PublicationStatus', 'AuthorList', 
        'GrantList', 'MeshHeadingList', 'ArticleIdList', 'ReferenceList')
    # Default __str__ output
    COLS = ('PMID', 'JournalTitle', 'VolumeIssue', 'ISSN', 'Title')
    # List attribute set
    LISTCOLS = ('GrantList', 'MeshHeadingList', 'ArticleIdList', 'ReferenceList')
    # Author list order
    AUTHCOLS = ('FullName', 'InitialName', 'Identifier', 'eMail', 'Affiliation')
    CONNECTOR = '\t'

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self[k] = v

    def __str__(self):
        rstr = []
        for col in self.COLS:
            if col in self:
                rstr.append(self[col])
            else:
                rstr.append('')
        return self.CONNECTOR.join(rstr)

class PubmedIO:
    """ Pubmed XML file parser

    Support file from: https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/
    from Bio import PubmedIO

    >>> pmio = PubmedIO(fn='pubmed20n001.xml')
    >>> for rec in pmio.parse():
    ...     print(rec)
    ...     print(rec['Abstract'])
        
    >>> pmio = PubmedIO(fn='pubmed20n001.xml.gz')
    >>> for rec in pmio.parse():
    ...     print(rec)
    ...     print(rec['Abstract'])
    >>> with open('pubmed20n001.xml') as fh:
    ...     pmio = PubmedIO(fh=fh)
    ...     for rec in pmio.parse():
    ...         print(rec)
    ...         print(rec['Abstract'])
    """
    def __init__(self, fn='', fh=None):
    """ PubmedIO in initiation

    fn: XML file name
    fh: XML file handle
    Support text or gzip XML file format to fh or fn, if not fn or fh
    would get string from sys.stdin
    """
        self.fn = fn
        self.fh = fh
        if self.fn:
            if self.fn.endswith('.gz'):
                self.fh = gzip.open(self.fn, "rb")
            else:
                self.fh = open(self.fn, "rt")
        elif not self.fh:
            self.fh = sys.stdin
        self.dom = minidom.parse(self.fh)

    def gotonode(self, path, pnode=None, index=0):
    """ Get XML DOM Node by given path
    
    path: path string, format: 'tag|subtag|...'
    pnode: parent node to find the target node by path
    index: if there is multi return node, which node to be retruned
    return target node by index

    >>> pmio = PubmedIO(fn='pubmed20n001.xml.gz')
    >>> pa = pmio.gotonode('PubmedArticleSet|PubedArticle', pnode=pmio.dom)

    """
        paths = path.split("|")
        node = pnode
        if not node:
            node = self.dom
        for p in paths:
            nodes = node.getElementsByTagName(p)
            if nodes:
                node = nodes[index]
            else:
                node = None
                break
        return node

    def childvalue(self, node, keys=[], connector="-", ifkey=False):
    """ Get child node text

    node: XML DOM node
    keys: child node(s) to get
    connector: connector to join multi node value
    ifkey: return tagname:value format result
    return: connected child value string
    
    >>> pmio = PubmedIO(fn='pubmed20n001.xml.gz')
    >>> dc = pmio.gotonode('PubmedArticleSet|PubedArticle|DateCompleted', pnode=pmio.dom)
    >>> date = pmio.childvalue(dc, keys=['Year', 'Month', 'Day'], connector='/')
    """
        rstrs = []
        if node:
            for c in node.childNodes:
                name, content = c.nodeName, ''
                if keys and not name in keys:
                    continue
                if c.nodeType == Node.ELEMENT_NODE:
                    cnodes = c.childNodes
                    if cnodes:
                        for cnode in cnodes:
                            if cnode.nodeType == Node.TEXT_NODE:
                                content = cnode.data.strip()
                if len(content)<=0:
                    continue
                if ifkey:
                    rstrs.append(name+":"+content)
                else:
                    rstrs.append(content)
        return connector.join(rstrs)

    def attrvalue(self, node, ifkey=False, keys=[], connector="-"):
    """ Get node attribute value

    Get node attribution value
    node: XML DOM node
    ifkey: return value with attribution tag, connector by ':'
    keys: attribution tag list 
    connector: connector to join multi attribution value
    return attribution value
    """
        rstrs = []
        if node:
            attrs = node.attributes
            if attrs:
                for item in attrs.items():
                    if keys and not item[0] in keys:
                        continue
                    if ifkey:
                        rstrs.append(item[0]+":"+item[1])
                    else:
                        rstrs.append(item[1])
        return connector.join(rstrs)

    def gettext(self, node, connector=' ', greedy=True):
    """ Get node text node value

    Get text string from a XML DOM node
    node: the DOM node
    connector: string connector to join multi text string
    greedy: not used yet
    return: text string
    """
        rstrs = []
        if node:
            for child in node.childNodes:
                if child.nodeType == Node.TEXT_NODE:
                    content = child.data.strip()
                    if len(content) <= 0:
                        continue
                # In aritcle title and abstract text string, there are <sub> or <sup> etc. tag
                # the method will get rid of them and leave the string inside
                elif child.nodeType == Node.ELEMENT_NODE:
                    content = self.childvalue(node, keys=[child.tagName])
                rstrs.append(content)
        return connector.join(rstrs)
    
    def getemail(self, src, emls):
    """ Get author email address

    Get email from a affiliation string
    src: Affiliation string
    emls: email list
    return: Cleaned affiliation string
    """
        ead = re.findall(r'([\w\d\.\-\_]+\@[\w\d\.\-\_]+)', src)
        if ead:
            for e in ead:
                e = re.sub(r'[\.\s]+$', '', e)
                emls[e] = 1
        src = re.sub(r'Electronic address:\s+', '', re.sub(r'[\w\d\.\-\_]+\@[\w\d\.\-\_]+', '', src))
        return src

    def getidens(self, src, ides):
    """ Get author identifiers

    Get ORCID identifier
    src: Identifier string
    ides: Identifiers list
    return: string get rid of identifer string
    """
        orcids = re.findall(r'ORCID:\s*([\w]{4}\-[\w]{4}\-[\w]{4}\-[\w]{4})', src)
        if orcids:
            for o in orcids:
                ides['ORCID:'+o] = 1
        src = re.sub(r'ORCID:\s*[\w]{4}\-[\w]{4}\-[\w]{4}\-[\w]{4}\.*', '', src)
        ocrids = re.findall(r'ORCID:\s*http[s]*:\/\/orcid\.org\/([\w]{4}\-[\w]{4}\-[\w]{4}\-[\w]{4})', src)
        if orcids:
            for o in orcids:
                ides['ORCID:'+o] = 1
        src = re.sub(r'ORCID:\s*http[s]*:\/\/orcid\.org\/[\w]{4}\-[\w]{4}\-[\w]{4}\-[\w]{4}', '', src)
        return src

    def getaffs(self, src, afs):
    """ Get author affilations

    Get and clean affilations, trim '.' and '\s' from the begin and end of an affiliation
    src: AffiliationInfo string, seperated by '|'
    afs: affiliation list
    return: length of affiliation list
    """
        tafs = re.split(r'[\;\|]', src)
        for a in tafs:
            a = re.sub(r'^[\.\s]+', '', a)
            a = re.sub(r'[\.\s]+$', '', a)
            afs[a] = 1
        return len(tafs)
    
    def abstract(self, node):
    """ Get article abstract

    node: XML DOM element, 'Article|Abstract'
    return: abstract text set. Paragraft join by '\n' character
    Below is a complex abstract content
    <Abstract>
      <AbstractText Label="OBJECTIVES">To evaluate and compare the diagnostic potential of <sup>18</sup> F-fluorodeoxyglucose positron emission tomography/magnetic resonance imaging (<sup>18</sup> FDG-PET/MRI) and MRI for recurrence diagnostics after primary therapy in patients with adenoid cystic carcinoma (ACC).</AbstractText>
      <AbstractText Label="METHODS">A total of 32 dedicated head and neck <sup>18</sup> F-FDG PET/MRI datasets were included in this analysis. MRI and <sup>18</sup> F-FDG PET/MRI datasets were analyzed in separate sessions by two readers for tumor recurrence or metastases.</AbstractText>
      <AbstractText Label="RESULTS">Lesion-based sensitivity, specificity, positive predictive value, negative predictive value and diagnostic accuracy were 96%, 84%, 90%, 93%, and 91% for <sup>18</sup> F-FDG PET/MRI and 77%, 94%, 95%, 73%, and 84% for MRI, resulting in a significantly higher diagnostic accuracy of <sup>18</sup> F-FDG PET/MRI compared to MRI (P &lt; .005).</AbstractText>
      <AbstractText Label="CONCLUSION"><sup>18</sup> F-FDG PET/MRI is superior to MRI in detecting local recurrence and metastases in patients with ACC of the head and neck. Especially concerning its negative predictive value, <sup>18</sup> F-FDG PET/MRI outperforms MRI.</AbstractText>
      <CopyrightInformation>© 2018 Wiley Periodicals, Inc.</CopyrightInformation>
    </Abstract>
    """
        rstr = []
        if node:
            for at in node.childNodes:
                label = self.attrvalue(at, keys=['Label'])
                content = self.gettext(at)
                if label:
                    rstr.append(label+":"+content)
                else:
                    rstr.append(content)
        return "\n".join(rstr)

    def authorlist(self, node):
    """ Get aruthor information, include full name, initial name, identifier, affiliation and email

    node: XML DOM element, 'Article|AuthorList'
    return: a list of authors with below format:
        [
            [(collective name, '')|(full name, initial name), identifier|..., affiliation|..., email|...],
            [...],
        ]
        identifier should be ORCID or other user identified ID
    Below is a sample:
      <Author ValidYN="Y">
        <LastName>Kirchner</LastName>
        <ForeName>Julian</ForeName>
        <Initials>J</Initials>
        <Identifier Source="ORCID">0000-0001-8224-3433</Identifier>
        <AffiliationInfo>
          <Affiliation>Department of Diagnostic and Interventional Radiology, University of Dusseldorf, Medical Faculty, Dusseldorf, Germany.</Affiliation>
        </AffiliationInfo>
      </Author>
      <Author ValidYN="Y">
        <LastName>Schaarschmidt</LastName>
        <ForeName>Benedikt M</ForeName>
        <Initials>BM</Initials>
        <AffiliationInfo>
          <Affiliation>Department of Diagnostic and Interventional Radiology, University of Dusseldorf, Medical Faculty, Dusseldorf, Germany.</Affiliation>
        </AffiliationInfo>
      </Author>
        ...
    """
        auths = []
        if node:
            for author in node.getElementsByTagName('Author'):
                auth, emls, affs, ides = [], {}, {}, {}
                austr = self.childvalue(author, keys=['CollectvieName'], connector=" ")
                if austr:
                    austr = self.getemail(austr, emls)
                    auth.append(austr)
                    auth.append('')
                else:
                    auth.append(self.childvalue(author, keys=['LastName', 'ForeName'], connector=" "))
                    auth.append(self.childvalue(author, keys=['LastName', 'Initials'], connector=" "))
                try:
                    iden = self.gotonode('Identifier', pnode=author)
                    if iden:
                        src = self.attrvalue(iden, keys=['Source'])
                        oid = self.gettext(iden, connector="|")
                        if src and oid:
                            ide = src+':'+oid
                            ide = self.getidens(ide, ides)
                    for affi in author.getElementsByTagName('AffiliationInfo'):
                        aff = self.childvalue(affi, keys=['Affiliation'], connector="|")
                        aff = self.getidens(aff, ides)
                        aff = self.getemail(aff, emls)
                        aff = self.getaffs(aff, affs)
                    auth.append('|'.join(list(ides.keys())))
                    auth.append('|'.join(list(affs.keys())))
                    auth.append('|'.join(list(emls.keys())))
                except:
                    auth.extend(['', '', ''])
                auths.append(auth)
        return auths

    def grantlist(self, node):
    """ Get grant list

    node: XML DOM element
    return: grant string list, format: [id:angency:country, ...]
    <GrantList CompleteYN="Y">
      <Grant>
        <GrantID>JCYJ20140903112959960</GrantID>
        <Agency>Shenzhen Basic Research Found</Agency>
        <Country>International</Country>
      </Grant>
      <Grant>
        <GrantID>JCYJ20140903112959960</GrantID>
        <Agency>Shenzhen Basic Research Fund</Agency>
        <Country>International</Country>
      </Grant>
    </GrantList>
    """
        grants = []
        if node:
            for grant in node.getElementsByTagName('Grant'):
                grants.append(self.childvalue(grant, connector=":"))
        return grants

    def meshheadinglist(self, node):
    """ Get mesh heading list

    node: XML DOM element
    return: grant string list, format: [ui:content, ...]
    <MeshHeadingList>
      <MeshHeading>
        <DescriptorName UI="D066300" MajorTopicYN="Y">Electronic Nicotine Delivery Systems</DescriptorName>
      </MeshHeading>
      <MeshHeading>
        <DescriptorName UI="D005060" MajorTopicYN="N" Type="Geographic">Europe</DescriptorName>
      </MeshHeading>
      <MeshHeading>
        <DescriptorName UI="D064424" MajorTopicYN="N">Tobacco Use</DescriptorName>
      </MeshHeading>
    <MeshHeadingList>
    """
        meshes = []
        if node:
            for mesh in node.getElementsByTagName('MeshHeading'):
                for tag in mesh.childNodes:
                    if tag.nodeType != Node.ELEMENT_NODE:
                        continue
                    meshes.append(self.attrvalue(tag, keys=['UI'])+":"+self.gettext(tag))
        return meshes

    def articleidlist(self, node):
    """ Get ariticle ID list

    node: XML DOM element
    return: grant string list, format: [type:id, ...]
    <ArticleIdList>
      <ArticleId IdType="pubmed">30571303</ArticleId>
      <ArticleId IdType="doi">10.2105/AJPH.2018.304813</ArticleId>
      <ArticleId IdType="pmc">PMC6336036</ArticleId>
    <ArticleIdList>
    """
        articleids = []
        if node:
            for aid in node.getElementsByTagName('ArticleId'):
                articleids.append(self.attrvalue(aid, keys=['IdType'])+":"+self.gettext(aid))
        return articleids

    def referencelist(self, node):
    """ Get reference list

    node: XML DOM element
    return: grant string list, format: [citation(id|...), ...]
    <ReferenceList>
      <Reference>
        <Citation>Nat Methods. 2009 Sep;6(9):639-41</Citation>
        <ArticleIdList>
          <ArticleId IdType="pubmed">19668203</ArticleId>
        </ArticleIdList>
      </Reference>
      <Reference>
        <Citation>Appl Environ Microbiol. 2010 Oct;76(20):6751-9</Citation>
        <ArticleIdList>
          <ArticleId IdType="pubmed">20729324</ArticleId>
        </ArticleIdList>
      </Reference>
    <ReferenceList>
    """
        refs = []
        if node:
            for ref in node.getElementsByTagName('Reference'):
                cit = self.childvalue(ref, keys=['Citation'])
                ids = self.gotonode('ArticleIdList', pnode=ref)
                aids = []
                if ids:
                    for aid in ref.getElementsByTagName('ArticleId'):
                        aids.append(self.attrvalue(aid, keys=['IdType'])+":"+self.gettext(aid))
                refs.append(cit+'('+'|'.join(aids)+')')
        return refs

    def parse(self):
    """ Parse Pubmed XML to Record object

    return: class Record() iteration list
    """
        rec = Record()
        for pa in self.dom.getElementsByTagName('PubmedArticle'):
            mc = pa.getElementsByTagName('MedlineCitation')[0]
            pd = pa.getElementsByTagName('PubmedData')[0]
            rec['PMID'] = "{:0>8s}".format(self.gettext(self.gotonode('PMID', pnode=mc)))
            rec['DateCompleted'] = self.childvalue(self.gotonode('DateCompleted', pnode=mc))
            rec['DateRevised'] = self.childvalue(self.gotonode('DateRevised', pnode=mc))
            rec['ISSN'] = self.gettext(self.gotonode('Article|Journal|ISSN', pnode=mc))
            rec['JournalTitle'] = self.gettext(self.gotonode('Article|Journal|Title', pnode=mc))
            rec['ISOAbbreviation'] = self.gettext(self.gotonode('Article|Journal|ISOAbbreviation', pnode=mc))
            rec['VolumeIssue'] = self.childvalue(
                self.gotonode('Article|Journal|JournalIssue', pnode=mc), keys=['Volume', 'Issue'])
            rec['PubDate'] = self.childvalue(self.gotonode('Article|Journal|JournalIssue|PubDate', pnode=mc))
            rec['Title'] = self.gettext(self.gotonode('Article|ArticleTitle', pnode=mc))
            rec['Pagination'] = self.childvalue(self.gotonode('Article|Pagination', pnode=mc), connector="|")
            rec['Abstract'] = self.abstract(self.gotonode('Article|Abstract', pnode=mc))
            rec['Language'] = self.gettext(self.gotonode('Article|Language', pnode=mc))
            rec['ELocationID'] = self.attrvalue(self.gotonode('Article|ELocationID', pnode=mc), keys=['EIdType']) + \
                ":" + \
                self.gettext(self.gotonode('Article|ELocationID', pnode=mc))
            rec['AuthorList'] = self.authorlist(self.gotonode('Article|AuthorList', pnode=mc))
            rec['GrantList'] = self.grantlist(self.gotonode('Article|GrantList', pnode=mc))
            rec['MeshHeadingList'] = self.meshheadinglist(self.gotonode('MeshHeadingList', pnode=mc))
            rec['ArticleIdList'] = self.articleidlist(self.gotonode('ArticleIdList', pnode=pd))
            rec['PublicationStatus'] = self.gettext(self.gotonode('PublicationStatus', pnode=pd))
            rec['ReferenceList'] = self.referencelist(self.gotonode('ReferenceList', pnode=pd))
            yield rec
            rec = Record()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile")
    parser.add_argument("-p", "--path")
    parser.add_argument("-l", "--level", type=int, default=0)
    parser.add_argument("-k", "--key", action="store_true")
    args = parser.parse_args()
    pio = PubmedIO(args.infile)
    for rec in pio.parse():
        rstr = str(rec)
        for author in rec['AuthorList']:
            print(rstr, "\t", "\t".join(author))

