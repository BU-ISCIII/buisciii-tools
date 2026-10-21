#!/usr/bin/env Rscript
# Attach original coordinates, alleles, FILTER and sample genotypes to VEP rows.
# Usage: Rscript merge_parse.R vep/variants.table vep/vep_dbNSFP.txt
suppressPackageStartupMessages(library(data.table))
setDTthreads(as.integer(Sys.getenv("SLURM_CPUS_PER_TASK", "1")))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("Expected variants.table and annotated VEP table")

variants <- fread(args[1], sep = "\t", header = TRUE, quote = "",
                  colClasses = "character", na.strings = NULL, check.names = TRUE)
annotations <- fread(args[2], sep = "\t", header = TRUE, quote = "",
                     colClasses = "character", na.strings = NULL, check.names = TRUE)
if (!"ID" %in% names(variants) || !"ID" %in% names(annotations)) {
    stop("Both tables require an ID column")
}
if (anyNA(variants$ID) || any(variants$ID %in% c("", ".")) ||
    anyDuplicated(variants$ID)) {
    stop("variants.table must contain one row per non-empty variant ID")
}

# Each VEP transcript/allele row
# receives the genotype fields for its original VCF record.
result <- merge(variants, annotations, by = "ID", all.x = FALSE, all.y = FALSE)
message("Genotype join: ", nrow(annotations), " annotation rows -> ",
        nrow(result), " rows")
if (nrow(result) != nrow(annotations)) {
    stop("Some annotation IDs have no match in variants.table; check the inputs")
}

output <- "./variants_annot_all.tab"
fwrite(result, paste0(output, ".partial"), sep = "\t", na = "-", quote = FALSE)
if (!file.rename(paste0(output, ".partial"), output)) stop("Cannot publish ", output)
