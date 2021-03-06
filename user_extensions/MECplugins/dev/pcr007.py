import                              string
import                              re
from math                           import log10,log
from Bio                            import SeqIO
from Bio.Seq                        import Seq
from Bio.Seq                        import reverse_complement
from Bio.Alphabet.IUPAC             import unambiguous_dna,ambiguous_dna
from Bio.SeqRecord                  import SeqRecord
from cStringIO                      import StringIO
from parse_string2                  import parse_string_into_formatted_records
from Bio.SeqUtils                   import GC
from Bio.SeqUtils.MeltingTemp       import Tm_staluc

def define_right_overlap(first_sequence,second_sequence):

    length = min(len(first_sequence),len(second_sequence))

    first_sequence  =  str(  first_sequence[ -( length) : ]).lower()
    second_sequence =  str( second_sequence[ -( length) : ]).lower()

    rghtpos=length
    leftpos=0

    while not (rghtpos-leftpos==1 or int(rghtpos)==0):

        if first_sequence[leftpos:rghtpos]==second_sequence[leftpos:rghtpos]:
            rghtpos=leftpos
            leftpos=(rghtpos)/2
        else:
            leftpos=(leftpos+rghtpos)/2

    if first_sequence[leftpos:rghtpos]==second_sequence[leftpos:rghtpos]:
        return length-leftpos
    else:
        return length-rghtpos

def annealing_positions(first_sequence,second_sequence,direction="forward",limit=13):
    
    assert type(direction) == str
    assert type(limit)     == int
    
    second_sequence=str(second_sequence).lower()
    three_end_part_of_first_sequence = str(first_sequence[-limit:]).lower()

    if direction =="forward":
        regex = '(?='+three_end_part_of_first_sequence+')'
        offset = limit
    elif direction =="reverse":
        regex = '(?='+reverse_complement(three_end_part_of_first_sequence)+')'
        offset=0
    else:
        raise Exception
    
    return [m.start()+offset for m in re.finditer(regex,second_sequence)]

class Primer(SeqRecord):
    def __init__(self, primer, annealing_position):
        assert type(primer) == SeqRecord
        primer.seq.alphabet = ambiguous_dna      
        SeqRecord.__init__(self,primer,primer.id,primer.name,primer.description)
        self.annealing_position = annealing_position

