#!/usr/bin/env Rscript

################################################
################################################
## LOAD LIBRARIES                             ##
################################################
################################################

library(plyr, quietly = TRUE, warn.conflicts = FALSE)
library(dplyr, quietly = TRUE, warn.conflicts = FALSE)
library(tidyr, quietly = TRUE, warn.conflicts = FALSE)
library(stringr, quietly = TRUE, warn.conflicts = FALSE)
library(jsonlite, quietly = TRUE, warn.conflicts = FALSE)
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
    name_user <- str_split(path, "_", simplify = T)[, 5]
    name_host <- tolower(str_split(path, "_", simplify = T)[, 9])
    date_service <- str_split(str_split(path, "_", simplify = T)[, 6], "/", simplify = T)[, 3]

    name_sequence <- as.character(samples_ref$ref[i])
    name_id <- as.character(samples_ref$id[i])

    # path outputfolder
    directorios <- list.dirs(recursive = FALSE)
    patron_workdir <- paste0(name_sequence, "_", date_service)
    workdir <- directorios[grepl(patron_workdir, directorios)][1]

    # totalreads
    json_fastp <- fromJSON(paste0(workdir, "/fastp/", name_id, ".fastp.json"))
    value_totalreads <- json_fastp$summary[["after_filtering"]]$total_reads

    # readshostR1
    table_kraken <- read.table(paste0(workdir, "/kraken2/", name_id, ".kraken2.report.txt"), sep = "\t")
    unclassified_reads <- as.numeric(subset(x = table_kraken, subset = V6 == "unclassified")[2])
    value_readhostr1 <- sum(table_kraken$V3)-unclassified_reads

    # readshosh
    value_readhost <- value_readhostr1 * 2

    # readshost
    value_percreadhost <- round((value_readhost * 100) / value_totalreads, 2)

    # non host reads
    value_nonhostreads <- value_totalreads - value_readhost

    # % non host
    value_percnonhostreads <- round((value_nonhostreads * 100) / value_totalreads, 2)
    
    # Contigs
    assembly_workdir <- paste(workdir, "/assembly", sep = "")
    quast_report_path <- paste("/",list.files(pattern = "transposed_report.tsv", recursive = TRUE, path = assembly_workdir), sep = "")
    table_quast <- read.delim(paste0(assembly_workdir, quast_report_path), skip = 0, header = T, sep = "\t")

    # no quast error
    if (exists("table_quast") == FALSE) {
        value_contigs <- NA
        value_lcontig <- NA
        value_genomef <- NA
    } else {

        sample_data <- subset(table_quast, Assembly == paste(name_id, "scaffolds", sep = "."))
        value_contigs <- as.numeric(sample_data$X..contigs)
        value_lcontig <- as.numeric(sample_data$Largest.contig)
        value_genomef <- as.numeric(as.character(sample_data$Genome.fraction....))
        
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

# characters
columnas_ch <- as.vector(1:5)
df_final[, columnas_ch] <- apply(df_final[, columnas_ch], 2, function(x) as.character(x))

# numeric
columnas_nu <- as.vector(6:length(colnames(df_final)))
df_final[, columnas_nu] <- apply(df_final[, columnas_nu], 2, function(x) as.numeric(as.character(x)))

# Write table csv
write.table(df_final, "assembly_stats.csv", row.names = F, col.names = T, sep = "\t", quote = F)

# Write table xlsx
write_xlsx(df_final, "assembly_stats.xlsx", format_headers = F)
