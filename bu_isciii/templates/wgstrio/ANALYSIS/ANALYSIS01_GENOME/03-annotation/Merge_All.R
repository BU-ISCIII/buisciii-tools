
# Cargar la tabla de datos
plugin <- read.table("dbNSFP_ENSG_plugin_hg19.txt", header = TRUE, sep = "\t", quote = "")

# Fusionar las cuatro columnas en una nueva columna llamada "ID"
plugin$ID <- paste(plugin$`chr`, plugin$`hg19_pos`, plugin$ref, plugin$alt, sep = "_")

#Borrar las columnas innecesarias
plugin <-plugin[,-c(1,2,3,4)]

# Guardar la tabla resultante
write.table(plugin, "dbNSFP_ENSG_plugin_Columns.txt", sep = "\t", quote = FALSE, row.names = FALSE)

#cargamos tabla vep_annot_head
vep <- read.table("./vep/vep_annot_head.txt",header=T, sep = "\t", quote = "")

#pegamos las tablas usando de referencia la columnas Uploadaded variation
vep_plugin <- merge(vep,plugin,by="ID",all.x=T,all.y=F)

# guardamos la tabla resultante
write.table(vep_plugin,file="./vep/vep_plugin.txt",sep="\t", na="-", row.names=F,quote=FALSE)

# cargamos tabla dbNSFP y vep_plugin
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

