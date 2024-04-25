# PlasmidID

Here we describe the results from the Viralrecon pipeline for viral genome reconstruction.

> [!WARNING]
> Some of the files listed here may not be in your  `RESULTS` folder. It will depend on the analysis you requested.

## Summary report

A summary report consolidating all samples in the analysis is created.

- `NO_GROUP_final_results.html`: report with same info as table below that can be viewed using chrome.
- `NO_GROUP_final_results.tab`: plasmid info for each sample. Header columns are described here:
  - id: plasmid unique identifier for each entry.
  - length: The length of the plasmid sequence.
  - species description: A description of the species from which the sequence originates.
  - fraction_covered: The fraction of the sequence that is covered by alignments.
  - contig_name: The name of the contigs associated with the sequence.
  - percentage: The percentage of the genome or sequence that is covered.
  - images: Links or references to related images or visual data.

## Circos images

Circos is used for creating one image for each identified plasmid and a summary image with all the plasmids identified in one figure. A manual for image interpretation can be found [here](https://github.com/BU-ISCIII/plasmidID/wiki/Understanding-the-image:-track-by-track) and a manual about how to select the correct plasmid can be found [here](https://github.com/BU-ISCIII/plasmidID/wiki/How-to-chose-the-right-plasmids).

- `images/SAMPLE_NAME_PLASMID_individual.png`: circos image for individual plasmidID
- `images/SAMPLE_NAME_summary_image.png`: summary image