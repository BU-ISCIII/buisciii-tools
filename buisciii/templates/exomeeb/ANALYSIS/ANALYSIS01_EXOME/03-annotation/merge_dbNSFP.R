#!/usr/bin/env Rscript
# Add gene descriptions to the existing VEP/plugin annotations.
# Usage: Rscript merge_dbNSFP.R vep/vep_annot_head.txt dbNSFP_ENSG_gene_GRCh38.txt
suppressPackageStartupMessages(library(data.table))
setDTthreads(as.integer(Sys.getenv("SLURM_CPUS_PER_TASK", "1")))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("Expected VEP table and dbNSFP gene table")

# Read literal TSV fields as text: retain IDs, '#' inside descriptions and
# leading zeroes.
vep <- fread(args[1], sep = "\t", header = TRUE, quote = "",
             colClasses = "character", na.strings = NULL, check.names = TRUE)
genes <- fread(args[2], sep = "\t", header = TRUE, quote = "",
               colClasses = "character", na.strings = NULL, check.names = TRUE)
if (!all(c("ID", "Gene") %in% names(vep)) || !"Gene" %in% names(genes)) {
    stop("VEP requires ID and Gene; the gene table requires Gene")
}
if (anyNA(genes$Gene) || any(genes$Gene %in% c("", ".", "-"))) {
    stop("Missing Gene identifier in the dbNSFP gene table")
}

# Keep every VEP row, including
# transcripts/variants without a matching gene description.
result <- merge(vep, genes, by = "Gene", all.x = TRUE, all.y = FALSE,
                allow.cartesian = TRUE)
message("Gene join: ", nrow(vep), " VEP rows -> ", nrow(result), " rows")

# Publish after the complete table has been written successfully.
output <- "./vep/vep_dbNSFP.txt"
fwrite(result, paste0(output, ".partial"), sep = "\t", na = "-", quote = FALSE)
if (!file.rename(paste0(output, ".partial"), output)) stop("Cannot publish ", output)
