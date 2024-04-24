# Assembly

Here, we describe the results from the Assembly pipeline for de novo genome assembly and annotation.

* **assemblies**: a symbolic link to the raw reads associated with the resolution.
* **kmerfinder_summary.csv**: a .csv file containing the main results from kmerfinder.
* **multiqc_report.html**: an interactive report containing the results from MultiQC (kmerfinder, QUAST, quality control, etc.)
* **quast_GCF_XXXXXXXXX.X_ASMXXXXXv2_report.html**: an interactive report obtained after the execution of QUAST, providing different metrics about the assembly QC against the reference.
* **quast_global_report.html**: an interactive report obtained after the execution of QUAST, providing different metrics about the global assembly QC.
* **summary_assembly_metrics_mqc.csv**: a custom table containing most relevant assembly QC metrics.

> [!WARNING]
> Software's versions used in this analysis can be obtained from the  `MultiQC` report.