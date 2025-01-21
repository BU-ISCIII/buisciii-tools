#!/usr/bin/env Rscript

################################################
################################################
## LOAD LIBRARIES                             ##
################################################
################################################

####DESeq2 libraries
library(DESeq2)
library(tximport)
library(readr)

####fishpond libraries
library(fishpond)
library(tximeta)
library(SummarizedExperiment)

####Other libraries
library(optparse)
#library(xlsx)
#options(java.parameters = "-Xmx4G")
library(dplyr)
library(pheatmap)
library(RColorBrewer)
library(ggplot2)
library(vsn)
library(crayon)
library(tidytable)
library(data.table)

################################################
################################################
## PARSE COMMAND-LINE PARAMETERS              ##
################################################
################################################
cat(cyan$bgRed$bold("########################\nStarting diferential expression pipeline\n###############################\n"))

option_list <- list(
    make_option(c("-d", "--differential_expression" ), type="character" , default='DEG'                  , metavar="string" , help="Type of differential expression to perform. DEG for Differentially expressed genes. DET for differential expressed transcripts. DEM for differential expression miRNAseq"),
    make_option(c("-e", "--deseq2"                  ), type="logical"   , default=TRUE                   , metavar="boolean", help="Perform DESeq2 DE or not."                                                                                                                                               ),
    make_option(c("-f", "--fishpond"                ), type="logical"   , default=TRUE                   , metavar="boolean", help="Perform fishpond DE or not."                                                                                                                                             ),
    make_option(c("-r", "--rnaseq_dir"              ), type="character" , default='../../01-rnaseq'      , metavar="path"   , help="Path to rna-seq results"                                                                                                                                                 ),
    make_option(c("-s", "--sample_data"             ), type="character" , default='../clinical_data.txt' , metavar="path"   , help="Path to clinical data file"                                                                                                                                              ),
    make_option(c("-g", "--group_col"               ), type="character" , default='Group'                , metavar="string" , help="Colname with the sample classes in sample_data of the experiment for the DE."                                                                                            ),
    make_option(c("-i", "--batch_col"               ), type="character" , default='batch'                , metavar="string" , help="Colname of the column with the batch information."                                                                                                                       ),
    make_option(c("-a", "--alpha"                   ), type="integer"   , default=NULL                   , metavar="integer", help="Alpha value to filter genes by p-value before BH correction in padj. Must be between 1 and 0"                                                                            ),
    make_option(c("-t", "--treatment"               ), type="character" , default=NULL                   , metavar="string" , help="Treatment group name."                                                                                                                                                   ),
    make_option(c("-c", "--control"                 ), type="character" , default=NULL                   , metavar="string" , help="Control group name."                                                                                                                                                     ),
    make_option(c("-b", "--batch_effect"            ), type="logical"   , default=FALSE                  , metavar="boolean", help="Correct by batch effect"                                                                                                                                                 ),
    make_option(c("-n", "--norm_counts"             ), type="logical"   , default=FALSE                  , metavar="boolean", help="Create table with normalized counts"                                                                                                                                     ),
    make_option(c("-q", "--quality_plots"           ), type="logical"   , default=TRUE                   , metavar="boolean", help="Create quality plots or not."                                                                                                                                            ),
    make_option(c("-k", "--multiple_groups"         ), type="logical"   , default=FALSE                  , metavar="boolean", help="Perform multiple groups or not. Eg: Group (A+B) vs Group C"                                                                                                              )
)

opt_parser <- OptionParser(option_list=option_list)
opt        <- parse_args(opt_parser)

if (opt$differential_expression != "DEG" && opt$differential_expression != "DET" && opt$differential_expression != "DEM") {
  print_help(opt_parser)
  stop("Differential expression options are: DEG, DET or DEM. Read help for more information", call.=FALSE)
}

if (is.null(opt$treatment)){
    print_help(opt_parser)
    stop("Please provide treatment group name", call.=FALSE)
}

if (is.null(opt$control)){
    print_help(opt_parser)
    stop("Please provide control group name", call.=FALSE)
}

if (grepl(x = opt$treatment, pattern = ",", fixed = TRUE)) {
  opt$treatment <- strsplit(x = opt$treatment, split = ",")[[1]]
}

if (grepl(x = opt$control, pattern = ",", fixed = TRUE)) {
  opt$control <- strsplit(x = opt$control, split = ",")[[1]]
}

if (opt$differential_expression == "DEG" && !opt$deseq2){
  print_help(opt_parser)
  stop("Gene differential expression must be performed using DESeq2", call.=FALSE)
}

