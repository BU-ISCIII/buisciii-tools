## cgMLST/wgMLST

Here we describe the results from the cgMLST/wgMLST service using ChewBBACA and GrapeTree

- `mlst/allelecall_report.html`: A HTML report, that contains the following components:
  - A table with the total number of samples, total number of loci, total number of coding sequences (CDSs) extracted from the samples, total number of CDSs classified and totals per classification type.
  - A tab panel with stacked bar charts for the classification type counts per sample and per locus.
  - A tab panel with detailed sample and locus statistics.
  - If a TSV file with annotations is provided to the --annotations parameter, the report will also include a table with the provided annotations. Otherwise, it will display a warning informing that no annotations were provided.
  - A Heatmap chart representing the loci presence-absence matrix for all samples in the dataset.
  - A Heatmap chart representing the allelic distance matrix for all samples in the dataset.
  - A tree drawn with Phylocanvas.gl based on the Neighbor-Joining (NJ) tree computed by FastTree.
- `mlst/distance_matrix_symmetric.tsv`: Symmetric distance matrix. The distances are computed by determining the number of allelic differences from the set of core loci (shared by 100% of the samples) between each pair of samples.
- `mlst/tree.nwk`: Newick tree from the Minimum Spannig Tree.
- `mlst/tree.svg`: Minimum Spannig Tree SVG (Scalable Vector Graphics) plot. Branches longer than = 700 are shown shortenned.
