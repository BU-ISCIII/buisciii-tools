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
  make_option(c("-r", "--rnaseq_dir"    ), type="character" , default='../../01-rnaseq'      , metavar="path"   , help="Path to rna-seq results"                                                      ),
  make_option(c("-c", "--clinical_data" ), type="character" , default='../clinical_data.txt' , metavar="path"   , help="Path to clinical data file"                                                   ),
  make_option(c("-g", "--group_col"     ), type="character" , default='Group'                , metavar="string" , help="Colname with the sample classes in sample_data of the experiment for the DE." ),
  make_option(c("-n", "--norm_counts"   ), type="logical"   , default=FALSE                  , metavar="boolean", help="Create table with normalized counts"                                          ),
  make_option(c("-q", "--quality_plots" ), type="logical"   , default=TRUE                   , metavar="boolean", help="Create quality plots or not."                                                 ),
  make_option(c("-t", "--time_order"    ), type="character" , default=NULL                   , metavar="string" , help="Order to plot the dates as list, eg: 15D,45D,3M."                                                     )
)

opt_parser <- OptionParser(option_list=option_list)
opt        <- parse_args(opt_parser)

cat(blue$bold("########################\nRunning analysis with the following params:\n###############################\n"))
cat(blue("-Path to RNAseq input folder: ")) + cat(blue(opt$rnaseq_dir))+cat(blue("\n"))
cat(blue("-Path to samples clinical data: ")) + cat(blue(opt$clinical_data))+cat(blue("\n"))
cat(blue("-Column with the group info: ")) + cat(blue(opt$group_col))+cat(blue("\n"))

if (is.null(opt$time_order)) {
    print_help(opt_parser)
    stop("You need to specify the order for the dates.", call.=FALSE)
} else {
  time_order <- unlist(strsplit(opt$time_order, ","))
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

cat(blue("Time order: ")) + cat(blue(time_order)) +cat(blue("\n"))

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
  time_col <- which(colnames(samples) %in% c("time"))
  samples <- samples[,c(1,compare_col, time_col)]
  colnames(samples) <- c("names","condition", "time")
  rownames(samples) <- samples$names
  return(samples)
}

################################################
## DESEQ2                                     ##
################################################

####DIFFERENTIAL EXPRESSION#########################

deseq2_analysis <- function(txi_data, samples){
  ddsTxi <- DESeqDataSetFromTximport(txi_data,
                                     colData = samples,
                                     design = ~ condition + time + condition:time)
  dds <- ddsTxi[ rowSums(counts(ddsTxi)) >= 1, ]
  dds <- DESeq(dds, test = "LRT", reduced = ~ condition + time)
  res <- results(dds)
  return(list(dds_matrix = dds, results =res))
}

####NORMALIZATION#########################

normalized_counts <- function(dds_table){
  ntd <- normTransform(dds_table)
  rld <- rlog(dds_table, blind=FALSE)
  vsd <- varianceStabilizingTransformation(dds_table, blind=FALSE)
  return(list(dds_norm=dds_table, norm = ntd, rlogtrans =rld, varstab=vsd))
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
  colnames(to_plot_geneid) <- "GeneID"
  to_plot_geneid_merged <- merge(x = to_plot_geneid, y = gene_genename, by.x="GeneID", by.y = "GENEID", all.x = TRUE, all.y = FALSE)
  rownames(to_plot) <- to_plot_geneid_merged$gene_name
  pdf(file="Differential_expression/DESeq2/heatmapCount_top20_differentially_expressed.pdf")
  pheatmap(to_plot, cluster_rows=TRUE, show_rownames=TRUE,
           cluster_cols=TRUE, annotation_col=df, main="Top 20 significant genes")
  dev.off()
}


####QUALITY PLOTS#########################