if (length(opt$treatment) > 1 | length(opt$control) > 1 ) {
  opt$multiple_groups = TRUE
  cat(blue("########################\nFound more than one group in one of the comparatives.\n"))
  cat(blue("Multiple group set to TRUE.\n###############################\n"))
}

if(opt$multiple_groups){
  if (length(opt$treatment) <= 1 & length(opt$control) <= 1 ) {
    print_help(opt_parser)
    stop("For multiple contidition group, one of the groups must be a list. Eg: -t 'MM_Dif,MZ_Dif' -c 'ZZ_Dif'", call.=FALSE)
  } else{
    deseq_design = '~0 + condition'
    treatment_string <- paste("condition",opt$treatment, sep = "")
    control_string <- paste("condition",opt$control, sep = "")
  }
} else {
  deseq_design = '~ condition'
}

cat(blue$bold("########################\nRunning analysis with the following params:\n###############################\n"))
cat(blue("-Differential espression type: ")) + cat(blue(opt$differential_expression))+cat(blue("\n"))
cat(blue("-Treatment group(s) name(s) for the comparison: ")) + cat(blue(opt$treatment))+cat(blue("\n"))
cat(blue("-Control group(s) name(s) for the comparison: ")) + cat(blue(opt$control))+cat(blue("\n"))
if (opt$multiple_groups) {
  cat(blue("-Multiple grouops are going to be compared in at least one of the classes (treatment or control)\n"))
  cat(blue("Treatment string: ")) + cat(blue(treatment_string)) +cat(blue("\n"))
  cat(blue("Control string: ")) + cat(blue(control_string)) +cat(blue("\n"))
} else{
  cat(blue("-Only one group per class (treatment or control)\n"))
}
if (opt$deseq2) {
  cat(blue("-DESeq2 process set to TRUE\n"))
} else{
  cat(blue("-DESeq2 process set to FALSE\n"))
}
if (opt$fishpond) {
  cat(blue("-Fishpond process set to TRUE\n"))
} else{
  cat(blue("-Fishpond process set to FALSE\n"))
}
cat(blue("-Path to RNAseq input folder: ")) + cat(blue(opt$rnaseq_dir))+cat(blue("\n"))
cat(blue("-Path to samples clinical data: ")) + cat(blue(opt$sample_data))+cat(blue("\n"))
cat(blue("-Column with the group info: ")) + cat(blue(opt$group_col))+cat(blue("\n"))
if (opt$batch_effect) {
  cat(blue("-Batch effect correction set to TRUE\n"))
  cat(blue("-Column with the batch info: ")) + cat(blue(opt$batch_col))+cat(blue("\n"))
} else{
  cat(blue("-Batch effect correction set to FALSE\n"))
}
if (length(opt$alpha) > 0) {
  cat(blue("-Alpha for differential expression: ")) + cat(blue(opt$alpha))+cat(blue("\n"))
} else{
  cat(blue("-Alpha set to FALSE\n"))
}
if (opt$norm_counts) {
  cat(blue("-Saving normalized counts to file\n"))
} else{
  cat(blue("-Not saving normalized counts to file\n"))
}
if (opt$quality_plots) {
  cat(blue("-Creating quality plots\n"))
} else{
  cat(blue("-Skipping quality plots\n"))
}

################################################
################################################
## FUNCTIONS                                  ##
################################################
################################################

################################################
## LOAD DATA                                  ##
################################################

####LOAD CLINICAL DATA FILE#########################
load_sample_data <- function(clinical_data, group) {
  samples <- read.table(clinical_data, header = T)
  compare_col <- which(colnames(samples) %in% group)
  if (opt$batch_effect) {
    batch_col <- which(colnames(samples) %in% opt$batch_col)
    samples <- samples[,c(1,compare_col, batch_col)]
    colnames(samples) <- c("names","condition","batch")
  } else {
    samples <- samples[,c(1,compare_col)]
    colnames(samples) <- c("names","condition")
  }
  rownames(samples) <- samples$names
  return(samples)
}

####LOAD EXPRESSION DATA FILE#########################

####TRANSCRIPTS FISHPOND#########################

load_transcript_data_fishpond <- function(coldata_table, compare_char1, compare_char2){
  #####Load quantification data####
  tximeta_data<- tximeta(coldata_table)
  scaled_inferential_replicates <- scaleInfReps(tximeta_data)

  #####Select data to compare
  scaled_inferential_replicates_selected <- scaled_inferential_replicates[,scaled_inferential_replicates$condition %in% c(compare_char1,compare_char2)]
  scaled_inferential_replicates_selected$condition <- factor(scaled_inferential_replicates_selected$condition, levels=c(compare_char1,compare_char2))

  ####Filter expression minimum 1 count and 1 sample
  scaled_inferential_replicates_selected <- labelKeep(scaled_inferential_replicates_selected, minCount = 1, minN = 1)
  scaled_inferential_replicates_selected <- scaled_inferential_replicates_selected[mcols(scaled_inferential_replicates_selected)$keep,]
  return(scaled_inferential_replicates_selected)
}

