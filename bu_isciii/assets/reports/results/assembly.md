# Assembly

Here, we describe the results from the Assembly pipeline for de novo genome assembly and annotation.

* **assemblies**: a symbolic link to the raw reads associated with the resolution.
* **kmerfinder_summary.csv**: a .csv file containing the main results from kmerfinder. For each sample, you should check that both the best hit and the second hit reported by kmerfinder correspond to the species name indicated by the researcher when requesting the service. If the second hit is associated to a different species, check other metrics like %GC or %genome fraction in the MultiQC report, since this might reveal a contamination in that sample.
  * *sample_name*: sample name.
  * *07-kmerfinder_best_hit_# Assembly*: RefSeq assembly accession ID.
  * *07-kmerfinder_best_hit_Accession Number*: accession number of entry ID in fasta file.
  * *07-kmerfinder_best_hit_Depth*: is the number of matched kmers in the query sequence divided by the total number of Kmers in the template. For read files this estimates the sequencing depth.
  * *07-kmerfinder_best_hit_Description*: additional descriptions available in fasta file, or in the case of organism databases the identifier lines of fasta files.
  * *07-kmerfinder_best_hit_Expected*: is the expected score, i.e.the expected total number of matching Kmers between query and template (randomly selected).
  * *07-kmerfinder_best_hit_Num*: is the sequence number of accession entry in the KmerFinder database.
  * *07-kmerfinder_best_hit_Query_Coverage*: is the percentage of input query/reads Kmers that match the template.
  * *07-kmerfinder_best_hit_Score*: is the total number of matching Kmers between the query and the template.
  * *07-kmerfinder_best_hit_Species*: Species name.
  * *07-kmerfinder_best_hit_TAXID*: NCBI's TaxID number of the hit.
  * *07-kmerfinder_best_hit_TAXID Species*: NCBI's species TaxID number of the hit (sometimes bacterial strain or substrain TaxIDs can be given above).
  * *07-kmerfinder_best_hit_Taxonomy*: complete taxonomy of the hit.
  * *07-kmerfinder_best_hit_Template_Coverage*: is the template/genome coverage.
  * *07-kmerfinder_best_hit_Template_length*: is the number of Kmers in the template.
  * *07-kmerfinder_best_hit_p_value*: is the p-value corresponding to the obtained q_value.
  * *07-kmerfinder_best_hit_q_value*: is the quantile in a standard Pearson Chi-square test, to test whether the current template is a significant hit.
  * *07-kmerfinder_best_hit_tot_depth*: depth value based on all query kmers that can be found in the template sequence.
  * *07-kmerfinder_best_hit_tot_query_Coverage*: is calculated based on the ratio of the score and the number of kmers in the query sequence, where the score includes kmers matched before.
  * *07-kmerfinder_best_hit_tot_template_Coverage*: is calculated based on ratio of the score and the number of unique kmers in the template sequence, where the score includes kmers matched before.
  * *07-kmerfinder_second_hit_# Assembly*: RefSeq assembly accession ID.
  * *07-kmerfinder_second_hit_Accession Number*: accession number of entry ID in fasta file.
  * *07-kmerfinder_second_hit_Depth*: is the number of matched kmers in the query sequence divided by the total number of Kmers in the template. For read files this estimates the sequencing depth.
  * *07-kmerfinder_second_hit_Description*:  additional descriptions available in fasta file, or in the case of organism databases the identifier lines of fasta files.
  * *07-kmerfinder_second_hit_Expected*: is the expected score, i.e.the expected total number of matching Kmers between query and template (randomly selected).
  * *07-kmerfinder_second_hit_Num*: is the sequence number of accession entry in the KmerFinder database.
  * *07-kmerfinder_second_hit_Query_Coverage*: is the percentage of input query Kmers that match the template.
  * *07-kmerfinder_second_hit_Score*: is the total number of matching Kmers between the query and the template.
  * *07-kmerfinder_second_hit_Species*: Species name.
  * *07-kmerfinder_second_hit_TAXID*: NCBI's TaxID number of the hit.
  * *07-kmerfinder_second_hit_TAXID Species*: NCBI's species TaxID number of the hit (sometimes bacterial strain or substrain TaxIDs can be given above).
  * *07-kmerfinder_second_hit_Taxonomy*: complete taxonomy of the hit.
  * *07-kmerfinder_second_hit_Template_Coverage*: is the template coverage.
  * *07-kmerfinder_second_hit_Template_length*: is the number of Kmers in the template.
  * *07-kmerfinder_second_hit_p_value*: is the p-value corresponding to the obtained q_value.
  * *07-kmerfinder_second_hit_q_value*: is the quantile in a standard Pearson Chi-square test, to test whether the current template is a significant hit.
  * *07-kmerfinder_second_hit_tot_depth*: depth value based on all query kmers that can be found in the template sequence.
  * *07-kmerfinder_second_hit_tot_query_Coverage*: is calculated based on the ratio of the score and the number of kmers in the query sequence, where the score includes kmers matched before.
  * *07-kmerfinder_second_hit_tot_template_Coverage*: is calculated based on ratio of the score and the number of unique kmers in the template sequence, where the score includes kmers matched before.
  * *Total_hits_07_kmerfinder*: number of total hits.
* **multiqc_report.html**: an interactive report containing the results from MultiQC (kmerfinder, QUAST, quality control, etc.)
* **quast_GCF_XXXXXXXXX.X_ASMXXXXXv2_report.html**: an interactive report obtained after the execution of QUAST, providing different metrics about the assembly QC against the reference.
* **quast_global_report.html**: an interactive report obtained after the execution of QUAST, providing different metrics about the global assembly QC.
* **summary_assembly_metrics_mqc.csv**: a custom table containing most relevant assembly QC metrics.
  * *Sample*: sample ID.
  * *Input reads*: number of input reads for each sample.
  * *Trimmed reads (fastp)*: number of trimmed reads.
  * *Contigs*: number of contigs.
  * *Largest contig*: length of the largest contig.
  * *N50*: is the contig length such that using longer or equal length contigs produces half of the bases of the assembly. Usually there is no value that produces exactly 50%, so the technical definition is the maximum length x such that using contigs of length at least x accounts for at least 50% of the total assembly length.
  * *% Genome fraction*: the total number of aligned bases in the reference, divided by the genome size. 
  * *Best hit (Kmerfinder)*: best hit species name.
  * *Best hit assembly ID (Kmerfinder)*: best hit RefSeq assembly accession ID.
  * *Best hit query coverage (Kmerfinder)*: best hit query coverage.
  * *Best hit depth (Kmerfinder)*: best hit depth.
  * *Second hit (Kmerfinder)*: second hit species name.
  * *Second hit assembly ID (Kmerfinder)*: second hit RefSeq assembly accession ID.
  * *Second hit query coverage (Kmerfinder)*: second hit query coverage.
  * *Second hit depth (Kmerfinder)*: second hit depth.

> [!WARNING]
> Software's versions used in this analysis can be obtained from the  `MultiQC` report.