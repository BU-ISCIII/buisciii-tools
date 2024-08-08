# bu-isciii tools Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.Xdev] - 2024-0X-XX : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.2.X

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
- Fixed IRMA's lablog so that the sequences of the samples are not displayed several times neither in the .txt files of each influenza type nor in all_samples_completo.txt [#305](https://github.com/BU-ISCIII/buisciii-tools/pull/305)
- Modified bioinfo_doc.py so that new lines in the delivery message are applied in the email [#307](https://github.com/BU-ISCIII/buisciii-tools/pull/307)
- Added several improvements in lablog_viralrecon (created log files, modified check_references function behaviour, enabled config files regeneration) [#306](https://github.com/BU-ISCIII/buisciii-tools/pull/306)

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

#### Changed

- Forcing python lint to success if no .py files are in PR [#279](https://github.com/BU-ISCIII/buisciii-tools/pull/279)

#### Removed

### Requirements

## [2.X.1hot] - 2024-0X-0X : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.X.1

### Credits

Code contributions to the hotfix:

### Template fixes and updates

### Modules

#### Added enhancements

#### Fixes

#### Changed

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

- Added new line in `buisciii_tools/bu_isciii/templates/viralrecon/ANALYSIS/lablog_viralrecon`, in order to automatically rename `ANALYSIS0X_MAG` directory with the current date. 
- Introduced handling of flu-C in `buisciii_tools/bu_isciii/templates/IRMA/ANALYSIS/ANALYSIS01_FLU_IRMA/04-irma/` `lablog` and `create_irma_stats.sh`
- Small changes to `buisciii_tools/bu_isciii/templates/viralrecon/RESULTS/viralrecon_results` for blast and new excel_generator.py
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