#####DEDUPLICATE MIRNA EXPRESSION KEEPING MEDIA#####
deduplicate_expression <- function(counts_dups){
  count_dups <- counts_dups
  count_dups$mirna <- paste(count_dups$mature, count_dups$precursor, sep = "_")
  mature_precursor_list_dups <- count_dups$mirna
  mature_precursor_list <- mature_precursor_list_dups[!duplicated(mature_precursor_list_dups)]
  count_dedup <- NULL
  for (row_mir in 1:length(mature_precursor_list)) {
    mir_name <- as.character(mature_precursor_list[row_mir])
    mir_found <- count_dups[count_dups$mirna %in% mir_name,]
    mir_res <- data.frame(matrix(ncol = 4, nrow = 1))
    colnames(mir_res) <- colnames(count_dups)
    if (nrow(mir_found) == 1) {
      mir_res <- mir_found
    } else {
      mir_res$mature <- as.character(mir_found[1,1])
      mir_res[,2] <- mean(mir_found[,2])
      mir_res$precursor <- as.character(mir_found[1,3])
      mir_res$mirna <- as.character(mir_found[1,4])
    }
    if (length(count_dedup) == 0) {
      count_dedup <- mir_res
    } else {
      count_dedup <- rbind(count_dedup, mir_res)
    }
  }
  return(count_dedup)
}

################################################
## DESEQ2                                     ##
################################################

####DIFFERENTIAL EXPRESSION#########################

deseq2_analysis <- function(txi_data, samples, compare_char1, compare_char2){
  if (opt$batch_effect) {
    if (opt$multiple_groups) {
      ddsTxi <- DESeqDataSetFromTximport(txi_data,
                                         colData = samples,
                                         design = ~0 + batch + condition)
    }
    else{
      if (opt$differential_expression == "DEM") {
        ddsTxi <- DESeqDataSetFromMatrix(round(txi_data),
                                           colData = samples,
                                           design = ~ batch + condition)
        
      } else {
        ddsTxi <- DESeqDataSetFromTximport(txi_data,
                                           colData = samples,
                                           design = ~ batch + condition)
      }
    }
  }
  else{
    if (opt$multiple_groups) {
      ddsTxi <- DESeqDataSetFromTximport(txi_data,
                                         colData = samples,
                                         design = ~0 + condition)
    }
    else{
      if (opt$differential_expression == "DEM") {
        ddsTxi <- DESeqDataSetFromMatrix(round(txi_data),
                                           colData = samples,
                                           design = ~ condition)
      }
      else{
        ddsTxi <- DESeqDataSetFromTximport(txi_data,
                                           colData = samples,
                                           design = ~ condition)
      }
    }
  }
  dds <- ddsTxi[ rowSums(counts(ddsTxi)) >= 1, ]
  dds <- DESeq(dds)
  if (is.null(opt$alpha)){
    if (opt$multiple_groups) {
      res <- results(dds,contrast = list( c(treatment_string),c(control_string) ), listValues = c(1/length(treatment_string),-1/length(control_string)))
    } else {
      res <- results(dds,contrast = c("condition",compare_char1,compare_char2))
    }
  } else{
    if (opt$multiple_groups) {
      res <- results(dds,contrast = list( c(treatment_string),c(control_string) ), listValues = c(1/length(treatment_string),-1/length(control_string)), alpha = opt$alpha)
    } else {
      res <- results(dds,contrast = c("condition",compare_char1,compare_char2), alpha = opt$alpha)
    }
  }
  return(list(dds_matrix = dds, results =res))
}

####NORMALIZATION#########################