class Amplicon:
    def __init__(self,forward_primer, reverse_primer, template):
        
        self.forward_primer = forward_primer
        self.reverse_primer = reverse_primer
        self.product_size   = len(forward_primer)+len(reverse_primer)+reverse_primer.annealing_position-forward_primer.annealing_position
        
        self.product_sequence = forward_primer + \
                                template[forward_primer.annealing_position:reverse_primer.annealing_position] + \
                                reverse_primer.reverse_complement()
                                
        #print ">>>>>>>>>>",type(self.product_sequence)
        self.product_sequence.id   = "id"
        self.product_sequence.name = "name"
        self.product_sequence.description = "description"
        
        
        flankup  = template[:forward_primer.annealing_position]
        flankdn  = template[reverse_primer.annealing_position:]
        
        self.forward_covered_template = flankup.seq[-len(forward_primer):]
        self.reverse_covered_template = flankdn.seq[:len(reverse_primer)]
        
        
        
    def detailed_figure(self, alternative_image=2):
        #print type(self.forward_primer)
        forward_annealing           = define_right_overlap(self.forward_primer.seq,self.forward_covered_template)
        forward_annealing_pins      = "|"*forward_annealing
        self.forward_annealing_zone = self.forward_covered_template[-forward_annealing:]
        
        reverse_annealing           = define_right_overlap(self.reverse_primer.seq,self.reverse_covered_template.reverse_complement())
        reverse_annealing_pins      = "|"*reverse_annealing
        self.reverse_annealing_zone = self.reverse_covered_template[:reverse_annealing]
        
        tmf = Tm_staluc(str(self.forward_annealing_zone))
        tmr = Tm_staluc(str(self.reverse_annealing_zone))

        K = 0.050 # 50 mM
        L = len(self.product_sequence)
        GC_prod=GC(str(self.product_sequence))
        tmp = 81.5 + 0.41*GC_prod + 16.6*log10(K) - 675/L
        tml = min([tmf,tmr])
        ta = 0.3*tml+0.7*tmp-14.9

        f = ""
        
        #print "cccccccccc",type(self.forward_primer)
        #print dir(self.forward_primer)
        #print self.forward_primer.name
        #print dir(self.forward_primer.seq)

        if alternative_image==1:
            f += str("5"+self.forward_annealing_zone).rjust(1+len(self.forward_primer.seq.tostring())) + "..."
            f += self.reverse_annealing_zone + "3\n"
            f += " "+reverse_annealing_pins.rjust(len(self.forward_primer.seq.tostring())+3+len(self.reverse_annealing_zone)) + "\n"
            f += str("3"+self.reverse_primer.seq.tostring()[::-1]).rjust(1+len(self.forward_primer.seq.tostring())+3+len(self.reverse_primer.seq.tostring())) +"5\n"
            f +=  "5"+self.forward_primer.seq.tostring() + "3\n"
            f += " "+forward_annealing_pins.rjust(len(self.forward_primer.seq.tostring())) + "\n"
            f += str("3"+self.forward_annealing_zone.complement()).rjust(1+len(self.forward_primer.seq.tostring())) + "..."
            f += self.reverse_annealing_zone.complement() + "5\n"

        if alternative_image==2:
            f += "5"+self.forward_primer.seq.seq.tostring() + "3\n"
            f += " "+forward_annealing_pins.rjust(len(self.forward_primer.seq.seq.tostring())) + " tm "+str(round(tmf,1))+"C\n"
            f += str("5"+self.forward_annealing_zone).rjust(1+len(self.forward_primer.seq.seq.tostring())) + "..."
            f += self.reverse_annealing_zone + "3\n"
            f += str("3"+self.forward_annealing_zone.complement()).rjust(1+len(self.forward_primer.seq.seq.tostring())) + "..."
            f += self.reverse_annealing_zone.complement() + "5\n"
            f += " "+reverse_annealing_pins.rjust(len(self.forward_primer.seq.seq.tostring())+3+len(self.reverse_annealing_zone)) + " tm "+str(round(tmr,1))+"C\n"
            f += str("3"+self.reverse_primer.seq.seq.tostring()[::-1]).rjust(1+len(self.forward_primer.seq.seq.tostring())+3+len(self.reverse_primer.seq.seq.tostring())) +"5    "
            f += "ta  "+str(round(ta))+"C\n"

        return f

class Anneal:
    def __init__(self, primers, template, topology="linear", homology_limit=13):

        assert type(primers)                            == list
        assert type(template)                           == SeqRecord
        assert template.seq # check if empty template record
        template.seq.alphabet = ambiguous_dna

        self.template = template
        self.homology_limit = homology_limit
        
        if topology=="circular":
            self.circular_template=True
        else:
            self.circular_template=False       

        for primer in primers:
            assert(primer.seq) # check if empty sequence records in primers
            
        self.fwd_primers = []
        self.rev_primers = []    
   
        for primer in primers:  # add annealing forward and reverse primers

            annealing_positions_on_watson_strand = annealing_positions(primer.seq, template.seq,"forward",homology_limit)            
            for position in annealing_positions_on_watson_strand:
                self.fwd_primers.append(Primer(primer, position))
                
            annealing_positions_on_crick_strand = annealing_positions(primer.seq, template.seq,"reverse",homology_limit)
            for position in annealing_positions_on_crick_strand:
                self.rev_primers.append(Primer(primer, position))


    def define_amplicons(self,fprim="all",rprim="all"):
        amplicons,sizes = [],[]
        for forward_primer in self.fwd_primers:
            for reverse_primer in self.rev_primers[::-1]:
                amplicons.append(Amplicon(forward_primer, reverse_primer,template))

        self.amplicons = sorted(amplicons,key=lambda Amplicon: Amplicon.product_size)
        return self.amplicons
    
    
    
    
    
