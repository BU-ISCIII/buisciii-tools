# Cargar la tabla de datos
plugin <- read.table("dbNSFP_ENSG_plugin.txt", header = TRUE, sep = "\t", quote = "")

# Fusionar las cuatro columnas en una nueva columna llamada "Uploaded_variation"
plugin$Uploaded_variation <- paste(plugin$`chr`, plugin$`pos.1.based.`, plugin$ref, plugin$alt, sep = "_")

#Borrar las columnas innecesarias
plugin <-plugin[,-c(1,2,3,4)]

# Guardar la tabla resultante
write.table(plugin, "dbNSFP_ENSG_plugin_Columns.txt", sep = "\t", quote = FALSE, row.names = FALSE)

#cargamos tabla vep_annot_head
vep <- read.table("./vep/vep_annot_head.txt",header=T, sep = "\t", quote = "")

#pegamos las tablas usando de referencia la columnas Uploadaded variation
vep_plugin <- merge(vep,plugin,by="Uploaded_variation",all.x=T,all.y=F)

# guardamos la tabla resultante
write.table(vep_plugin,file="./vep/vep_plugin.txt",sep="\t", na="-", row.names=F,quote=FALSE)
