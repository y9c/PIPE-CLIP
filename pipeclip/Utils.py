#!/usr/bin/python
# programmer: beibei.chen@utsouthwestern.edu
# Usage: definition of utilities to handel pysam classes

import logging
import subprocess
import sys

from . import Alignment

try:
    assert sys.version_info > (3, 6)
except AssertionError:
    raise RuntimeError("Requires Python 3.6+!")


def get_logger(name: str) -> logging.Logger:
    """global logging."""
    logger: logging.Logger = logging.getLogger(name)
    if not logger.handlers:
        handler: logging.StreamHandler = logging.StreamHandler()
        formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        #  logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.INFO)
    return logger


LOGGER: logging.Logger = get_logger(__name__)


def is_sorted(header):
    """Get a BAM header, and check if this file is sorted or not
    Return: True: sorted, False: unsorted
    Header variable is a list
    """
    for row in header.split("\n"):
        buf = row.rstrip().split("\t")
        if buf[0] == "@HD":
            if buf[2] in ["SO:unsorted", "SO:unknown"]:
                return False
            elif buf[2] in ["SO:coordinate", "SO:queryname"]:
                return True
    # If no HD header contains SO info, return False
    return False


def readQuaFilter(read, mlen, mis):
    matchlen = 0
    mismatch = 0
    # LOGGER.debug("read %s,cigar %s,tags %s" % (read.qname,read.cigar,read.tags))
    try:
        for i in read.cigar:
            # LOGGER.debug(i)
            if i[0] == 0:
                matchlen += i[1]
            elif i[0] == 1:
                mismatch += i[1]
        for j in read.tags:
            if j[0] == "NM":
                mismatch += j[1]
                break
        # LOGGER.debug("matchlen %d,mismatch %d" % (matchlen,mismatch))
    except:
        # LOGGER.debug("Problematic read %s" % (read))
        pass
    if matchlen >= mlen and mismatch <= mis:
        return (True, matchlen, mismatch)
    else:
        return (False, 0, 0)


def rmdupKey_Start(read):
    # print >>sys.stderr,"Remove duplicate by alignment start"
    k = str(read.tid) + ":" + str(read.pos) + ":" + str(read.is_reverse)
    # print >>sys.stderr,k
    return k


def rmdupKey_Seq(read):
    k = (
        str(read.tid)
        + ":"
        + str(read.pos)
        + ":"
        + str(read.is_reverse)
        + ":"
        + read.seq
    )
    return k


def filterMutations(mlist, feature, keep=True):
    newList = []
    for i in mlist:
        if i.type == feature:
            if keep:
                newList.append(i)
        else:
            if not keep:
                newList.append(i)
    return newList


def annotation(fileaddr, species):
    """Call Homer annotation script."""
    outfile = open(fileaddr + ".anno", "w")
    args = ["annotatePeaks.pl", fileaddr, species]
    p = subprocess.Popen(args, stdout=outfile)
    stdout_value = p.communicate()[0]
    outfile.close()


def makeWig(bamfile):
    wig = {}
    for r in bamfile.references:
        wig[r] = {}
        for pileupColumn in bamfile.pileup(r):
            wig[r][str(pileupColumn.pos)] = pileupColumn.n
    return wig


def makeWigByChr(bamfile, chr):
    wig = {}
    for pileupColumn in bamfile.pileup(chr):
        wig[pileupColumn.pos] = pileupColumn.n
    return wig


def makeWigListByChr(bamfile, chr):
    wig = Alignment.wiglist()
    for pileupColumn in bamfile.pileup(chr):
        wig.update(pileupColumn.pos, pileupColumn.n)
    return wig


def makeWigListByChr_array(bamfile, chr, chrlen):
    wig = []
    for _ in range(chrlen):
        wig.append(0)
    for pileupColumn in bamfile.pileup(chr):
        wig[pileupColumn.pos] = pileupColumn.n
    return wig


def bisort(alist, b):
    """List is a list of bed instances, b is also an instance."""
    if isinstance(alist[0], Alignment.BED) and isinstance(b, Alignment.BED):
        pass
