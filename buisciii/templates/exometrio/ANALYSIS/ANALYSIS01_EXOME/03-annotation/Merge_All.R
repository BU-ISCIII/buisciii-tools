#!/usr/bin/env Rscript
# ============================================================================
# Merge_All.R
# ----------------------------------------------------------------------------
# OBJECTIVE:
#   Combine four sources of data into one final annotated variant table:
#     1. VEP annotations (header + variants)        (vep/vep_annot_head.txt)
#     2. dbNSFP variant-level annotations           (full dbNSFP5.4a_grch38.gz + .tbi index)
#     3. dbNSFP gene-level annotations              (dbNSFP_ENSG_gene_GRCh38.txt)
#     4. Variant/genotype table (w/o annotations)   (vep/variants.table)
#
# KEY CONCEPTS:
#   - VEP writes one row per ALLELE and per TRANSCRIPT. Its ID column holds the
#     original VCF record (e.g. chr1_1543953_A_G; chr1_100_A_G,*), which may contain several ALTs.
#   - dbNSFP only contains single-nucleotide variants (SNVs), one row per SNV and
#     amino-acid change. Some of its fields describe the variant itself (CADD,
#     conservation, ClinVar); while others describe its effect per transcript
#     (SIFT, PolyPhen, ...).
#
# JOINS (performed in sequence for each chunk of VEP rows):
#     JOIN 1a  VEP            LEFT JOIN  dbNSFP variant fields     on SNV key (ID: CHROM_POS_REF_ALT)
#     JOIN 1b  that result    LEFT JOIN  dbNSFP transcript fields  on SNV key + ENST + amino-acid change
#     JOIN 2   that result    LEFT JOIN  dbNSFP genes              on Gene
#     JOIN 3   that result    INNER JOIN variants.table            on the original ID
#
    ## PER-ALLELE AND PER-TRANSCRIPT MATCHING:
    ##   JOIN 1 is not done on the original ID, but on a key built from CHROM, POS,
    ##   REF and VEP's Allele, so that each SNV inside a multiallelic record (e.g.
    ##   ALT=G,*, where VEP's Allele is G) gets its own dbNSFP annotation and is therefore
    ##   not lost in the final table. JOIN 1b appends ENST and the corresponding
    ##   amino-acid change to that key, so each transcript receives only the scores
    ##   for its own protein effect (without this, a variant would be assigned a wrong transcript-effect pair).
    ##   Stop codons are normalised between source ('X')
    ##   and VEP ('*') spellings before building the keys. The column dbNSFP_match
    ##   records the outcome for every row (see AD HOC COLUMNS below).
#
# WORKFLOW:
#   1. Validate inputs and create a temporary directory. Nothing is written to
#      the final locations yet.
#   2. Run subset_dbnsfp.py. It queries the full dbNSFP with tabix (too large to
#      load in RAM) and keeps only the SNVs found in variants.table.
#   3. Load both lookups, the gene table and variants.table in RAM.
#   4. Read VEP in chunks of rows. For each chunk, build the SNV and transcript
#      keys, run JOINs 1a, 1b, 2 and 3, and check that no row was lost or
#      duplicated. Write each result to the temporary directory.
#   5. Only if every chunk passed all checks, move the results to their final
#      locations and delete the temporary directory.

# MEMORY STRATEGY:
#   The whole dbNSFP v5.4 table does NOT fit in RAM. This script:
#     - streams dbNSFP once with AWK (by means of subset_dbnsfp.py) and keeps only the
#       rows whose variant key appears in variants.table;
#     - reads VEP in chunks instead of loading the whole file.
#   Gene annotations and variants.table are still fully loaded in memory;
#   since they are smaller than dbNSFP's variant-level annotations file.
#
# INPUTS:
#   vep/variants.table               Variant/genotype table (must have ID).
#   vep/vep_annot_head.txt           VEP output, header + rows, must have ID column.
#   dbNSFP5.4a_grch38.gz             dbNSFP variant annotations (GRCh38).
#   dbNSFP_ENSG_gene_GRCh38.txt      dbNSFP gene annotations (GRCh38).
#   subset_dbnsfp.py                 Helper script.
#
# OUTPUTS:
#   vep/vep_plugin.txt               VEP table + dbNSFP variants.
#   vep/vep_dbNSFP.txt               Previous result + dbNSFP genes.
#   variants_annot_all.tab           Previous result + variants.table --> final table.
#   vep/dbNSFP_case.txt              dbNSFP subset used (only for traceability).
#
#   Bear in mind that the three intermediate VEP outputs only contain annotations for IDs that
#   also appear in variants.table, because the final INNER join would discard
#   the rest anyway.

