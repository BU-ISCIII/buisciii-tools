# Cargar la tabla de datos
tabla <- read.table("dbNSFP_ENSG_plugin.txt", header = TRUE, sep = "\t", quote = "")

# Fusionar las cuatro columnas en una nueva columna llamada "Uploaded_variation"
tabla$Uploaded_variation <- paste(tabla$`chr`, tabla$`pos.1.based.`, tabla$ref, tabla$alt, sep = "_")

#Borrar las columnas innecesarias
tabla <-tabla[,-c(1,2,3,4)]

# Guardar la tabla resultante
write.table(tabla, "dbNSFP_ENSG_plugin_Columns.txt", sep = "\t", quote = FALSE, row.names = FALSE)

#cargamos tabla vep_annot_head
vep <- read.table("./vep/vep_annot_head.txt",header=T, sep = "\t", quote = "")

#pegamos las tablas usando de referencia la columnas Uploadaded variation
vep_plugin <- merge(vep,tabla,by="Uploaded_variation",all.x=T,all.y=F)

#guardamos la tabla resultante
write.table(vep_plugin,file="./vep/vep_plugin.txt",sep="\t", na="-", row.names=F,quote=FALSE)
