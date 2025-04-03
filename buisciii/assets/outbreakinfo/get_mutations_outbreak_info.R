library(outbreakinfo)
library(optparse)
library(readxl)
library(writexl)
library(openxlsx)
library(crayon)
library(purrr)
library(dplyr)
library(stringr)
options(browser = "xdg-open")
################################################
################################################
##       PARSE COMMAND-LINE PARAMETERS        ##
################################################
################################################

source("/data/ucct/bi/references/outbreakinfo/setAuthToken.R")
source("/data/ucct/bi/references/outbreakinfo/getAuthToken.R")

manageAuthToken <- function() {
    token <- getAuthToken()
    if (is.null(token)) {
        # If token is not found, request authentication
        message(crayon::yellow("No token found. Authenticating the user..."))
        outbreakinfo::authenticateUser()
        token <- Sys.getenv("OUTBREAK_INFO_TOKEN")
        if (nzchar(token)) {
            setAuthToken(token)
            message(crayon::green("Token authenticated and successfully saved."))
        } else {
            stop(crayon::red("Could not obtain token after authentication."))
        }
    } else {
        message(crayon::green("Token successfully loaded from file."))
    }
    Sys.setenv("OUTBREAK_INFO_TOKEN" = token)
}

manageAuthToken()

message(crayon::blue("Continuing the analysis after token authentication."))

cat(cyan$bgRed$bold("########################\nStarting outbreakinfo pipeline\n###############################\n"))

option_list <- list(
  make_option(c("-l", "--lineage_list"             ), type="character" , default='./Lineages_Mutations.xlsx'   , metavar="path"   , help="Path to lineage list file"),
  make_option(c("-o", "--output_folder"            ), type="character" , default=NULL                    , metavar="path"   , help="Path to output directory" )
)

opt_parser <- OptionParser(option_list=option_list)
opt        <- parse_args(opt_parser)

if (is.null(opt$lineage_list)){
  print_help(opt_parser)
  stop("Please provide a lineage list file", call.=FALSE)
}

if (is.null(opt$output_folder)){
    print_help(opt_parser)
    stop("Please provide a path to output directory", call.=FALSE)
}

cat("########################\nRunning analysis with the following params:\n###############################\n")
cat("-Lineage list file: ") + cat(opt$lineage_list)+cat("\n")
cat("-Output directory: ") + cat(opt$output_folder)+cat("\n")

####LOAD DATA####
lineages_of_interest <- read_excel(opt$lineage_list, sheet = 1, col_names = TRUE)
colnames(lineages_of_interest) = c("Lineages")
lineages_of_interest <- as.vector(lineages_of_interest$Lineages)


getMutationsByLineage <- function(pangolin_lineage, frequency=0.75, logInfo=TRUE){

  if(length(pangolin_lineage) > 1) {
    # Set frequency to 0 and then filter after the fact.
    df <- map_df(pangolin_lineage, function(lineage) getGenomicData(query_url="lineage-mutations", pangolin_lineage = lineage, frequency = 0.75, logInfo = logInfo))

    if(!is.null(df) && nrow(df) != 0){
      mutations = df %>%
        filter(prevalence >= frequency) %>%
        pull(mutation) %>%
        unique()

      df <- df %>%
        filter(mutation %in% mutations)
    }

  } else {
    df <- getGenomicData(query_url="lineage-mutations", pangolin_lineage = pangolin_lineage, frequency = frequency, logInfo = logInfo)
  }

  return(df)
}

##GET LINEAGES DATA###
mutations = getMutationsByLineage(pangolin_lineage=lineages_of_interest, frequency=0.75, logInfo = TRUE)
table_name = paste(str_remove_all(as.Date(Sys.Date(), format = "%Y%m%d"), "-"), "mutaciones_definitorias_linaje.csv", sep = "_")
table_path = paste(opt$output_folder, table_name, sep = "/")
#write_xlsx(mutations, table_path, format_headers = F)
write.csv(mutations, table_path, row.names = FALSE)

####Find if missing mutations###
missing <- setdiff(lineages_of_interest,unique(mutations$lineage))
if (length(missing) > 0) {
  cat("There are some missing lineages in the table: ") + cat(missing, sep = ", ")+cat("\n")
}

cat("Excel of defining mutations generated as:", table_name)
save.image()