normalized_counts <- function(dds_table){

  ntd <- normTransform(dds_table)
  if (opt$batch_effect) {
    mat_ntd <- assay(ntd)
    mat_ntd <- limma::removeBatchEffect(mat_ntd, ntd$Batch)
    assay(ntd) <- mat_ntd
  }

  rld <- rlog(dds_table, blind=FALSE)
  if (opt$batch_effect) {
    mat_rld <- assay(rld)
    mat_rld <- limma::removeBatchEffect(mat_rld, rld$Batch)
    assay(rld) <- mat_rld
  }

  vsd <- varianceStabilizingTransformation(dds_table, blind=FALSE)
  if (opt$batch_effect) {
    mat_vsd <- assay(vsd)
    mat_vsd <- limma::removeBatchEffect(mat_vsd, vsd$Batch)
    assay(vsd) <- mat_vsd
  }

  if (opt$batch_effect) {
    mat_dds <- assay(dds_table)
    mat_dds <- limma::removeBatchEffect(mat_dds, dds_table$Batch)
    assay(dds_table) <- mat_dds
  }

  return(list(dds_norm=dds_table, norm = ntd, rlogtrans =rld, varstab=vsd))
}


####SUBSETTING#########################

subset_samples <- function(samples_data, compare_char1, compare_char2, norm_data){
  row_1 <- which(samples_data$condition %in% compare_char1)
  row_2 <- which(samples_data$condition %in% compare_char2)
  row_nums <- c(row_1,row_2)
  sample_list <- rownames(samples_data[row_nums,, drop = FALSE])

  dds_subset <- norm_data$dds_norm[,sample_list]
  ntd_subset <- norm_data$norm[,sample_list]
  rld_subset <- norm_data$rlogtrans[,sample_list]
  vsd_subset <- norm_data$varstab[,sample_list]
  return(list(subset_dds = dds_subset, subset_ntd =ntd_subset, subset_rld=rld_subset, subset_vsd=vsd_subset))
}


####DE PLOTS#########################

differential_plots <- function(res_de, de_results, ntd_subset, dds_subset){
  #MA-plotThe  MA-plot  shows  the  log2  fold  changes  from  the  treatment  over  the  meanof  normalized  counts.
  #The  average  of  counts  normalized  by  size  factor.
  pdf(file="Differential_expression/DESeq2/maPlot_all.pdf")
  plotMA( res_de, ylim = c(-1, 1) )
  dev.off()

  #############DISPERSION PLOTS################
  pdf(file="Differential_expression/DESeq2/pvalues.pdf")
  hist( res_de$pvalue, breaks=20, col="grey", main = "pvalues test for differential expression")
  dev.off()

  ##############PHEATMAP##############
  assay_ntd <- assay(ntd_subset)
  ordered_table <- de_results[order(de_results$pvalue, -abs(de_results$log2FoldChange)),]
  ordered_table$identifier <- rownames(ordered_table)
  col_num <- which(colnames(ordered_table) == "identifier")
  top_sig_genes <- ordered_table[1:20,col_num]
  select <- which(rownames(assay_ntd) %in% top_sig_genes)
  df <- as.data.frame(colData(dds_subset)[,c("condition")])
  colnames(df) <- c("condition")
  rownames(df) <- colnames(ntd_subset)
  to_plot <- assay_ntd[select,]
  to_plot_geneid <- as.data.frame(rownames(to_plot))
  if ( opt$differential_expression == "DEG") {
    colnames(to_plot_geneid) <- "GeneID"
    to_plot_geneid_merged <- merge(x = to_plot_geneid, y = gene_genename, by.x="GeneID", by.y = "GENEID", all.x = TRUE, all.y = FALSE)
    rownames(to_plot) <- to_plot_geneid_merged$gene_name
  }

  if ( opt$differential_expression == "DET") { 
    colnames(to_plot_geneid) <- "TranscriptID"
    rownames(to_plot) <- to_plot_geneid$TranscriptID
  }

  pdf(file="Differential_expression/DESeq2/heatmapCount_top20_differentially_expressed.pdf")
  pheatmap(to_plot, cluster_rows=TRUE, show_rownames=TRUE,
           cluster_cols=TRUE, annotation_col=df, main="Top 20 significant genes")
  dev.off()
}


####QUALITY PLOTS#########################

