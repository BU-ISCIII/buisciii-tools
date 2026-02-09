# bu-isciii tools Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [2.3.0] - 2025-02-09 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.3.0

### Credits

- [Victor Lopez](https://github.com/victor5lm)
- [Pau Pascual](https://github.com/PauPascualMas)
- [Magdalena Matito](https://github.com/magdasmat)
- [Juan Ledesma](https://github.com/juanledesma78)

### Template fixes and updates

- Updated taxprofiler version in lablog [#584](https://github.com/BU-ISCIII/buisciii-tools/pull/584).
- Fixed snippy folder in iqtree's lablog [#584](https://github.com/BU-ISCIII/buisciii-tools/pull/584).
- Fixed minor mistake in generate_summary_outbreak.py [#584](https://github.com/BU-ISCIII/buisciii-tools/pull/584).
- Enhanced differential_expression.R when reporting results [#584](https://github.com/BU-ISCIII/buisciii-tools/pull/584).
- Updated the lowfreq_panel template [#586](https://github.com/BU-ISCIII/buisciii-tools/pull/586).
- Updated sftp_user.json to add mcoiras [#595](https://github.com/BU-ISCIII/buisciii-tools/pull/595).
- Replace MTBseq with TBProfiler in README.md [#597](https://github.com/BU-ISCIII/buisciii-tools/pull/597).
- Replace MTBseq with TBProfiler in templates/services.json [#598](https://github.com/BU-ISCIII/buisciii-tools/pull/598).
- Updated emmtyper's lablog [#603](https://github.com/BU-ISCIII/buisciii-tools/pull/603).
- Updated bacass version in assembly's template [#604](https://github.com/BU-ISCIII/buisciii-tools/pull/604).
- Updated sftp_user.json to add bdandres to LabInmunology [#605](https://github.com/BU-ISCIII/buisciii-tools/pull/605). 
- Refactor MTBseq template for TBProfiler pipleine with its lablogs [#607](https://github.com/BU-ISCIII/buisciii-tools/pull/607)
- Added new authors contact in pyproject.toml [#607](https://github.com/BU-ISCIII/buisciii-tools/pull/607)
- Update tbprofiler assets/reports/md markdown file and tbprofiler assets/reports/results markdown file [#607](https://github.com/BU-ISCIII/buisciii-tools/pull/607)
- Added new BLAST database created in July 2025 [#608](https://github.com/BU-ISCIII/buisciii-tools/pull/608)
- Added hgil and Labviruspapiloma to sft_user.json [#609](https://github.com/BU-ISCIII/buisciii-tools/pull/609)
- Updated taxprofiler's lablog so that Bowtie2 uses an already built index [#612](https://github.com/BU-ISCIII/buisciii-tools/pull/612).
- Updated viralrecon's lablog to avoid exiting when the refgenie env is not loaded, even when it actually is [#613](https://github.com/BU-ISCIII/buisciii-tools/pull/613).
- Completed service info in services.json [#619](https://github.com/BU-ISCIII/buisciii-tools/pull/619).
- Updated sftp_user.json to add lorena.pozo to labantibiotics [#620](https://github.com/BU-ISCIII/buisciii-tools/pull/620).
- Replaced conda by the corresponding micromamba's env in amrfinderplus's lablog [#621](https://github.com/BU-ISCIII/buisciii-tools/pull/621).
- Removed exomiser.html part from trios' results md and fixed wrong image paths in exomeeb results md [#622](https://github.com/BU-ISCIII/buisciii-tools/pull/622).
- Added new exometrio bed files [#624](https://github.com/BU-ISCIII/buisciii-tools/pull/624).
- Fixed minor mistake in chewbbaca's lablog [#625](https://github.com/BU-ISCIII/buisciii-tools/pull/625).

### Modules

- Fixed new-service to properly check MD5 files when samples do not belong to the same run [#583](https://github.com/BU-ISCIII/buisciii-tools/pull/583).

#### Added enhancements

- Implemented logging and error handling in buisciii-tools [#619](https://github.com/BU-ISCIII/buisciii-tools/pull/619).
- Replaced pkg_resources by importlib.metadata due to pkg_resources being deprecated [#619](https://github.com/BU-ISCIII/buisciii-tools/pull/619).

#### Fixes

#### Changed

#### Removed

### Requirements

- Updated GitHub action: `python_lint` now uses Python 3.10 [#615](https://github.com/BU-ISCIII/buisciii-tools/pull/615)

## [2.2.13] - 2025-09-16 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.13

### Credits

- [Victor Lopez](https://github.com/victor5lm)
- [Alejandro Bernabeu](https://github.com/Aberdur)

### Template fixes and updates

- Updated sftp_user.json [#568](https://github.com/BU-ISCIII/buisciii-tools/pull/568).
- Fixed the parse_ariba.py script and stored in the 99-stats folder from the CHARACTERIZATION template [#568](https://github.com/BU-ISCIII/buisciii-tools/pull/568).
- Updated IRMA template to comply with new sample id format in relecov analysis [578](https://github.com/BU-ISCIII/buisciii-tools/pull/578)
- Fix pkg_resources installation error and pin bacass version in Assembly template [579](https://github.com/BU-ISCIII/buisciii-tools/pull/579)

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.12] - 2025-07-18 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.12

### Credits

- [Victor Lopez](https://github.com/victor5lm)

### Template fixes and updates

- Fixed IRMA's 99-stats lablog to take host reads from samtools stats instead of kraken [#564](https://github.com/BU-ISCIII/buisciii-tools/pull/564).
- Fixed sgene_metrics.sh to handle warnings properly [#565](https://github.com/BU-ISCIII/buisciii-tools/pull/565).

### Modules

- Fixed finish module so that the clean module is run correctly [#564](https://github.com/BU-ISCIII/buisciii-tools/pull/564).
- Fixed bioinfo_doc module so that a text file can properly be used for email notes [#564](https://github.com/BU-ISCIII/buisciii-tools/pull/564).

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.11] - 2025-07-11 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.11

### Credits

- [Juan Ledesma](https://github.com/juanledesma78)
- [Victor Lopez](https://github.com/victor5lm)
- [Jaime Ozáez](https://github.com/jaimeozaez)

### Template fixes and updates

- Added micromamba environment PikaVirus_dev_2.6 to file hpc_slurm_pikavirus.config [#535](https://github.com/BU-ISCIII/buisciii-tools/pull/535).
- Changed analysis_date in create_summary_report.sh to take properly dates from RSV services when using viralrecon [#540](https://github.com/BU-ISCIII/buisciii-tools/pull/540).
- Fixed date formats for IRMA's template and excel_generator.py [#549](https://github.com/BU-ISCIII/buisciii-tools/pull/549).
- Fixed the way whether samples are paired or single-end is detected [#550](https://github.com/BU-ISCIII/buisciii-tools/pull/550).
- Removed pseudo_aligner parameter from RNASeq's lablog and added all missing symlinks in its RESULTS's lablog [#552](https://github.com/BU-ISCIII/buisciii-tools/pull/552).
- Updated scratch.py and __main__.py to properly handle custom paths and temporary directories [#555](https://github.com/BU-ISCIII/buisciii-tools/pull/555).
- Updated create_summary_report.sh to transform negative values into 0 [#556](https://github.com/BU-ISCIII/buisciii-tools/pull/556).
- Updated the assembly stats script to handle files in RAW properly and when quast results are not available for any sample [#557](https://github.com/BU-ISCIII/buisciii-tools/pull/557).

### Modules

- Fixed clean module to handle subpaths stated in services.json [#543](https://github.com/BU-ISCIII/buisciii-tools/pull/543).
- Fixed bioinfo_doc module to be able to indicate type (service_info or delivery) via CLI [#558](https://github.com/BU-ISCIII/buisciii-tools/pull/558).
- Fixed the bioinfo_doc module to properly ask for email text notes and the scratch module to use proper scratch_tmp_path [#559](https://github.com/BU-ISCIII/buisciii-tools/pull/559).

#### Added enhancements

- Added new script to download multiple SRA entries in fastq format when necessary [#551](https://github.com/BU-ISCIII/buisciii-tools/pull/551).

#### Fixes

#### Changed

- Modified bu-isciii > buisciii for all commands in README text [#548](https://github.com/BU-ISCIII/buisciii-tools/pull/548).

#### Removed

### Requirements

## [2.2.10] - 2025-05-21 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.10

### Credits

- [Victor Lopez](https://github.com/victor5lm)
- [Alejandro Bernabeu](https://github.com/Aberdur)

### Template fixes and updates

- Redefinition of analysis_date and lineage_analysis_date based on mapping folder and DOC config in viralrecon's template [#523](https://github.com/BU-ISCIII/buisciii-tools/pull/523).
- Fix analysis_date and lineage_assignment_date format in create_summary_report.sh [#525](https://github.com/BU-ISCIII/buisciii-tools/pull/525).
- Created a new script to correctly merge all nextclade results into one .csv file in IRMA's template, apart from updating lablog_irma_results with new symlinks to relevant files [#526](https://github.com/BU-ISCIII/buisciii-tools/pull/526).
- Adapted create_summary_report.sh to handle multiple references and add lineage columns to pangolin .csv only if they do not exist yet [#530](https://github.com/BU-ISCIII/buisciii-tools/pull/530).

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.9] - 2025-05-13 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.9

### Credits

- [Victor Lopez](https://github.com/victor5lm)
- [Alejandro Bernabeu](https://github.com/Aberdur)
- [Juan Ledesma](https://github.com/juanledesma78)

### Template fixes and updates

- Updated create_summary_report.sh to properly handle single end reads [#509](https://github.com/BU-ISCIII/buisciii-tools/pull/509).
- Fix relative path handling in snpeff/snpsift annotation [#509](https://github.com/BU-ISCIII/buisciii-tools/pull/509).
- Added sed to lablog_bam2fq so that _R1.bam is removed and the variable sample is created properly for those sample ids having several underscores (i.e. EPI_ISL_666)[#490](https://github.com/BU-ISCIII/buisciii-tools/pull/490)
- Update IRMA 99-stats lablog to raise Error if taxprofiler results are missing [#515](https://github.com/BU-ISCIII/buisciii-tools/pull/515).
- Added a new lablog to create a .csv file for software versions in IRMA's template [#514](https://github.com/BU-ISCIII/buisciii-tools/pull/514/files).
- Fixed wrong variable definition in IRMA's 99-stats lablog and added Nextclade's info into viralrecon's create_summary_report.sh script to be added into the mapping_illumina report [#518](https://github.com/BU-ISCIII/buisciii-tools/pull/518).
- Added virus_sequence variable into IRMA's 99-stats lablog for the creation of the summary stats report [#519](https://github.com/BU-ISCIII/buisciii-tools/pull/519).

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.8] - 2025-04-29 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.8

### Credits

- [Alejandro Bernabeu](https://github.com/Aberdur)
- [Sergio Olmos](https://github.com/OPSergio)
- [Sara Monzon](https://github.com/saramonzon)
- [Jaime Ozáez](https://github.com/jaimeozaez)
- [Victor Lopez](https://github.com/victor5lm)
- [Sarai Varona](https://github.com/svarona)

### Template fixes and updates

- Updated snippy template, now using a modified version of snippy with different low coverage masking[#489](https://github.com/BU-ISCIII/buisciii-tools/pull/489)
- Update PlasmidID Report Generation to Output Summary by Sample [#483](https://github.com/BU-ISCIII/buisciii-tools/pull/483)
- Update of the execution of summary_report_pid.py in plasmidID lablog [#484](https://github.com/BU-ISCIII/buisciii-tools/pull/484)
- Added `sort -u` to wgs_metrics_all.txt file generation command in 99-stats lablog (snippy template) [#494](https://github.com/BU-ISCIII/buisciii-tools/pull/494)
- Avoided error messages when running 99-stats lablog several times (snippy template) [#495](https://github.com/BU-ISCIII/buisciii-tools/pull/495)
- Added Nextclade, variant calling and stats extraction scripts into the IRMA template [#499](https://github.com/BU-ISCIII/buisciii-tools/pull/499).
- Added flu_type to summary_stats (IRMA template) [#501](https://github.com/BU-ISCIII/buisciii-tools/pull/501).
- Fixed errors in IRMA template and fixed errors in irma2vcf script [#500](https://github.com/BU-ISCIII/buisciii-tools/pull/500)
- Modified artic bed version in lablog_viralrecon for SARS-CoV-2 analysis [#505](https://github.com/BU-ISCIII/buisciii-tools/pull/505)


### Modules

#### Added enhancements

- Implemented multi-attachment support in Bioinfo-doc email sending workflow [#488](https://github.com/BU-ISCIII/buisciii-tools/pull/488)
- Added kmerfinder to snippy template [#498](https://github.com/BU-ISCIII/buisciii-tools/pull/498)

#### Fixes

#### Changed

- Expanded the maximum width of email body to 1000px for better desktop display [#488](https://github.com/BU-ISCIII/buisciii-tools/pull/488)
- Corrected the logo URL to use a direct raw link for proper rendering in email clients [#488](https://github.com/BU-ISCIII/buisciii-tools/pull/488)

#### Removed

### Requirements

## [2.2.7] - 2025-04-03 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.7

### Credits

- [Jaime Ozáez](https://github.com/jaimeozaez)
- [Alejandro Bernabeu](https://github.com/Aberdur)
- [Sergio Olmos](https://github.com/OPSergio)
- [Victor Lopez](https://github.com/victor5lm)
- [Sarai Varona](https://github.com/svarona)
- [Pablo Mata](https://github.com/Shettland)
- [Sara Monzon](https://github.com/saramonzon)

### Template fixes and updates

- Fixed bug in 08_create_quality_control_summary.sh (viralrecon template) [#447](https://github.com/BU-ISCIII/buisciii-tools/pull/447).
- Updated `services.json` file in order to properly delete folders and files when running clean module [#451](https://github.com/BU-ISCIII/buisciii-tools/pull/451).
- Add assets for Updating Lineage-Defining Mutations from outbreak-info [#452](https://github.com/BU-ISCIII/buisciii-tools/pull/452)
- Fix get_percentage_LDM.py to Use Versioned CSV File[#453](https://github.com/BU-ISCIII/buisciii-tools/pull/453).
- Moved `lablog_bam2fq.sh` to `RAW/`** to centralize BAM-to-FASTQ processing [#455](https://github.com/BU-ISCIII/buisciii-tools/pull/455)
- Updated `_01_bam2fq.sh` to correctly detect all BAM files in `RAW/` [#455](https://github.com/BU-ISCIII/buisciii-tools/pull/455)
- Refactored `_02_pgzip.sh` to compress `.fastq` files and remove uncompressed versions [#455](https://github.com/BU-ISCIII/buisciii-tools/pull/455)
- Created `_03_symlink.sh` to manage symbolic links in `ANALYSIS/00-reads/`, preventing broken links [#455](https://github.com/BU-ISCIII/buisciii-tools/pull/455)
- Removed single quotes from sftp_copy in configuration.json [#458](https://github.com/BU-ISCIII/buisciii-tools/pull/458)
- Fixed and enhanced some issues for lablog_viralrecon [#461](https://github.com/BU-ISCIII/buisciii-tools/pull/461)
- Update sftp_users.json with new user for e.abascal [#464](https://github.com/BU-ISCIII/buisciii-tools/pull/464)
- Update sample handling in get_percentage_LDM [#465](https://github.com/BU-ISCIII/buisciii-tools/pull/465)
- Added _02_filter_results.sh script to pikavirus template [#466](https://github.com/BU-ISCIII/buisciii-tools/pull/466)
- Changed short_obx for middle_idx in 02-clean.sh [#468](https://github.com/BU-ISCIII/buisciii-tools/pull/468)
- Update exometrio lablog to Handle Fourth Individual [#469](https://github.com/BU-ISCIII/buisciii-tools/pull/469)
- Update get_percentage_LDM.py to read sample column as string [#470](https://github.com/BU-ISCIII/buisciii-tools/pull/470)
- Updated ivar varsion in viralrecon template to makwe it work with IonTorrent data [#471](https://github.com/BU-ISCIII/buisciii-tools/pull/471)
- Update get_percentage_LDM.py to Handle Cases with No Lineage Found in outbreak.info CSV [#473](https://github.com/BU-ISCIII/buisciii-tools/pull/473)
- Added autorun.sh script for automation of multiple sbatch running in viralrecon pipeline [#474](https://github.com/BU-ISCIII/buisciii-tools/pull/474)
- Modified clean.py in order to properly delete exact matching-name folders and files [#476](https://github.com/BU-ISCIII/buisciii-tools/pull/476)
- Added information on the period of permanence of the results in the sftp folder in email template [#477](https://github.com/BU-ISCIII/buisciii-tools/pull/477)
- Updated snippy template, now using a modified version of snippy with different low coverage masking[#489](https://github.com/BU-ISCIII/buisciii-tools/pull/489)

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements


## [2.2.6] - 2025-02-25 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.6

### Credits

- [Alejandro Bernabeu](https://github.com/Aberdur)
- [Sara Monzón](https://github.com/saramonzon)
- [Victor Lopez](https://github.com/victor5lm)
- [Jaime Ozáez](https://github.com/jaimeozaez)

### Template fixes and updates

- User added to sftp_user.json [#404] (https://github.com/BU-ISCIII/buisciii-tools/pull/404).
- Fix archived path [#405](https://github.com/BU-ISCIII/buisciii-tools/pull/405)
- Updated characterization/03-amrfinderplus lablog with summary generator [#406](https://github.com/BU-ISCIII/buisciii-tools/pull/406)
- Updated lablog_viralrecon to replace conda by micromamba, and updated the output message from remove_columns_mapping_table.sh [#409](https://github.com/BU-ISCIII/buisciii-tools/pull/409)
- Created lablog_bam2fq in viralrecon's template [#409](https://github.com/BU-ISCIII/buisciii-tools/pull/409)
- Replaced bu_isciii by buisciii where necessary, and bu_isciii by buisciii-tools in __init__.py [#411](https://github.com/BU-ISCIII/buisciii-tools/pull/411)
- Added versions for all dependencies in requirements.txt [#411](https://github.com/BU-ISCIII/buisciii-tools/pull/411)
- Implemented a non-interactive mode for running lablog_viralrecon [#410](https://github.com/BU-ISCIII/buisciii-tools/pull/410)
- Fixes in several service templates [#414](https://github.com/BU-ISCIII/buisciii-tools/pull/414)
- Modified path for temporal files in irma_config.sh [#414](https://github.com/BU-ISCIII/buisciii-tools/pull/421)
- Modified field (cut) where extracted flu type information in lablog_irma_results [#414](https://github.com/BU-ISCIII/buisciii-tools/pull/421)
- Implemented QC scripts into viralrecon template [#422](https://github.com/BU-ISCIII/buisciii-tools/pull/422)
- Fixed minor mistakes in chewBBACA's template [#425](https://github.com/BU-ISCIII/buisciii-tools/pull/425).
- Fixed some issues in outbreak services [#428](https://github.com/BU-ISCIII/buisciii-tools/pull/428)
- Add micromamba activation comment to viralrecon template lablog and add total_N_count to sgene_metrics script[#432](https://github.com/BU-ISCIII/buisciii-tools/pull/432)
- Added last_folder field to plasmidid_assembly service in services.json [#434](https://github.com/BU-ISCIII/buisciii-tools/pull/434)
- Fixed bioinfo-doc crashing after resuming [#435](https://github.com/BU-ISCIII/buisciii-tools/pull/435)
- Fixed create_summary_report.sh to latest /data/ucct/bi/ layout [#436](https://github.com/BU-ISCIII/buisciii-tools/pull/436)
- Changed taxprofiler lablog to skip kaiju, centrifuge and metaphlan [#439](https://github.com/BU-ISCIII/buisciii-tools/pull/439)
- Conditional Copy of QC Scripts in lablog_viralrecon and Fixes in 99-stats (SNIPPY) & parse_ariba.py [#449](https://github.com/BU-ISCIII/buisciii-tools/pull/449)
- Add generate_summary_outbreak.py to Complete Template with Outbreak Analysis Results [#450](https://github.com/BU-ISCIII/buisciii-tools/pull/450)
- Update remove_columns_mapping_table_RELECOV.sh in lablog_viralrecon [#496](https://github.com/BU-ISCIII/buisciii-tools/pull/496)

### Modules

#### Added enhancements

#### Fixes

- Fixed drylab_api.py to show a more descriptive message when the resolution ID does not exist [#437](https://github.com/BU-ISCIII/buisciii-tools/pull/437).

#### Changed

#### Removed

### Requirements

## [2.2.5] - 2025-01-09 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.5

### Credits

- [Victor Lopez](https://github.com/victor5lm)

### Template fixes and updates

- Changed mag.md by taxprofiler.md in assets/reports [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Modified irma_output.md to include only taxprofiler [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Updated services.json with taxprofiler [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Created a lablog file for chewbbaca/REFERENCES [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Updated lablog_irma and renamed ANALYSIS01 folders [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Updated IRMA template and its files to include RSV [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Updated chewbbaca results' lablog to include cgMLST_MSA.fasta [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Updated exometrio and wgstrio results lablogs not to include exomiser's html [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Created plasmidid's results lablog [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Updated mtbseq's lablog to remove unnecessary single quotes [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Fixed snippy's lablog to be better explained and updated its results' lablog [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
- Updated version in pyproject.toml and __main__.py [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).
### Modules

#### Added enhancements

#### Fixes

#### Changed

- Replaced setup.py by pyproject.toml [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).

#### Removed

- Removed MAG template and replaced it with taxprofiler [#396](https://github.com/BU-ISCIII/buisciii-tools/pull/396).

### Requirements

## [2.2.4] - 2024-12-27 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.4

### Credits

- [Victor Lopez](https://github.com/victor5lm)

### Template fixes and updates

- Replaced /data/bi/ by /data/ucct/bi where necessary [#385](https://github.com/BU-ISCIII/buisciii-tools/pull/385).
- Removed middle_obx from config files [#385](https://github.com/BU-ISCIII/buisciii-tools/pull/385).

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.3] - 2024-12-23 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.3

### Credits

Code contributions to the new version:

- [Victor Lopez](https://github.com/victor5lm)
- [Sarai Varona](https://github.com/svarona)

### Template fixes and updates

- Updated sftp_user.json, added the locus-tag option for the PROKKA process in the bacass config file and changed new_service.py so that integrity is checked only for the samples of interest [#363](https://github.com/BU-ISCIII/buisciii-tools/pull/363).
- Replaced /data/bi/ by /data/ucct/bi/ [#380](https://github.com/BU-ISCIII/buisciii-tools/pull/380).
- Updated bacass version in all pertinent files [#380](https://github.com/BU-ISCIII/buisciii-tools/pull/380).
- Updated read length variable definition when creating the mapping_illumina.tab file [#380](https://github.com/BU-ISCIII/buisciii-tools/pull/380).
- Updated create_irma_stats.sh to include %mapped_reads [#380](https://github.com/BU-ISCIII/buisciii-tools/pull/380).
- Changed "Buenas" by "Estimado/a" in email.j2 [#380](https://github.com/BU-ISCIII/buisciii-tools/pull/380).

### Modules

#### Added enhancements

#### Fixes

- Fixed new-service to correctly handle when there are no samples in service [#372](https://github.com/BU-ISCIII/buisciii-tools/pull/372). Fixes issue [#371](https://github.com/BU-ISCIII/buisciii-tools/issues/371)

#### Changed

#### Removed

### Requirements

## [2.X.Xhot] - 2024-0X-0X : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.X.2

### Credits

### Template fixes and updates

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.2] - 2024-10-28 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.2

### Credits

Code contributions to the new version:

- [Pablo Mata](https://github.com/Shettland)
- [Victor Lopez](https://github.com/victor5lm)

### Template fixes and updates

- Updated the fix-permissions module in __main__.py [#356](https://github.com/BU-ISCIII/buisciii-tools/pull/356).
- Fixed the singularity cache directory in taxprofiler.config [#356](https://github.com/BU-ISCIII/buisciii-tools/pull/356).
- Updated sftp_user.json [#356](https://github.com/BU-ISCIII/buisciii-tools/pull/356).
- Fixed viralrecon's lablog and the remove_columns_mapping_table.sh auxiliary script [#356](https://github.com/BU-ISCIII/buisciii-tools/pull/356).
- Updated the singularity image in the mtbseq templates [#356](https://github.com/BU-ISCIII/buisciii-tools/pull/356).
- Fixed a bug in bioinfo_doc.py [#356](https://github.com/BU-ISCIII/buisciii-tools/pull/356).
- Updated new_service.py to check FASTQ integrity via md5sum [#356](https://github.com/BU-ISCIII/buisciii-tools/pull/356).

### Modules

#### Added enhancements

- Included a new github action to automatically publish releases to pypi [#351](https://github.com/BU-ISCIII/buisciii-tools/pull/351)

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.X.Xhot] - 2024-0X-0X : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.X.1

### Credits

Code contributions to the hotfix:

### Template fixes and updates

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.1] - 2024-10-01 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.1

### Credits

Code contributions to the new version:

- [Daniel Valle](https://github.com/Daniel-VM)
- [Sarai Varona](https://github.com/svarona)
- [Victor Lopez](https://github.com/victor5lm)
- [Sergio Olmos](https://github.com/OPSergio)

### Template fixes and updates

- Fixed path to blast database and update Emmtyper params [#339](https://github.com/BU-ISCIII/buisciii-tools/pull/339)
- Updated sarek version (v3.4.4) in ExomeEB-ExomeTrio-WGSTrio templates [#341] (https://github.com/BU-ISCIII/buisciii-tools/pull/341)
- Fixed IRMAs config for amended consensus [#325](https://github.com/BU-ISCIII/buisciii-tools/pull/325).
- Improved excel_generator.py and bioinfo_doc.py email creation function, and updated sftp_user.json, setup.py, main.py and some lablogs [#344](https://github.com/BU-ISCIII/buisciii-tools/pull/344).

### Modules

#### Added enhancements

#### Fixes

#### Changed

#### Removed

### Requirements

## [2.2.0] - 2024-09-12 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.0

### Credits

Code contributions to the new version:
- [Pablo Mata](https://github.com/Shettland)
- [Jaime Ozáez](https://github.com/jaimeozaez)
- [Sara Monzón](https://github.com/saramonzon)
- [Sarai Varona](https://github.com/svarona)
- [Daniel Valle](https://github.com/Daniel-VM)
- [Víctor López](https://github.com/victor5lm)
- [Juan Ledesma](https://github.com/juanledesma78)

### Template fixes and updates

- Updated documentation and results markdown for viralrecon, pikavirus and MAG [#247](https://github.com/BU-ISCIII/buisciii-tools/pull/247)
- Added documentation and results markdown for RNAseq [#248](https://github.com/BU-ISCIII/buisciii-tools/pull/248)
- Added documentation both output and results for plasmidID[#258](https://github.com/BU-ISCIII/buisciii-tools/pull/258)
- Added markdown of assembly analysis procedure [#244](https://github.com/BU-ISCIII/buisciii-tools/pull/244)
- Added output and results markdowns for ExomeEB, ExomeTrio and WGStrio [#249](https://github.com/BU-ISCIII/buisciii-tools/pull/249)
- Added markdown of assembly results folder [#250](https://github.com/BU-ISCIII/buisciii-tools/pull/250)
- Updated lablog results filenames where necessary (IRMA, seekndestroy, viralrecon and genomeev) [#253](https://github.com/BU-ISCIII/buisciii-tools/pull/253)
- Added output and results markdowns for cgMLST/wgMLST [#255](https://github.com/BU-ISCIII/buisciii-tools/pull/255)
- Added markdown for IRMA [#256](https://github.com/BU-ISCIII/buisciii-tools/pull/256)
- Included RESULTS/lablog for exomeeb, exometrio and wgstrio templates and updated files to clean  [#260](https://github.com/BU-ISCIII/buisciii-tools/pull/260)
- Changed scratch copy queue to middle_obx
- Included missing folders in wgstrio template
- Changed exomiser-html-description to png format and fixed location of irma-sarek markdowns [#261](https://github.com/BU-ISCIII/buisciii-tools/pull/261)
- Updated configuration.json so that either idx or obx is used in case one of these queues is full [#263](https://github.com/BU-ISCIII/buisciii-tools/pull/263)
- Updated lablog_viralrecon script for the automation of the setup of viralrecon services. [#264](https://github.com/BU-ISCIII/buisciii-tools/pull/264)
- Included MULTIQC v.1.19 in viralrecon.config to fix error with string and numeric samples [#267](https://github.com/BU-ISCIII/buisciii-tools/pull/267)
- Updated MTBSeq template to fit bacass pipeline. [#268](https://github.com/BU-ISCIII/buisciii-tools/pull/268)
- IRMA template modified in order to avoid average overload.
- Added "01" to results folder creation in assembly template.
- Some prompt answers limited to 1 character in lablog_viralrecon.
- Created lablog_mtbseq_results. [#270](https://github.com/BU-ISCIII/buisciii-tools/pull/270)
- PR #271. Closes [#235](https://github.com/BU-ISCIII/buisciii-tools/issues/235), [#228](https://github.com/BU-ISCIII/buisciii-tools/issues/228) and [#196](https://github.com/BU-ISCIII/buisciii-tools/issues/196)
- Included annotated tab description in exome-trios markdowns [#273](https://github.com/BU-ISCIII/buisciii-tools/pull/273)
- Installed all necessary singularity images and modified all templates so that, instead of using conda environments or loaded modules, the corresponding singularity images are used [#272](https://github.com/BU-ISCIII/buisciii-tools/pull/272)
- Updated sarek version in exomeeb, exometrio and wgstrio templates [#277](https://github.com/BU-ISCIII/buisciii-tools/pull/277)
- Extension file of all_samples_virus_table_filtered (from csv to tsv) in lablog_viralrecon_results changed [#278](https://github.com/BU-ISCIII/buisciii-tools/pull/278)
- Fixed singularity-images path when updating pangolin database in lablog_viralrecon. Added line break after prompted input. [#282](https://github.com/BU-ISCIII/buisciii-tools/pull/282)
- Updated characterization and snippy templates to fit bacass pipeline. Corrected path in 05-iqtree in snippy template. [#283](https://github.com/BU-ISCIII/buisciii-tools/pull/283)
- Included multiqc_report.html in RESULTS folder in every service, where necessary [#265] (https://github.com/BU-ISCIII/buisciii-tools/pull/265)
- Added MAG tempalte and removed MAG from other templates [#288](https://github.com/BU-ISCIII/buisciii-tools/pull/288)
- Added amrfinderplus to characterization template. [#289] (https://github.com/BU-ISCIII/buisciii-tools/pull/289)
- Updated all files so that paths referring to /pipelines/ are updated according to the new structure [#287](https://github.com/BU-ISCIII/buisciii-tools/pull/287)
- Updated assembly, ariba, snippy, amrfinderplus and iqtree templates, removed genomeev and mtbseq_assembly templates and updated services.json [#295](https://github.com/BU-ISCIII/buisciii-tools/pull/295)
- Changed viralrecon's lablog so that references are available within refgenie [#296](https://github.com/BU-ISCIII/buisciii-tools/pull/296)
- Updated services.json, mtbseq's lablog, viralrecon's lablog and assembly's config file [#299](https://github.com/BU-ISCIII/buisciii-tools/pull/299)
- Added lablog to automate gene characterization with emmtyper, including unzipping assemblies. [#300](https://github.com/BU-ISCIII/buisciii-tools/pull/300)
- Fixed 99-stats (MAG) template. [#301](https://github.com/BU-ISCIII/buisciii-tools/pull/301)
- Created a python script to process IRMA's results and create a standard vcf file against reference. [#304](https://github.com/BU-ISCIII/buisciii-tools/pull/304)
- Fixed IRMA's lablog so that the sequences of the samples are not displayed several times neither in the .txt files of each influenza type nor in all_samples_completo.txt [#305](https://github.com/BU-ISCIII/buisciii-tools/pull/305)
- Modified bioinfo_doc.py so that new lines in the delivery message are applied in the email [#307](https://github.com/BU-ISCIII/buisciii-tools/pull/307)
- Added several improvements in lablog_viralrecon (created log files, modified check_references function behaviour, enabled config files regeneration) [#306](https://github.com/BU-ISCIII/buisciii-tools/pull/306)
- Fixed bug when lablog_viralrecon tries to download references that don't belong to any family. [#310](https://github.com/BU-ISCIII/buisciii-tools/pull/310)
- Added mvmoneo to SFTP users. [#317](https://github.com/BU-ISCIII/buisciii-tools/pull/317)
- Added scripts for time series RNAseq and updated differential expression code for differentially expressed transcripts [#316](https://github.com/BU-ISCIII/buisciii-tools/pull/316).
- Added bbaladron to SFTP users [#316](https://github.com/BU-ISCIII/buisciii-tools/pull/316).
- Added new template for comprehensive taxonomy profiling using the nf-core/taxprofiler pipeline [#320](https://github.com/BU-ISCIII/buisciii-tools/pull/320).
- Added full execution support for the MAG template [#321](https://github.com/BU-ISCIII/buisciii-tools/pull/321).
- Added labels to services.json and updated bioinfo_doc.py and jinja_template_delivery.j2 so that software versions data is displayed in the delivery pdf [#330](https://github.com/BU-ISCIII/buisciii-tools/pull/330).
- Updated several templates (singularity images, outdated paths, improvements, etc) [#331](https://github.com/BU-ISCIII/buisciii-tools/pull/331)
- Added permissions fixing after running scratch_copy, as well as a new fix-permissions module in the tools [#332](https://github.com/BU-ISCIII/buisciii-tools/pull/332).
- Updated MAG lablogs and utils.py [#334](https://github.com/BU-ISCIII/buisciii-tools/pull/334).
- Updated some files (setup.py, __main__.py, README, etc) for the 2.2.0 release [#335](https://github.com/BU-ISCIII/buisciii-tools/pull/335).

### Modules

#### Added enhancements

- PR [#274](https://github.com/BU-ISCIII/buisciii-tools/pull/274): added `--dev` option, configuration dev and test folder structure.
- PR [#276](https://github.com/BU-ISCIII/buisciii-tools/pull/276): wkhtmlpdf does not need absolute path to executable. Added better error handling when executable does not exists.
- PR [#288](https://github.com/BU-ISCIII/buisciii-tools/pull/288) Allowed to handle more than one service at a time, related to issue [#217](https://github.com/BU-ISCIII/buisciii-tools/issues/217)

#### Fixes

- Fixed archive module. Updated correct header for scout tsv [#258](https://github.com/BU-ISCIII/buisciii-tools/pull/258).
- Fixed clean module. Corrected purge_files function. Renaming stage moved from clean to rename_nocopy option. Updated services.json file with correct paths for some services. [#280](https://github.com/BU-ISCIII/buisciii-tools/pull/280)
- Fixed autoclean-sftp function. [#281](https://github.com/BU-ISCIII/buisciii-tools/pull/281)
- Fixed bioinfo_doc.py. Modified it so that this module creates a .pdf file including new-line characters, without merging lines into one single line [#259](https://github.com/BU-ISCIII/buisciii-tools/pull/259).
- PR [#288](https://github.com/BU-ISCIII/buisciii-tools/pull/288) Fixed updating service's state to in_progress multiple times, related with issue [#285](https://github.com/BU-ISCIII/buisciii-tools/issues/285)
- Review and update of services.json for files and folders cleaning [#318](https://github.com/BU-ISCIII/buisciii-tools/pull/318).

#### Changed

- Forcing python lint to success if no .py files are in PR [#279](https://github.com/BU-ISCIII/buisciii-tools/pull/279)

#### Removed

### Requirements

## [2.1.0] - 2024-04-19 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.1.0

### Credits

Code contributions to the new version:
- [Sarai Varona](https://github.com/svarona)
- [Pablo Mata](https://github.com/Shettland)
- [Daniel Valle](https://github.com/Daniel-VM)

### Template fixes and updates

- Added blast_nt template to services.json [#208](https://github.com/BU-ISCIII/buisciii-tools/pull/208)
- Included new user to sftp_user.json
- Included a missing sed inside IRMA's 04-irma/lablog [#213](https://github.com/BU-ISCIII/buisciii-tools/pull/213)
- Changed singularity mount options in Viralrecon template to fix errors with Nextflow v23.10.0
- excel_generator.py reverted to last state, now lineage tables are merged when argument -l is given
- Adapted viralrecon_results lablog to new excel_generator.py argument
- IRMA/RESULTS now creates a summary of the different types of flu found in irma_stats.txt
- Updated IRMA to v1.1.4 date 02-2024 and reduced threads to 16
- IRMA 04-irma/lablog now creates B and C dirs only if those flu-types are present
- Fixed characterization template [#220](https://github.com/BU-ISCIII/buisciii-tools/pull/220)
- Created Chewbbaca template [#230](https://github.com/BU-ISCIII/buisciii-tools/pull/230)

### Modules

#### Added enhancements

- [#207](https://github.com/BU-ISCIII/buisciii-tools/pull/207) - Bioinfo-doc updates: email password can be given in buisciii_config.yml and delivery notes in a text file

#### Fixes

- Added missing url for service assembly_annotation in module list
- Autoclean-sftp refined folder name parsing with regex label adjustment
- Autoclean_sftp does not crash anymore. New argument from 'utils.prompt_yn_question()' in v2.0.0 was missing: 'dflt'
- Bioinfo-doc now sends email correctly to multiple CCs

#### Changed

#### Removed

- Removed empty strings from services.json

### Requirements

## [2.0.0] - 2024-03-01 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.0.0

### Credits

Code contributions to the release:

- [Sara Monzón](https://github.com/saramonzon)
- [Sarai Varona](https://github.com/svarona)
- [Pablo Mata](https://github.com/Shettland)
- [Guillermo Gorines](https://github.com/GuilleGorines)


### Template fixes and updates

- Added templates:
    - freebayes


### Modules

#### Added enhancements

- Added credential parameters: --api_user, --api_password and --cred_file
- Make modules to create folder's paths automatically from DB
- Added finish module
- Added json files: sftp_user.json
- Added delivery jinja templates
- Added IRMA template to services.json
- Scratch module now executes rsync using SLURM's srun

#### Fixes

#### Changed

- Fixed API requests to fit in the new database format
- Updated README

#### Removed

### Requirements

- Added PyYAML


## [1.0.1] - 2024-02-01 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/1.0.1

### Credits

Code contributions to the hotfix:

- [Pablo Mata](https://github.com/Shettland)
- [Jaime Ozaez](https://github.com/jaimeozaez)
- [Sara Monzón](https://github.com/saramonzon)
- [Sarai Varona](https://github.com/svarona)
- [Daniel Valle](https://github.com/Daniel-VM)

### Template fixes and updates

- Added new line in `buisciii_tools/buisciii/templates/viralrecon/ANALYSIS/lablog_viralrecon`, in order to automatically rename `ANALYSIS0X_MAG` directory with the current date.
- Introduced handling of flu-C in `buisciii_tools/buisciii/templates/IRMA/ANALYSIS/ANALYSIS01_FLU_IRMA/04-irma/` `lablog` and `create_irma_stats.sh`
- Small changes to `buisciii_tools/buisciii/templates/viralrecon/RESULTS/viralrecon_results` for blast and new excel_generator.py
- Introduced better error handling in excel_generator.py. Now it can also be used for single files
- Brought back `PASS_ONLY` to exometrio's `exomiser_configfile.yml`
- [#187](https://github.com/BU-ISCIII/buisciii-tools/pull/187) - Added new template for bacterial assembly. Allowing for short, long and hybrid assembly.
- [#190](https://github.com/BU-ISCIII/buisciii-tools/pull/190) - renamed some variables in create-summary_report from viralrecon template as their name was misleading and fixed a small typo in regex finding in excel_generator.py
- [#192](https://github.com/BU-ISCIII/buisciii-tools/pull/192) - Small changes in excel_generator.py to automatically merge pangolin/nextclade tables when more than 1 reference is found

### Modules

#### Added enhancements
- Added CHANGELOG
- Added template for Pull Request
- Added Contributing guidelines
- Added github action to sync branches

#### Fixes

#### Changed

#### Removed


### Requirements


## [1.0.0] - 2024-01-08 : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/1.0.0

### Credits

Code contributions to the inital release:

- [Sara Monzón](https://github.com/saramonzon)
- [Saria Varona](https://github.com/svarona)
- [Guillermo Gorines](https://github.com/GuilleGorines)
- [Pablo Mata](https://github.com/Shettland)
- [Luis Chapado](https://github.com/luissian)
- [Erika Kvalem](https://github.com/ErikaKvalem)
- [Alberto Lema](https://github.com/Alema91)
- [Daniel Valle](https://github.com/Daniel-VM)
- [Fernando Gomez](https://github.com/FGomez-Aldecoa)