if __name__=="__main__":

    import textwrap
    
    raw=textwrap.dedent('''
    >fp
    atcgacaactgactgagacact

    >rp
    agtcatgcatgcaggctgggcgta

    >99_CRE_cds_r_BsiWI
    NNNGTCAAGCTTCGTACGATCGCCATCTTCCAG

    >98_CRE_cds_f_Acc65I
    GATCGGTACCATGTCCAATTTACTG

    >CRE
    AAatcgacaactgactgagacactAAatcgccatcttccagcaggcgcaccattgcccctttggtgtacggtcagtaaattggacatCCCtacgcccagcctgcatgcatgactC
    ''')
    
    
    '''
    >PCR product (123 bp) primers fp and rp
    NNNNNatcgacaactgactgagacactaAatcgccatcttccagcaggcgcaccattgcccctttggtgtacggtcagtaaattggacatCCCtacgcccagcctgcatgcatgactNNNNNN

    5NNNNNatcgacaactgactgagacacta3
          ||||||||||||||||||||||| tm 53.0C
         5atcgacaactgactgagacactA...tacgcccagcctgcatgcatgact3
         3tagctgttgactgactctgtgaT...atgcgggtcggacgtacgtactga5
                                    |||||||||||||||||||||||| tm 62.8C
                                   3atgcgggtcggacgtacgtactgaNNNNNN5    ta  53.0C
    '''

    new_sequences = parse_string_into_formatted_records(raw)
    
    template = new_sequences.pop().record
    
    primer_sequences  = [sequence.record for sequence in new_sequences]
    
    topology="linear"
    
    homology_limit=13

    aobj = Anneal(primer_sequences, template, topology, homology_limit)

    #print aobj.fwd_primers[1]

    #print aobj.rev_primers[1]
 
    aaa = aobj.define_amplicons()
    
    #print aaa
    
    for a in aaa:
        print a.product_size
        #print a.product_sequence
        print a.detailed_figure()



'''
>PCR product (89 bp) primers 99_CRE_cds_r_BsiWI and 98_CRE_cds_f_Acc65I





    >99_CRE_cds_r_BsiWI
    NNNGTCAAGCTTCGTACGATCGCCATCTTCCAG

    >98_CRE_cds_f_Acc65I
    GATCGGTACCATGTCCAATTTACTG
    
    '''

'''
New command line interface to PCR.py

Input:

one ore more textfiles with primer sequences in gb or fasta format

if there are not delimiter, last sequence is template, otherwise all seqs after delimiter

this indata is processed into one or more templates and primer sequences stored as lists of 
primer and template objects.

anneal:

test annealing of all primers against one templates.
add annealing primers and positions to the template object

sort primers by annealing position

product:


import argparse

parser = argparse.ArgumentParser(description='Process opts')
parser.add_argument('-c','--circ','--circular', action='store_true')
parser.add_argument('-s','--split',     action='store_true')
parser.add_argument('-f','--files',     nargs='+')
parser.add_argument('-p','--primers',   nargs='+')    
parser.add_argument('-t','--templates', nargs='+')   


##                   help='an integer for the accumulator')
#parser.add_argument('--sum', dest='accumulate', action='store_const',
#                   const=sum, default=max,
#                   help='sum the integers (default: find the max)')


args = parser.parse_args('-c -s'.split())

print args



# PCR --primers primers.txt --templates templates.txt --output prod.txt -verbose 3

# -o, --output                  use as output file
# -v, --verbose                 verbose
# -a, --anneal-only             report primer annealing only

'''










