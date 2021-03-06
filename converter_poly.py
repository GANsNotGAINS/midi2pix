import music21
import sys
import numpy as np
import os
from scipy.misc import imsave
import math

class MIDI2PIXConverter():

    def __init__(self, input_file, format, resolution=5, column_length=.25):
        self.input_file = input_file
        self.score = music21.converter.parse(input_file, format=format)
        self.wholeLength = 4
        self.lengths = [self.wholeLength / (2**i) for i in range(resolution)]
        self.octaveRange = 2
        self.minNote = 60
        self.noteRange = 12 * self.octaveRange
        self.maxNote = self.minNote + self.noteRange
        # 1 means each column is a quarter note, .5 means eight note (following music21 convetion)
        self.column_length = column_length
        # Inverse of the fraction, 2 for eigth notes, 4 for sixteenth ect..
        self.multiplier = 1 / self.column_length

    def buildImage(self, saveImage=True):
        maxDuration = 0
       
        for score in self.score.parts:
            duration = 0
            note_rest_iterator = score.recurse().notesAndRests
            for note in note_rest_iterator:
                duration += note.duration.quarterLength
            maxDuration = max(maxDuration, duration)
        
        print(maxDuration)
        maxDuration *=  self.multiplier
        
        output = np.zeros((int(maxDuration), int(self.noteRange) + 1, 3), dtype=int)

        i = 0
        # Iterate through all
        # each column is a eigth note
        # use componentStartTime
        # Red, 0/255 if that is being played
        # Green  0/255 based on if note is ending (255 to hold, 0 to end)
        # Blue 0 - 255 if it's a rest or not. Fractions define which score is resting
        # TODO what does rest + notes mean in a single column
        # TODO do we need to differentiate streams
        # TODO chords
        # TODO maybe longer range of notes
        for i in range(len(self.score.parts)):
            score = self.score.parts[i]
            start = 0
            note_rest_iterator = score.recurse().notesAndRests
            for note in note_rest_iterator:
                                
                end =  start + note.duration.quarterLength * self.multiplier
                end = int(math.floor(end))
                
                if not note.isRest:
                    index = self.getNoteIndex(note) + 1 # rest is index 0
                # Red and blue are 
                # Iterate and set notes until the last time step of the dict
                for i in xrange(start, end - 1):                
                    if note.isRest:
                        output[i][0] = (0, 0, 255)
                    else:
                        output[i][index] = (255, 255, 0)
                if not note.isRest:
                    # Signal end of note
                    output[end - 1][index] = (255, 0, 0)
                start = end


        transpose = np.array(output).transpose(1, 0, 2)

        if saveImage:
            imageName = 'images/' + os.path.basename(self.input_file).split('.')[0] + '.png'
            imsave(imageName, transpose)

        return transpose

    def getNoteIndex(self, note_rest):
        note = None
        if note_rest.__module__ == 'music21.chord':
            note = note_rest.pitches[-1].midi
        elif hasattr(note_rest, 'getFirst'):
            print("get first")
            note = note_rest.getFirst().pitch.midi
        else:
            note = note_rest.pitch.midi

        return self.scaleNoteToRange(note) - self.minNote
    def scaleNoteToRange(self, noteMidi):
        while noteMidi >= self.maxNote:
            noteMidi -= 12

        while noteMidi < self.minNote:
            noteMidi += 12

        return noteMidi
    # this is bad, but we don't want triplets bc it makes state space bigger
    # even though they're sparse af
    def roundFraction(self, num):
        if hasattr(num, '__module__') and num.__module__ != 'fractions':
            return num

        deltas = [abs(length - float(num)) for length in self.lengths]
        min_delta_index = min(range(len(deltas)), key=deltas.__getitem__)

        return self.lengths[min_delta_index]

import glob
import sys, traceback

files = glob.glob('in/*.mxl')
for f in files:
    try:
        c = MIDI2PIXConverter(f, 'musicxml')
        c.buildImage()
    except:
        print("Failed for " + f)
        traceback.print_exc(file=sys.stdout)