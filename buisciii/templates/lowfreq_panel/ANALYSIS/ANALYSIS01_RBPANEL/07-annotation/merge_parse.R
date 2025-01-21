## Script en R que va a hacer un merge del fichero vcf que se obtiene de gatk y las anotaciones que se obtienen con kggseq.
args = commandArgs(trailingOnly=TRUE)
sample <- args[1]

variants_phased <- read.table(paste(sample, "/", sample,"_header.table",sep=""),header=T,sep="\t")
variants_annotated <- read.csv(paste(sample, "/",sample,"_annot.txt.flt.txt",sep=""),header=T,sep="\t")
variants_annotated$Chromosome <- paste("chr",variants_annotated$Chromosome,sep="")

variants_phased$merged <- paste(variants_phased$CHROM,variants_phased$POS,sep="_")
variants_annotated$merged <- paste(variants_annotated$Chromosome,variants_annotated$StartPositionHg38,sep="_")

table_comp <- merge(variants_phased,variants_annotated,by="merged",all.x=F,all.y=T)
write.table(table_comp,file=paste(sample,"_all_annotated.tab",sep=""),sep="\t",row.names=F)