quality_plots <- function(norm_data){
  ###########SAMPLE DISTANCE##############
  sampleDists <- dist( t( assay(norm_data$rlogtrans) ) )
  
  sampleDistMatrix <- as.matrix( sampleDists )
  colours = colorRampPalette(rev(brewer.pal(9, "Blues"))) (255)
  pdf(file="Quality_plots/DESeq2/heatmap_sample_to_sample.pdf")
  pheatmap(sampleDistMatrix,
           clustering_distance_rows=sampleDists,
           clustering_distance_cols=sampleDists,
           col=colours)
  dev.off()
  
  #############PCA PLOTS################
  pcaData <- plotPCA(norm_data$rlogtrans, intgroup=c("condition"), returnData=TRUE)
  pcaData_2 <- plotPCA(norm_data$varstab, intgroup=c("condition"), returnData=TRUE)
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
  boxplot(assay(norm_data$norm), col="blue", las =2)
  title(main="Boxplot: normalized counts")
  boxplot(log10(assays(norm_data$dds_norm)[["cooks"]]), range=0, las=2)
  title(main="Boxplot see outliers: cooks distance")
  dev.off()
  
  #############DISPERSION PLOTS################
  pdf(file="Quality_plots/DESeq2/plotDispersions.pdf")
  plotDispEsts(norm_data$dds_norm)
  dev.off()
  
  #############DESVIATION PLOT################
  pdf(file="Quality_plots/DESeq2/plotSD.pdf")
  meanSdPlot(assay(norm_data$norm))
  dev.off()
  
  ##############HCLUST###################
  assay_ntd <- assay(norm_data$norm)
  pdf(file="Quality_plots/DESeq2/cluster_dendrogram.pdf")
  plot(hclust(dist(t(assay_ntd)),method="average"))
  dev.off()
  
  ##############PHEATMAP##############
  select <- order(rowMeans(counts(norm_data$dds_norm,normalized=TRUE)),
                  decreasing=TRUE)[1:20]
  df <- as.data.frame(colData(norm_data$dds_norm)[,c("condition")])
  colnames(df) <- c("Condition")
  rownames(df) <- colnames(norm_data$norm)
  
  to_plot <- assay(norm_data$norm)[select,]
  to_plot_geneid <- as.data.frame(rownames(to_plot))
  colnames(to_plot_geneid) <- "GeneID"
  to_plot_geneid_merged <- merge(x = to_plot_geneid, y = gene_genename, by.x="GeneID", by.y = "GENEID", all.x = TRUE, all.y = FALSE)
  rownames(to_plot) <- to_plot_geneid_merged$gene_name
  
  pdf(file="Quality_plots/DESeq2/heatmapCount_top20_highest_expression.pdf")
  pheatmap(to_plot, cluster_rows=FALSE, show_rownames=TRUE,
           cluster_cols=TRUE, annotation_col=df, main="Normalized counts top 20 more expressed genes")
  dev.off()
  
  ######FULL PHEATMAP#################
  pdf(file="Quality_plots/DESeq2/heatmapCount_all_genes.pdf")
  pheatmap(assay(norm_data$norm), cluster_rows=FALSE, show_rownames=FALSE,
           cluster_cols=TRUE,main="Normalized counts", annotation_col=df)
  dev.off()
}

####TIME SERIES PLOTS#########################
time_series_plots <- function(gene, res, dds) {
  plot_name <- paste(gene, "expression.pdf", sep = "_")
  file_path <- paste("Time_series_plots", plot_name, sep = "/")
  index = which(rownames(res) == gene, arr.ind = TRUE)
  gene_name <- DE_results_merged[index,2]
  fiss <- plotCounts(dds, index, 
                    intgroup = c("time","condition"), returnData = TRUE)
  fiss$time <- factor(fiss$time, levels = time_order)
  p <- ggplot(fiss, aes(x = time, y = count, color = condition, group = condition)) + 
    geom_point() + 
    stat_summary(fun = mean, geom = "line") +
    scale_y_log10() +
    labs(title = paste("Expression evolution of gene: ", gene_name, sep = ""))
  pdf(file=file_path)
  print(p)
  dev.off()
}

####WALD TEST FOR TIME SERIES#########################

wald_test <- function(dds, condition){
  condition_test <- results(dds, name=condition, test="Wald")
  print(condition_test[which.min(condition_test$padj),])
}

####BETAS PLOT FOR TIME SERIES#########################

