### PROC config ###
SINGLE_LOCAL_PROC=4	# local maximum processes
DOUBLE_LOCAL_PROC=2	# local maximum processes (double this number)
MATCH_PROC=8		# grid maximum processes for the MATCH
SORT_PROC=8		    # currently not used
ALIGN_PROC=8		# grid maximum processes for the rough align
ASSEM_PROC=8		# grid maximum processes for assembly
TMP=/data/ucct/bi/tmp # use this path for temporal files instead of /tmp

### RESIDUAL AND SECONDARY ASSEMBLIES ###
RESIDUAL_ASSEMBLY_FACTOR=400            # integer Assembles secondary data if observed factor is less than integer RESIDUAL_ASSEMBLY_FACTOR. Leave 0 for off.
MIN_RP_RESIDUAL=150                     #≥ 1 Minimum number of read patterns to continue to attempt residual assembly per gene segment.
MIN_RC_RESIDUAL=150                     #≥ 1 Minimum read count to continue to attempt residual assembly per gene segment.
DO_SECONDARY=1                          #0, 1 off, on Given a successful residual assembly, create a patchwork consensus and run a secondary assembly.

### AMENDED CONSENSUS ###
MIN_AMBIG=0.75          # Sets ambiguities to off
MIN_CONS_SUPPORT=9      # Mask low coverage <= 9 (10 is ok)