quality_plots <- function(data_subset){
  ###########SAMPLE DISTANCE##############
  sampleDists <- dist( t( assay(data_subset$subset_rld) ) )

  sampleDistMatrix <- as.matrix( sampleDists )
  colours = colorRampPalette(rev(brewer.pal(9, "Blues"))) (255)
  pdf(file="Quality_plots/DESeq2/heatmap_sample_to_sample.pdf")
  pheatmap(sampleDistMatrix,
           clustering_distance_rows=sampleDists,
           clustering_distance_cols=sampleDists,
           col=colours)
  dev.off()

  #############PCA PLOTS################
  pcaData <- plotPCA(data_subset$subset_rld, intgroup=c("condition"), returnData=TRUE)
  pcaData_2 <- plotPCA(data_subset$subset_vsd, intgroup=c("condition"), returnData=TRUE)
  percentVar <- round(100 * attr(pcaData, "percentVar"))
  pdf(file="Quality_plots/DESeq2/plotPCA.pdf")
  pca_plot_rld <- ggplot(pcaData, aes(PC1, PC2, color=condition)) +
    geom_point(size=3) +
    xlab(paste0("PC1: ",percentVar[1],"% variance")) +
    ylab(paste0("PC2: ",percentVar[2],"% variance")) +
    geom_text(aes(label = name), color = "black", size=2, position = position_nudge(y = 0.8)) +
    labs(title="PCA: rlog") +
    coord_fixed()
  pca_plot_vsd <- ggplot(pcaData_2, aes(PC1, PC2, color=condition)) +
    geom_point(size=3) +
    xlab(paste0("PC1: ",percentVar[1],"% variance")) +
    ylab(paste0("PC2: ",percentVar[2],"% variance")) +
    geom_text(aes(label = name), color = "black", size=2, position = position_nudge(y = 0.8)) +
    labs(title="PCA: vsd") +
    coord_fixed()
  print(pca_plot_rld)
  print(pca_plot_vsd)
  dev.off()

  #############BOX PLOTS################
  pdf(file="Quality_plots/DESeq2/boxplot.pdf")
  boxplot(assay(data_subset$subset_ntd), col="blue", las =2)
  title(main="Boxplot: normalized counts")
  boxplot(log10(assays(data_subset$subset_dds)[["cooks"]]), range=0, las=2)
  title(main="Boxplot see outliers: cooks distance")
  dev.off()

  #############DISPERSION PLOTS################
  pdf(file="Quality_plots/DESeq2/plotDispersions.pdf")
  plotDispEsts(data_subset$subset_dds)
  dev.off()

  #############DESVIATION PLOT################
  pdf(file="Quality_plots/DESeq2/plotSD.pdf")
  meanSdPlot(assay(data_subset$subset_ntd))
  dev.off()

  ##############HCLUST###################
  assay_ntd <- assay(data_subset$subset_ntd)
  pdf(file="Quality_plots/DESeq2/cluster_dendrogram.pdf")
  plot(hclust(dist(t(assay_ntd)),method="average"))
  dev.off()

  ##############PHEATMAP##############
  select <- order(rowMeans(counts(data_subset$subset_dds,normalized=TRUE)),
                  decreasing=TRUE)[1:20]
  df <- as.data.frame(colData(data_subset$subset_dds)[,c("condition")])
  colnames(df) <- c("Condition")
  rownames(df) <- colnames(data_subset$subset_ntd)
  
  to_plot <- assay(data_subset$subset_ntd)[select,]
  to_plot_geneid <- as.data.frame(rownames(to_plot))
  if ( opt$differential_expression == "DEG") {
    colnames(to_plot_geneid) <- "GeneID"
    to_plot_geneid_merged <- merge(x = to_plot_geneid, y = gene_genename, by.x="GeneID", by.y = "GENEID", all.x = TRUE, all.y = FALSE)
    rownames(to_plot) <- to_plot_geneid_merged$gene_name
  }

  if ( opt$differential_expression == "DET") { 
    colnames(to_plot_geneid) <- "TranscriptID"
    rownames(to_plot) <- to_plot_geneid$TranscriptID
  }
  
  pdf(file="Quality_plots/DESeq2/heatmapCount_top20_highest_expression.pdf")
  pheatmap(to_plot, cluster_rows=FALSE, show_rownames=TRUE,
           cluster_cols=TRUE, annotation_col=df, main="Normalized counts top 20 more expressed genes")
  dev.off()

  ######FULL PHEATMAP#################
  pdf(file="Quality_plots/DESeq2/heatmapCount_all_genes.pdf")
  pheatmap(assay(data_subset$subset_ntd), cluster_rows=FALSE, show_rownames=FALSE,
           cluster_cols=TRUE,main="Normalized counts", annotation_col=df)
  dev.off()
}

################################################
## fishpond                                   ##
################################################

