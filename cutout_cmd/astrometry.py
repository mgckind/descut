"""

A collection of useful functions in astrometry. The functions ported
here correspond to a subset of inhereted from Felipe Menanteau's
astrometry.py old library. Removed all wcs/header transformations as
this are better handled by Erin Sheldon wcsutil

The functions will:
     - format decimal <---> DDMMSS/HHMMMSS
     - greater circle distance(ra,dec)
     - area in polygon

 Requires:
     numpy

 Felipe Menanteau, Apr/Oct 2014
 
"""


def circle_distance(ra1,dec1,ra2,dec2,units='deg'):
    """
    Calculates great-circle distances between the two points that is,
    the shortest distance over the earth's surface using the Haversine
    formula, see http://www.movable-type.co.uk/scripts/latlong.html
    """
    import numpy
    from math import pi
    
    cos   = numpy.cos
    sin   = numpy.sin
    acos  = numpy.arccos
    asin  = numpy.arcsin
    
    if units == 'deg':
        ra1  = ra1*pi/180.
        ra2  = ra2*pi/180.
        dec1 = dec1*pi/180.
        dec2 = dec2*pi/180.

    x = sin(dec1)*sin(dec2) + cos(dec1)*cos(dec2) * cos(ra2-ra1)
    x = numpy.where(x>1.0, 1, x) # Avoid x>1.0 values
    
    d = acos(x)
    if units == 'deg':
        d=d*180.0/pi
    return d

def deg2dec(deg,sep=":"):
    """
    Degrees to decimal, one element or list/array object.
    """
    if hasattr(deg,'__iter__'):
        return [deg2dec_one(d,sep=sep) for d in deg]
    else:
        return deg2dec_one(deg,sep=sep)
    return

def deg2dec_one(deg,sep=":"):
    """
    Degrees to decimal, one element only.
    It should be generalized to an array or list of string.
    """
    vals = deg.split(sep)
    dd = float(vals[0])
    mm = float(vals[1])/60.
    ss = float(vals[2])/3600.
    if dd < 0 or vals[0] == '-00' or vals[0] == '-0':
        mm = -mm
        ss = -ss
    return dd + mm + ss

def dec2deg(dec,sep=":",plussign=False,short=False,sectol=1e-3):

    """
    From decimal to degress, array or scalar
    """

    import numpy
    import sys
    import math

    # Make it a numpy object if iterable
    if hasattr(dec,'__iter__'):
        dec = numpy.asarray(dec)
        # Keep the sign for later
        sig = numpy.where(dec < 0, -1, +1)
        dd = abs(dec.astype("Int32"))
        mm = (abs(dec-dd)*60).astype("Int32")
        ss = (abs(dec-dd)*60 - mm)*60
        # Truncating ss < 0.001
        ids = numpy.where(abs(ss-60.) <= sectol)
        ss[ids] = 0.0
        mm[ids] = mm[ids] + 1
        
        # Make an numpy array structures -- probably unnecessary
        x  =  numpy.concatenate((sig,dd,mm,ss))
        # re-shape
        x = numpy.resize(x,(4,len(dec)))
        x = numpy.swapaxes(x,0,1)
        return [format_deg(element,short=short,sep=sep,plussign=plussign) for element in x]

    else:
        sig = math.copysign(1,dec)
        dd = int(dec)
        mm = int( abs(dec-dd)*60.)
        ss = (abs(dec-dd)*60 - mm)*60
        
        if float(abs(ss-60.)) < sectol :
            ss = 0.0
            mm = mm + 1
        return format_deg((sig,dd,mm,ss),short=short,sep=sep,plussign=plussign)

    return


def format_deg(x,short=False,sep=":",plussign=False):

    sign,dd,mm,ss = x

    if sign < 0:
        sig = "-"
    else:
        if plussign:     sig = "+"
        if not plussign: sig = "" 

    # Zero padded formatting for fields
    f1 = "%02d"
    f2 = sep+"%02d"
    f3 = sep+"%04.1f" 

    if short=='ra':
        format = sig+f1+sep+f2+".%1d"
        return format % (abs(dd),mm,int(ss/6))
    
    elif short:
        format = sig+f1+sep+f2
        return format % (abs(dd),mm)

    format = sig + f1+ sep +f2+ sep +f3
    return format % (abs(dd),mm,ss)

