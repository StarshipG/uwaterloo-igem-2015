# gene/genome de-activation defined by
# 1. frameshift mutation in an ORF
# 2. deletion of a promoter

# TODO
# function for cut porbability: foo_cut_prob(self.grna, self.target, dt, complex_concentration)
# function for cut location: foo_cut_posn()
# function for indel type (L/R, del/oinsert) foo_indel(), foo_nt_rand(insert_right) etc
# if repair is big deletion, what do we fill in at the end of the target? cant be random, must come from sequence data
# need to update all genome locations with each indel or deletion
# code for deletions

# classes
class Target(object):

    def __init__(
            self, label, grna, sequence, start, complex_concentration, dt,
            direction, right_buffer, left_buffer):  # may want to make dt adaptive
        self.label = label  # string
        self.grna = grna  # string
        self.sequence = sequence  # string, include PAM, should be ~ 23 chars, maybe need buffer on opposite end
        self.start = start  # int
        self.total_cuts = 0
        self.cut_position = None  # number of nt from PAM site, starting at 0
        self.repaired = True  # defined by open/closed
        self.targetable = True  # defined by targetable or not (PAM broken or indel size > 5)
        self.cut_probability = self.compute_cut_probability(dt)
        self.shift = 0  # defined by sum of net indel sizes, used to compute frameshift if orf region
        self.complex_concentration = complex_concentration  # conc of gRNA-cas9 complex inside nucleus
        self.direction = direction # direction target is pointing (for merging sites after large dels)
        self.right_buffer = right_buffer # ~100 nucleotides in genome right of sequence
        self.left_buffer = left_buffer # ~100 nucleotides in genome left of sequence

    def is_repaired(self):
        return self.repaired

    def is_targetable(self):
        return self.targetable

    def get_shift(self):
        return self.shift

    def compute_cut_probability(self, dt):
        # TODO: function to compute probability or time until next cut
        # return foo_cut_prob(self.grna, self.target, self.complex_concentration, dt)
        return 0.0

    def cut(self):
        self.total_cuts += 1
        self.cut_position = 6  # 0-indexed posn of the nt right of the cut, usually 3-4nt from pam: foo_cut_posn()
        self.repaired = False

    def repair(self):
        # TODO: indel size module
        # del_left, del_right, insert_left, insert_right = foo_indel()  # e.g. 0, 0, 1, 1
        del_left, del_right = 0, 0  # fn
        insert = 2  # fn
        # TODO: nucleotide insertion module
        insert_nt = 'XY'  # foo_nt_rand(insert_nt)
        # rewrite target sequence
        sequence_left = self.sequence[0:self.cut_position-del_left]
        sequence_right = self.sequence[self.cut_position+del_right:]
        self.sequence = sequence_left + insert_nt + sequence_right  # may need to get buffer from genome data if deletion
        del_left = fix_pam(del_left) # fixing in case of damaged PAM
        net_indel_size = insert - del_left - del_right
        if net_indel_size < 0: # tack on nucleotides
            self.sequence = self.sequence + self.right_buffer[0:-net_indel_size]
            self.right_buffer = self.right_buffer[-net_indel_size:]
        elif net_indel_size > 0: # shave of nucleotides
            self.right_buffer = self.sequence[-net_indel_size:] + self.right_buffer
            self.sequence = self.sequence[:-net_indel_size]
        self.cut_position = None
        self.repaired = True
        if net_indel_size > 5 or self.sequence[1:3] != "GG": # big insertion or broken PAM
            self.targetable = False
            self.cut_probability = 0.0
        else:
            self.cut_probability = self.compute_cut_probability(dt)
        self.shift += net_indel_size

    def fix_pam(self, del_left):
        if del_left == 0 or self.sequence[1:3] == "GG": # out of insertions or working PAM
            return del_left
        else: # tries to fix broken PAM by adding to the left
            self.sequence = self.left_buffer[-1:] + self.sequence
            self.left_buffer = self.left_buffer[:-1]
            fix_pam(del_left-1)

class Domain(object):

    def __init__(self, label, domain_start, domain_end, domain_type, promoter=None, targets=None):
        assert domain_type in ["orf", "promoter", "ncr"]
        self.domain_type = domain_type # 'orf' or 'promoter' or 'ncr'
        self.domain_start = domain_start  # int
        self.domain_end = domain_end  # int
        if domain_type == 'orf':
            assert promoter is not None
            self.promoter = promoter  # promoter is a domain too
        self.sequence = None  # to be implemented
        self.functional = True  # bool
        self.targets = targets  # list of Target objects

    def update_functionality(self):
        if self.domain_type == "orf":
            if not self.promoter.is_functional() or sum(target.get_shift() for target in self.targets) % 3 != 0:
                self.functional = False
            else:
                self.functional = True
        elif self.domain_type == "promoter":  # how to define functional promoter
            self.functional = True
        else:  # how to define functional NCR
            self.functional = True


class Genome(object):

    def __init__(self, length, domains):
        self.length = length  # int
        self.sequence = None  # to be implemented
        self.domains = domains  # list of all domains (ORFs, promoters, NCRs)
        self.repaired = True