fishpond_plots <- function(swish_data, expr){
  #############DISPERSION PLOTS################
  pdf(file="Differential_expression/fishpond/maPlot_all.pdf")
  plotMASwish(swish_data, alpha=.05)
  dev.off()

  #############VULCANO PLOTS################
  res1 <- as_tidytable(mcols(swish_data))
  data <- res1
  Expression <- as.factor(ifelse(data$qvalue <= 0.05 & abs(data$log2FC) >= log2(2) , ifelse(data$log2FC >= log2(2) ,'Up qvalue < 0.05','Down qvalue < 0.05'), ifelse(data$pvalue <= 0.05 & abs(data$log2FC) >= log2(2) , ifelse(data$log2FC >= log2(2) ,'Up pvalue < 0.05','Down pvalue < 0.05'),'Not')))

  pdf("Differential_expression/fishpond/vulcano_plot.pdf")
  vulcano_plot <- ggplot(data,aes(x=log2FC,y=-log10(pvalue),colour=Expression)) +
    xlab("log2FC")+ylab("-log10(pvalue)") +
    geom_point(size = 2,alpha=1) +
    ylim(0,7) + xlim(-5,5) +
    scale_color_manual(values=c("blue", "green","grey", "red", "orange"))+
    geom_vline(xintercept = c(-log2(2), log2(2)), lty = 2,colour="#000000")+
    geom_hline(yintercept = c(-log10(0.05)), lty = 2,colour="#000000") +
    ggtitle("Vulcano plot") +
    theme(plot.title = element_text(hjust = -0.06,size = 20),
          legend.text = element_text(size = 10),
          legend.position = 'right',
          legend.key.size=unit(0.4,'cm'))+
    theme(panel.grid.major =element_blank(), panel.grid.minor = element_blank(),panel.background = element_blank(), axis.line = element_line(colour = "black"),axis.text=element_text(size=12,face = "bold"),axis.title.x=element_text(size=15),axis.title.y=element_text(size=15))
  print(vulcano_plot)
  dev.off()

  #############DISPERSION PLOTS################
  pdf(file="Differential_expression/fishpond/significant_hist.pdf")
  hist(mcols(swish_data)$pvalue, col="grey", main = "pvalues test for differential expression")
  hist(mcols(swish_data)$qvalue, col="grey", main = "qvalues test for differential expression")
  dev.off()

  ##############HCLUST###################
  pdf(file="Quality_plots/fishpond/cluster_dendrogram.pdf")
  plot(hclust(dist(t(expr)),method="average"))
  dev.off()

  ###########SAMPLE DISTANCE##############
  sampleDists <- dist( t( expr ) )

  sampleDistMatrix <- as.matrix( sampleDists )
  colours = colorRampPalette(rev(brewer.pal(9, "Blues"))) (255)
  pdf(file="Quality_plots/fishpond/heatmap_sample_to_sample.pdf")
  pheatmap(sampleDistMatrix,
           clustering_distance_rows=sampleDists,
           clustering_distance_cols=sampleDists,
           col=colours)
  dev.off()

  sig_genes <- subset(DE_data_frame, qvalue<=0.05 & (log2FC>=2 | log2FC<=-2))
  gene_list <- sig_genes$Geneid
  expression_subset <- as.data.frame(expr[which(rownames(expr) %in% gene_list),])
}

################################################
## WARNINGS                                   ##
################################################

test_data <- function(samples_data, txi_data){
  if (all(rownames(samples_data) %in% colnames(txi_data$counts)) == FALSE) {
    print("Warning: Check sample names")
  }
  if (all(rownames(samples_data) == colnames(txi_data$counts)) == FALSE) {
    print("Warning: Check sample names")
  }
}

##############################################################################################################################################
##############################################################################################################################################
##################################################### MAIN                                  ##################################################
##############################################################################################################################################
##############################################################################################################################################


################################################
################################################
## LOAD DATA                                  ##
################################################
################################################

cat(blue("########################\nStarting with loading data\n###############################\n"))

####LOAD TRANSCRIPT RELATION DATA FILE #########################
if (opt$differential_expression != "DEM") {
  tx2gene <- read.table(file.path(opt$rnaseq_dir, "star_salmon", "tx2gene.tsv"), header = F)
  colnames(tx2gene) <- c("TXNAME", "GENEID", "gene_name")
  if ( opt$differential_expression == "DEG") {
    gene_genename <- tx2gene[,c(2:3)]
    gene_genename <- gene_genename %>% distinct()
  }
}

####LOAD CLINICAL DATA FILE #########################
samples_clin_data <- load_sample_data(clinical_data = opt$sample_data, group = opt$group_col)

