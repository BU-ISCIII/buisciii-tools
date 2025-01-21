# ExomeEB

This markdown briefly describes the files found in `RESULTS/` folder for ExomeEB service.

## exomiser.html

This file includes information regarding variant annotation, effect prediction and inheritance typing:

![HTML Description 1](images/exomiser-html-description-1.png)

![HTML Description 2](images/exomiser-html-description-2.png)

## picard_hsmetrics.csv

This table includes mapping quality metrics from sarek's pipeline results, with the following columns:
- SAMPLE
- MEAN TARGET COVERAGE: The mean coverage of a target region.
- PCT USABLE BASES ON TARGET: The number of aligned, de-duped, on-bait bases out of the PF bases available (those that pass the vendor's filter).
- FOLD ENRICHMENT: The fold by which the baited region has been amplified above genomic background.
- PCT TARGET BASES 10X: The fraction of all target bases achieving 10X or greater coverage.
- PCT TARGET BASES 20X: The fraction of all target bases achieving 20X or greater coverage.
- PCT TARGET BASES 30X: The fraction of all target bases achieving 30X or greater coverage.
- PCT TARGET BASES 40X: The fraction of all target bases achieving 40X or greater coverage.
- PCT TARGET BASES 50X: The fraction of all target bases achieving 50X or greater coverage.

You may find further documentation for the metrics in this table [here](http://broadinstitute.github.io/picard/picard-metric-definitions.html#HsMetrics).

## variants_annot_highmoderate.tab

This table includes all the variants from VEP and Exomiser annotation with a predicted high or moderate effect.

ID: Variant identifier
Chrom: Chromosome number
Pos: Reference position according to hg19
Ref: Nucleotides found in the reference genome
Alt: Nucleotides found in the individual's genome
Filter: Indicates whether it has passed the filter or not
Sample_GT: Genotype of sample
Sample_DP: Coverage depth of sample
Sample_AD: Allelic Depth of Genotype of sample
Sample_GQ: Quality of Genotype of sample
Gene: Gene affected by the variant
Location: Location of the variant in the genome
Allele: Alternative allele of the variant
Feature: Genomic element affected by the variant
Feature_type: Type of genomic element affected by the variant
Consequence: Functional consequence of the variant
cDNA_position: Position of the variant in the cDNA sequence
CDS_position: Position of the variant in the gene's coding sequence
Protein_position: Position of the variant in the protein encoded by the gene
Amino_acids: Amino acids affected by the variant
Codons: Codons affected by the variant
Existing_variation: Existing genetic variation at this position
Impact: Fundamental impact of the variant
Distance: Distance of the variant to the nearest exon
Strand: DNA strand on which the variant is located
Flags: Indicators of additional variant features
Variant_class: Variant class
Symbol: Gene symbol affected by the variant
Symbol_source: Source of the variant symbol
HGNC_ID: Unique identifier in the HGNC database
Biotype: Gene biotype
Canonical: Indicates if it is the canonical transcript of the gene
Mane_sel: Indicates if the transcript is identified by Mane
Mane_plus: Indicates if the transcript is identified by Mane+
TSL: Indicates if the transcript is identified by TSL
Appris: Indicates if the transcript is identified by Appris
ENSP: Unique identifier of the transcript in Ensembl
Swissprot: Unique identifier of the transcript in Swissprot
TREMBL: Unique identifier of the transcript in TREMBL
Uniparc: Unique identifier of the protein in the Uniparc database
Uniparc_Isoform: Unique identifier of the protein isoform in Uniparc
Gene_pheno: Indicates if the gene is associated with a phenotype
SIFT: SIFT pathogenicity of the variant
PolyPhen: PolyPhen pathogenicity of the variant
Exon: Indicates if the variant is located in an exon
Intron: Indicates if the variant is located in an intron
Domains: Protein domains affected by the variant
miRNA: miRNA binding to the region affected by the variant
HGVSc: HGVS notation for the variant in cDNA sequence
HGVSp: HGVS notation for the variant in protein sequence
HGVS_offset: Offset of the variant in cDNA or protein sequence
AF: Allelic frequency of the variant in the general population
AFR_AF: Allelic frequency of the variant in the African population
AMR_AF: Allelic frequency of the variant in the American population
EAS_AF: Allelic frequency of the variant in the East Asian population
EUR_AF: Allelic frequency of the variant in the European population
SAS_AF: Allelic frequency of the variant in the South Asian population
AA_AF: Allelic frequency of the variant in the African American population
EA_AF: Allelic frequency of the variant in the European American population
gnomAD_AF: Allelic frequency of the variant in the gnomAD database
gnomAD_AFR_AF: Allelic frequency of the variant in the African population in gnomAD
gnomAD_AMR_AF: Allele frequency of the variant in the American population in gnomAD
gnomAD_ASJ_AF: Allele frequency of the variant in the Asian and Japanese population in gnomAD
gnomAD_EAS_AF: Allele frequency of the variant in the East Asian population in gnomAD
gnomAD_FIN_AF: Allele frequency of the variant in the Finnish population in gnomAD
gnomAD_NFE_AF: Allele frequency of the variant in the non-Finnish European population in gnomAD
gnomAD_OTH_AF: Allele frequency of the variant in other populations in gnomAD
gnomAD_SAS_AF: Allele frequency of the variant in the South Asian population in gnomAD
MAX_AF: Maximum allele frequency of the variant in all populations
MAX_AF_POPS: Population with the maximum allele frequency of the variant
CLIN_SIG: Clinical significance of the variant
SOMATIC: Indicates if the variant is somatic or germline
PHENO: Phenotype associated with the variant
HGNC_ID: Unique identifier of the gene affected by the variant
PUBMED: Scientific articles describing the variant
MOTIF_NAME: Transcription factor binding motif affected by the variant
MOTIF_POS: Position of the transcription factor binding motif affected
HIGH_INF_POS: High information position in the transcription factor binding motif
MOTIF_SCORE_CHANGE: Change in the transcription factor binding motif score caused by the variant
TRANSCRIPTION_FACTORS: Transcription factors that bind to the affected transcription factor binding motif
HGVSp_snpEff: HGVS notation for the variant in the protein sequence in snpEff
SIFT_score: SIFT score of the pathogenicity of the variant
SIFT_pred: SIFT prediction of the pathogenicity of the variant
Polyphen2_HDIV_score: PolyPhen2_HDIV score of the pathogenicity of the variant
Polyphen2_HDIV_pred: PolyPhen2_HDIV prediction of the pathogenicity of the variant
Polyphen2_HVAR_score: PolyPhen2_HVAR score of the pathogenicity of the variant
Polyphen2_HVAR_pred: PolyPhen2_HVAR prediction of the pathogenicity of the variant
MutationTaster_score: MutationTaster score of the pathogenicity of the variant
MutationTaster_pred: MutationTaster prediction of the pathogenicity of the variant
MutationAssessor_score: MutationAssessor score of the pathogenicity of the variant
MutationAssessor_pred: MutationAssessor prediction of the pathogenicity of the variant
FATHMM_score: FATHMM score of the pathogenicity of the variant
FATHMM_pred: FATHMM prediction of the pathogenicity of the variant
HGVSp: HGVS notation for the variant in the protein sequence
HGVS_offset: Displacement of the variant in the cDNA or protein sequence
PROVEAN_score: PROVEAN score of the pathogenicity of the variant
PROVEAN_pred: PROVEAN prediction of the pathogenicity of the variant
VEST4_score: VEST4 score of the pathogenicity of the variant
MetaSVM_score: MetaSVM score of the pathogenicity of the variant
MetaSVM_pred: MetaSVM prediction of the pathogenicity of the variant
MetaLR_score: MetaLR score of the pathogenicity of the variant
MetaLR_pred: MetaLR prediction of the pathogenicity of the variant
CADD_raw: Raw CADD score
CADD_phred: CADD Phred score
CADD_raw_hg19: Raw CADD score for the hg19 genome version
CADD_phred_hg19: CADD Phred score for the hg19 genome version
GERP++_NR: GERP++ score for the non-coding region
GERP++_RS: GERP++ score for the synonymous region
phyloP100way_vertebrate: phyloP score for 100 vertebrate species
phastCons100way_vertebrate: phastCons score for 100 vertebrate species
clinvar_trait: Clinical trait or condition associated with the variant
clinvar_id: Unique identifier of the variant in ClinVar
clinvar_OMIM_id: Unique identifier of the variant in OMIM
OMIM_id: Unique identifier of the disease in OMIM
Function_description: Description of the function of the gene affected by the variant
Disease_description: Description of the disease associated with the variant
HPO_id: Unique identifier of the phenotype in the HPO database
HPO_name: Name of the phenotype in the HPO database

## multiqc_report.html

Most of sarek's QC results are visualised in this report and further statistics are available in the report data directory. 
Results generated by MultiQC collect pipeline QC from supported tools e.g. FastQC. The pipeline has special steps which also allow the software versions to be reported in the MultiQC output for future traceability. For more information about how to use MultiQC reports, see http://multiqc.info.
