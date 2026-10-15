# ============================================================================
# subset_dbnsfp.awk
# ----------------------------------------------------------------------------
# This is a helper file for Merge_All.R execution.
#
# OBJECTIVE:
# Streams dbNSFP once and writes to stdout only the rows whose variant
# appears in variants.table. This avoids loading the full dbNSFP table into R,
# which has previously proven to cause out-of-memory errors.
#
# INPUT FILES:
#   1- ./vep/variants.table
#      Trio's variant/genotype table. Only its ID column is used (EXAMPLE: chr1_10397_CCCCTAA_C).
#   2- dbNSFP_ENSG_plugin_hg38.txt
#      Full dbNSFP table. It is read line by line; it is NOT loaded into memory (loading the whole table has proven to result in an OOM error).
#      The columns chr, hg38_pos, ref and alt are used to build the comparison key against info from variants.table.
#      EXAMPLE:
#      chr     ref     alt     hg38_pos
#      1       A       C       65565
#
# OUTPUT FILES:
#   A TSV containing:
#     - the original dbNSFP header, unchanged,
#     - and all dbNSFP rows whose key matches a variant's ID.
#   R redirects this stdout to dbNSFP_case.txt, which will be used by Merge_All.R to generate the final variants_annot_all.tab file with all annotated variants.
#
# VARIANT TRANSFORMATION (applied to BOTH sides)
#   - Remove the "chr" prefix              -> chr1_... becomes 1_... (in variants.table)
#   - Rename "M_" to "MT_" (if any)        -> M_...    becomes MT_... (chrM --> MT, taking variants.table)
#   So "chr1_123_A_G" and "1_123_A_G" are treated the same way, for instance.

BEGIN { FS=OFS="\t" }
function fail(msg) { print "ERROR: " msg > "/dev/stderr"; bad=1; exit 2 }
function normalise(id) { sub(/^chr/, "", id); sub(/^M_/, "MT_", id); return id }
{ sub(/\r$/, "") }
# First input: variants.table. Only its set of IDs stays in memory.
FNR==NR {
    if (FNR==1) {
        for (i=1; i<=NF; i++) if ($i=="ID") { idcol=i; idcols++ }
        if (idcols!=1) fail("variants.table should have an ID column")
        next
    }
    if ($idcol=="" || $idcol==".") fail("ID empty in variants.table")
    wanted[normalise($idcol)]=1
    ncase++
    next
}
# Second input: identify the dbNSFP coordinate/allele columns and save their location.
FNR==1 {
    for (i=1; i<=NF; i++) col[$i]=i
    if (!("chr" in col) || !("hg38_pos" in col) ||
        !("ref" in col) || !("alt" in col))
        fail("dbNSFP should have chr, hg38_pos, ref & alt columns")
    header=1
    print
    next
}
# Stream dbNSFP rows: compare dbNSFP and variants.table rows based on variant ID's and save the dbNSFP row only if it matches a reported variant.
{
    key=normalise($(col["chr"]) "_" $(col["hg38_pos"]) "_" $(col["ref"]) "_" $(col["alt"]))
    if (key in wanted) { print; selected++ }
    scanned++
    if (scanned % 10000000 == 0)
        printf "dbNSFP: %.0f rows scanned; %.0f selected\n", scanned, selected > "/dev/stderr"
}
# Status and progress go to stderr so stdout remains a clean TSV for R.
END {
    if (bad) exit 2
    if (!ncase || !header) fail("Headless or empty entry")
    printf "dbNSFP: %.0f rows of the case; %.0f scanned rows; %.0f selected\n", ncase, scanned, selected > "/dev/stderr"
}
