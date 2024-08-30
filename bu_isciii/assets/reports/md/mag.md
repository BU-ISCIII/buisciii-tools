# nf-core/mag: Output

## Introduction

This document describes the output produced by the pipeline. Most of the plots are taken from the MultiQC report, which summarises results at the end of the pipeline.

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

## Pipeline overview

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes data using the following steps:

- [Quality control](#quality-control) of input reads - trimming and contaminant removal
- [Taxonomic classification of trimmed reads](#taxonomic-classification-of-trimmed-reads)
- [Digital sequencing normalisation](#digital-normalization-with-BBnorm)
- [Assembly](#assembly) of trimmed reads
- [Protein-coding gene prediction](#gene-prediction) of assemblies
- [Virus identification](#virus-identification-in-assemblies) of assemblies
- [Binning and binning refinement](#binning-and-binning-refinement) of assembled contigs
- [Taxonomic classification of binned genomes](#taxonomic-classification-of-binned-genomes)
- [Genome annotation of binned genomes](#genome-annotation-of-binned-genomes)
- [Additional summary for binned genomes](#additional-summary-for-binned-genomes)
- [Ancient DNA](#ancient-dna)
- [MultiQC](#multiqc) - aggregate report, describing results of the whole pipeline
- [Pipeline information](#pipeline-information) - Report metrics generated during the workflow execution

Note that when specifying the parameter `--coassemble_group`, for the corresponding output filenames/directories of the assembly or downsteam processes the group ID, or more precisely the term `group-[group_id]`, will be used instead of the sample ID.

## Quality control

These steps trim away the adapter sequences present in input reads, trims away bad quality bases and sicard reads that are too short.
It also removes host contaminants and sequencing controls, such as PhiX or the Lambda phage.
FastQC is run for visualising the general quality metrics of the sequencing runs before and after trimming.

<!-- TODO: Add example MultiQC plots generated for this pipeline -->

### FastQC

<details markdown="1">
<summary>Output files</summary>

- `QC_shortreads/fastqc/`
  - `[sample]_[1/2]_fastqc.html`: FastQC report, containing quality metrics for your untrimmed raw fastq files
  - `[sample].trimmed_[1/2]_fastqc.html`: FastQC report, containing quality metrics for trimmed and, if specified, filtered read files

</details>

[FastQC](http://www.bioinformatics.babraham.ac.uk/projects/fastqc/) gives general quality metrics about your sequenced reads. It provides information about the quality score distribution across your reads, per base sequence content (%A/T/G/C), adapter contamination and overrepresented sequences. For further reading and documentation see the [FastQC help pages](http://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/).

### fastp

[fastp](https://github.com/OpenGene/fastp) is a all-in-one fastq preprocessor for read/adapter trimming and quality control. It is used in this pipeline for trimming adapter sequences and discard low-quality reads. Its output is in the results folder and part of the MultiQC report.

<details markdown="1">
<summary>Output files</summary>

- `QC_shortreads/fastp/[sample]/`
  - `fastp.html`: Interactive report
  - `fastp.json`: Report in json format

</details>

### AdapterRemoval2

[AdapterRemoval](https://adapterremoval.readthedocs.io/en/stable/) searches for and removes remnant adapter sequences from High-Throughput Sequencing (HTS) data and (optionally) trims low quality bases from the 3' end of reads following adapter removal. It is popular in the field of palaeogenomics. The output logs are stored in the results folder, and as a part of the MultiQC report.

<details markdown="1">
<summary>Output files</summary>

- `QC_shortreads/adapterremoval/[sample]/`
  - `[sample]_ar2.settings`: AdapterRemoval log file.

</details>

### Remove PhiX sequences from short reads

The pipeline uses bowtie2 to map the reads against PhiX and removes mapped reads.

<details markdown="1">
<summary>Output files</summary>

- `QC_shortreads/remove_phix/`
  - `[sample].phix_removed.bowtie2.log`: Contains a brief log file indicating how many reads have been retained.

</details>

### Host read removal

The pipeline uses bowtie2 to map short reads against the host reference genome specified with `--host_genome` or `--host_fasta` and removes mapped reads. The information about discarded and retained reads is also included in the MultiQC report.

<details markdown="1">
<summary>Output files</summary>

- `QC_shortreads/remove_host/`
  - `[sample].host_removed.bowtie2.log`: Contains the bowtie2 log file indicating how many reads have been mapped.
  - `[sample].host_removed.mapped*.read_ids.txt`: Contains a file listing the read ids of discarded reads.

</details>

### Remove Phage Lambda sequences from long reads

The pipeline uses Nanolyse to map the reads against the Lambda phage and removes mapped reads.

<details markdown="1">
<summary>Output files</summary>

- `QC_longreads/NanoLyse/`
  - `[sample]_nanolyse.log`: Contains a brief log file indicating how many reads have been retained.

</details>

### Filtlong and porechop

The pipeline uses filtlong and porechop to perform quality control of the long reads that are eventually provided with the TSV input file.

No direct host read removal is performed for long reads.
However, since within this pipeline filtlong uses a read quality based on k-mer matches to the already filtered short reads, reads not overlapping those short reads might be discarded.
The lower the parameter `--longreads_length_weight`, the higher the impact of the read qualities for filtering.
For further documentation see the [filtlong online documentation](https://github.com/rrwick/Filtlong).

### Quality visualisation for long reads

NanoPlot is used to calculate various metrics and plots about the quality and length distribution of long reads. For more information about NanoPlot see the [online documentation](https://github.com/wdecoster/NanoPlot).

<details markdown="1">
<summary>Output files</summary>

- `QC_longreads/NanoPlot/[sample]/`
  - `raw_*.[png/html/txt]`: Plots and reports for raw data
  - `filtered_*.[png/html/txt]`: Plots and reports for filtered data

</details>

## Digital normalization with BBnorm

If the pipeline is called with the `--bbnorm` option, it will normalize sequencing depth of libraries prior assembly by removing reads to 1) reduce coverage of very abundant kmers and 2) delete very rare kmers (see `--bbnorm_target` and `--bbnorm_min` parameters).
When called in conjunction with `--coassemble_group`, BBnorm will operate on interleaved (merged) FastQ files, producing only a single output file.
If the `--save_bbnorm_reads` parameter is set, the resulting FastQ files are saved together with log output.

<details markdown="1">
<summary>Output files</summary>

- `bbmap/bbnorm/[sample]\*.fastq.gz`
- `bbmap/bbnorm/log/[sample].bbnorm.log`

</details>

## Taxonomic classification of trimmed reads

### Kraken

Kraken2 classifies reads using a k-mer based approach as well as assigns taxonomy using a Lowest Common Ancestor (LCA) algorithm.

<details markdown="1">
<summary>Output files</summary>

- `Taxonomy/kraken2/[sample]/`
  - `kraken2.report`: Classification in the Kraken report format. See the [kraken2 manual](https://github.com/DerrickWood/kraken2/wiki/Manual#output-formats) for more details
  - `taxonomy.krona.html`: Interactive pie chart produced by [KronaTools](https://github.com/marbl/Krona/wiki)

</details>

### Centrifuge

Centrifuge is commonly used for the classification of DNA sequences from microbial samples. It uses an indexing scheme based on the Burrows-Wheeler transform (BWT) and the Ferragina-Manzini (FM) index.

More information on the [Centrifuge](https://ccb.jhu.edu/software/centrifuge/) website

<details markdown="1">
<summary>Output files</summary>

- `Taxonomy/centrifuge/[sample]/`
  - `report.txt`: Tab-delimited result file. See the [centrifuge manual](https://ccb.jhu.edu/software/centrifuge/manual.shtml#centrifuge-classification-output) for information about the fields
  - `kreport.txt`: Classification in the Kraken report format. See the [kraken2 manual](https://github.com/DerrickWood/kraken2/wiki/Manual#output-formats) for more details
  - `taxonomy.krona.html`: Interactive pie chart produced by [KronaTools](https://github.com/marbl/Krona/wiki)

</details>

## Assembly

Trimmed (short) reads are assembled with both megahit and SPAdes. Hybrid assembly is only supported by SPAdes.

### MEGAHIT

[MEGAHIT](https://github.com/voutcn/megahit) is a single node assembler for large and complex metagenomics short reads.

<details markdown="1">
<summary>Output files</summary>

- `Assembly/MEGAHIT/`
  - `[sample/group].contigs.fa.gz`: Compressed metagenome assembly in fasta format
  - `[sample/group].log`: Log file
  - `QC/[sample/group]/`: Directory containing QUAST files and Bowtie2 mapping logs
    - `MEGAHIT-[sample].bowtie2.log`: Bowtie2 log file indicating how many reads have been mapped from the sample that the metagenome was assembled from, only present if `--coassemble_group` is not set.
    - `MEGAHIT-[sample/group]-[sampleToMap].bowtie2.log`: Bowtie2 log file indicating how many reads have been mapped from the respective sample ("sampleToMap").
    - `MEGAHIT-[sample].[bam/bai]`: Optionally saved BAM file of the Bowtie2 mapping of reads against the assembly.

</details>

### SPAdes

[SPAdes](http://cab.spbu.ru/software/spades/) was originally a single genome assembler that later added support for assembling metagenomes.

<details markdown="1">
<summary>Output files</summary>

- `Assembly/SPAdes/`
  - `[sample/group]_scaffolds.fasta.gz`: Compressed assembled scaffolds in fasta format
  - `[sample/group]_graph.gfa.gz`: Compressed assembly graph in gfa format
  - `[sample/group]_contigs.fasta.gz`: Compressed assembled contigs in fasta format
  - `[sample/group].log`: Log file
  - `QC/[sample/group]/`: Directory containing QUAST files and Bowtie2 mapping logs
    - `SPAdes-[sample].bowtie2.log`: Bowtie2 log file indicating how many reads have been mapped from the sample that the metagenome was assembled from, only present if `--coassemble_group` is not set.
    - `SPAdes-[sample/group]-[sampleToMap].bowtie2.log`: Bowtie2 log file indicating how many reads have been mapped from the respective sample ("sampleToMap").
    - `SPAdes-[sample].[bam/bai]`: Optionally saved BAM file of the Bowtie2 mapping of reads against the assembly.

</details>

### SPAdesHybrid

SPAdesHybrid is a part of the [SPAdes](http://cab.spbu.ru/software/spades/) software and is used when the user provides both long and short reads.

<details markdown="1">
<summary>Output files</summary>

- `Assembly/SPAdesHybrid/`
  - `[sample/group]_scaffolds.fasta.gz`: Compressed assembled scaffolds in fasta format
  - `[sample/group]_graph.gfa.gz`: Compressed assembly graph in gfa format
  - `[sample/group]_contigs.fasta.gz`: Compressed assembled contigs in fasta format
  - `[sample/group].log`: Log file
  - `QC/[sample/group]/`: Directory containing QUAST files and Bowtie2 mapping logs
    - `SPAdesHybrid-[sample].bowtie2.log`: Bowtie2 log file indicating how many reads have been mapped from the sample that the metagenome was assembled from, only present if `--coassemble_group` is not set.
    - `SPAdesHybrid-[sample/group]-[sampleToMap].bowtie2.log`: Bowtie2 log file indicating how many reads have been mapped from the respective sample ("sampleToMap").
    - `SPAdesHybrid-[sample].[bam/bai]`: Optionally saved BAM file of the Bowtie2 mapping of reads against the assembly.

</details>

### Metagenome QC with QUAST

[QUAST](http://cab.spbu.ru/software/quast/) is a tool that evaluates metagenome assemblies by computing various metrics. The QUAST output is also included in the MultiQC report, as well as in the assembly directories themselves.

<details markdown="1">
<summary>Output files</summary>

- `Assembly/[assembler]/QC/[sample/group]/QUAST/`
  - `report.*`: QUAST report in various formats, such as html, pdf, tex, tsv, or txt
  - `transposed_report.*`: QUAST report that has been transposed into wide format (tex, tsv, or txt)
  - `quast.log`: QUAST log file
  - `metaquast.log`: MetaQUAST log file
  - `icarus.html`: Icarus main menu with links to interactive viewers
  - `icarus_viewers/contig_size_viewer.html`: Diagram of contigs that are ordered from longest to shortest
  - `basic_stats/cumulative_plot.pdf`: Shows the growth of contig lengths (contigs are ordered from largest to shortest)
  - `basic_stats/GC_content_plot.pdf`: Shows the distribution of GC content in the contigs
  - `basic_stats/[assembler]-[sample/group]_GC_content_plot.pdf`: Histogram of the GC percentage for the contigs
  - `basic_stats/Nx_plot.pdf`: Plot of Nx values as x varies from 0 to 100%.
  - `predicted_genes/[assembler]-[sample/group].rna.gff`: Contig positions for rRNA genes in gff version 3 format
  - `predicted_genes/barrnap.log`: Barrnap log file (ribosomal RNA predictor)

</details>

## Gene prediction

Protein-coding genes are predicted for each assembly.

<details markdown="1">
<summary>Output files</summary>

- `Annotation/Prodigal/`
  - `[assembler]-[sample/group].gff.gz`: Gene Coordinates in GFF format
  - `[assembler]-[sample/group].faa.gz`: The protein translation file consists of all the proteins from all the sequences in multiple FASTA format.
  - `[assembler]-[sample/group].fna.gz`: Nucleotide sequences of the predicted proteins using the DNA alphabet, not mRNA (so you will see 'T' in the output and not 'U').
  - `[assembler]-[sample/group]_all.txt.gz`: Information about start positions of genes.

</details>

## Virus identification in assemblies

### geNomad

[geNomad](https://github.com/apcamargo/genomad) identifies viruses and plasmids in sequencing data (isolates, metagenomes, and metatranscriptomes)

<details markdown="1">
<summary>Output files</summary>

- `VirusIdentification/geNomad/[assembler]-[sample/group]*/`
  - `[assembler]-[sample/group]*_annotate`
    - `[assembler]-[sample/group]*_taxonomy.tsv`: Taxonomic assignment data
  - `[assembler]-[sample/group]*_aggregated_classification`
    - `[assembler]-[sample/group]*_aggregated_classification.tsv`: Sequence classification in tabular format
  - `[assembler]-[sample/group]*_find_proviruses`
    - `[assembler]-[sample/group]*_provirus.tsv`: Characteristics of proviruses identified by geNomad
  - `[assembler]-[sample/group]*_summary`
    - `[assembler]-[sample/group]*_virus_summary.tsv`: Virus classification summary file in tabular format
    - `[assembler]-[sample/group]*_plasmid_summary.tsv`: Plasmid classification summary file in tabular format
    - `[assembler]-[sample/group]*_viruses_genes.tsv`: Virus gene annotation data in tabular format
    - `[assembler]-[sample/group]*_plasmids_genes.tsv`: Plasmid gene annotation data in tabular format
    - `[assembler]-[sample/group]*_viruses.fna`: Virus nucleotide sequences in FASTA format
    - `[assembler]-[sample/group]*_plasmids.fna`: Plasmid nucleotide sequences in FASTA format
    - `[assembler]-[sample/group]*_viruses_proteins.faa`: Virus protein sequences in FASTA format
    - `[assembler]-[sample/group]*_plasmids_proteins.faa`: Plasmid protein sequences in FASTA format
  - `[assembler]-[sample/group]*.log`: Plain text log file detailing the steps executed by geNomad (annotate, find-proviruses, marker-classification, nn-classification, aggregated-classification and summary)

</details>

## Binning and binning refinement

### Contig sequencing depth

Sequencing depth per contig and sample is generated by MetaBAT2's `jgi_summarize_bam_contig_depths --outputDepth`. The values correspond to `(sum of exactly aligned bases) / ((contig length)-2*75)`. For example, for two reads aligned exactly with `10` and `9` bases on a 1000 bp long contig the depth is calculated by `(10+9)/(1000-2*75)` (1000bp length of contig minus 75bp from each end, which is excluded).

These depth files are used for downstream binning steps.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/depths/contigs/`
  - `[assembler]-[sample/group]-depth.txt.gz`: Sequencing depth for each contig and sample or group, only for short reads.

</details>

### MetaBAT2

[MetaBAT2](https://bitbucket.org/berkeleylab/metabat) recovers genome bins (that is, contigs/scaffolds that all belongs to a same organism) from metagenome assemblies.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/MetaBAT2/`
  - `bins/[assembler]-[binner]-[sample/group].*.fa.gz`: Genome bins retrieved from input assembly
  - `unbinned/[assembler]-[binner]-[sample/group].unbinned.[1-9]*.fa.gz`: Contigs that were not binned with other contigs but considered interesting. By default, these are at least 1 Mbp (`--min_length_unbinned_contigs`) in length and at most the 100 longest contigs (`--max_unbinned_contigs`) are reported

</details>

All the files and contigs in these folders will be assessed by QUAST and BUSCO.

All other files that were discarded by the tool, or from the low-quality unbinned contigs, can be found here.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/MetaBAT2/discarded/`
  - `*.lowDepth.fa.gz`: Low depth contigs that are filtered by MetaBAT2
  - `*.tooShort.fa.gz`: Too short contigs that are filtered by MetaBAT2
- `GenomeBinning/MetaBAT2/unbinned/discarded/`
  - `*.unbinned.pooled.fa.gz`: Pooled unbinned contigs equal or above `--min_contig_size`, by default 1500 bp.
  - `*.unbinned.remaining.fa.gz`: Remaining unbinned contigs below `--min_contig_size`, by default 1500 bp, but not in any other file.

</details>

All the files in this folder contain small and/or unbinned contigs that are not further processed.

Files in these two folders contain all contigs of an assembly.

### MaxBin2

[MaxBin2](https://sourceforge.net/projects/maxbin2/) recovers genome bins (that is, contigs/scaffolds that all belongs to a same organism) from metagenome assemblies.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/MaxBin2/`
  - `bins/[assembler]-[binner]-[sample/group].*.fa.gz`: Genome bins retrieved from input assembly
  - `unbinned/[assembler]-[binner]-[sample/group].noclass.[1-9]*.fa.gz`: Contigs that were not binned with other contigs but considered interesting. By default, these are at least 1 Mbp (`--min_length_unbinned_contigs`) in length and at most the 100 longest contigs (`--max_unbinned_contigs`) are reported.

</details>

All the files and contigs in these folders will be assessed by QUAST and BUSCO.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/MaxBin2/discarded/`
  - `*.tooshort.gz`: Too short contigs that are filtered by MaxBin2
- `GenomeBinning/MaxBin2/unbinned/discarded/`
  - `*.noclass.pooled.fa.gz`: Pooled unbinned contigs equal or above `--min_contig_size`, by default 1500 bp.
  - `*.noclass.remaining.fa.gz`: Remaining unbinned contigs below `--min_contig_size`, by default 1500 bp, but not in any other file.

</details>

All the files in this folder contain small and/or unbinned contigs that are not further processed.

Files in these two folders contain all contigs of an assembly.

### CONCOCT

[CONCOCT](https://github.com/BinPro/CONCOCT) performs unsupervised binning of metagenomic contigs by using nucleotide composition, coverage data in multiple samples and linkage data from paired end reads.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/CONCOCT/`
  - `bins/[assembler]-[binner]-[sample/group].*.fa.gz`: Genome bins retrieved from input assembly
  - `stats/[assembler]-[binner]-[sample/group].csv`: Table indicating which contig goes with which cluster bin.
  - `stats/[assembler]-[binner]-[sample/group]*_gt1000.csv`: Various intermediate PCA statistics used for clustering.
  - `stats/[assembler]-[binner]-[sample/group]_*.tsv`: Coverage statistics of each sub-contig cut up by CONOCOCT prior in an intermediate step prior to binning. Likely not useful in most cases.
  - `stats/[assembler]-[binner]-[sample/group].log.txt`: CONCOCT execution log file.
  - `stats/[assembler]-[binner]-[sample/group]_*.args`: List of arguments used in CONCOCT execution.
  - </details>

All the files and contigs in these folders will be assessed by QUAST and BUSCO, if the parameter `--postbinning_input` is not set to `refined_bins_only`.

Note that CONCOCT does not output what it considers 'unbinned' contigs, therefore no 'discarded' contigs are produced here. You may still need to do your own manual curation of the resulting bins.

### DAS Tool

[DAS Tool](https://github.com/cmks/DAS_Tool) is an automated binning refinement method that integrates the results of a flexible number of binning algorithms to calculate an optimized, non-redundant set of bins from a single assembly. nf-core/mag uses this tool to attempt to further improve bins based on combining the MetaBAT2 and MaxBin2 binning output, assuming sufficient quality is met for those bins.

DAS Tool will remove contigs from bins that do not pass additional filtering criteria, and will discard redundant lower-quality output from binners that represent the same estimated 'organism', until the single highest quality bin is represented.

> ⚠️ If DAS Tool does not find any bins passing your selected threshold it will exit with an error. Such an error is 'ignored' by nf-core/mag, therefore you will not find files in the `GenomeBinning/DASTool/` results directory for that particular sample.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/DASTool/`
  - `[assembler]-[sample/group]_allBins.eval`: Tab-delimited description with quality and completeness metrics for the input bin sets. Quality and completeness are estimated by DAS TOOL using a scoring function based on the frequency of bacterial or archaeal reference single-copy genes (SCG). Please see note at the bottom of this section on file names.
  - `[assembler]-[sample/group]_DASTool_summary.tsv`: Tab-delimited description with quality and completeness metrics for the refined output bin sets.
  - `[assembler]-[sample/group]_DASTool_contig2bin.tsv`: File describing which contig is associated to which bin from the input binners.
  - `[assembler]-[sample/group]_DASTool.log`: Log file from the DAS Tool run describing the command executed and additional runtime information.
  - `[assembler]-[sample/group].seqlength`: Tab-delimited file describing the length of each contig.
  - `bins/[assembler]-[binner]Refined-[sample/group].*.fa`: Refined bins in fasta format.
  - `unbinned/[assembler]-DASToolUnbinned-[sample/group].*.fa`: Unbinned contigs from bin refinement in fasta format.

</details>

By default, only the raw bins (and unbinned contigs) from the actual binning methods, but not from the binning refinement with DAS Tool, will be used for downstream bin quality control, annotation and taxonomic classification. The parameter `--postbinning_input` can be used to change this behaviour.

⚠️ Due to ability to perform downstream QC of both raw and refined bins in parallel (via `--postbinning_input)`, bin names in DAS Tools's `*_allBins.eval` file will include `Refined`. However for this particular file, they _actually_ refer to the 'raw' input bins. The pipeline renames the input files prior to running DASTool to ensure they can be disambiguated from the original bin files in the downstream QC steps.

### Tiara

Tiara is a contig classifier that identifies the domain (prokarya, eukarya) of contigs within an assembly. This is used in this pipeline to rapidly and with few resources identify the most likely domain classification of each bin or unbin based on its contig identities.

<details markdown="1">
<summary>Output files</summary>

- `Taxonomy/Tiara/`
  - `[assembler]-[sample/group].tiara.txt` - Tiara output classifications (with probabilities) for all contigs within the specified sample/group assembly
  - `log_[assembler]-[sample/group].txt` - log file detailing the parameters used by the Tiara model for contig classification.
- `GenomeBinning/tiara_summary.tsv` - Summary of Tiara domain classification for all bins.

</details>

Typically, you would use `tiara_summary.tsv` as the primary file to see which bins or unbins have been classified to which domains at a glance, whereas the files in `Taxonomy/Tiara` provide classifications for each contig.

### Bin sequencing depth

For each bin or refined bin the median sequencing depth is computed based on the corresponding contig depths.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/depths/bins/`
  - `bin_depths_summary.tsv`: Summary of bin sequencing depths for all samples. Depths are available for samples mapped against the corresponding assembly, i.e. according to the mapping strategy specified with `--binning_map_mode`. Only for short reads.
  - `bin_refined_depths_summary.tsv`: Summary of sequencing depths for refined bins for all samples, if refinement was performed. Depths are available for samples mapped against the corresponding assembly, i.e. according to the mapping strategy specified with `--binning_map_mode`. Only for short reads.
  - `[assembler]-[binner]-[sample/group]-binDepths.heatmap.png`: Clustered heatmap showing bin abundances of the assembly across samples. Bin depths are transformed to centered log-ratios and bins as well as samples are clustered by Euclidean distance. Again, sample depths are available according to the mapping strategy specified with `--binning_map_mode`.

</details>

### QC for metagenome assembled genomes with QUAST

[QUAST](http://cab.spbu.ru/software/quast/) is a tool that evaluates genome assemblies by computing various metrics. The QUAST output is in the bin directories shown below. This QUAST output is not shown in the MultiQC report.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/QC/QUAST/[assembler]-[bin]/`
  - `report.*`: QUAST report in various formats, such as html, pdf, tex, tsv, or txt
  - `transposed_report.*`: QUAST report that has been transposed into wide format (tex, tsv, or txt)
  - `quast.log`: QUAST log file
  - `metaquast.log`: MetaQUAST log file
  - `icarus.html`: Icarus main menu with links to interactive viewers
  - `icarus_viewers/contig_size_viewer.html`: Diagram of contigs that are ordered from longest to shortest
  - `basic_stats/cumulative_plot.pdf`: Shows the growth of contig lengths (contigs are ordered from largest to shortest)
  - `basic_stats/GC_content_plot.pdf`: Shows the distribution of GC content in the contigs
  - `basic_stats/[assembler]-[bin]_GC_content_plot.pdf`: Histogram of the GC percentage for the contigs
  - `basic_stats/Nx_plot.pdf`: Plot of Nx values as x varies from 0 to 100%.
  - `predicted_genes/[assembler]-[bin].rna.gff`: Contig positions for rRNA genes in gff version 3 format
  - `predicted_genes/barrnap.log`: Barrnap log file (ribosomal RNA predictor)
- `GenomeBinning/QC/`
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group]-quast_summary.tsv`: QUAST output summarized per sample/condition.
  - `quast_summary.tsv`: QUAST output for all bins summarized

</details>

### QC for metagenome assembled genomes

#### BUSCO

[BUSCO](https://busco.ezlab.org/) is a tool used to assess the completeness of a genome assembly. It is run on all the genome bins and high quality contigs obtained by the applied binning and/or binning refinement methods (depending on the `--postbinning_input` parameter). By default, BUSCO is run in automated lineage selection mode in which it first tries to select the domain and then a more specific lineage based on phylogenetic placement. If available, result files for both the selected domain lineage and the selected more specific lineage are placed in the output directory. If a lineage dataset is specified already with `--busco_db`, only results for this specific lineage will be generated.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/QC/BUSCO/`
  - `[assembler]-[bin]_busco.log`: Log file containing the standard output of BUSCO.
  - `[assembler]-[bin]_busco.err`: File containing potential error messages returned from BUSCO.
  - `short_summary.domain.[lineage].[assembler]-[bin].txt`: BUSCO summary of the results for the selected domain when run in automated lineage selection mode. Not available for bins for which a viral lineage was selected.
  - `short_summary.specific_lineage.[lineage].[assembler]-[bin].txt`: BUSCO summary of the results in case a more specific lineage than the domain could be selected or for the lineage provided via `--busco_db`.
  - `[assembler]-[bin]_buscos.[lineage].fna.gz`: Nucleotide sequence of all identified BUSCOs for used lineages (domain or specific).
  - `[assembler]-[bin]_buscos.[lineage].faa.gz`: Aminoacid sequence of all identified BUSCOs for used lineages (domain or specific).
  - `[assembler]-[bin]_prodigal.gff`: Genes predicted with Prodigal.

</details>

If the parameter `--save_busco_db` is set, additionally the used BUSCO lineage datasets are stored in the output directory.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/QC/BUSCO/`
  - `busco_downloads/`: All files and lineage datasets downloaded by BUSCO when run in automated lineage selection mode. (Can currently not be used to reproduce analysis, see the [nf-core/mag website documentation](https://nf-co.re/mag/usage#reproducibility) how to achieve reproducible BUSCO results).
  - `reference/*.tar.gz`: BUSCO reference lineage dataset that was provided via `--busco_db`.

</details>

Besides the reference files or output files created by BUSCO, the following summary files will be generated:

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/QC/`
  - `busco_summary.tsv`: A summary table of the BUSCO results, with % of marker genes found. If run in automated lineage selection mode, both the results for the selected domain and for the selected more specific lineage will be given, if available.

</details>

#### CheckM

[CheckM](https://ecogenomics.github.io/CheckM/) CheckM provides a set of tools for assessing the quality of genomes recovered from isolates, single cells, or metagenomes. It provides robust estimates of genome completeness and contamination by using collocated sets of genes that are ubiquitous and single-copy within a phylogenetic lineage

By default, nf-core/mag runs CheckM with the `check_lineage` workflow that places genome bins on a reference tree to define lineage-marker sets, to check for completeness and contamination based on lineage-specific marker genes. and then subsequently runs `qa` to generate the summary files.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/QC/CheckM/`
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group]_qa.txt`: Detailed statistics about bins informing completeness and contamamination scores (output of `checkm qa`). This should normally be your main file to use to evaluate your results.
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group]_wf.tsv`: Overall summary file for completeness and contamination (output of `checkm lineage_wf`).
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group]/`: intermediate files for CheckM results, including CheckM generated annotations, log, lineage markers etc.
  - `checkm_summary.tsv`: A summary table of the CheckM results for all bins (output of `checkm qa`).

</details>

If the parameter `--save_checkm_reference` is set, additionally the used the CheckM reference datasets are stored in the output directory.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/QC/CheckM/`
  - `checkm_downloads/`: All CheckM reference files downloaded from the CheckM FTP server, when not supplied by the user.
    - `checkm_data_2015_01_16/*`: a range of directories and files required for CheckM to run.

</details>

#### GUNC

[Genome UNClutterer (GUNC)](https://grp-bork.embl-community.io/gunc/index.html) is a tool for detection of chimerism and contamination in prokaryotic genomes resulting from mis-binning of genomic contigs from unrelated lineages. It does so by applying an entropy based score on taxonomic assignment and contig location of all genes in a genome. It is generally considered as a additional complement to CheckM results.

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/QC/gunc_summary.tsv`
- `GenomeBinning/QC/gunc_checkm_summary.tsv`
- `[gunc-database].dmnd`
- `GUNC/`
  - `raw/`
    - `[assembler]-[binner]-[domain]-[refinement]-[sample/group]/GUNC_checkM.merged.tsv`: Per sample GUNC [output](https://grp-bork.embl-community.io/gunc/output.html) containing with taxonomic and completeness QC statistics.
  - `checkmmerged/`
    - `[assembler]-[binner]-[domain]-[refinement]-[sample/group]/GUNC.progenomes_2.1.maxCSS_level.tsv`: Per sample GUNC output merged with output from [CheckM](#checkm)

</details>

GUNC will be run if specified with `--run_gunc` as a standalone, unless CheckM is also activated via `--qc_tool 'checkm'`, in which case GUNC output will be merged with the CheckM output using `gunc merge_checkm`.

If `--gunc_save_db` is specified, the output directory will also contain the requested database (progenomes, or GTDB) in DIAMOND format.

## Taxonomic classification of binned genomes

### CAT

[CAT](https://github.com/dutilh/CAT) is a toolkit for annotating contigs and bins from metagenome-assembled-genomes. The nf-core/mag pipeline uses CAT to assign taxonomy to genome bins based on the taxnomy of the contigs.

<details markdown="1">
<summary>Output files</summary>

- `Taxonomy/CAT/[assembler]/[binner]/`
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group].ORF2LCA.names.txt.gz`: Tab-delimited files containing the lineage of each contig, with full lineage names
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group].bin2classification.names.txt.gz`: Taxonomy classification of the genome bins, with full lineage names
- `Taxonomy/CAT/[assembler]/[binner]/raw/`
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group].concatenated.predicted_proteins.faa.gz`: Predicted protein sequences for each genome bin, in fasta format
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group].concatenated.predicted_proteins.gff.gz`: Predicted protein features for each genome bin, in gff format
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group].ORF2LCA.txt.gz`: Tab-delimited files containing the lineage of each contig
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group].bin2classification.txt.gz`: Taxonomy classification of the genome bins
  - `[assembler]-[binner]-[domain]-[refinement]-[sample/group].log`: Log files

</details>

If the parameters `--cat_db_generate` and `--save_cat_db` are set, additionally the generated CAT database is stored:

<details markdown="1">
<summary>Output files</summary>

- `Taxonomy/CAT/CAT_prepare_*.tar.gz`: Generated and used CAT database.

</details>

### GTDB-Tk

[GTDB-Tk](https://github.com/Ecogenomics/GTDBTk) is a toolkit for assigning taxonomic classifications to bacterial and archaeal genomes based on the Genome Database Taxonomy [GTDB](https://gtdb.ecogenomic.org/). nf-core/mag uses GTDB-Tk to classify binned genomes which satisfy certain quality criteria (i.e. completeness and contamination assessed with the BUSCO analysis).

<details markdown="1">
<summary>Output files</summary>

- `Taxonomy/GTDB-Tk/[assembler]/[binner]/[sample/group]/`
  - `gtdbtk.[assembler]-[binner]-[sample/group].{bac120/ar122}.summary.tsv`: Classifications for bacterial and archaeal genomes (see the [GTDB-Tk documentation for details](https://ecogenomics.github.io/GTDBTk/files/summary.tsv.html)).
  - `gtdbtk.[assembler]-[binner]-[domain]-[refinement]-[sample/group].{bac120/ar122}.classify.tree.gz`: Reference tree in Newick format containing query genomes placed with pplacer.
  - `gtdbtk.[assembler]-[binner]-[domain]-[refinement]-[sample/group].{bac120/ar122}.markers_summary.tsv`: A summary of unique, duplicated, and missing markers within the 120 bacterial marker set, or the 122 archaeal marker set for each submitted genome.
  - `gtdbtk.[assembler]-[binner]-[domain]-[refinement]-[sample/group].{bac120/ar122}.msa.fasta.gz`: FASTA file containing MSA of submitted and reference genomes.
  - `gtdbtk.[assembler]-[binner]-[domain]-[refinement]-[sample/group].{bac120/ar122}.filtered.tsv`: A list of genomes with an insufficient number of amino acids in MSA.
  - `gtdbtk.[assembler]-[binner]-[domain]-[refinement]-[sample/group].*.log`: Log files.
  - `gtdbtk.[assembler]-[binner]-[domain]-[refinement]-[sample/group].failed_genomes.tsv`: A list of genomes for which the GTDB-Tk analysis failed, e.g. because Prodigal could not detect any genes.
- `Taxonomy/GTDB-Tk/gtdbtk_summary.tsv`: A summary table of the GTDB-Tk classification results for all bins, also containing bins which were discarded based on the BUSCO QC, which were filtered out by GTDB-Tk (listed in `*.filtered.tsv`) or for which the analysis failed (listed in `*.failed_genomes.tsv`).

</details>

## Genome annotation of binned genomes

### Prokka

Whole genome annotation is the process of identifying features of interest in a set of genomic DNA sequences, and labelling them with useful information. [Prokka](https://github.com/tseemann/prokka) is a software tool to annotate bacterial, archaeal and viral genomes quickly and produce standards-compliant output files.

<details markdown="1">
<summary>Output files</summary>

- `Annotation/Prokka/[assembler]/[bin]/`
  - `[assembler]-[binner]-[bin].gff`: annotation in GFF3 format, containing both sequences and annotations
  - `[assembler]-[binner]-[bin].gbk`: annotation in GenBank format, containing both sequences and annotations
  - `[assembler]-[binner]-[bin].fna`: nucleotide FASTA file of the input contig sequences
  - `[assembler]-[binner]-[bin].faa`: protein FASTA file of the translated CDS sequences
  - `[assembler]-[binner]-[bin].ffn`: nucleotide FASTA file of all the prediction transcripts (CDS, rRNA, tRNA, tmRNA, misc_RNA)
  - `[assembler]-[binner]-[bin].sqn`: an ASN1 format "Sequin" file for submission to Genbank
  - `[assembler]-[binner]-[bin].fsa`: nucleotide FASTA file of the input contig sequences, used by "tbl2asn" to create the .sqn file
  - `[assembler]-[binner]-[bin].tbl`: feature Table file, used by "tbl2asn" to create the .sqn file
  - `[assembler]-[binner]-[bin].err`: unacceptable annotations - the NCBI discrepancy report.
  - `[assembler]-[binner]-[bin].log`: contains all the output that Prokka produced during its run
  - `[assembler]-[binner]-[bin].txt`: statistics relating to the annotated features found
  - `[assembler]-[binner]-[bin].tsv`: tab-separated file of all features (locus_tag, ftype, len_bp, gene, EC_number, COG, product)

</details>

### MetaEuk

In cases where eukaryotic genomes are recovered in binning, [MetaEuk](https://github.com/soedinglab/metaeuk) is also available to annotate eukaryotic genomes quickly with standards-compliant output files.

<details markdown="1">
<summary>Output files</summary>

- `Annotation/MetaEuk/[assembler]/[bin]`
  - `[assembler]-[binner]-[bin].fas`: fasta file of protein sequences identified by MetaEuk
  - `[assembler]-[binner]-[bin].codon.fas`: fasta file of nucleotide sequences corresponding to the protein sequences fasta
  - `[assembler]-[binner]-[bin].headersMap.tsv`: tab-separated table containing the information from each header in the fasta files
  - `[assembler]-[binner]-[bin].gff`: annotation in GFF3 format

</details>

## Additional summary for binned genomes

<details markdown="1">
<summary>Output files</summary>

- `GenomeBinning/bin_summary.tsv`: Summary of bin sequencing depths together with BUSCO, CheckM, QUAST and GTDB-Tk results, if at least one of the later was generated. This will also include refined bins if `--refine_bins_dastool` binning refinement is performed. Note that in contrast to the other tools, for CheckM the bin name given in the column "Bin Id" does not contain the ".fa" extension.

</details>

## Ancient DNA

Optional, only running when parameter `-profile ancient_dna` is specified.

### `PyDamage`

[Pydamage](https://github.com/maxibor/pydamage), is a tool to automate the process of ancient DNA damage identification and estimation from contigs. After modelling the ancient DNA damage using the C to T transitions, Pydamage uses a likelihood ratio test to discriminate between truly ancient, and modern contigs originating from sample contamination.

<details markdown="1">
<summary>Output files</summary>

- `Ancient_DNA/pydamage/analyze`
  - `[assembler]_[sample/group]/pydamage_results/pydamage_results.csv`: PyDamage raw result tabular file in `.csv` format. Format described here: [pydamage.readthedocs.io/en/0.62/output.html](https://pydamage.readthedocs.io/en/0.62/output.html)
- `Ancient_DNA/pydamage/filter`
  - `[assembler]_[sample/group]/pydamage_results/pydamage_results.csv`: PyDamage filtered result tabular file in `.csv` format. Format described here: [pydamage.readthedocs.io/en/0.62/output.html](https://pydamage.readthedocs.io/en/0.62/output.html)

</details>

### `variant_calling`

Because of aDNA damage, _de novo_ assemblers sometimes struggle to call a correct consensus on the contig sequence. To avoid this situation, the consensus is optionally re-called with a variant calling software using the reads aligned back to the contigs when `--run_ancient_damagecorrection` is supplied.

<details markdown="1">
<summary>Output files</summary>

- `variant_calling/consensus`
  - `[assembler]_[sample/group].fa`: contigs sequence with re-called consensus from read-to-contig alignment
- `variant_calling/unfiltered`
  - `[assembler]_[sample/group].vcf.gz`: raw variant calls of the reads aligned back to the contigs.
- `variant_calling/filtered`
  - `[assembler]_[sample/group].filtered.vcf.gz`: quality filtered variant calls of the reads aligned back to the contigs.

</details>

### MultiQC

<details markdown="1">
<summary>Output files</summary>

- `multiqc/`
  - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
  - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
  - `multiqc_plots/`: directory containing static images from the report in various formats.

</details>

[MultiQC](http://multiqc.info) is a visualization tool that generates a single HTML report summarising all samples in your project. Most of the pipeline QC results are visualised in the report and further statistics are available in the report data directory.

Results generated by MultiQC collate pipeline QC from supported tools e.g. FastQC. The pipeline has special steps which also allow the software versions to be reported in the MultiQC output for future traceability. For more information about how to use MultiQC reports, see <http://multiqc.info>.

The general stats table at the top of the table will by default only display the most relevant pre- and post-processing statistics prior to assembly, i.e., FastQC, fastp/Adapter removal, and Bowtie2 PhiX and host removal mapping results.

Note that the FastQC raw and processed columns are right next to each other for improved visual comparability, however the processed columns represent the input reads _after_ fastp/Adapter Removal processing (the dedicated columns of which come directly after the two FastQC set of columns). Hover your cursor over each column name to see the which tool the column is derived from.

Summary tool-specific plots and tables of following tools are currently displayed (if activated):

- FastQC (pre- and post-trimming)
- fastp
- Adapter Removal
- bowtie2
- BUSCO
- QUAST
- Kraken2 / Centrifuge
- PROKKA

### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `pipeline_info/`
  - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
  - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
  - Parameters used by the pipeline run: `params.json`.

</details>

[Nextflow](https://www.nextflow.io/docs/latest/tracing.html) provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.

# nf-core/taxprofiler: Output

## Introduction

This document describes the output produced by the pipeline. Most of the plots are taken from the MultiQC report, which summarises results at the end of the pipeline.

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

## Pipeline overview

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes data using the following steps:

- [UNTAR](#untar) - Optionally saved decompressed input databases
- [FastQC](#fastqc) - Raw read QC
- [falco](#fastqc) - Alternative to FastQC for raw read QC
- [fastp](#fastp) - Adapter trimming for Illumina data
- [AdapterRemoval](#adapterremoval) - Adapter trimming for Illumina data
- [Porechop](#porechop) - Adapter removal for Oxford Nanopore data
- [BBDuk](#bbduk) - Quality trimming and filtering for Illumina data
- [PRINSEQ++](#prinseq) - Quality trimming and filtering for Illunina data
- [Filtlong](#filtlong) - Quality trimming and filtering for Nanopore data
- [Bowtie2](#bowtie2) - Host removal for Illumina reads
- [minimap2](#minimap2) - Host removal for Nanopore reads
- [SAMtools stats](#samtools-stats) - Statistics from host removal
- [SAMtools fastq](#samtools-fastq) - Converts unmapped BAM file to fastq format (minimap2 only)
- [Analysis Ready Reads](#analysis-read-reads) - Optional results directory containing the final processed reads used as input for classification/profiling.
- [Bracken](#bracken) - Taxonomic classifier using k-mers and abundance estimations
- [Kraken2](#kraken2) - Taxonomic classifier using exact k-mer matches
- [KrakenUniq](#krakenuniq) - Taxonomic classifier that combines the k-mer-based classification and the number of unique k-mers found in each species
- [Centrifuge](#centrifuge) - Taxonomic classifier that uses a novel indexing scheme based on the Burrows-Wheeler transform (BWT) and the Ferragina-Manzini (FM) index.
- [Kaiju](#kaiju) - Taxonomic classifier that finds maximum (in-)exact matches on the protein-level.
- [Diamond](#diamond) - Sequence aligner for protein and translated DNA searches.
- [MALT](#malt) - Sequence alignment and analysis tool designed for processing high-throughput sequencing data, especially in the context of metagenomics
- [MetaPhlAn](#metaphlan) - Genome-level marker gene based taxonomic classifier
- [mOTUs](#motus) - Tool for marker gene-based OTU (mOTU) profiling.
- [KMCP](#kmcp) - Taxonomic classifier that utilizes genome coverage information by splitting the reference genomes into chunks and stores k-mers in a modified and optimized COBS index for fast alignment-free sequence searching.
- [ganon](#ganon) - Taxonomic classifier and profile that uses Interleaved Bloom Filters as indices based on k-mers/minimizers.
- [TAXPASTA](#taxpasta) - Tool to standardise taxonomic profiles as well as merge profiles across samples from the same database and classifier/profiler.
- [MultiQC](#multiqc) - Aggregate report describing results and QC from the whole pipeline
- [Pipeline information](#pipeline-information) - Report metrics generated during the workflow execution

![](images/taxprofiler_tube.png)

### untar

untar is used in nf-core/taxprofiler to decompress various input files ending in `.tar.gz`. This process is mainly used for decompressing input database archive files.

<details markdown="1">
<summary>Output files</summary>

- `untar/`
  - `database/`
    - `<database_file_name>`: directory containing contents of the decompressed archive

</details>

This directory will only be present if `--save_untarred_databases` is supplied. The contained directories can be useful for moving the decompressed directories to a central 'cache' location allowing users to re-use the same databases. This is useful to save unnecessary computational time of decompressing the archives on every run.

### FastQC or Falco

<details markdown="1">
<summary>Output files</summary>

- `{fastqc,falco}/`
  - {raw,preprocessed}
    - `*html`: FastQC or Falco report containing quality metrics in HTML format.
    - `*.txt`: FastQC or Falco report containing quality metrics in TXT format.
    - `*.zip`: Zip archive containing the FastQC report, tab-delimited data file and plot images (FastQC only).

</details>

[FastQC](http://www.bioinformatics.babraham.ac.uk/projects/fastqc/) gives general quality metrics about your sequenced reads. It provides information about the quality score distribution across your reads, per base sequence content (%A/T/G/C), adapter contamination and overrepresented sequences. For further reading and documentation see the [FastQC help pages](http://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/).

If preprocessing is turned on, nf-core/taxprofiler runs FastQC/Falco twice -once before and once after adapter removal/read merging, to allow evaluation of the performance of these preprocessing steps. Note in the General Stats table, the columns of these two instances of FastQC/Falco are placed next to each other to make it easier to evaluate. However, the columns of the actual preprocessing steps (i.e, fastp, AdapterRemoval, and Porechop) will be displayed _after_ the two FastQC/Falco columns, even if they were run 'between' the two FastQC/Falco jobs in the pipeline itself.

:::info
Falco produces identical output to FastQC but in the `falco/` directory.
:::

![MultiQC - FastQC sequence counts plot](images/mqc_fastqc_counts.png)

![MultiQC - FastQC mean quality scores plot](images/mqc_fastqc_quality.png)

![MultiQC - FastQC adapter content plot](images/mqc_fastqc_adapter.png)

:::note
The FastQC plots displayed in the MultiQC report shows _untrimmed_ reads. They may contain adapter sequence and potentially regions with low quality.
:::

### fastp

[fastp](https://github.com/OpenGene/fastp) is a FASTQ pre-processing tool for quality control, trimmming of adapters, quality filtering and other features.

It is used in nf-core/taxprofiler for adapter trimming of short-reads.

<details markdown="1">
<summary>Output files</summary>

- `fastp/`
  - `<sample_id>.fastp.fastq.gz`: File with the trimmed unmerged fastq reads.
  - `<sample_id>.merged.fastq.gz`: File with the reads that were successfully merged.
  - `<sample_id>.*{log,html,json}`: Log files in different formats.

</details>

By default nf-core/taxprofiler will only provide the `<sample_id>.fastp.fastq.gz` file if fastp is selected. The file `<sample_id>.merged.fastq.gz` will be available in the output folder if you provide the argument ` --shortread_qc_mergepairs` (optionally retaining un-merged pairs when in combination with `--shortread_qc_includeunmerged`).

You can change the default value for low complexity filtering by using the argument `--shortread_complexityfilter_fastp_threshold`.

### AdapterRemoval

[AdapterRemoval](https://adapterremoval.readthedocs.io/en/stable/) searches for and removes remnant adapter sequences from High-Throughput Sequencing (HTS) data and (optionally) trims low quality bases from the 3' end of reads following adapter removal. It is popular in the field of palaeogenomics. The output logs are stored in the results folder, and as a part of the MultiQC report.

<details markdown="1">
<summary>Output files</summary>

- `adapterremoval/`
  - `<sample_id>.settings`: AdapterRemoval log file containing general adapter removal, read trimming and merging statistics
  - `<sample_id>.collapsed.fastq.gz` - read-pairs that merged and did not undergo trimming (only when `--shortread_qc_mergepairs` supplied)
  - `<sample_id>.collapsed.truncated.fastq.gz` - read-pairs that merged underwent quality trimming (only when `--shortread_qc_mergepairs` supplied)
  - `<sample_id>.pair1.truncated.fastq.gz` - read 1 of pairs that underwent quality trimming
  - `<sample_id>.pair2.truncated.fastq.gz` - read 2 of pairs that underwent quality trimming (and could not merge if `--shortread_qc_mergepairs` supplied)
  - `<sample_id>.singleton.truncated.fastq.gz` - orphaned read pairs where one of the pair was discarded
  - `<sample_id>.discard.fastq.gz` - reads that were discarded due to length or quality filtering

</details>

By default nf-core/taxprofiler will only provide the `.settings` file if AdapterRemoval is selected.

You will only find the `.fastq` files in the results directory if you provide ` --save_preprocessed_reads`. If this is selected, you may receive different combinations of `.fastq` files for each sample depending on the input types - e.g. whether you have merged or not, or if you're supplying both single- and paired-end reads. Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

:::warning
The resulting `.fastq` files may _not_ always be the 'final' reads that go into taxprofiling, if you also run other steps such as complexity filtering, host removal, run merging etc..
:::

### Porechop

[Porechop](https://github.com/rrwick/Porechop) is a tool for finding and removing adapters from Oxford Nanopore reads. Adapters on the ends of reads are trimmed and if a read has an adapter in its middle, it is considered a chimeric and it chopped into separate reads.

<details markdown="1">
<summary>Output files</summary>

- `porechop/`
  - `<sample_id>.log`: Log file containing trimming statistics
  - `<sample_id>.fastq.gz`: Adapter-trimmed file

</details>

The output logs are saved in the output folder and are part of MultiQC report.You do not normally need to check these manually.

You will only find the `.fastq` files in the results directory if you provide ` --save_preprocessed_reads`. Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

:::warning
We do **not** recommend using Porechop if you are already trimming the adapters with ONT's basecaller Guppy.
:::

### BBDuk

[BBDuk](https://jgi.doe.gov/data-and-tools/software-tools/bbtools/bb-tools-user-guide/bbduk-guide/) stands for Decontamination Using Kmers. BBDuk was developed to combine most common data-quality-related trimming, filtering, and masking operations into a single high-performance tool.

It is used in nf-core/taxprofiler for complexity filtering using different algorithms. This means that it will remove reads with low sequence diversity (e.g. mono- or dinucleotide repeats).

<details markdown="1">
<summary>Output files</summary>

- `bbduk/`
  - `<sample_id>.bbduk.log`: log file containing filtering statistics
  - `<sample_id>.fastq.gz`: resulting FASTQ file without low-complexity reads

</details>

By default nf-core/taxprofiler will only provide the `.log` file if BBDuk is selected as the complexity filtering tool. You will only find the complexity filtered reads in your results directory if you provide ` --save_complexityfiltered_reads`. Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

:::warning
The resulting `.fastq` files may _not_ always be the 'final' reads that go into taxprofiling, if you also run other steps such as host removal, run merging etc..
:::

### PRINSEQ++

[PRINSEQ++](https://github.com/Adrian-Cantu/PRINSEQ-plus-plus) is a C++ implementation of the [prinseq-lite.pl](https://prinseq.sourceforge.net/) program. It can be used to filter, reformat or trim genomic and metagenomic sequence data.

It is used in nf-core/taxprofiler for complexity filtering using different algorithms. This means that it will remove reads with low sequence diversity (e.g. mono- or dinucleotide repeats).

<details markdown="1">
<summary>Output files</summary>

- `prinseqplusplus/`
  - `<sample_id>.log`: log file containing number of reads. Row IDs correspond to: `min_len, max_len, min_gc, max_gc, min_qual_score, min_qual_mean, ns_max_n, noiupac, derep, lc_entropy, lc_dust, trim_tail_left, trim_tail_right, trim_qual_left, trim_qual_right, trim_left, trim_right`
  - `<sample_id>_good_out.fastq.gz`: resulting FASTQ file without low-complexity reads

</details>

By default nf-core/taxprofiler will only provide the `.log` file if PRINSEQ++ is selected as the complexity filtering tool. You will only find the complexity filtered `.fastq` files in your results directory if you supply ` --save_complexityfiltered_reads`. Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

:::warning
The resulting `.fastq` files may _not_ always be the 'final' reads that go into taxprofiling, if you also run other steps such as host removal, run merging etc..
:::

### Filtlong

[Filtlong](https://github.com/rrwick/Filtlong) is a quality filtering tool for long reads. It can take a set of small reads and produce a smaller, better subset.

<details markdown="1">
<summary>Output files</summary>

- `filtlong/`
  - `<sample_id>_filtered.fastq.gz`: Quality or short read data filtered file
  - `<sample_id>_filtered.log`: log file containing summary statistics

</details>

You will only find the `.fastq` files in the results directory if you provide ` --save_preprocessed_reads`. Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

:::warning
We do _not_ recommend using Filtlong if you are performing filtering of low quality reads with ONT's basecaller Guppy.
:::

### Bowtie2

[Bowtie 2](https://bowtie-bio.sourceforge.net/bowtie2/index.shtml) is an ultrafast and memory-efficient tool for aligning sequencing reads to long reference sequences. It is particularly good at aligning reads of about 50 up to 100s or 1,000s of characters, and particularly good at aligning to relatively long (e.g. mammalian) genomes.

It is used with nf-core/taxprofiler to allow removal of 'host' (e.g. human) and/or other possible contaminant reads (e.g. Phi X) from short-read `.fastq` files prior to profiling.

<details markdown="1">
<summary>Output files</summary>

- `bowtie2/`
  - `build/`
    - `*.bt2`: Bowtie2 indicies of reference genome, only if `--save_hostremoval_index` supplied.
  - `align/`
    - `<sample_id>.bam`: BAM file containing reads that aligned against the user-supplied reference genome as well as unmapped reads
    - `<sample_id>.bowtie2.log`: log file about the mapped reads
    - `<sample_id>.unmapped.fastq.gz`: the off-target reads from the mapping that is used in downstream steps.

</details>

By default nf-core/taxprofiler will only provide the `.log` file if host removal is turned on. You will only have a `.bam` file if you specify `--save_hostremoval_bam`. This will contain _both_ mapped and unmapped reads. You will only get FASTQ files if you specify to save `--save_hostremoval_unmapped` - these contain only unmapped reads. Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

:::info
Unmapped reads in FASTQ are only found in this directory for short-reads, for long-reads see [`samtools/fastq/`](#samtools-fastq).
:::

:::info
The resulting `.fastq` files may _not_ always be the 'final' reads that go into taxprofiling, if you also run other steps such as run merging etc..
:::

:::info
While there is a dedicated section in the MultiQC HTML for Bowtie2, these values are not displayed by default in the General Stats table. Rather, alignment statistics to host genome is reported via samtools stats module in MultiQC report for direct comparison with minimap2 (see below).
:::

### minimap2

[minimap2](https://github.com/lh3/minimap2) is an alignment tool suited to mapping long reads to reference sequences.

It is used with nf-core/taxprofiler to allow removal of 'host' (e.g. human) or other possible contaminant reads from long-read `.fastq` files prior to taxonomic classification/profiling.

<details markdown="1">
<summary>Output files</summary>

- `minimap2/`
  - `build/`
    - `*.mmi2`: minimap2 indices of reference genome, only if `--save_hostremoval_index` supplied.
  - `align/`
    - `<sample_id>.bam`: Alignment file in BAM format containing both mapped and unmapped reads.

</details>

By default, nf-core/taxprofiler will only provide the `.bam` file containing mapped and unmapped reads if saving of host removal for long reads is turned on via `--save_hostremoval_bam`.

:::info
minimap2 is not yet supported as a module in MultiQC and therefore there is no dedicated section in the MultiQC HTML. Rather, alignment statistics to host genome is reported via samtools stats module in MultiQC report.
:::

:::info
Unlike Bowtie2, minimap2 does not produce an unmapped FASTQ file by itself. See [`samtools/fastq`](#samtools-fastq).
:::

### SAMtools fastq

[SAMtools fastq](http://www.htslib.org/doc/1.1/samtools.html) converts a `.sam`, `.bam`, or `.cram` alignment file to FASTQ format

<details markdown="1">
<summary>Output files</summary>

- `samtools/stats/`
  - `<sample_id>_interleaved.fq.gz`: Unmapped reads only in FASTQ gzip format

</details>

This directory will be present and contain the unmapped reads from the `.fastq` format from long-read minimap2 host removal, if `--save_hostremoval_unmapped` is supplied. Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

:::info
For short-read unmapped reads, see [bowtie2](#bowtie2).
:::

### Analysis Ready Reads

:::info
This optional results directory will only be present in the pipeline results when supplying `--save_analysis_ready_reads`.
:::

<details markdown="1">
<summary>Output files</summary>

- `samtools/stats/`
  - `<sample_id>_{fq,fastq}.gz`: Final reads that underwent preprocessing and were sent for classification/profiling.

</details>

The results directory will contain the 'final' processed reads used as input for classification/profiling. It will _only_ include the output of the _last_ step of any combinations of preprocessing steps that may have been specified in the run configuration. For example, if you perform the read QC and host-removal preprocessing steps, the final reads that are sent to classification/profiling are the host-removed FASTQ files - those will be the ones present in this directory.

:::warning
If you turn off all preprocessing steps, then no results will be present in this directory. This happens independently for short- and long-reads. I.e. you will only have FASTQ files for short reads in this directory if you skip all long-read preprocessing.
:::

### SAMtools stats

[SAMtools stats](http://www.htslib.org/doc/samtools-stats.html) collects statistics from a `.sam`, `.bam`, or `.cram` alignment file and outputs in a text format.

<details markdown="1">
<summary>Output files</summary>

- `samtools/stats/`
  - `<sample_id>.stats`: File containing samtools stats output.

</details>

In most cases you do not need to check this file, as it is rendered in the MultiQC run report.

### Run Merging

nf-core/taxprofiler offers the option to merge FASTQ files of multiple sequencing runs or libraries that derive from the same sample, as specified in the input samplesheet.

This is the last possible preprocessing step, so if you have multiple runs or libraries (and run merging turned on), this will represent the final reads that will go into classification/profiling steps.

<details markdown="1">
<summary>Output files</summary>

- `run_merging/`
  - `*.fastq.gz`: Concatenated FASTQ files on a per-sample basis

</details>

Note that you will only find samples that went through the run merging step in this directory. For samples that had a single run or library will not go through this step of the pipeline and thus will not be present in this directory.

This directory and its FASTQ files will only be present if you supply `--save_runmerged_reads`.Alternatively, if you wish only to have the 'final' reads that go into classification/profiling (i.e., that may have additional processing), do not specify this flag but rather specify `--save_analysis_ready_reads`, in which case the reads will be in the folder `analysis_ready_reads`.

### Bracken

[Bracken](https://ccb.jhu.edu/software/bracken/) (Bayesian Reestimation of Abundance with Kraken) is a highly accurate statistical method that computes the abundance of species in DNA sequences from a metagenomics sample. Braken uses the taxonomy labels assigned by Kraken, a highly accurate metagenomics classification algorithm, to estimate the number of reads originating from each species present in a sample.

:::info
The first step of using Bracken requires running Kraken2, therefore the initial results before abundance estimation will be found in `<your_results>/kraken2/<your_bracken_db_name>`.
:::

<details markdown="1">
<summary>Output files</summary>

- `bracken/`
  - `<db_name>/`
    - `bracken_<db_name>_combined_reports.txt`: combined bracken results as output from Bracken's `combine_bracken_outputs.py` script
    - `<db_name>/`
      - `<sample>_<db_name>.tsv`: TSV file containing per-sample summary of Bracken results with abundance information
      - `<sample>_<db_name>.report_bracken_species.txt`: Kraken2 style report with Bracken abundance information

</details>

The main taxonomic profiling file from Bracken is the `*.tsv` file. This provides the basic results from Kraken2 but with the corrected abundance information. Note that the raw Kraken2 version of the upstream step of Bracken can be found in the `kraken2/` directory with the suffix of `<sample_id>_<db_name>.bracken.report.txt` (with a 6 column variant when `--save_minimizers` specified).

### Kraken2

[Kraken](https://ccb.jhu.edu/software/kraken2/) is a taxonomic sequence classifier that assigns taxonomic labels to DNA sequences. Kraken examines the k-mers within a query sequence and uses the information within those k-mers to query a database. That database maps -mers to the lowest common ancestor (LCA) of all genomes known to contain a given k-mer.

<details markdown="1">
<summary>Output files</summary>

- `kraken2/`
  - `<db_name>_combined_reports.txt`: A combined profile of all samples aligned to a given database (as generated by `krakentools`)
    - If you have also run Bracken, the original Kraken report (i.e., _before_ read re-assignment) will also be included in this directory with `-bracken` suffixed to your Bracken database name if you supply `--bracken_save_intermediatekraken2` to the run. For example: `kraken2-<mydatabase>-bracken.tsv`. However in most cases you want to use the actual Bracken file (i.e., `bracken_<mydatabase>.tsv`).
  - `<db_name>/`
    - `<sample_id>_<db_name>.classified.fastq.gz`: FASTQ file containing all reads that had a hit against a reference in the database for a given sample
    - `<sample_id>_<db_name>.unclassified.fastq.gz`: FASTQ file containing all reads that did not have a hit in the database for a given sample
    - `<sample_id>_<db_name>.<kraken2/bracken2>report.txt`: A Kraken2 report that summarises the fraction abundance, taxonomic ID, number of Kmers, taxonomic path of all the hits in the Kraken2 run for a given sample. Will be 6 column rather than 8 if `--save_minimizers` specified. This report will **only** be included if you supply `--bracken_save_intermediatekraken2` to the run.
    - `<sample_id>_<db_name>.classifiedreads.txt`: A list of read IDs and the hits each read had against each database for a given sample

</details>

The main taxonomic classification file from Kraken2 is the `_combined_reports.txt` or `*report.txt` file. The former provides you the broadest over view of the taxonomic classification results across all samples against a single database, where you get two columns for each sample e.g. `2_all` and `2_lvl`, as well as a summarised column summing up across all samples `tot_all` and `tot_lvl`. The latter gives you the most information for a single sample. The report file is also used for the taxpasta step.

You will only receive the `.fastq` and `*classifiedreads.txt` file if you supply `--kraken2_save_reads` and/or `--kraken2_save_readclassifications` parameters to the pipeline.

When running Bracken, you will only get the 'intermediate' Kraken2 report files in this directory if you supply `--bracken_save_intermediatekraken2` to the run.

### KrakenUniq

[KrakenUniq](https://github.com/fbreitwieser/krakenuniq) (formerly KrakenHLL) is an extension to the fast k-mer-based classification performed by [Kraken](https://github.com/DerrickWood/kraken) with an efficient algorithm for additionally assessing the coverage of unique k-mers found in each species in a dataset.

<details markdown="1">
<summary>Output files</summary>

- `krakenuniq/`
  - `<db_name>/`
    - `<sample_id>_<db_name>[.merged].classified.fast{a,q}.gz`: Optional FASTA file containing all reads that had a hit against a reference in the database for a given sample. Paired-end input reads are merged in this output.
    - `<sample_id>_<db_name>[.merged].unclassified.fast{a,q}.gz`: Optional FASTA file containing all reads that did not have a hit in the database for a given sample. Paired-end input reads are merged in this output.
    - `<sample_id>_<db_name>.krakenuniq.report.txt`: A Kraken2-style report that summarises the fraction abundance, taxonomic ID, number of Kmers, taxonomic path of all the hits, with an additional column for k-mer coverage, that allows for more accurate distinguishing between false-positive/true-postitive hits.
    - `<sample_id>_<db_name>.krakenuniq.classified.txt`: An optional list of read IDs and the hits each read had against each database for a given sample.

</details>

The main taxonomic classification file from KrakenUniq is the `*.krakenuniq.report.txt` file. This is an extension of the Kraken2 report with the additional k-mer coverage information that provides more information about the accuracy of hits.

You will only receive the `.fasta.gz` and `*.krakenuniq.classified.txt` file if you supply `--krakenuniq_save_reads` and/or `--krakenuniq_save_readclassification` parameters to the pipeline.

:::info
The output system of KrakenUniq can result in other `stdout` or `stderr` logging information being saved in the report file, therefore you must check your report files before downstream use!
:::

### Centrifuge

[Centrifuge](https://github.com/DaehwanKimLab/centrifuge) is a taxonomic sequence classifier that uses a Burrows-Wheeler transform and Ferragina-Manzina index for storing and mapping sequences.

<details markdown="1">
<summary>Output files</summary>

- `centrifuge/`
  - `<db_name>/`
    - `<sample_id>.centrifuge.mapped.fastq.gz`: `FASTQ` files containing all mapped reads
    - `<sample_id>.centrifuge.report.txt`: A classification report that summarises the taxonomic ID, the taxonomic rank, length of genome sequence, number of classified and uniquely classified reads
    - `<sample_id>.centrifuge.results.txt`: A file that summarises the classification assignment for a read, i.e read ID, sequence ID, score for the classification, score for the next best classification, number of classifications for this read
    - `<sample_id>.centrifuge.txt`: A Kraken2-style report that summarises the fraction abundance, taxonomic ID, number of k-mers, taxonomic path of all the hits in the centrifuge run for a given sample
    - `<sample_id>.centrifuge.unmapped.fastq.gz`: FASTQ file containing all unmapped reads

</details>

The main taxonomic classification files from Centrifuge are the `_combined_reports.txt`, `*report.txt`, `*results.txt` and the `*centrifuge.txt`. The latter is used by the taxpasta step. You will receive the `.fastq` files if you supply `--centrifuge_save_reads`.

### Kaiju

[Kaiju](https://github.com/bioinformatics-centre/kaiju) is a taxonomic classifier that finds maximum exact matches on the protein-level using the Burrows-Wheeler transform.

<details markdown="1">
<summary>Output files</summary>

- `kaiju/`
  - `kaiju_<db_name>_combined_reports.txt`: A combined profile of all samples aligned to a given database (as generated by kaiju2table)
  - `<db_name>/`
    - `<sample_id>_<db_name>.kaiju.tsv`: Raw output from Kaiju with taxonomic rank, read ID and taxonic ID
    - `<sample_id>_<db_name>.kaijutable.txt`: Summarised Kaiju output with fraction abundance, taxonomic ID, number of reads, and taxonomic names (as generated by `kaiju2table`)

</details>

The most useful summary file is the `_combined_reports.txt` file which summarises hits across all reads and samples. Separate per-sample versions summaries can be seen in `<db>/*.txt`. However if you wish to look at more precise information on a per-read basis, see the `*tsv` file. The default taxonomic rank is `species`. You can provide a different one by updating the argument `--kaiju_taxon_rank`.

### DIAMOND

[DIAMOND](https://github.com/bbuchfink/diamond) is a sequence aligner for translated DNA searches or protein sequences against a protein reference database such as NR. It is a replacement for the NCBI BLAST software tools.It has many key features and it is used as taxonomic classifier in nf-core/taxprofiler.

<details markdown="1">
<summary>Output files</summary>

- `diamond/`
  - `<db_name>/`
    - `<sample_id>.log`: A log file containing stdout information
    - `<sample_id>*.{blast,xml,txt,daa,sam,tsv,paf}`: A file containing alignment information in various formats, or taxonomic information in a text-based format. Exact output depends on user choice.

</details>

By default you will receive a TSV output. Alternatively, you will receive a `*.sam` file if you provide the parameter `--diamond_save_reads` but in this case no taxonomic classification will be available(!), only the aligned reads in sam format.

:::info
DIAMOND has many output formats, so depending on your [choice](https://github.com/bbuchfink/diamond/wiki/3.-Command-line-options) with ` --diamond_output_format` you will receive the taxonomic information in a different format.
:::

### MALT

[MALT](https://software-ab.cs.uni-tuebingen.de/download/malt) is a fast replacement for BLASTX, BLASTP and BLASTN, and provides both local and semi-global alignment capabilities.

<details markdown="1">
<summary>Output files</summary>

- `malt/`
  - `<db_name>/`
    - `<sample_id>.blastn.sam`: sparse SAM file containing alignments of each hit
    - `<sample_id>.megan`: summary file that can be loaded into the [MEGAN6](https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/lehrstuehle/algorithms-in-bioinformatics/software/megan6/) interactive viewer. Generated by MEGAN6 companion tool `rma2info`
    - `<sample_id>.rma6`: binary file containing all alignments and taxonomic information of hits that can be loaded into the [MEGAN6](https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/lehrstuehle/algorithms-in-bioinformatics/software/megan6/) interactive viewer
    - `<sample_id>.txt.gz`: text file containing taxonomic IDs and read counts against each taxon. Generated by MEGAN6 companion tool `rma2info`

</details>

The main output of MALT is the `.rma6` file format, which can be only loaded into MEGAN and it's related tools. We provide the `rma2info` text files for improved compatibility with spreadsheet programs and other programmtic data manipulation tools, however this has only limited information compared to the 'binary' RMA6 file format (the `.txt` file only contains taxonomic ID and count, whereas RMA6 has taxonomic lineage information).

You will only receive the `.sam` and `.megan` files if you supply `--malt_save_reads` and/or `--malt_generate_megansummary` parameters to the pipeline.

### MetaPhlAn

[MetaPhlAn](https://github.com/biobakery/metaphlan) is a computational tool for profiling the composition of microbial communities (Bacteria, Archaea and Eukaryotes) from metagenomic shotgun sequencing data (i.e. not 16S) with species-level resolution via marker genes.

<details markdown="1">
<summary>Output files</summary>

- `metaphlan/`
  - `metaphlan_<db_name>_combined_reports.txt`: A combined profile of all samples aligned to a given database (as generated by `metaphlan_merge_tables`)
  - `<db_name>/`
    - `<sample_id>.biom`: taxonomic profile in BIOM format
    - `<sample_id>.bowtie2out.txt`: BowTie2 alignment information (can be re-used for skipping alignment when re-running MetaPhlAn with different parameters)
    - `<sample_id>_profile.txt`: MetaPhlAn taxonomic profile including abundance estimates

</details>

The output contains a file named `*_combined_reports.txt`, which provides an overview of the classification results for all samples. The main taxonomic profiling file from MetaPhlAn is the `*_profile.txt` file. This provides the abundance estimates from MetaPhlAn however does not include raw counts by default. Additionally, it contains intermediate Bowtie2 output `.bowtie2out.txt`, which presents a condensed representation of the mapping results of your sequencing reads to MetaPhlAn's marker gene sequences. The alignments are listed in tab-separated columns, including Read ID and Marker Gene ID, with each alignment represented on a separate line.

### mOTUs

[mOTUS](https://github.com/motu-tool/mOTUs) is a taxonomic profiler that maps reads to a unique marker specific database and estimates the relative abundance of known and unknown species.

<details markdown="1">
<summary>Output files</summary>

- `motus/`
  - `<db_name>/`
    - `<sample_id>.log`: A log file that contains summary statistics
    - `<sample_id>.out`: A classification file that summarises taxonomic identifiers, by default at the rank of mOTUs (i.e., species level), and their relative abundances in the profiled sample.
  - `motus_<db_name>_combined_reports.txt`: A combined profile of all samples aligned to a given database (as generated by `motus_merge`)

</details>

Normally `*_combined_reports.txt` is the most useful file for downstream analyses, but the per sample `.out` file can provide additional more specific information. By default, nf-core/taxprofiler is providing a column describing NCBI taxonomic ID as this is used in the taxpasta step. You can disable this column by activating the argument `--motus_remove_ncbi_ids`.
You will receive the relative abundance instead of read counts if you provide the argument `--motus_use_relative_abundance`.

### KMCP

[KMCP](https://github.com/shenwei356/kmcp) utilises genome coverage information by splitting the reference genomes into chunks and stores k-mers in a modified and optimised COBS index for fast alignment-free sequence searching. KMCP combines k-mer similarity and genome coverage information to reduce the false positive rate of k-mer-based taxonomic classification and profiling methods.

<details markdown="1">
<summary>Output files</summary>

- `kmcp/`

  - `<db_name>/`
    - `<sample_id>.gz`: output of `kmcp_search` containing search sequences against a database in tab-delimited format with 15 columns.
    - `<sample_id>_kmcp.profile`: output of `kmcp_profile` containing the taxonomic profile from search results.

  </details>

You will receive the `<sample_id>.gz` file if you supply `--kmcp_save_search`. Please note that there is no taxonomic label assignment in this output file.

The main taxonomic classification file from KMCP is the `*kmcp.profile` which is also used by the taxpasta step.

### ganon

[ganon](https://pirovc.github.io/ganon/) is designed to index large sets of genomic reference sequences and to classify reads against them efficiently. The tool uses Interleaved Bloom Filters as indices based on k-mers/minimizers. It was mainly developed, but not limited, to the metagenomics classification problem: quickly assign sequence fragments to their closest reference among thousands of references. After classification, taxonomic abundance is estimated and reported.

<details markdown="1">
<summary>Output files</summary>

- `ganon/`

  - `<db_name>/`

    - `<sample_id>_report.tre`: output of `ganon report` containing taxonomic classifications with possible formatting and/or filtering depending on options specified.
    - `<sample_id>`.tre: output of `ganon classify` containing raw taxonomic classifications and abundance estimations with no additional formatting or filtering.
    - `<sample_id>`.rep: 'raw' report of counts against each taxon.
    - `<sample_id>`.all: per-read summary of all hits of each reads.
    - `<sample_id>`.lca: per-read summary of the best single hit after LCA for each read.
    - `<sample_id>`.unc: list of read IDs with no hits.
    - `<sample_id>`.log: the stdout console messages printed by `ganon classify`, containing some classification summary information

  - `ganon_<db_name>_combined_reports.txt`: A combined profile of all samples aligned to a given database (as generated by `ganon table`)

</details>

Generally you will want to refer to the `combined_reports.txt` or `_report.tre` file. For further descriptions of the contents of each file, see the [ganon documentation](https://pirovc.github.io/ganon/outputfiles/).

You will only receive the `.all`, `.lca`, and `.unc` files if you supply the `--ganon_save_readclassifications` parameter to the pipeline.

### Krona

[Krona](https://github.com/marbl/Krona) allows the exploration of (metagenomic) hierarchical data with interactive zooming, multi-layered pie charts.

Krona charts will be generated by the pipeline for supported tools (Kraken2, Centrifuge, Kaiju, and MALT)

<details markdown="1">
<summary>Output files</summary>

- `krona/`
  - `<tool_name>_<db_name>.html`: per-tool/per-database interactive HTML file containing hierarchical piecharts

</details>

The resulting HTML files can be loaded into your web browser for exploration. Each file will have a dropdown to allow you to switch between each sample aligned against the given database of the tool.

### TAXPASTA

[TAXPASTA](https://github.com/taxprofiler/taxpasta) standardises and optionally merges two or more taxonomic profiles across samples into one single table. It supports multiple different classifiers simplifying comparison of taxonomic classification results between tools and databases.

<details markdown="1">
<summary>Output files</summary>

- `taxpasta/`

  - `<tool>_<database>*.{tsv,csv,arrow,parquet,biom}`: Standardised taxon table containing multiple samples. The standard format is the `tsv`.
    - The first column describes the taxonomy ID and the rest of the columns describe the read counts for each sample.
    - Note that the file naming scheme will apply regardless of whether `TAXPASTA_MERGE` (multiple sample run) or `TAXPASTA_STANDARDISE` (single sample run) are executed.
    - If you have also run Bracken, the initial Kraken report (i.e., _before_ read re-assignment) will also be included in this directory with `-bracken` suffixed to your Bracken database name. For example: `kraken2-<mydatabase>-bracken.tsv`. However in most cases you want to use the actual Bracken file (i.e., `bracken_<mydatabase>.tsv`).

  </details>

By providing the path to a directory containing taxdump files to `--taxpasta_taxonomy_dir`, the taxon name, the taxon rank, the taxon's entire lineage including taxon names and/or the taxon's entire lineage including taxon identifiers can also be added in the output in addition to just the taxon ID. Addition of this extra information can be turned by using the parameters `--taxpasta_add_name`, `--taxpasta_add_rank`, `--taxpasta_add_lineage` and `--taxpasta_add_idlineage` respectively.

These files will likely be the most useful files for the comparison of differences in classification between different tools or building consensuses, with the caveat they have slightly less information than the actual output from each tool (which may have non-standard information e.g. taxonomic rank, percentage of hits, abundance estimations).

The following report files are used for the taxpasta step:

- Bracken: `<sample>_<db_name>.tsv` Taxpasta used the `new_est_reads` column for the standardised profile.
- Centrifuge: `<sample_id>.centrifuge.txt` Taxpasta uses the `direct_assigned_reads` column for the standardised profile.
- Diamond: `<sample_id>` Taxpasta summarises number of reads per NCBI taxonomy ID standardised profile.
- Kaiju: `<sample_id>_<db_name>.kaijutable.txt` Taxpasta uses the `reads` column from kaiju2table standardised profile.
- KrakenUniq: `<sample_id>_<db_name>.report.txt` Taxpasta uses the `reads` column for the standardised profile.
- Kraken2: `<sample_id>_<db_name>.report.txt` Taxpasta uses the `direct_assigned_reads` column for the standardised profile.
- MALT: `<sample_id>.txt.gz` Taxpasta uses the `count` (second) column from the output of MEGAN6's rma2info for the standardised profile.
- MetaPhlAn: `<sample_id>_profile.txt` Taxpasta uses the `relative_abundance` column multiplied with a fixed number to yield an integer for the standardised profile.
- mOTUs: `<sample_id>.out` Taxpasta uses the `read_count` column for the standardised profile.

:::warning
Please aware the outputs of each tool's standardised profile _may not_ be directly comparable between each tool. Some may report raw read counts, whereas others may report abundance information. Please always refer to the list above, for which information is used for each tool.
:::

### MultiQC

<details markdown="1">
<summary>Output files</summary>

- `multiqc/`
  - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
  - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
  - `multiqc_plots/`: directory containing static images from the report in various formats.

</details>

[MultiQC](http://multiqc.info) is a visualization tool that generates a single HTML report summarising all samples in your project. Most of the pipeline QC results are visualised in the report and further statistics are available in the report data directory.

Results generated by MultiQC collate pipeline QC from supported tools e.g. FastQC. The pipeline has special steps which also allow the software versions to be reported in the MultiQC output for future traceability. For more information about how to use MultiQC reports, see <http://multiqc.info>.

All tools in taxprofiler supported by MultiQC will have a dedicated section showing summary statistics of each tool based on information stored in log files.

You can expect in the MultiQC reports either sections and/or general stats columns for the following tools:

- fastqc
- adapterRemoval
- fastp
- bbduk
- prinseqplusplus
- porechop
- filtlong
- bowtie2
- minimap2
- samtools (stats)
- kraken
- bracken
- centrifuge
- kaiju
- diamond
- malt
- motus

:::info
The 'General Stats' table by default will only show statistics referring to pre-processing steps, and will not display possible values from each classifier/profiler, unless turned on by the user within the 'Configure Columns' menu or via a custom MultiQC config file (`--multiqc_config`)
:::

### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `pipeline_info/`
  - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
  - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
  - Reformatted samplesheet files used as input to the pipeline: `samplesheet.valid.csv`.
  - Parameters used by the pipeline run: `params.json`.

</details>

[Nextflow](https://www.nextflow.io/docs/latest/tracing.html) provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.

