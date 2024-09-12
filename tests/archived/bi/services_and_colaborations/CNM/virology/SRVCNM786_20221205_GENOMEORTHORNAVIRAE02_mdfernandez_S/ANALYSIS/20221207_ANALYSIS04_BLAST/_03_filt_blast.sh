awk 'BEGIN{OFS="\t";FS="\t"}{print $0,$5/$15,$5/$14}' PTA201.blast.txt | awk 'BEGIN{OFS="\t";FS="\t"} $15 > 200 && $17 > 0.7 && $1 !~ /phage/ {print $0}' > PTA201.blast.filt.txt
awk 'BEGIN{OFS="\t";FS="\t"}{print $0,$5/$15,$5/$14}' PTA203.blast.txt | awk 'BEGIN{OFS="\t";FS="\t"} $15 > 200 && $17 > 0.7 && $1 !~ /phage/ {print $0}' > PTA203.blast.filt.txt
awk 'BEGIN{OFS="\t";FS="\t"}{print $0,$5/$15,$5/$14}' PTA205.blast.txt | awk 'BEGIN{OFS="\t";FS="\t"} $15 > 200 && $17 > 0.7 && $1 !~ /phage/ {print $0}' > PTA205.blast.filt.txt
awk 'BEGIN{OFS="\t";FS="\t"}{print $0,$5/$15,$5/$14}' PTA200.blast.txt | awk 'BEGIN{OFS="\t";FS="\t"} $15 > 200 && $17 > 0.7 && $1 !~ /phage/ {print $0}' > PTA200.blast.filt.txt
awk 'BEGIN{OFS="\t";FS="\t"}{print $0,$5/$15,$5/$14}' PTA202.blast.txt | awk 'BEGIN{OFS="\t";FS="\t"} $15 > 200 && $17 > 0.7 && $1 !~ /phage/ {print $0}' > PTA202.blast.filt.txt
awk 'BEGIN{OFS="\t";FS="\t"}{print $0,$5/$15,$5/$14}' PTA204.blast.txt | awk 'BEGIN{OFS="\t";FS="\t"} $15 > 200 && $17 > 0.7 && $1 !~ /phage/ {print $0}' > PTA204.blast.filt.txt
awk 'BEGIN{OFS="\t";FS="\t"}{print $0,$5/$15,$5/$14}' PTA206.blast.txt | awk 'BEGIN{OFS="\t";FS="\t"} $15 > 200 && $17 > 0.7 && $1 !~ /phage/ {print $0}' > PTA206.blast.filt.txt
