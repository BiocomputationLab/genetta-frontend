from Bio import Align
from Bio.Seq import Seq

class Aligner:
    def __init__(self):
        self._aligner = Align.PairwiseAligner()
        self._aligner.mode = 'global'
        self._aligner.substitution_matrix = Align.substitution_matrices.load("BLOSUM62")
        self._aligner.match_score = 1.0 
        self._aligner.mismatch_score = -1.0
        self._p_diff_threshold = 60

    def sequence_match(self,seq1,seq2):
        seq1 = self._cast_seq(seq1)
        seq2 = self._cast_seq(seq2)
        return self._aligner.score(seq2,seq1)/len(max([seq2,seq1], key=len))

    def string_length_diff(self,len1,len2):
        '''
        If difference length of sequence sizes 
        is past a threshold dont consider.
        '''
        try:
            p_diff = (abs(len1 - len2) / 
                        max(len1, len2)) * 100
        except ZeroDivisionError:
            p_diff = 0
        return p_diff > self._p_diff_threshold

    def _cast_seq(self,seq):
        return Seq(seq.lower().replace("\n", "").replace("\t", "").replace(" ", ""))
    
aligner = Aligner()