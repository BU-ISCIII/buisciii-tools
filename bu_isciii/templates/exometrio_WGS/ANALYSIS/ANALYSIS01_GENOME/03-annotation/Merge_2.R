# cargamos tabla dbNSFP y vep_plugin
vep_plugin <- read.table("./vep/vep_plugin.txt",header=T, sep = "\t", quote = "")
dbNSFP <- read.table("dbNSFP_ENSG_gene_GRCh37.txt",header=T, sep = "\t", quote = "")

#pegamos dbNSFP con vep usando de referencia la columna gene
vep_dbNSFP <- merge(vep_plugin,dbNSFP,by="Gene",all.x=T,all.y=F)

# guardamos la tabla resultante
write.table(vep_dbNSFP,file="./vep/vep_dbNSFP.txt",sep="\t", na="-", row.names=F,quote=FALSE)

# cargamos la tabla vep/variants.table
variants <- read.table("./vep/variants.table",header=T, sep = "\t", quote = "")

# pegamos vep_dbNSFP junto con variants
vep_dbNSFP_variants <- merge(variants,vep_dbNSFP,by="ID",all.x=F,all.y=F)

# guardamos la tabla resultante
write.table(vep_dbNSFP_variants, file="variants_annot_all.tab", sep="\t", na="-", row.names=F, quote=FALSE)
