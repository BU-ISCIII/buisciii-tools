# TBProfiler

<img src="images/tb-profiler-logo-rectangle.png" alt="TBProfiler" width="300"/>


## Introduction
[**TBProfiler**](https://github.com/jodyphelan/TBProfiler) is a computational pipeline designed for the analysis of **Mycobacterium tuberculosis (MTB) whole genome sequencing (WGS) data**. The pipeline aligns reads to the H37Rv reference using [bowtie2](https://github.com/BenLangmead/bowtie2), [BWA](https://github.com/lh3/bwa) or [minimap2](https://github.com/lh3/minimap2) and then calls variants using [bcftools](https://github.com/samtools/bcftools). These variants are then compared to a [drug-resistance database](https://github.com/jodyphelan/tbdb) and annotated using [SnpEff](https://pcingola.github.io/SnpEff/). It also predicts the number of reads supporting drug resistance variants as an insight into hetero-resistance. The collated data can be graphically viewed on top of a phylogenetic tree using [iTOL](https://github.com/iBiology/iTOL). Config files can be generated and uploaded to iTOL to visualise drug resistance types, lineage and individual drug resistance predictions.

It provides:

- Rapid detection of **drug resistance mutations**.
- Lineage identification and **phylogenetic insights**.
- Summarized reports for clinical or research purposes.

---

## Pipeline Overview

The TBProfiler pipeline typically consists of the following steps:

1. **Read Alignment**
    - Mapping reads to the **H37Rv reference genome** using a high-performance aligner.

2. **Variant Calling**
    - Detection of SNPs and indels associated with drug resistance.
    - Identification of lineage-defining mutations.

3. **Resistance Profiling**
    - Interpretation of mutations according to known **drug resistance databases**.
    - Classification of isolates as sensitive or resistant to specific drugs.

4. **Reporting**
    - Generation of standardized **CSV, JSON, and CSV reports**.
    - Summaries include lineage, drug resistance profile, and mutation details.

---

## Scripts

`_01_tbprofiler.sh`: script that runs whole pipeline for each sample.

`_02_tbcollate.sh`: script that automatically creates a number of collated result files from all the individual result files in the result directory.

## Input Files

TBProfiler requires:

- **FASTQ files** (paired-end or single-end) from MTB WGS experiments (stored in `00-reads/`)

---

## Output

TBProfiler produces structured outputs organized per project or sample:

- **bam/**  
Aligned sequencing reads in BAM format:
```bash
bam/
├── SAMPLE1.bam
├── SAMPLE1.bam.bai
├── SAMPLE2.bam
└── SAMPLE2.bam.bai
```

- **results/**  
Contains summary reports, lab logs, and analysis results:
```bash
results/
├── tbprofiler.txt
├── tbprofiler.variants.csv
├── tbprofiler.variants.txt
├── SAMPLE1.results.csv
├── SAMPLE1.results.json
├── SAMPLE2.results.csv
└── SAMPLE2.results.txt
```
- **vcf/**  
Variant Call Format files for each sample, containing all detected SNPs/indels:
```bash
vcf/
├── SAMPLE1.targets.vcf.gz
└── SAMPLE2.targets.vcf.gz
```

- **logs/**
Logs for `_01_tbprofiler.sh` and `_02_tbcollate.sh`:
```bash
logs/
├── TBCOLLATE.JOBID.log
├── TBPROFILER.SAMPLE1.log
└── TBPROFILER.SAMPLE2.log
```


