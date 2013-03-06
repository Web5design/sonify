#!/usr/bin/python
import sys
import math
import argparse
import Image
from itertools import *  # used for count()

from matplotlib import pyplot as pl     # Use for plotting only
import wavebender as wb
# Define the musical scale (note, Hertz)
scale = ['A3', 'B3', 'C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5']
tones = [220.00, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.26, 698.46, 783.99, 880.00] # in Hertz
notes = dict(zip(scale,tones))

def plot_histogram(im):
    pl.plot(im.histogram())
    pl.title("Pixel Counts by color value for all bands.")
    if im.mode == 'RGB':
        pl.xlabel("Color: R(0-255), B(256-511), G(512-767)")
    elif im.mode == 'YCbCr':
        pl.xlabel("Color: Y(0-255), Cb(256-511), Cr(512-767)")
    pl.ylabel("Number of Pixels")
    pl.yscale("log")
    pl.show()

def phi_from_YCbCr(im):
    """From (Y,Cb,Cr), get (phi,rad,lum).

    Read in (Y,Cb,Cr) from each pixel of the
    input image.  Convert each pixel value to
    (phi, rad, lum).  These correspond to the 
    rotation around the color wheel, distance
    from the center, and black/white brightness.

    Returns a 3-tuple of 1D lists.  Spatial information
    of the image is lost, and a flattened list is returned.
    """
    # This may not be the fastest method.
    # Consider using im.getdata() or im.split() or colorsys.rgb_to_yiq(r, g, b).
    phi, rad, lum = [], [], []
    pix = im.load()
    for x in range(im.size[0]):
        for y in range(im.size[1]):
            L, Cb, Cr = pix[x,y]
            Cb = Cb - 128                           # Offset so values range from [-128,127].
            Cr = Cr - 128
            if Cb == 0:                             # Ensure no divide-by-zero in atan().
                Cb = 1                    
            if Cr == 0: 
                Cr = 1
            lum.append(L)
            rad.append(math.sqrt(Cb*Cb + Cr*Cr))
            phi0 = math.atan(Cr/Cb)
            if Cb >= 0 and Cr >= 0:
                phi.append(phi0)
            elif Cb < 0 and Cr >= 0:
                phi.append(phi0 + math.pi)
            elif Cb < 0 and Cr < 0:
                phi.append(phi0 + math.pi)
            else:
                phi.append(phi0 + 2*math.pi)
    return phi, rad, lum

def print_statistics(im):
    print "\nThe color mode for this image is %s." % im.mode
    bands = im.getbands()
    print "The %d bands in this image are %s." % (len(bands), bands)
    thisPix = im.getpixel((2, 2))    # slow.  use .load() instead.
    print "Color values for pixel(2,1) are %s" % str(thisPix)
    size = im.size
    print "The image is %d by %d pixels in size (%d total)." % (size[0], size[1], size[0]*size[1])
    colors = im.getcolors(maxcolors=size[0]*size[1])
    print "There are %d unique colors in this image." % len(colors)
    flatSequence = im.getdata()
    print "When flattened, the image is %d pixels long." % len(flatSequence)
    extrema = im.getextrema()
    minmax = ""
    for b in range(len(bands)):
        minmax += bands[b]
        minmax += ':'
        if len(bands) == 1:
            minmax += str(extrema)
        else:
            minmax += str(extrema[b]) + ' '
    print "The min/max for the colors are %s." % minmax

def get_amplitudes(phi, binCount=15, showPlot=False):
    n, bins, patches = pl.hist(phi, binCount, log=True)
    nMax = math.log10(max(n))
    amp = []
    for val in n:
        if val == 0:
            amp.append(0)
        else:
            amp.append(math.log10(val) / nMax)
    if showPlot:
        pl.xlabel('$\phi$ Tone Parameter')
        pl.ylabel('Number of Pixels')
        pl.show()
    return amp

def super_sine_wave(freqs=[440.0], framerate=8000, amps=[0.5]):
    '''
    Generate a superposition of sine waves given a set of frequencies and amplitudes.
    '''
    for j in range(len(amps)):
        if amps[j] > 1.0: amps[j] = 1.0
        if amps[j] < 0.0: amps[j] = 0.0
    for i in count(0):
        superposition = 0.0
        for w in range(len(freqs)):
            sine = math.sin(2.0 * math.pi * float(freqs[w]) * (float(i) / float(framerate)))
            superposition += float(amps[w]) * sine
        yield superposition / float(len(freqs))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rate', help="Sample rate in Hz", default=8000, type=int)
    parser.add_argument('-t', '--time', help="Duration of the wave in seconds.", default=4, type=int)
    parser.add_argument('-v', '--verbose', help="Print information to screen. Dont use if piping stdout to aplay!", action='store_true')
    parser.add_argument('-p', '--plot', help="Plot the power spectruem", action='store_true')
    parser.add_argument('-o', '--outfile', help="The .wav file to generate. Type '-' for stdout.", default=None, type=str)
    parser.add_argument('infile', help="The image file to read in. Type '-' to use test.jpg")
    args = parser.parse_args()
    
    if args.outfile == None:
        outfile = sys.stdout
    else:
        outfile = args.outfile

    # Open image file and read in the image.
    imOrig = Image.open(args.infile)
    if imOrig.mode != 'RGB':
        raise Exception('Not RGB.  %s is invalid.' % imOrig.mode)
    imR, imG, imB = imOrig.split()                  # Split into three images (one for each band).
    imYCbCr = imOrig.convert("YCbCr")                       # Convert the image to YCbCr
    imY, imCb, imCr = imYCbCr.split()                  # Split into three images (one for each band).

    if args.verbose:
        print_statistics(imOrig)
        print_statistics(imR)
        print_statistics(imG)
        print_statistics(imB)
        print_statistics(imYCbCr)
        print_statistics(imY)
        print_statistics(imCb)
        print_statistics(imCr)

    phi, rad, lum = phi_from_YCbCr(imYCbCr)
    amps = get_amplitudes(phi, showPlot=args.plot)

    #channels = ((wb.sine_wave(notes['A4'], amplitude=0.8, framerate=args.rate),),)
    channels = ((super_sine_wave(freqs=tones, amps=amps, framerate=args.rate),),)
    samples = wb.compute_samples(channels, nsamples=args.rate*args.time)
    wb.write_wavefile(outfile, samples=samples, nframes=(args.rate*args.time), nchannels=1, framerate=args.rate)

if __name__ == "__main__":
    main()
