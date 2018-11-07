# -*- coding: utf-8 -*-
"""
hgvs2vcf.py
report_hgvs2vcf
Used to report the Most true representation of the VCF i.e. 5 prime normalized but no
additional bases added. NOTE: no gap handling capabilities

"""

# Import  modules
import re
from hgvs.dataproviders import seqfetcher, uta
import hgvs.normalizer
import supportedChromosomeBuilds

# Import Biopython modules
from Bio.Seq import Seq

# Set variables
hdp = hgvs.dataproviders.uta.connect(pooling=True)

# Reverse normalizer (5 prime)
reverse_normalize = hgvs.normalizer.Normalizer(hdp,
                                               cross_boundaries=False,
                                               shuffle_direction=5,
                                               alt_aln_method='splign'
                                               )

# SeqFetcher
sf = hgvs.dataproviders.seqfetcher.SeqFetcher()


def report_hgvs2vcf(hgvs_genomic_variant, primary_assembly):
    # Reverse normalize hgvs_genomic_variant: NOTE will replace ref
    reverse_normalized_hgvs_genomic = reverse_normalize.normalize(hgvs_genomic_variant)

    # UCSC Chr
    ucsc_chr = supportedChromosomeBuilds.to_chr_num_ucsc(reverse_normalized_hgvs_genomic.ac, primary_assembly)
    if ucsc_chr is not None:
        pass
    else:
        ucsc_chr = reverse_normalized_hgvs_genomic.ac

    # GRC Chr
    grc_chr = supportedChromosomeBuilds.to_chr_num_refseq(reverse_normalized_hgvs_genomic.ac, primary_assembly)
    if grc_chr is not None:
        pass
    else:
        grc_chr = reverse_normalized_hgvs_genomic.ac

    if re.search('[GATC]+\=', str(reverse_normalized_hgvs_genomic.posedit)):
        pos = str(reverse_normalized_hgvs_genomic.posedit.pos.start)
        ref = reverse_normalized_hgvs_genomic.posedit.edit.ref
        alt = reverse_normalized_hgvs_genomic.posedit.edit.ref

    # Insertions
    elif (re.search('ins', str(reverse_normalized_hgvs_genomic.posedit)) and not re.search('del', str(
            reverse_normalized_hgvs_genomic.posedit))):
        end = int(reverse_normalized_hgvs_genomic.posedit.pos.end.base)
        start = int(reverse_normalized_hgvs_genomic.posedit.pos.start.base)
        alt_start = start - 1  #
        # Recover sequences
        ref_seq = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), alt_start, end - 1)
        ins_seq = reverse_normalized_hgvs_genomic.posedit.edit.alt
        # Assemble
        pos = start
        ref = ref_seq
        alt = ref_seq + ins_seq

    # Substitutions
    elif re.search('>', str(reverse_normalized_hgvs_genomic.posedit)):
        ref = reverse_normalized_hgvs_genomic.posedit.edit.ref
        alt = reverse_normalized_hgvs_genomic.posedit.edit.alt
        pos = str(reverse_normalized_hgvs_genomic.posedit.pos)

    # Deletions
    elif re.search('del', str(reverse_normalized_hgvs_genomic.posedit)) and not re.search('ins', str(
            reverse_normalized_hgvs_genomic.posedit)):
        end = int(reverse_normalized_hgvs_genomic.posedit.pos.end.base)
        start = int(reverse_normalized_hgvs_genomic.posedit.pos.start.base)
        adj_start = start - 2
        start = start - 1
        try:
            ins_seq = reverse_normalized_hgvs_genomic.posedit.edit.alt
        except:
            ins_seq = ''
        else:
            if str(ins_seq) == 'None':
                ins_seq = ''
        # Recover sequences
        hgvs_del_seq = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), start, end)
        pre_base = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), adj_start, start)
        # Assemble
        pos = str(start)
        ref = pre_base + hgvs_del_seq
        alt = pre_base


    # inv
    elif re.search('inv', str(reverse_normalized_hgvs_genomic.posedit)):
        end = int(reverse_normalized_hgvs_genomic.posedit.pos.end.base)
        start = int(reverse_normalized_hgvs_genomic.posedit.pos.start.base)
        adj_start = start - 1
        start = start
        try:
            ins_seq = reverse_normalized_hgvs_genomic.posedit.edit.alt
        except:
            ins_seq = ''
        else:
            if str(ins_seq) == 'None':
                ins_seq = ''
        # Recover sequences
        hgvs_del_seq = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), start, end)
        vcf_del_seq = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), adj_start, end)
        bs = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), adj_start - 1, adj_start)
        # Assemble
        pos = str(start)
        # pos = str(start-1)
        # ref = bs + vcf_del_seq
        ref = vcf_del_seq
        alt = ins_seq
        if re.search('inv', str(reverse_normalized_hgvs_genomic.posedit)):
            my_seq = Seq(vcf_del_seq)
            # alt = bs + str(my_seq.reverse_complement())
            alt = str(my_seq.reverse_complement())

    # Delins
    elif (re.search('del', str(reverse_normalized_hgvs_genomic.posedit)) and re.search('ins', str(
            reverse_normalized_hgvs_genomic.posedit))):
        end = int(reverse_normalized_hgvs_genomic.posedit.pos.end.base)
        start = int(reverse_normalized_hgvs_genomic.posedit.pos.start.base - 1)
        adj_start = start - 1
        start = start
        try:
            ins_seq = reverse_normalized_hgvs_genomic.posedit.edit.alt
        except:
            ins_seq = ''
        else:
            if str(ins_seq) == 'None':
                ins_seq = ''
        # Recover sequences
        hgvs_del_seq = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), start, end)
        vcf_del_seq = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), adj_start, end)
        # Assemble
        # pos = str(start)
        # ref = vcf_del_seq
        # alt = vcf_del_seq[:1] + ins_seq
        pos = str(start + 1)
        ref = vcf_del_seq[1:]
        alt = ins_seq

    # Duplications
    elif (re.search('dup', str(reverse_normalized_hgvs_genomic.posedit))):
        end = int(reverse_normalized_hgvs_genomic.posedit.pos.end.base)  #
        start = int(reverse_normalized_hgvs_genomic.posedit.pos.start.base)
        adj_start = start - 2  #
        start = start - 1  #
        # Recover sequences
        dup_seq = reverse_normalized_hgvs_genomic.posedit.edit.ref
        vcf_ref_seq = sf.fetch_seq(str(reverse_normalized_hgvs_genomic.ac), adj_start, end)
        # Assemble
        pos = str(start+1)
        ref = vcf_ref_seq[1:]
        alt = vcf_ref_seq[1:] + dup_seq
    else:
        chr = ''
        ref = ''
        alt = ''
        pos = ''

    # Dictionary the VCF
    vcf_dict = {'pos': str(pos), 'ref': ref, 'alt': alt, 'ucsc_chr': ucsc_chr, 'grc_chr': grc_chr,
                'normalized_hgvs': reverse_normalized_hgvs_genomic}
    return vcf_dict