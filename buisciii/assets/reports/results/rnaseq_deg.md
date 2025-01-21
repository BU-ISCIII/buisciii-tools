# mRNAseq (DEG): results

Here we describe the results from the mRNAseq pipeline for transcriptomic analysis and differential gene expression.

> [!WARNING]
> Some of the files listed here may not be in your  `RESULTS` folder. It will depend on the analysis you requested.

## Alignment and quantification

<!--  BU-ISCIII
TODO: Penging to discuss which generic/common files are going to be reported in `RESULTS`
-->
> [!WARNING]
> Please note that the files in the RESULTS directory are still pending determination by our administrative team. We are currently discussing which generic/common files will be included in this section to ensure that you receive the most relevant and useful information for your analysis.

## Differential expression analysis with DESEQ2

<!--  BU-ISCIII
TODO: Penging to discuss which generic/common files are going to be reported in `RESULTS`
-->
> [!WARNING]
> Please note that the files in the RESULTS directory are still pending determination by our administrative team. We are currently discussing which generic/common files will be included in this section to ensure that you receive the most relevant and useful information for your analysis.

## Interpretation of Differential Expression Results:

For each comparison conducted, a separate folder has been created, following the naming convention outlined below:

    1_Treatment1_Control1/
    2_Treatment2_Control2/
    3_Treatment3_Control3/
    4_Treatment1_Treatment2_Treatment3_Control1_Control2_Control3/

Within each folder, you will find the results of the differential expression analysis. When interpreting the results, it's important to note that:

    A positive log2FC indicates that the mRNA is overexpressed in the Treatment group compared to the Control group.
    Conversely, a negative log2FC suggests that the mRNA is downregulated in the Treatment group compared to the Control group.

Additionally, the file `normalized_expression.xlsx` contains the normalized expression counts matrix, providing further insight into the expression levels of the mRNAs across the experimental conditions.

> [!WARNING]
> Software's versions used in this analysis can be obtained from the  `MultiQC` report.

### Description of output files
- `<EXPERIMENT>/Differential_expression/DESeq2/Differential_expression.csv`: This file contains the results of the differential expression analysis performed using DESeq2, including information on differentially expressed genes and associated statistical metrics such as fold change, p-values, and adjusted p-values.

- `<EXPERIMENT>/Differential_expression/DESeq2/heatmapCount_top20_differentially_expressed.pdf`: This PDF file presents a heatmap visualization displaying the expression patterns of the top 20 differentially expressed genes, clustered by sample distance, as determined by the DESeq2 analysis.

- `<EXPERIMENT>/Differential_expression/DESeq2/maPlot_all.pdf`: This PDF file illustrates MA plots depicting the log fold changes (M) versus the mean average (A) expression levels of all genes analyzed in the DESeq2 differential expression analysis.

- `<EXPERIMENT>/Differential_expression/DESeq2/pvalues.pdf`: This PDF file provides graphical representations, such as histograms or scatter plots, illustrating the distribution and significance of p-values calculated during the DESeq2 analysis.

- `<EXPERIMENT>/Quality_plots/DESeq2/boxplot.pdf`: This PDF file displays boxplots depicting the distribution of normalized count expression values values across samples, allowing for the assessment of data variability and potential batch effects.

- `<EXPERIMENT>/Quality_plots/DESeq2/cluster_dendrogram.pdf`: This PDF file presents a dendrogram visualization illustrating the hierarchical clustering of samples based on gene expression profiles, enabling the identification of sample similarities and differences.

- `<EXPERIMENT>/Quality_plots/DESeq2/heatmapCount_all_genes.pdf`: This PDF file contains a heatmap visualization showing the expression patterns of all genes analyzed in the experiment, facilitating the identification of gene expression trends and patterns.

- `<EXPERIMENT>/Quality_plots/DESeq2/heatmapCount_top20_highest_expression.pdf`: This PDF file presents a heatmap visualization highlighting the expression patterns of the top 20 genes with the highest expression levels across samples, aiding in the identification of highly expressed genes.

- `<EXPERIMENT>/Quality_plots/DESeq2/heatmap_sample_to_sample.pdf`: This PDF file contains a heatmap visualization illustrating the pairwise sample-to-sample correlation matrix based on gene expression profiles, enabling the assessment of sample similarities and reproducibility.

- `<EXPERIMENT>/Quality_plots/DESeq2/plotDispersions.pdf`: This PDF file displays dispersion plots showing the relationship between the mean expression levels and the dispersion estimates for each gene, allowing for the assessment of data variability and the adequacy of the statistical model.

- `<EXPERIMENT>/Quality_plots/DESeq2/plotPCA.pdf`: This PDF file presents a PCA (Principal Component Analysis) plot visualizing the distribution of samples in a multidimensional space based on their gene expression profiles, allowing for the exploration of sample relationships and potential batch effects.

- `<EXPERIMENT>/Quality_plots/DESeq2/plotSD.pdf`:The standard deviation of the transformed data, across samples, against the mean, using the shifted logarithm transformation, the regularized log transformation and the variance stabilizing transformation. This plot enables the assessment of data variability and the identification of potential outliers.

- `99-stats/Quality_plots/`: This folder contains the same quality plots as described above, but they are generated considering all samples in the service without accounting for the expermiental design specified in DESeq2. This allows for a general overview of the data in the service without incorporating the experimental design.