def sky_area(ra,dec,units='degrees'):

    """
    Based on: 'Computing the Area of a Spherical Polygon" by Robert D. Miller
    in "Graphics Gems IV', Academic Press, 1994
    
    http://users.soe.ucsc.edu/~pang/160/f98/Gems/GemsIV/sph_poly.c
    
    Translated from J.D. Smith's IDL routine spherical_poly_area
    Returns the area (solid angle) projected in the sky by a polygon with
    vertices (ra,dec) in degrees
    
    Doesn't work well on wide range of RA's
    """
    
    import math
    import numpy

    sterad2degsq = (180/math.pi)**2 # sterad --> deg2
    RADEG  = 180.0/math.pi          # rad    --> degrees
    HalfPi = math.pi/2.
    lam1   = ra/RADEG
    lam2   = numpy.roll(lam1,1)
    beta1  = dec/RADEG
    beta2  = numpy.roll(beta1,1)
    cbeta1 = numpy.cos(beta1)
    cbeta2 = numpy.roll(cbeta1,1)

    HavA=numpy.sin((beta2-beta1)/2.0)**2 + cbeta1*cbeta2*numpy.sin((lam2-lam1)/2.0)**2
    
    A= 2.0*numpy.arcsin(numpy.sqrt(HavA))         
    B= HalfPi-beta2              
    C= HalfPi-beta1              
    S= 0.5*(A+B+C)                
    T = numpy.tan(S/2.0) * numpy.tan((S-A)/2.0) * numpy.tan((S-B)/2.0) * numpy.tan((S-C)/2.0)

    lam = (lam2-lam1) + 2.0*math.pi*(numpy.where( lam1 >= lam2, 1, 0 ))

    Excess = numpy.abs(4.0*numpy.arctan(numpy.sqrt(numpy.abs(T)))) * (1.0 - 2.0*(numpy.where(lam > math.pi, 1.0 ,0.0 )))

    area = abs((Excess*numpy.where(lam2 != lam1,1,0)).sum())
    if units == 'degrees':
        area = area*sterad2degsq

    return area


def get_pixelscale(header,units='arcsec'):
    """
    Returns the pixel-scale from the CDX_X matrix in an WCS-compiant header
    """
    import math
    if units == 'arcsec':
        scale = 3600
    elif units == 'arcmin':
        scale = 60
    elif units == 'degree':
        scale = 1
    else:
        raise ValueError("must define units as arcses/arcmin/degree only")

    CD1_1 = header['CD1_1']
    CD1_2 = header['CD1_2']
    CD2_1 = header['CD2_1']
    CD2_2 = header['CD2_2']
    return scale*math.sqrt( abs(CD1_1*CD2_2-CD1_2*CD2_1) )

def update_wcs_matrix(header,x0,y0,naxis1,naxis2):
    
    """
    Update the wcs header object with the right CRPIX[1,2] CRVAL[1,2] for a given subsection
    """

    import copy
    from despyastro import wcsutil

    # We need to make a deep copy/otherwise if fails
    h = copy.deepcopy(header)
    # Get the wcs object
    wcs = wcsutil.WCS(h)
    # Recompute CRVAL1/2 on the new center x0,y0
    CRVAL1,CRVAL2 = wcs.image2sky(x0,y0)
    # Asign CRPIX1/2 on the new image
    CRPIX1 = int(naxis1/2.0)
    CRPIX2 = int(naxis2/2.0)
    # Update the values
    h['CRVAL1'] = CRVAL1
    h['CRVAL2'] = CRVAL2
    h['CRPIX1'] = CRPIX1
    h['CRPIX2'] = CRPIX2
    return h
