library(data.table)

# Cargar la tabla de datos
plugin <- fread(
  "dbNSFP_ENSG_plugin_hg19.txt",
  sep = "\t",
  quote = "",
  header = TRUE,
  check.names = TRUE
)

# Fusionar las cuatro columnas en una nueva columna llamada "ID"
plugin[, ID := paste(chr, hg19_pos, ref, alt, sep = "_")]

# Borrar las columnas innecesarias
plugin[, c("chr", "hg19_pos", "ref", "alt") := NULL]

# Guardar la tabla resultante
fwrite(
  plugin,
  "dbNSFP_ENSG_plugin_Columns.txt",
  sep = "\t",
  quote = FALSE,
  na = "-"
)

# Cargamos tabla vep_annot_head
vep <- fread(
  "./vep/vep_annot_head.txt",
  sep = "\t",
  quote = "",
  header = TRUE,
  check.names = TRUE,
  fill = TRUE
)

# Pegamos las tablas usando de referencia la columna ID
vep_plugin <- merge(
  vep,
  plugin,
  by = "ID",
  all.x = TRUE,
  all.y = FALSE,
  sort = TRUE
)

# Guardamos la tabla resultante
fwrite(
  vep_plugin,
  file = "./vep/vep_plugin.txt",
  sep = "\t",
  na = "-",
  quote = FALSE
)

# Cargamos tabla dbNSFP y vep_plugin
dbNSFP <- fread(
  "dbNSFP_ENSG_gene_GRCh37.txt",
  sep = "\t",
  quote = "",
  header = TRUE,
  check.names = TRUE
)

# Pegamos dbNSFP con vep usando de referencia la columna Gene
vep_dbNSFP <- merge(
  vep_plugin,
  dbNSFP,
  by = "Gene",
  all.x = TRUE,
  all.y = FALSE,
  sort = TRUE
)

# Guardamos la tabla resultante
fwrite(
  vep_dbNSFP,
  file = "./vep/vep_dbNSFP.txt",
  sep = "\t",
  na = "-",
  quote = FALSE
)

# Cargamos la tabla vep/variants.table
variants <- fread(
  "./vep/variants.table",
  sep = "\t",
  quote = "",
  header = TRUE,
  check.names = TRUE
)

# Pegamos vep_dbNSFP junto con variants
vep_dbNSFP_variants <- merge(
  variants,
  vep_dbNSFP,
  by = "ID",
  all.x = FALSE,
  all.y = FALSE,
  sort = TRUE
)

# Guardamos la tabla resultante
fwrite(
  vep_dbNSFP_variants,
  file = "variants_annot_all.tab",
  sep = "\t",
  na = "-",
  quote = FALSE
)