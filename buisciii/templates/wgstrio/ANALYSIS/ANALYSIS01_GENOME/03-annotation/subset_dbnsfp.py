#!/usr/bin/env python3
"""============================================================================
subset_dbnsfp.py -- helper script called by Merge_All.R
----------------------------------------------------------------------------
OBJECTIVE:
    Prepare dbNSFP annotations for the case's individual SNV alleles and their
    transcripts, without loading the complete reference database into memory.

INPUTS:
    --variants   vep/variants.table: CHROM, POS, REF, ALT and ID columns.
    --db         Full dbNSFP5.4a_grch38.gz, with its tabix .tbi/.csi index.
    --out-dir    Existing temporary directory created by Merge_All.R.

OUTPUTS:
    dbNSFP_case.txt          Selected source columns, including transcript metadata.
    dbNSFP_variant.tsv       One row per genomic SNV, for general annotations. Temporary lookup read by R; not published.
    dbNSFP_transcript.tsv    One row per SNV/ENST/protein effect, for transcript joins. Temporary lookup read by R; not published.
    dbNSFP_regions.bed       Temporary query positions; not a new reference resource.

WORKFLOW:
    1. Read variants.table and collect each eligible ALT separately.
    2. Query dbNSFP at those positions using tabix.
    3. Keep exact REF/ALT matches, then separate general and transcript annotations.
    4. Validate the lists associated with transcripts and write the two lookups.

KEY EXAMPLES:
    Original record: CHROM=chr1 POS=100 REF=A ALT=G,* ID=chr1_100_A_G,*
    Requested SNV:   ('1', '100', 'A', 'G'); '*' is not queried as an SNV.
    Variant key:     1_100_A_G
    Transcript key:  1_100_A_G|ENST00000000001|C/R:143
    Stop-gained key: 1_100_A_G|ENST00000000001|R/*:143   (dbNSFP 'X' -> '*')
    These keys are internal. R preserves the original ID and the whole ALT list.

STOP CODON NOTATION:
    dbNSFP writes a stop codon as 'X' in aaref/aaalt, whereas VEP writes '*' in
    Amino_acids. Merge_All.R converts VEP's 'X' to '*' before building its
    transcript key, so this helper must use '*' in the key too. Only the KEY is
    normalised: dbNSFP_aaref / dbNSFP_aaalt keep the source spelling ('X').

MEMORY STRATEGY:
    Source dbNSFP rows are streamed. Only case allele keys and the two case
    lookups remain in memory; the entire reference is never loaded into RAM.
    indexed mode uses tabix -R; stream mode uses tabix -T for dense WGS targets.
============================================================================"""
import argparse
import csv
import gzip
import os
import shutil
import re
import subprocess
import sys
from pathlib import Path

# --- COLUMN GROUPS ----------------------------------------------------------
# Field definitions: https://dist.genos.us/release/dbNSFP5.4a_variant.columns.txt
# These columns describe the allele, independently of its transcript.
BASE = ['CADD_raw', 'CADD_phred', 'GERP++_NR', 'GERP++_RS',
        'phyloP100way_vertebrate', 'phastCons100way_vertebrate',
        'clinvar_id', 'clinvar_trait', 'clinvar_MedGen_id',
        'clinvar_OMIM_id', 'clinvar_Orphanet_id']

# Transcript-specific fields.
VECTOR = ['HGVSc_snpEff', 'HGVSp_snpEff', 'SIFT_score', 'SIFT_pred',
          'Polyphen2_HDIV_score', 'Polyphen2_HDIV_pred',
          'Polyphen2_HVAR_score', 'Polyphen2_HVAR_pred',
          'MutationAssessor_score', 'MutationAssessor_pred',
          'PROVEAN_score', 'PROVEAN_pred', 'VEST4_score']

# Record-specific fields.
RECORD = ['MutationTaster_score', 'MutationTaster_pred',
          'MetaSVM_score', 'MetaSVM_pred', 'MetaLR_score', 'MetaLR_pred']

# These metadata lists establish the protein/UniProt/position at each ENST index.
META_VECTOR = ['Ensembl_proteinid', 'Uniprot_acc', 'Uniprot_entry', 'aapos']

# The complete set of fields to be written to the final file.
RAW_FIELDS = (['#chr', 'pos(1-based)', 'ref', 'alt', 'Ensembl_transcriptid',
               'aaref', 'aaalt'] + META_VECTOR + BASE + VECTOR + RECORD)

