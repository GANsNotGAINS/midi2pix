import music21
import sys
import numpy as np
import os
from scipy.misc import imsave


class MIDI2PIXConverter():
    # currently only works on

    def __init__(self, input_file, format, resolution=5):
        self.input_file = input_file
        self.score = music21.converter.parse(input_file, format=format)
        self.wholeLength = 4
        self.lengths = [self.wholeLength / (2**i) for i in range(resolution)]
        self.octaveRange = 2
        self.minNote = 60
        self.noteRange = 12 * self.octaveRange
        self.maxNote = self.minNote + self.noteRange

    def buildImage(self, saveImage=True):
        main_score = self.score.parts[0]
        note_rest_iterator = main_score.recurse().notesAndRests

        output = []

        i = 0
        for note_rest in note_rest_iterator:
            col = [(0,0,0) for _ in range(self.noteRange)]
            # hoping there are no tied whole notes...
            scaled_length = int(self.roundFraction(note_rest.duration.quarterLength) * 255 / self.wholeLength)
            if note_rest.isRest:
                col[0] = (scaled_length, 0, 0)
            else:
                note = None
                if note_rest.__module__ == 'music21.chord':
                    note = note_rest.pitches[-1].midi
                elif hasattr(note_rest, 'getFirst'):
                    print("get first")
                    note = note_rest.getFirst().pitch.midi
                else:
                    note = note_rest.pitch.midi

                index = self.scaleNoteToRange(note) - self.minNote
                col[index] = (0, 0, scaled_length)

            i += 1
            output.append(col)

        transpose = np.array(output).transpose(1, 0, 2)

        print(transpose.shape)

        if saveImage:
            imageName = os.path.splitext(self.input_file)[0] + '.png'
            imsave(imageName, transpose)

        return transpose

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


c = MIDI2PIXConverter('song.mxl', 'musicxml')
c.buildImage()