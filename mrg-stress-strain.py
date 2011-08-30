#!/usr/bin/python2

# Copyright 2011 Tim Hartman <tbhartman@gmail.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

version='alpha'

import argparse
import re
from collections import *
import datetime
import time
import sys
import tempfile
#import console
import os

# imports for mpl
import matplotlib as mpl
mpl.use('Agg')
from matplotlib import pyplot
#matplotlib.use('SVG')
from matplotlib.font_manager import fontManager, FontProperties

#terminal_width,_ = console.getTerminalSize()

def write_message(message, level=0):
    if args.verbose:
        if re.search('\r',message):
            sys.stdout.write(message)
            sys.stdout.flush()
        else:
            print(message, end="")

# argument parsing definitions

parser = argparse.ArgumentParser(prog='mrg-stress-strain',
                                 description='Plot from csv')
parser.add_argument('input',
                    metavar='INPUT',
                    help='csv file to parse',
                    nargs='*',
                    #type=argparse.FileType('r'),
                    )
parser.add_argument('-p', '--pause',
                    action='store_true',
                    dest='pause',
                    help='Give me some time, I\'m a little slow')
parser.add_argument('-n', '--dry-run',
                    action='store_true',
                    dest='dry',
                    help='Just show files to be processed')
parser.add_argument('-f', '--force',
                    action='store_true',
                    dest='force',
                    help='Force rewrite of old files')
parser.add_argument('-a', '--all',
                    action='store_true',
                    dest='all',
                    help='Run all files (even if not csv)')
parser.add_argument('-V', '--verbose',
                    action='store_true',
                    dest='verbose',
                    help='Be verbose')
parser.add_argument('-v', '--version',
                    action='version',
                    version='%(prog)s ' + version)
args = parser.parse_args()

csvs = []
csvs_update = []

ext = {}
ext['csv'] = 'tsv'
ext['plot'] = 'pdf'

def check_uptodate(filename):
    mtime={}
    basename = os.path.splitext(filename)[0]
    #mtime['csv'] = os.stat(basename + '.' + ext['csv']).st_mtime
    mtime['csv'] = os.stat(filename).st_mtime
    if os.path.exists(basename + '.' + ext['plot']):
        mtime['plot'] = os.stat(basename + '.' + ext['plot']).st_mtime
    else:
        mtime['plot'] = 0
    if mtime['plot'] >= mtime['csv']:
        return True
    else:
        return False

regex = {}
regex['csv'] = re.compile('\.' + ext['csv'] + '$')

if args.all:
    write_message('Skipping check for .' + ext['csv'] + ' extension...\n')

def check_for_csv(filename):
    if os.path.isdir(filename):
        for subfile in os.listdir(filename):
            check_for_csv(os.path.join(filename,subfile))
    else:
        if args.all or regex['csv'].search(filename):
            csvs.append(filename)
            if args.force or not check_uptodate(filename):
                csvs_update.append(filename)

for filename in args.input:
    check_for_csv(filename)
            

write_message(("Found {:d} " + ext['csv'].upper() + " file(s).\n").format(len(csvs)))
write_message(("Updating {:d} " + ext['csv'].upper() + " file(s).\n").format(len(csvs_update)))

def plot(data):
    sp_adjust = {'bottom':0.1,'top':0.9,'left':0.1,'right':0.9}
    fig = mpl.pyplot.figure(figsize=(16,8))
    fig.subplots_adjust(**sp_adjust)

    stroke = fig.add_subplot(132)
    strain = stroke.twinx()
    strain.yaxis.set_label_position('left')
    strain.yaxis.set_ticks_position('left')
    strain.set_frame_on(True)
    strain.spines["left"].set_position(("axes",-0.3))
    strain.patch.set_visible(False)
    for sp in strain.spines.itervalues():
        sp.set_visible(False)
    strain.spines['left'].set_visible(True)
    
    load = stroke.twinx()
    load.yaxis.set_label_position('left')
    load.yaxis.set_ticks_position('left')
    load.spines['left'].set_visible(True)
    load.set_frame_on(True)
    load.spines["left"].set_position(("axes",-0.6))
    load.patch.set_visible(False)
    for sp in load.spines.itervalues():
        sp.set_visible(False)
    load.spines['left'].set_visible(True)

    stroke_kwargs = {'label':'Stroke','color':(0.7,0.7,0.7)}
    stroke_p, = stroke.plot(data['datetime'],data['stroke'],**stroke_kwargs)
    load_p, = load.plot(data['datetime'],data['load'],'b-',label='Load')
    strain_p, = strain.plot(data['datetime'],data['strain'],'r-',label='Strain')
    lines = [load_p, strain_p, stroke_p]
    stroke.legend(lines, [l.get_label() for l in lines],loc=2)
    stroke.grid(True)
    #load.set_ylim(0.5,-0.5)
    stroke.set_xlabel('Time (s)')
    load.set_ylabel('Load')
    strain.set_ylabel('Strain')
    stroke.set_ylabel('Stroke')

    load.yaxis.label.set_color(load_p.get_color())
    strain.yaxis.label.set_color(strain_p.get_color())
    stroke.yaxis.label.set_color(stroke_p.get_color())
    load.tick_params(axis='y',colors=load_p.get_color())
    strain.tick_params(axis='y',colors=strain_p.get_color())
    stroke.tick_params(axis='y',colors=stroke_p.get_color())

    ax = fig.add_subplot(133)
    ax.plot(data['strain'],data['load'],label='hi')
    #ax.legend(loc='best')
    ax.grid(True)
    #ax.set_ylim(0.5,-0.5)
    ax.set_xlabel('Strain')
    ax.set_ylabel('Load')

    mpl.pyplot.savefig(data['filename'] + '.' + ext['plot'])

if args.dry:
    write_message('Dry run, no processing...\n')
else:
    for filename in csvs_update:
        csv = open(filename,'r')
        write_message('\rParsing {:s}...'.format(csv.name))
        data = {}
        data['filename'] = os.path.splitext(filename)[0]
        data['datetime'] = []
        data['load'] = []
        data['stroke'] = []
        data['strain'] = []
        for line in csv:
            split = line.split('\t')
            this_time = float(split[0])
            if len(data['datetime']):
                this_time -= start_time
                this_time *= 60*60*24
            else:
                start_time = this_time
                this_time = 0
            data['datetime'].append(this_time)
            data['load'].append(split[1])
            data['stroke'].append(split[2])
            data['strain'].append(split[4])
        write_message('\rPlotting {:s}...'.format(csv.name))
        plot(data)
        write_message('\rFinished with {:s}.\n'.format(csv.name))


write_message('I was being verbose.\nSeriously.\n')
if args.pause:
    write_message('Fine, I\'ll give you some extra time...')
    time.sleep(3)
