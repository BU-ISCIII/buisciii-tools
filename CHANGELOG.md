# bu-isciii tools Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0dev] - 2024-0X-0X : https://github.com/BU-ISCIII/buisciii-tools/releases/tag/2.1.X

### Credits

Code contributions to the hotfix:

### Template fixes and updates

### Modules

#### Added enhancements

- [#207](https://github.com/BU-ISCIII/buisciii-tools/pull/207) - Bioinfo-doc updates: email password can be given in buisciii_config.yml and delivery notes in a text file

#### Fixes

#### Changed

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