# COLUMN PROVENANCE IN THE FINAL TABLE (variants_annot_all.tab):
#   vep/vep_annot_head.txt   All VEP columns (ID, Allele, Feature,
#                            Feature_type, Consequence, Amino_acids,
#                            Protein_position, Gene, and any other VEP field).
#   variants.table           All genotype columns (ID, CHROM, POS, REF, ALT, FILTER and
#                            any other sample columns).
#   dbNSFP_ENSG_gene_GRCh38.txt
#                            Gene-level: OMIM_id, Function_description,
#                            Disease_description, HPO_id, HPO_name.
#   dbNSFP5.4a_grch38.gz     Variant-level: CADD_raw, CADD_phred, GERP++_NR,
#                            GERP++_RS, phyloP100way_vertebrate,
#                            phastCons100way_vertebrate, clinvar_id,
#                            clinvar_trait, clinvar_MedGen_id,
#                            clinvar_OMIM_id, clinvar_Orphanet_id.
#
#                            Transcript-level: HGVSc_snpEff, HGVSp_snpEff,
#                            SIFT_score/pred, Polyphen2_HDIV_*,
#                            Polyphen2_HVAR_*, MutationAssessor_*,
#                            PROVEAN_*, VEST4_score.
#
#                            Transcript metadata: dbNSFP_transcript,
#                            dbNSFP_aaref, dbNSFP_aaalt, dbNSFP_aapos,
#                            dbNSFP_protein, dbNSFP_Uniprot_acc,
#                            dbNSFP_MutationTaster_scope (originally Ensembl_transcriptid,
#                            aaref, aaalt, aapos, Ensembl_proteinid and Uniprot_acc in dbNSFP).
#
#                            Record-level (not indexed by ENST):
#                            MutationTaster_score/pred, MetaSVM_score/pred,
#                            MetaLR_score/pred.
#
#   Merge_All.R (ad hoc)     dbNSFP_match.
#   Missing values are written as '-'.
#
# COLUMNS CREATED BY subset_dbnsfp.py:
#   dbNSFP_transcript            ENST of the dbNSFP transcript matched to this
#                                VEP row (version suffix stripped).
#   dbNSFP_aaref / dbNSFP_aaalt  Source amino-acid spelling; stop codon is 'X'.
#   dbNSFP_aapos                 Amino-acid position in the matched transcript.
#   dbNSFP_protein               Ensembl protein ID (ENSP) for that transcript.
#   dbNSFP_Uniprot_acc           UniProt accession for that transcript.
#
# EXAMPLE (ad hoc columns):
#   VCF record: chr1 100 A G  (ID = chr1_100_A_G)
#
#   dbNSFP source row for allele 1_100_A_G:
#     Ensembl_transcriptid = ENST00000000001.7;ENST00000000002.3
#     aaref                 = C;L
#     aaalt                 = R;P
#     aapos                 = 143;97
#     Ensembl_proteinid     = ENSP00000000001;ENSP00000000002
#     Uniprot_acc           = P11111;Q22222
#     MutationTaster_score  = 0.99;0.95
#
#   Resulting VEP rows (only dbNSFP ad hoc columns shown; variant-level
#   columns such as CADD_raw or clinvar_id are filled whenever the allele
#   matched dbNSFP, i.e. in every row except NOT_SNV):
#
#   VEP Feature     dbNSFP_match            dbNSFP_transcript  dbNSFP_aaref  dbNSFP_aaalt  dbNSFP_aapos  dbNSFP_protein   dbNSFP_Uniprot_acc
#   ENST00000000001 TRANSCRIPT_AND_PROTEIN  ENST00000000001    C             R             143           ENSP00000000001  P11111            
#   ENST00000000002 TRANSCRIPT_AND_PROTEIN  ENST00000000002    L             P             97            ENSP00000000002  Q22222            
#   ENST00000000003 VARIANT_ONLY            -                  -             -             -             -                -                 
#
#   Notes on the example:
#     - Row 1 and row 2 matched their own transcript and amino-acid change, so
#       each receives only its own SIFT/PolyPhen/... scores (JOIN 1b).
#     - Row 3 has variant-level fields filled (CADD, ClinVar, ...) but no
#       transcript-level match, so all tx-level and ad hoc columns are '-'.