# Explicit provenance columns added to the final annotation table by R so
# that variant/transcript/protein information is properly reflected.
TS_META = ['dbNSFP_transcript', 'dbNSFP_aaref', 'dbNSFP_aaalt',
           'dbNSFP_aapos', 'dbNSFP_protein', 'dbNSFP_Uniprot_acc']


# --- HELPER FUNCTIONS -------------------------------------------------------
def norm_chrom(chrom):
    """Harmonise chr/M/MT spelling for keys; do not change coordinates or assembly."""
    chrom = chrom[3:] if chrom.startswith('chr') else chrom
    return 'MT' if chrom == 'M' else chrom


def read_table(path, columns):
    """Use names, not column numbers; quotes are literal TSV content."""
    with open(str(path), encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t', quoting=csv.QUOTE_NONE)
        for name in columns:
            if (reader.fieldnames or []).count(name) != 1:
                raise ValueError('{}: missing/duplicated {}'.format(path, name))
        for row in reader:
            if any(row.get(name) is None for name in columns):
                raise ValueError('{}: incomplete line {}'.format(path, reader.line_num))
            yield row


def wanted_alleles(path):
    """Collect unique genomic SNV alleles, not the complete original record ID.

    For example, for ALT=G,T both SNVs are queried from dbNSFP; for ALT=G,* only G is queried. 
    Indels, MNVs, symbolic alleles and '*' still survive in R's later LEFT joins.
    """
    wanted = set()
    for row in read_table(path, ['CHROM', 'POS', 'REF', 'ALT', 'ID']):
        if not row['POS'].isdigit() or int(row['POS']) < 1:
            raise ValueError('Invalid POS in variants.table')
        if not re.fullmatch('[ACGT]', row['REF']):
            continue
        # A,G and G,* each yield a key for every literal SNV ALT, independently.
        # '*' and indels are kept by the later LEFT JOIN, but never queried as SNVs
        # for annotation using dbNSFP.
        for alt in row['ALT'].split(','):
            if re.fullmatch('[ACGT]', alt) and alt != row['REF']:
                wanted.add((norm_chrom(row['CHROM']), row['POS'], row['REF'], alt))
    return wanted


def vector(value, n, label):
    """Return one value per transcript, validating that the mapping is possible.

    A single '.' means the entire field is unavailable, expanding it to n missing
    elements. Any other list must have exactly n entries.
    """
    if value == '.':
        return ['.'] * n
    values = value.split(';')
    if len(values) != n:
        raise ValueError('{} has {} values for {} transcripts; cannot assign safely'
                         .format(label, len(values), n))
    return values


def add_unique(lookup, key, value, label):
    """Collapse only identical annotations; conflicting annotations stop the run."""
    if key in lookup and lookup[key] != value:
        raise ValueError('Conflicting {} annotations for {}'.format(label, key))
    lookup[key] = value


def write_tsv(path, header, rows):
    """Write a TSV file: one header line, then one line per row. Fields are written as-is (no quoting or escaping)."""
    with open(str(path), 'w', encoding='utf-8') as handle:
        handle.write('\t'.join(header) + '\n')
        for row in rows:
            handle.write('\t'.join(row) + '\n')


def effect_key(aaref, aaalt, pos):
    """Build the protein-effect part of the transcript key, matching R.

    transcript_keys() in Merge_All.R replaces 'X' with '*' in VEP's Amino_acids.
    dbNSFP spells a stop codon 'X', so the same replacement is applied here.
    Only the key is affected; the stored aaref/aaalt columns are unchanged.
    """
    aa = (aaref + '/' + aaalt).replace('X', '*')
    # Missing amino acids plus aapos=-1 identify a source splice record.
    if aa == './.' and pos == '-1':
        return 'SPLICE'
    if re.fullmatch(r'[A-Z*]/[A-Z*]', aa) and pos.isdigit():
        return aa + ':' + pos
    return None


def project(rows, wanted, directory):
    """Retain source rows and construct the lookups consumed by R.

    base --> maps genomic allele keys to CADD/conservation/ClinVar fields.
    transcripts --> maps allele + ENST + protein effect to the corresponding scores.
    Source records may mention several transcripts; each gets its own key and
    the element at its own index in the documented, validated parallel lists.
    """
    base, transcripts = {}, {}
    source_count = 0
    with (directory / 'dbNSFP_case.txt').open('w', encoding='utf-8') as raw:
        raw.write('\t'.join(RAW_FIELDS) + '\n')
        for row in rows:
            variant = (norm_chrom(row['#chr']), row['pos(1-based)'],
                       row['ref'], row['alt'])
            # tabix selects positions, which may contain other REF/ALT pairs.
            # This second check restricts annotations to alleles actually within the case of interest.
            if variant not in wanted:
                continue
            source_count += 1
            if source_count % 10000 == 0:
                print('dbNSFP: {} source rows selected'.format(source_count),
                      file=sys.stderr, flush=True)
            raw.write('\t'.join(row[c] for c in RAW_FIELDS) + '\n')
            key = '_'.join(variant)
            # General annotations must agree across source rows for the same SNV.
            add_unique(base, key, tuple(row[c] for c in BASE), 'variant')
            ids = row['Ensembl_transcriptid'].split(';')
            if ids == ['.']:
                continue  # Variant-level fields remain available.
            n = len(ids)
            # Validate the metadata and prediction arrays before selecting any
            # element. Protein/UniProt arrays follow the same transcript ordering.
            values = {c: vector(row[c], n, key + ':' + c)
                      for c in META_VECTOR + VECTOR}
            for i, transcript in enumerate(ids):
                if not re.fullmatch(r'ENST[0-9]+(?:\.[0-9]+)?', transcript):
                    raise ValueError('Unsupported transcript ID: ' + transcript)
                transcript = re.sub(r'\.[0-9]+$', '', transcript)
                pos = values['aapos'][i]
                # Same effect representation as transcript_keys() in R,
                # including the dbNSFP 'X' -> VEP '*' stop-codon normalisation.
                effect = effect_key(row['aaref'], row['aaalt'], pos)
                if effect is None:
                    raise ValueError('Unsupported protein effect for ' + key)
                tskey = key + '|' + transcript + '|' + effect
                # Source spelling of aaref/aaalt is preserved here (stop = 'X').
                meta = (transcript, row['aaref'], row['aaalt'], pos,
                        values['Ensembl_proteinid'][i], values['Uniprot_acc'][i])
                value = tuple(values[c][i] for c in VECTOR) + tuple(row[c] for c in RECORD) + meta
                add_unique(transcripts, tskey, value, 'transcript/effect')
    # Sort lookup keys for auxiliar files.
    write_tsv(directory / 'dbNSFP_variant.tsv', ['DBNSFP_KEY'] + BASE,
              ((key,) + value for key, value in sorted(base.items())))
    write_tsv(directory / 'dbNSFP_transcript.tsv', ['DBNSFP_TRANSCRIPT_KEY'] + VECTOR + RECORD + TS_META,
              ((key,) + value for key, value in sorted(transcripts.items())))
    print('dbNSFP: {} source rows; {} alleles; {} transcript/effect keys'.format(
          source_count, len(base), len(transcripts)), file=sys.stderr, flush=True)


def tabix_command():
    """Run tabix from the VEP Singularity image.

    Binds /data, the current working directory and /scratch (when present) so
    tabix can read the BGZF file and the temporary regions BED.
    """
    singularity = shutil.which('singularity')
    image = os.environ.get('VEP_IMAGE',
        '/data/ucct/bi/pipelines/singularity-images/ensembl-vep:116.0--pl5321h2a3209d_0')
    if not singularity or not Path(image).exists():
        raise ValueError('singularity not on PATH or VEP image not found: ' + image)
    cwd = str(Path.cwd())
    command = [singularity, 'exec', '--cleanenv', '-B', '/data:/data', '-B', cwd + ':' + cwd]
    if Path('/scratch').is_dir():
        command += ['-B', '/scratch:/scratch']
    print('Using tabix from VEP image: ' + image, file=sys.stderr, flush=True)
    return command + [image, 'tabix']


def contig_order(command, db):
    """Get contig names in the order stored in the BGZF index (tabix -l).

    tabix -T needs its targets in the same contig order as the data file, and
    the index is the authority on both the order and the spelling of contigs
    (dbNSFP 5.4a: 1..22, X, Y, M; no 'chr' prefix).
    """
    out = subprocess.run(command + ['-l', db], stdout=subprocess.PIPE,
                         encoding='utf-8', check=True)
    order = {name: i for i, name in enumerate(out.stdout.split())}
    if not order:
        raise ValueError('tabix -l returned no contigs for ' + db)
    return order


def index_contig(chrom, order):
    """Map an internal key chromosome ('1', 'MT') to the contig name in the index.

    Returns None when the contig does not exist in dbNSFP.
    """
    names = ['M', 'chrM', 'MT'] if chrom == 'MT' else [chrom, 'chr' + chrom]
    for name in names:
        if name in order:
            return name
    return None


# --- MAIN -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--variants', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--query-mode', choices=['indexed', 'stream'], default='indexed',
                        help='indexed: tabix -R (exome); stream: tabix -T (dense WGS targets)')
    args = parser.parse_args()
    directory = Path(args.out_dir)
    if not directory.is_dir():
        raise ValueError('--out-dir must already exist')
    
    # STEP 1. Collect separate case SNVs.
    wanted = wanted_alleles(args.variants)
    print('dbNSFP: {} individual SNV alleles; {} query mode'.format(
          len(wanted), args.query_mode), file=sys.stderr, flush=True)
    with gzip.open(args.db, 'rt', encoding='utf-8') as handle:
        header = handle.readline().rstrip('\r\n').split('\t')
    for field in RAW_FIELDS:
        if header.count(field) != 1:
            raise ValueError('Full dbNSFP 5.4a required: missing/duplicated ' + field)
    if not (Path(args.db + '.tbi').is_file() or Path(args.db + '.csi').is_file()):
        raise ValueError('Missing dbNSFP tabix index')
    
    # STEP 2. Write unique positions from variants.table as zero-based, half-open BED intervals.
    # This is done since tabix requires to know where to look within dbNSFP's full table.
    # A VCF position P therefore becomes [P-1, P) in the BED file; its REF/ALT is checked after querying.
    # Contig names and order come from the index (tabix -l), not from sorting
    # strings: text order (1, 10, 11, ..., 2) breaks tabix -T, and dbNSFP names
    # the mitochondrial contig 'M', not 'MT'.
    if not wanted:
        project([], wanted, directory)
        return
    tabix = tabix_command()
    order = contig_order(tabix, args.db)
    targets, skipped = set(), set()
    for chrom, pos, _ref, _alt in wanted:
        contig = index_contig(chrom, order)
        if contig is None:
            skipped.add(chrom)
        else:
            targets.add((contig, int(pos)))
    if skipped:
        print('dbNSFP: contigs absent from the index, not queried: ' +
              ', '.join(sorted(skipped)), file=sys.stderr, flush=True)
    regions = directory / 'dbNSFP_regions.bed'
    with regions.open('w', encoding='utf-8') as handle:
        for contig, pos in sorted(targets, key=lambda t: (order[t[0]], t[1])):
            handle.write('{}\t{}\t{}\n'.format(contig, pos - 1, pos))
    if not targets:
        project([], wanted, directory)
        return
    
    # STEP 3. Stream tabix's output and project the requested fields by NAME.
    # -R jumps through the index; -T scans the reference and selects targets.
    indices = [header.index(c) for c in RAW_FIELDS]
    # stderr is inherited: tabix errors/warnings remain visible in the job log.
    option = '-R' if args.query_mode == 'indexed' else '-T'
    proc = subprocess.Popen(tabix + [option, str(regions), args.db],
                            stdout=subprocess.PIPE, encoding='utf-8')
    def source_rows():
        for line in proc.stdout:
            fields = line.rstrip('\r\n').split('\t')
            if len(fields) != len(header):
                raise ValueError('Malformed dbNSFP record returned by tabix')
            yield dict(zip(RAW_FIELDS, (fields[i] for i in indices)))
            
    # STEP 4. Build the case lookups. Check the query exit status even when its
    # output looked valid: truncated query output must never be published by R.
    try:
        project(source_rows(), wanted, directory)
        if proc.wait() != 0:
            raise RuntimeError('tabix failed; results must not be published')
    # Clean up the child process on success or on a schema/annotation error.
    # Output files stay in R's temporary directory if the run fails.
    finally:
        proc.stdout.close()
        if proc.poll() is None:
            proc.terminate()
            proc.wait()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('ERROR: {}'.format(error), file=sys.stderr)
        sys.exit(2)