####LOAD ESPRESSION DATA #########################
if (opt$differential_expression == "DEM") {
  expression_matrix <- NULL
  csv_list <- list.files(path = opt$rnaseq_dir, pattern = "miRNAs_expressed_all_samples*", full.names = TRUE)
  for (sample in samples_clin_data$names) {
    sample_file <- grep(x = csv_list, pattern = sample, value = TRUE)
    sample_counts_dups <- read.table(file = sample_file)
    sample_counts_dups <- sample_counts_dups[,c(1,2,3)]
    colnames(sample_counts_dups) <- c("mature", sample, "precursor")
    sample_counts <- deduplicate_expression(sample_counts_dups)
    sample_counts <- sample_counts[,c(4,2)]
    if (length(expression_matrix) > 0) {
      expression_matrix <- merge(x = expression_matrix, y= sample_counts, by = "mirna", all = TRUE)
    } else {
      expression_matrix <- sample_counts
    }
  }
  rownames(expression_matrix) <- expression_matrix$mirna
} else {
  files <- file.path(opt$rnaseq_dir,"star_salmon", samples_clin_data$names, "quant.sf")
  names(files) <- samples_clin_data$names
  coldata <- data.frame(files, samples_clin_data, stringsAsFactors=FALSE)
  
  if (!all(file.exists(coldata$files))) {
    cat(red("############WARNING############\nNo todos los ficheros existen\n###############################\n"))
  }
}

################################################
################################################
## DIFFERENTIAL EXPRESSION                    ##
################################################
################################################


if ( opt$deseq2 ) {
  ################################################
  ################################################
  ## DIFFERENTIAL EXPRESSION DESEQ2             ##
  ################################################
  ################################################

  cat(blue("########################\nStarting with DESeq2\n###############################\n"))
  if (opt$differential_expression != "DEM") {
    if (opt$differential_expression == "DEG") {
      txi <- tximport(files, type="salmon", tx2gene=tx2gene)
    } 
    else {
      txi <- tximport(files, type="salmon", txOut = TRUE)
    }
    test_data(samples_data = samples_clin_data, txi_data = txi)
  } else {
    expression_matrix <- expression_matrix[,-1]
    cts <- as.matrix(expression_matrix)
    coldata <- samples_clin_data
    if (all(rownames(coldata) %in% colnames(cts)) == FALSE) {
      print("Warning: Check sample names")
    } 
    cts <- cts[, rownames(coldata)]
    all(rownames(coldata) == colnames(cts))
    cts <- as.matrix(cts)
  }

  cat(blue("########################\nStarting with differential expression\n###############################\n"))
  if (opt$differential_expression != "DEM") {
    deseq2_results <- deseq2_analysis(txi_data = txi, samples = samples_clin_data, compare_char1 = opt$treatment, opt$control)
  } else{
    deseq2_results <- deseq2_analysis(txi_data = cts, samples = samples_clin_data, compare_char1 = opt$treatment, opt$control)
  }
  mcols(deseq2_results$results, use.names = T)
  DE_results <- as.data.frame(deseq2_results$results)

  if (opt$differential_expression == "DEG") {
    DE_results$GeneID <- row.names(DE_results)
    DE_results_merged <- merge(x = gene_genename, y = DE_results, by.x = "GENEID", by.y= "GeneID", all.y = T, all.x=F)
  } else if (opt$differential_expression == "DEM"){
    mirna <- row.names(DE_results)
    DE_results$miRNA <- stringr::str_split(string = mirna, pattern = "_", n = 2, simplify = TRUE)[,1]
    DE_results$precursor <- stringr::str_split(string = mirna, pattern = "_", n = 2, simplify = TRUE)[,2]
    DE_results_merged <- DE_results[,c(7,8,1:6)]
  } else {
    DE_results$TranscriptID <- row.names(DE_results)
    DE_results_merged <- merge(x = tx2gene, y = DE_results, by.x = "TXNAME", by.y= "TranscriptID", all.y = T, all.x=F)
  }
  
  DE_results_merged_sig <- subset(x = DE_results_merged, padj <= 0.05 & (log2FoldChange <= -2 | log2FoldChange >= 2))
  
  dir.create("Differential_expression",showWarnings = FALSE)
  dir.create("Differential_expression/DESeq2",showWarnings = FALSE)
  write.table(x = DE_results_merged, file = "Differential_expression/DESeq2/Differential_expression.csv", sep = ",", quote = F, col.names = T, row.names = F)
  #write.xlsx(x = DE_results_merged, file = "Differential_expression/DESeq2/Differential_expression.xlsx", sheetName = "Diff_exp", col.names = TRUE, row.names = FALSE, append = FALSE, showNA = TRUE, password = NULL)


  cat(blue("########################\nStarting with normalization\n###############################\n"))
  norm_count <- normalized_counts(dds_table = deseq2_results$dds_matrix)

  if (opt$norm_counts) {
    if (opt$differential_expression == "DEG") {
      ntd_gene <- as.data.frame(assay(norm_count$norm))
      ntd_gene$GeneID <- rownames(ntd_gene)
      norm_name_table <- merge(x = gene_genename, y = ntd_gene, by.x = "GENEID", by.y= "GeneID", all.y = T, all.x=F)
    } else if (opt$differential_expression == "DET") {
      ntd_gene <- as.data.frame(assay(norm_count$norm))
      ntd_gene$TranscriptID <- rownames(ntd_gene)
      norm_name_table <- merge(x = tx2gene, y = ntd_gene, by.x = "TXNAME", by.y= "TranscriptID", all.y = T, all.x=F)
    } else {
      ntd_gene <- as.data.frame(assay(norm_count$norm))
      mirna <- row.names(ntd_gene)
      ntd_gene$miRNA <- stringr::str_split(string = mirna, pattern = "_", n = 2, simplify = TRUE)[,1]
      ntd_gene$precursor <- stringr::str_split(string = mirna, pattern = "_", n = 2, simplify = TRUE)[,2]
      norm_name_table <- ntd_gene[,c((ncol(ntd_gene)-1),ncol(ntd_gene),1:(ncol(ntd_gene)-2))]
    }
    write.table(x = norm_name_table, file = "normalized_expression.csv", quote = F, sep = ",", row.names = F, col.names = T)
    #write.xlsx(x = norm_name_table, file = "normalized_expression.xlsx", sheetName = "Norm_exp", col.names = TRUE, row.names = FALSE, append = FALSE, showNA = TRUE, password = NULL)
  }

  cat(blue("########################\nStarting with data subsettion\n###############################\n"))
  subset_data <- subset_samples(samples_data = samples_clin_data, compare_char1 = opt$treatment, compare_char2 = opt$control, norm_data = norm_count)

  differential_plots(res_de = deseq2_results$results, de_results = DE_results, ntd_subset = subset_data$subset_ntd, dds_subset = subset_data$subset_dds)

  if (opt$quality_plots) {
    cat(blue("########################\nStarting with Quality plots\n###############################\n"))
    dir.create("Quality_plots",showWarnings = FALSE)
    dir.create("Quality_plots/DESeq2",showWarnings = FALSE)
    quality_plots(data_subset = subset_data)
  }

}