# AD HOC COLUMN CREATED BY Merge_All.R:
#   dbNSFP_match  Outcome of the dbNSFP joins for that VEP row. Values:
#     NOT_SNV                 Allele not eligible for a dbNSFP query (e.g. '*',
#                             indel, MNV, symbolic); no key was built and no
#                             dbNSFP field is filled.
#     NO_DBNSFP_VARIANT       SNV key built but the allele is absent from the
#                             dbNSFP database for this case; no field filled.
#     VARIANT_ONLY            Variant-level fields filled; no transcript
#                             matched (ENST and/or amino-acid change differ
#                             or are absent).
#     TRANSCRIPT_AND_PROTEIN  Variant-level and transcript/amino-acid fields
#                             both filled correctly.
#     TRANSCRIPT_SPLICE       Variant-level and splice-site fields filled (VEP
#                             reported a donor/acceptor consequence and no amino acid change was reported).
#
# USAGE:
#   From the 03-annotation directory:
#     Rscript Merge_All.R [rows_per_chunk]
#
#   rows_per_chunk counts INPUT VEP ROWS (default 50000, it is not mandatory
#   to indicate this number when running the script). You can lower it if you hit
#   memory limits in the joins.
#
# ============================================================================

suppressPackageStartupMessages(library(data.table))

# --- CONFIGURATION -----------------------------------------------------------
# Three settings control how the script runs. All have sensible defaults, so
# you only need to touch them if you hit memory or CPU problems.

# SETTING 1: chunk size (command-line argument)
# VEP is read in blocks of this many ROWS (default 50000), not all at once.
# Rows, not variants: one variant takes several rows (one per transcript).
# A variant split across two chunks is fine, because every join below is
# row-wise: each row is resolved on its own, independently of its neighbours.
# If you run out of RAM, lower it:
#     Rscript Merge_All.R 20000
args <- commandArgs(trailingOnly=TRUE)
annotations_only <- identical(Sys.getenv("MERGE_ANNOTATIONS_ONLY"), "1")
chunk_rows <- if (!annotations_only && length(args)) as.integer(args[1]) else 50000L
if (is.na(chunk_rows) || chunk_rows < 1L) stop("Invalid chunk size")

# SETTING 2: CPU threads (set automatically by Slurm)
# Use only the CPUs Slurm allocated to this job (SLURM_CPUS_PER_TASK), or
# 1 thread outside Slurm. Without this, data.table would grab every core of
# the node.
threads <- as.integer(Sys.getenv("SLURM_CPUS_PER_TASK", "1"))
setDTthreads(if (is.na(threads)) 1L else max(1L, threads))

# --- HELPER FUNCTIONS -----------------------------------------------------------------

logmsg <- function(...) message(format(Sys.time(), "%F %T"), " | ", ...)

# required(): fail if a table lacks columns we depend on, since it is better to stop
# here with a clear message than to run a join on a wrong or
# malformed file and silently get empty or misleading results.
required <- function(x, columns, label) {
    if (anyDuplicated(names(x)) || !all(columns %in% names(x)))
        stop(label, ": missing required or duplicated columns")
}

# read_table(): read a TSV with EVERY column as text, so that every value is exactly as written in the file.
#   quote=""          : no quote handling, so a stray " in a description is
#                       just text, not the start of a quoted field.
#   na.strings="NA"   : only the literal NA counts as missing. '-' and '.' stay
#                       as normal text (missing values are WRITTEN as '-' later).
#   check.names=TRUE  : turn column names into valid R names (spaces -> dots).
read_table <- function(path) {
    fread(file=path, sep="\t", quote="", header=TRUE, check.names=TRUE,
          colClasses="character", na.strings="NA", showProgress=FALSE)
}

