#!/usr/bin/env Rscript

################################################
################################################
## LOAD LIBRARIES                             ##
################################################
################################################

library(plyr, quietly = TRUE, warn.conflicts = FALSE)
library(dplyr, quietly = TRUE, warn.conflicts = FALSE)
library(tidyr, quietly = TRUE, warn.conflicts = FALSE)
library(readxl, quietly = TRUE, warn.conflicts = FALSE)
library(stringr, quietly = TRUE, warn.conflicts = FALSE)
library(jsonlite, quietly = TRUE, warn.conflicts = FALSE)
library(writexl, quietly = TRUE, warn.conflicts = FALSE)
library(writexl, quietly = TRUE, warn.conflicts = FALSE)

################################################
################################################
## DATA          ###############################
################################################
################################################

# PATHS
path <- getwd()
samples_ref <- read.table(paste0(path, "/samples_ref.txt"), header = F)

if (ncol(samples_ref) == 2) {
    colnames(samples_ref) <- c("id", "ref")
} else {
    colnames(samples_ref) <- c("id", "ref", "host")
}

# Fastq path

fastq_names <- list.files("../../RAW/")
path_run <- Sys.readlink(paste0("../../RAW/", fastq_names[1]))

# columnas
columnas <- "run\tuser\thost\tVirussequence\tsample\ttotalreads\treadshostR1\treadshost\t%readshost\tNon-host-reads\t%Non-host-reads\tContigs\tLargest_contig\t%Genome_fraction"
name_columns <- as.vector(str_split(columnas, "\t", simplify = T))

list_assembly <- list(0)
for (i in 1:nrow(samples_ref)) {

    # Run, user, host and sequence
    name_run <- str_split(path_run, "/", simplify = T)[, 4]
    name_user <- str_split(path, "_", simplify = T)[, 6]
    name_host <- tolower(str_split(path, "_", simplify = T)[, 10])
    date_service_1 <- str_split(path, "_", simplify = T)[, 7]
    date_service <- str_split(date_service_1, "/", simplify = T)[, 3]

    name_sequence <- samples_ref$ref[i]
    name_id <- samples_ref$id[i]

    # path outputfolder
    directorios <- list.dirs()
    patron_workdir <- paste0(name_sequence, "_", date_service)
    workdir <- directorios[grepl(patron_workdir, directorios)][1]

    # totalreads
    json_fastp <- fromJSON(paste0(workdir, "/fastp/", name_id, ".fastp.json"))
    value_totalreads <- json_fastp$summary[["after_filtering"]]$total_reads

    # readshostR1
    table_kraken <- read.table(paste0(workdir, "/kraken2/", name_id, ".kraken2.report.txt"), sep = "\t")
    value_readhostr1 <- table_kraken$V2[table_kraken$V5 == 1]

    # readshosh
    value_readhost <- value_readhostr1 * 2

    # readshost
    value_percreadhost <- table_kraken$V1[table_kraken$V5 == 1]

    # non host reads
    value_nonhostreads <- value_totalreads - value_readhost

    # % non host
    value_percnonhostreads <- round((value_readhost * 100) / value_totalreads, 2)

    # Contigs
    table_quast <- read.csv2(paste0(workdir, "/assembly/spades/rnaviral/quast/transposed_report.tsv"), skip = 0, sep = "\t", header = T)

    # no quast error
    if (exists("table_quast") == FALSE) {
        value_contigs <- NA
        value_lcontig <- NA
        value_genomef <- NA
    } else {
        table_quast$id <- str_split(table_quast$Assembly, ".scaffolds", simplify = T)[, 1]
        table_ref_quast <- join(table_quast, samples_ref, by = "id")

        value_contigs <- suppressWarnings(as.numeric(table_ref_quast$X..contigs[table_ref_quast$id == name_id & table_ref_quast$ref == name_sequence]))
        value_lcontig <- suppressWarnings(as.numeric(table_ref_quast$Largest.contig[table_ref_quast$id == name_id & table_ref_quast$ref == name_sequence]))
        value_genomef <- suppressWarnings(as.numeric(table_ref_quast$Genome.fraction....[table_ref_quast$id == name_id & table_ref_quast$ref == name_sequence]))

        # empty values
        # empty values
        if (length(value_contigs) == 0) {
            value_contigs <- NA
        }

        if (length(value_lcontig) == 0) {
            value_lcontig <- NA
        }

        if (length(value_genomef) == 0) {
            value_genomef <- NA
        }
    }

    # Create table
    list_assembly[[i]] <- c(name_run, name_user, name_host, name_sequence, name_id, value_totalreads, value_readhostr1, value_readhost, value_percreadhost, value_nonhostreads, value_percnonhostreads, value_contigs, value_lcontig, value_genomef)
}

df_final <- as.data.frame(do.call("rbind", list_assembly))
colnames(df_final) <- name_columns

# Write table
write.table(df_final, "assembly_stats.csv", row.names = F, col.names = T, sep = "\t", quote = F)