if (opt$differential_expression == "DET" && opt$fishpond) {
  ################################################
  ################################################
  ## DIFFERENTIAL EXPRESSION FISHPOND           ##
  ################################################
  ################################################

  cat(blue("########################\nStarting with fishpond\n###############################\n"))
  dir.create("Differential_expression",showWarnings = FALSE)
  dir.create("Differential_expression/fishpond", showWarnings = FALSE)

  fishpond_input_data <- load_transcript_data_fishpond(coldata_table = coldata, compare_char1 = opt$treatment, compare_char2 = opt$control)

  set.seed(1)
  swish_data <- swish(fishpond_input_data, x="condition", nperms=64)

  #############Significant info##############
  cat(green("###############################\nSignifican transcripts\n###############################\n"))
  cat(green("###############################\nUp genes\n###############################\n"))
  print(table(mcols(swish_data)$pvalue <= .05, mcols(swish_data)$log2FC >= 2))
  cat(green("###############################\nDown genes\n###############################\n"))
  print(table(mcols(swish_data)$pvalue <= .05, mcols(swish_data)$log2FC <= -2))

  #############DE TABLE##############
  DE_matrix <- mcols(swish_data)[,c("log2FC","stat","pvalue","qvalue")]
  DE_data_frame <- as.data.frame(DE_matrix)
  DE_data_frame$Geneid <- rownames(DE_data_frame)
  DE_annot <- merge(tx2gene, DE_data_frame, by.x = "TXNAME", by.y = "Geneid", all.x = FALSE, all.y = TRUE)
  write.table(x = DE_annot, file = "Differential_expression/fishpond/Differential_expression.csv", sep = ",", quote = F, col.names = T, row.names = F)
  #write.xlsx(x = DE_annot, file = "Differential_expression/fishpond/Differential_expression.xlsx", sheetName = "Diff_exp", col.names = TRUE, row.names = FALSE, append = FALSE, showNA = TRUE, password = NULL)

  #############PLOTS##############
  expr <- assay(swish_data)
  dir.create("Quality_plots",showWarnings = FALSE)
  dir.create("Quality_plots/fishpond", showWarnings = FALSE)
  fishpond_plots(swish_data = swish_data, expr = expr)
}
save.image()
cat(blue("########################\nNumber of genes with padj < 0.05 and log2FC >= |2|:\n"))
cat(blue(nrow(DE_results_merged_sig)))
cat(blue("\n###############################\n"))

cat(green("########################\nPipeline completed succesfully\n###############################\n"))

