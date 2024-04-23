## mRNAseq

Here we describe the results from the mRNAseq pipeline for transcriptomic analysis and differential gene expression.

> [!WARNING]
> Some of the files listed here may not be in your  `RESULTS` folder. It will depend on the analysis you requested.

### Alignment and quantification

<!--  BU-ISCIII
TODO: Penging to discuss which generic/common files are going to be reported in `RESULTS`
-->
> [!WARNING]: Please note that the files in the RESULTS directory are still pending determination by our administrative team. We are currently discussing which generic/common files will be included in this section to ensure that you receive the most relevant and useful information for your analysis.

### Differential expression analysis with DESEQ2

<!--  BU-ISCIII
TODO: Penging to discuss which generic/common files are going to be reported in `RESULTS`
-->
> [!WARNING]: Please note that the files in the RESULTS directory are still pending determination by our administrative team. We are currently discussing which generic/common files will be included in this section to ensure that you receive the most relevant and useful information for your analysis.

### Interpretation of Differential Expression Results:

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