betas_plot <- function(res, dds) {
  betas <- coef(dds)
  colnames(betas)

  topGenes <- head(order(res$padj),20)
  mat <- betas[topGenes, -c(1,2)]
  thr <- 3
  mat[mat < -thr] <- -thr
  mat[mat > thr] <- thr
  pdf(file="Time_series_plots/betas_pheatmap.pdf")
  pheatmap(mat, breaks=seq(from=-thr, to=thr, length=101),
          cluster_col=TRUE, main = "log2FC of top20 significant genes")
  dev.off()
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

tx2gene <- read.table(file.path(opt$rnaseq_dir, "star_salmon", "tx2gene.tsv"), header = F)
colnames(tx2gene) <- c("TXNAME", "GENEID", "gene_name")
gene_genename <- tx2gene[,c(2:3)]
gene_genename <- gene_genename %>% distinct()

####LOAD CLINICAL DATA FILE #########################
samples_clin_data <- load_sample_data(clinical_data = opt$clinical_data, group = opt$group_col)

####LOAD ESPRESSION DATA #########################
files <- file.path(opt$rnaseq_dir,"star_salmon", samples_clin_data$names, "quant.sf")
names(files) <- samples_clin_data$names
coldata <- data.frame(files, samples_clin_data, stringsAsFactors=FALSE)
if (!all(file.exists(coldata$files))) {
  cat(red("############WARNING############\nNo todos los ficheros existen\n###############################\n"))
}


################################################
################################################
## DIFFERENTIAL EXPRESSION                    ##
################################################
################################################


################################################
################################################
## DIFFERENTIAL EXPRESSION DESEQ2             ##
################################################
################################################

cat(blue("########################\nStarting with DESeq2\n###############################\n"))
txi <- tximport(files, type="salmon", tx2gene=tx2gene)
test_data(samples_data = samples_clin_data, txi_data = txi)

cat(blue("########################\nStarting with differential expression\n###############################\n"))
deseq2_results <- deseq2_analysis(txi_data = txi, samples = samples_clin_data)
mcols(deseq2_results$results, use.names = T)
DE_results <- as.data.frame(deseq2_results$results)

DE_results$GeneID <- row.names(DE_results)
DE_results_merged <- merge(x = gene_genename, y = DE_results, by.x = "GENEID", by.y= "GeneID", all.y = T, all.x=F)

DE_results_merged_sig <- subset(x = DE_results_merged, padj <= 0.05 & (log2FoldChange <= -2 | log2FoldChange >= 2))

dir.create("Differential_expression",showWarnings = FALSE)
dir.create("Differential_expression/DESeq2",showWarnings = FALSE)
write.table(x = DE_results_merged, file = "Differential_expression/DESeq2/Differential_expression.csv", sep = ",", quote = F, col.names = T, row.names = F)
#write.xlsx(x = DE_results_merged, file = "Differential_expression/DESeq2/Differential_expression.xlsx", sheetName = "Diff_exp", col.names = TRUE, row.names = FALSE, append = FALSE, showNA = TRUE, password = NULL)


cat(blue("########################\nStarting with normalization\n###############################\n"))
norm_count <- normalized_counts(dds_table = deseq2_results$dds_matrix)

if (opt$norm_counts) {
  ntd_gene <- as.data.frame(assay(norm_count$norm))
  ntd_gene$GeneID <- rownames(ntd_gene)
  norm_name_table <- merge(x = gene_genename, y = ntd_gene, by.x = "GENEID", by.y= "GeneID", all.y = T, all.x=F)
  write.table(x = norm_name_table, file = "normalized_expression.csv", quote = F, sep = ",", row.names = F, col.names = T)
  #write.xlsx(x = norm_name_table, file = "normalized_expression.xlsx", sheetName = "Norm_exp", col.names = TRUE, row.names = FALSE, append = FALSE, showNA = TRUE, password = NULL)
}

cat(blue("########################\nStarting with data subsettion\n###############################\n"))

differential_plots(res_de = deseq2_results$results, de_results = DE_results, ntd_subset = norm_count$norm, dds_subset = norm_count$dds_norm)

if (opt$quality_plots) {
  cat(blue("########################\nStarting with Quality plots\n###############################\n"))
  dir.create("Quality_plots",showWarnings = FALSE)
  dir.create("Quality_plots/DESeq2",showWarnings = FALSE)
  quality_plots(norm_data = norm_count)
}

cat(blue("########################\nStarting with time series plots\n###############################\n"))

top4 <- rownames(head(deseq2_results$dds_matrix[order(deseq2_results$results$padj),], 4))

dir.create("Time_series_plots",showWarnings = FALSE)

for (gene in top4) {
  time_series_plots(gene, res = deseq2_results$results, dds = deseq2_results$dds_matrix)
}

all_conditions <- resultsNames(deseq2_results$dds_matrix)
for (condition in all_conditions) {
  wald_test(dds = deseq2_results$dds_matrix, condition)
}

betas_plot(res = deseq2_results$results, dds = deseq2_results$dds_matrix)

save.image()
cat(blue("########################\nNumber of genes with padj < 0.05 and log2FC >= |2|:\n"))
cat(blue(nrow(DE_results_merged_sig)))
cat(blue("\n###############################\n"))

cat(green("########################\nPipeline completed succesfully\n###############################\n"))