# write_part(): write a chunk's result to disk, building one file over time.
# First chunk: create the file WITH a header. Later chunks: append WITHOUT one,
# so the final file has a single header. R NA is written as '-'.
# Each chunk is sorted on its own, so the final file is NOT globally sorted.
write_part <- function(x, path, first) {
    fwrite(x, path, sep="\t", quote=FALSE, na="-", append=!first, col.names=first)
}

# normalise_id(): chromosome nomenclature normalisation
norm_chr <- function(x) {
    x <- sub("^chr", "", x)
    x[!is.na(x) & x == "M"] <- "MT"
    x
}

# Single-letter VEP alleles can also represent trimmed insertions. Require that
# the letter is a literal ALT in the original record and REF is one base too.
allele_keys <- function(vep, variants) {
    idx <- match(vep$ID, variants$ID)
    if (anyNA(idx)) stop("VEP ID absent from variants.table")
    ref <- variants$REF[idx]
    alt <- vep$Allele
    keys <- rep(NA_character_, nrow(vep))
    eligible <- which(!is.na(ref) & !is.na(alt) & grepl("^[ACGT]$", ref) &
                      grepl("^[ACGT]$", alt) & ref != alt)
    if (length(eligible)) {
        belongs <- mapply(function(a, choices) a %in% choices,
                          alt[eligible], strsplit(variants$ALT[idx[eligible]], ",", fixed=TRUE),
                          USE.NAMES=FALSE)
        eligible <- eligible[belongs]
        keys[eligible] <- paste(norm_chr(variants$CHROM[idx[eligible]]),
                               variants$POS[idx[eligible]], ref[eligible], alt[eligible], sep="_")
    }
    keys
}

# Transcript equality alone does not prove effect equality. Check the amino-acid
# substitution AND its position. For splice-site source records, require a VEP
# donor/acceptor consequence instead. Unmatched effects keep variant-level fields.
transcript_keys <- function(vep) {
    feature <- sub("\\.[0-9]+$", "", vep$Feature)
    aa <- gsub("X", "*", vep$Amino_acids, fixed=TRUE)
    position <- sub("/[0-9]+$", "", vep$Protein_position)
    effect <- rep(NA_character_, nrow(vep))
    coding <- which(grepl("^[A-Z*]/[A-Z*]$", aa) & grepl("^[0-9]+$", position))
    effect[coding] <- paste(aa[coding], position[coding], sep=":")
    splice <- which(vep$Amino_acids %in% c("-", ".") &
                    grepl("(^|,)(splice_donor_variant|splice_acceptor_variant)(,|$)", vep$Consequence))
    effect[splice] <- "SPLICE"
    good <- which(!is.na(vep$DBNSFP_KEY) & !is.na(effect) &
                  vep$Feature_type == "Transcript" & grepl("^ENST[0-9]+$", feature))
    keys <- rep(NA_character_, nrow(vep))
    keys[good] <- paste(vep$DBNSFP_KEY[good], feature[good], effect[good], sep="|")
    keys
}

# --- MAIN --------------------------------------------------------------------

