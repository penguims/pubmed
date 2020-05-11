# pubmed
A pubmed xml file parser

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
