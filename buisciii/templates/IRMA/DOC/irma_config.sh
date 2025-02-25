### PROC config ###
SINGLE_LOCAL_PROC=8	# local maximum processes
DOUBLE_LOCAL_PROC=4	# local maximum processes (double this number)
MATCH_PROC=8		# grid maximum processes for the MATCH
SORT_PROC=8		# currently not used
ALIGN_PROC=8		# grid maximum processes for the rough align
ASSEM_PROC=8		# grid maximum processes for assembly
TMP=/data/ucct/bi/tmp # use this path for temporal files instead of /tmp

### AMENDED CONSENSUS ###
MIN_AMBIG=0.75          # Sets ambiguities to off
MIN_CONS_SUPPORT=9      # Mask low coverage <= 9 (10 is ok)