main <- function() {
    script <- sub("^--file=", "", grep("^--file=", commandArgs(), value=TRUE)[1])
    helper <- file.path(dirname(normalizePath(script)), "subset_dbnsfp.py")

    db <- Sys.getenv("DBNSFP_VARIANTS", "/data/ucct/bi/references/refgenie/alias/Homo_sapiens_dbNSFP/GRCh38/v5.4/dbNSFP5.4a_grch38.gz")
    genes_path <- Sys.getenv("DBNSFP_GENES", "dbNSFP_ENSG_gene_GRCh38.txt")
    variant_path <- "vep/variants.table"
    vep_path <- Sys.getenv("MERGE_VEP_FILE", "vep/vep_annot_head.txt")

    for (path in c(helper, db, genes_path, variant_path, vep_path))
        if (!file.exists(path) || file.info(path)$size == 0) stop("Missing or empty: ", path)
    
    variants <- read_table(variant_path)
    required(variants, c("ID", "CHROM", "POS", "REF", "ALT"), "variants.table")
    if (!nrow(variants) || anyNA(variants$ID) || any(variants$ID %in% c("", ".")) ||
        anyDuplicated(variants$ID)) stop("variants.table needs unique non-empty IDs")
    genes <- read_table(genes_path)
    required(genes, c("Gene", "OMIM_id", "Function_description", "Disease_description", "HPO_id", "HPO_name"), "Genes")
    if (!nrow(genes) || anyNA(genes$Gene) || any(genes$Gene %in% c("", ".", "-")) || anyDuplicated(genes$Gene))
        stop("Gene lookup needs unique non-empty Gene IDs")
    setkeyv(variants, "ID")

    # Work in a hidden temporary directory ("staging area") instead of writing
    # straight to the final files. This avoids leaving a mixture of old and new outputs if the script fails partway through.
    # The directory is removed at the end.
    # The final output files are written only after every chunk has completed successfully.
    stage <- tempfile(pattern=".merge_all_", tmpdir=".")
    dir.create(stage)
    logmsg("Temporary directory: ", stage, " (retained for debugging purposes)")

    # ------------------------------------------------------------------------
    # STEP 1. Extract the dbNSFP annotations needed for this case.
    # ------------------------------------------------------------------------
    # The full dbNSFP file is too large to load into R, so a Python helper
    # (subset_dbnsfp.py) reads it with tabix and keeps only the SNVs found in
    # variants.table.
    # The helper also checks that its transcript-level lists are consistent.
    status <- system2(Sys.getenv("PYTHON", "python3"), c(shQuote(helper), "--db", shQuote(db),
                      "--variants", shQuote(variant_path), "--out-dir", shQuote(stage),
                      "--query-mode", shQuote(Sys.getenv("DBNSFP_QUERY_MODE", "indexed"))))
    if (status != 0L) stop("dbNSFP preparation failed")

    # ------------------------------------------------------------------------
    # STEP 2. Load the smaller dbNSFP table, then the gene and case tables.
    # ------------------------------------------------------------------------
    # Relevant columns from the dbNSFP plugin table are selected.
    base <- read_table(file.path(stage, "dbNSFP_variant.tsv"))
    tx <- read_table(file.path(stage, "dbNSFP_transcript.tsv"))
    if (anyDuplicated(base$DBNSFP_KEY) || anyDuplicated(tx$DBNSFP_TRANSCRIPT_KEY))
        stop("Non-unique dbNSFP lookup keys")
    db_columns <- setdiff(c(names(base), names(tx)), c("DBNSFP_KEY", "DBNSFP_TRANSCRIPT_KEY"))
    
    # ------------------------------------------------------------------------
    # STEP 3. Open VEP once, validate the header and process chunk by chunk.
    # ------------------------------------------------------------------------
    con <- file(vep_path, "rt")
    on.exit(close(con), add=TRUE)
    header <- readLines(con, n=1L, warn=FALSE)
    if (!length(header)) stop("VEP has no header")

    names_in <- names(fread(text=paste0(header, "\n"), sep="\t", quote="", check.names=TRUE, header=TRUE))
    need <- c("ID", "Gene", "Allele", "Feature", "Feature_type", "Amino_acids", "Protein_position", "Consequence")
    if (!all(need %in% names_in)) stop("VEP header lacks required matching fields")

    block <- 0L
    total <- 0
    status_counts <- integer()

    repeat {
        lines <- readLines(con, n=chunk_rows, warn=FALSE)
        if (!length(lines)) break
        block <- block + 1L
        if (any(!nzchar(lines))) stop("Empty line in VEP table; check input")

        vep <- fread(text=paste0(paste(c(header, lines), collapse="\n"), "\n"),
                     sep="\t", quote="", header=TRUE, check.names=TRUE, fill=FALSE,
                     colClasses="character", na.strings="NA", showProgress=FALSE)
        if (!identical(names(vep), names_in) || nrow(vep) != length(lines)) stop("Malformed VEP block")
        n <- nrow(vep)
        rm(lines)
        vep[, DBNSFP_KEY := allele_keys(vep, variants)]
        vep[, DBNSFP_TRANSCRIPT_KEY := transcript_keys(vep)]
        # Record why a row has general fields only, full transcript annotations,
        # no source hit, or no eligible SNV. This is not a filter.
        has_variant <- vep$DBNSFP_KEY %in% base$DBNSFP_KEY
        has_tx <- vep$DBNSFP_TRANSCRIPT_KEY %in% tx$DBNSFP_TRANSCRIPT_KEY
        vep[, dbNSFP_match := ifelse(is.na(DBNSFP_KEY), "NOT_SNV",
              ifelse(!has_variant, "NO_DBNSFP_VARIANT", ifelse(!has_tx, "VARIANT_ONLY",
              ifelse(grepl("[|]SPLICE$", DBNSFP_TRANSCRIPT_KEY), "TRANSCRIPT_SPLICE", "TRANSCRIPT_AND_PROTEIN"))))]
        

        # --- JOIN 1: VEP LEFT JOIN dbNSFP ------------------------------
        # Different keys keep variant-level fields independent of transcript hits.
        # A missing hit produces '-' cells, not a missing VEP row.
        joined <- merge(vep, base, by="DBNSFP_KEY", all.x=TRUE, sort=FALSE)
        joined <- merge(joined, tx, by="DBNSFP_TRANSCRIPT_KEY", all.x=TRUE, sort=FALSE)
        # Remove temporary keys only; keep ID/Allele and the new audit columns.
        joined[, c("DBNSFP_KEY", "DBNSFP_TRANSCRIPT_KEY") := NULL]
        if (nrow(joined) != n) stop("Unexpected dbNSFP row multiplication")
        write_part(joined, file.path(stage, "vep_plugin.txt"), block==1L)

        # --- JOIN 2: previous result LEFT JOIN gene descriptions on Gene ----
        with_genes <- merge(joined, genes, by="Gene", all.x=TRUE, sort=TRUE)
        write_part(with_genes, file.path(stage, "vep_dbNSFP.txt"), block==1L)
        if (nrow(with_genes) != n) stop("Gene join multiplied VEP rows")

        # --- JOIN 3: previous result INNER JOIN genotypes on original ID -----
        # All IDs were checked earlier, so this join must preserve every VEP row.
        if (!annotations_only) {
            gt <- variants[.(unique(with_genes$ID)), nomatch=0L]
            final <- merge(gt, with_genes, by="ID", all=FALSE, sort=TRUE)
            if (nrow(final) != n) stop("Genotype join lost or multiplied VEP rows")
            write_part(final, file.path(stage, "variants_annot_all.tab"), block==1L)
            rm(gt, final)
        }
        # Counts refer to annotation rows, not unique variants. Release the block
        # before reading the next one; the lookups and genotype table stay in RAM.
        counts <- table(joined$dbNSFP_match)
        for (label in names(counts)) {
            if (!(label %in% names(status_counts))) status_counts[label] <- 0L
            status_counts[label] <- status_counts[label] + as.numeric(counts[label])
        }
        total <- total + n
        logmsg("Block ", block, ": VEP=", total, "; final=", total)
        rm(vep, joined, with_genes)
        invisible(gc())
    }
    if (!total) stop("No VEP rows")

    # ------------------------------------------------------------------------
    # STEP 4. Publish only after every chunk has completed.
    # ------------------------------------------------------------------------
    logmsg("Publishing complete results")
    files <- c("vep_plugin.txt", "vep_dbNSFP.txt", "dbNSFP_case.txt")
    for (name in files)
        if (!file.rename(file.path(stage, name), file.path("vep", name))) stop("Cannot publish ", name)
    if (!annotations_only && !file.rename(file.path(stage, "variants_annot_all.tab"), "variants_annot_all.tab"))
        stop("Cannot publish final table")
    unlink(stage, recursive=TRUE)
    for (label in names(status_counts)) logmsg(label, ": ", status_counts[label])
    logmsg(if (annotations_only) "ANNOTATIONS_COMPLETED: " else "MERGE_COMPLETED: ",
           total, " VEP rows; ", total, if (annotations_only) " rows in vep_dbNSFP.txt" else " final rows")
}

main()
