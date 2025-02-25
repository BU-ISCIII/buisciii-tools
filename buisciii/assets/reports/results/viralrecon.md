# Viralrecon

Here we describe the results from the Viralrecon pipeline for viral genome reconstruction.

> [!WARNING]
> Some of the files listed here may not be in your  `RESULTS` folder. It will depend on the analysis you requested.

## Mapping approach results

* mapping_illumina.xlsx: statistics for mapped reads against viral and host genomes.
  * run: Run name
  * user: User name
  * host: Host name
  * Virussequence: Reference virus used
  * sample: Sample name
  * totalreads: Total reads after trimming
  * readshostR1: Total reads of host genome in R1
  * readshost: Total reads of host genome in R1 and R2
  * %readshost: Percentage of reads that correspond to the host genome
  * readsvirus: Number of reference viral genome reads
  * %readsvirus: Percentage of reference viral genome reads
  * unmappedreads: number of reads that did not correspond to viral reference or host genome.
  * %unmapedreads: Percentage of reads that did not correspond to viral reference or host genome.
  * medianDPcoveragevirus: Median depth of coverage of the reference viral genome
  * Coverage>10x(%): Percentage of viral reference genome coverage to more than 10X
  * Variantsinconsensusx10: Number of variants included in the consensus after filtering: more than 10X and 0.75 AF
  * %Ns10x: Percentage of consesus genome masked due to having less than 10X depth
  * Lineage: Pangolin assigned lineage. *Warning: Only for SARS-CoV-2 sequencing data*
  * Date: Analysis date. *Warning: Only for SARS-CoV-2 sequencing data*
* mapping_consensus: this folder contains the masked (<10x) genomes obtained with consensus sequences using mapping and majority variant calling
* variants_annot: table with all annotated variants. *Warning: Only when annotation .gff file was provided*
* variants_long_table.xlsx: Table with variants for all the samples in long format. *Warning: Only when annotation .gff file was provided*
  * SAMPLE: sample name
  * CHROM: Reference ID
  * POS: Position of the variant
  * REF: Ref allele
  * ALT: Alt allele
  * FILTER: Column indicating if the variant passed the filters. If PASS the variant passed all the filters. If not, the name of the filter that wasn't passed will appear
  * DP: Position depth
  * REF_DP: Ref allele depth
  * ALT_DP: Alt allele depth
  * AF: Allele frequency
  * GENE: Gene name in annotation file​
  * EFFECT: Effect of the variant
  * HGVS_C: Position annotation at CDS level
  * HGVS_P: Position annotation at protein level
  * HGVS_P_1LETTER: Position annotation at protein level with the aminoacid annotation in 1 letter format
  * Caller: Variant caller used
* pangolin.xlsx: Pangolin complete results *Warning: Only for SARS-CoV-2 sequencing data*
* nextclade.xlsx: Results from Nextclade *Warning: Only for SARS-CoV-2 sequencing data*

## *de novo* assembly approach results

* assembly_stats.xlsx: Stats of the *de novo* assembly steps. This table contains the following columns:
  * run: Run name
  * user: User name
  * host: Host name
  * Virussequence: Reference virus used
  * sample: Sample name
  * totalreads: Total reads after trimming
  * readshostR1: Total reads of host genome in R1
  * readshost: Total reads of host genome in R1 and R2
  * %readshost: Percentage of reads that correspond to the host genome
  * Non-host-reedas: Number of reads remaining after host removal
  * \#Contigs: Number of contigs in the assembly
  * Largest contig: Size in nucleotides of the larges contig in the assembly
  * % Genome fraction: Percentage of the reference genome covered by the assembly. *Warning: Only when reference genome was provided*
* assembly_spades: Scaffolds fasta files with the spades de novo assembly. *Warning: Only when NO reference genome was provided, or reference genome didn't match*
* abacas_assembly: spades de novo assembly where contigs were contiguated using ABACAS and the reference genome. *Warning: Only when reference genome was provided*

> [!WARNING]
> Software's versions used in this analysis can be obtained from the  `MultiQC` report.
