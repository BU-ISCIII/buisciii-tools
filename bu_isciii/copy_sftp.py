#Copy delivery to sftp (e.g: SARS service) 
#Deliver automatization
##Copy in sftp
import json
import sys
import sysrsync

import argparse


from drylab_api import RestServiceApi




def parser_args(args=None):
    Description = 'Copy resolution files to sftp'
    Epilog = """Example usage: python copy_sftp.py --source /home/erika.kvalem/Documents/BU_ISCIII/pruebas_source --destination /home/erika.kvalem/Documents/BU_ISCIII/prubas_destination --options -r --exclusions "*_NC" """ 
    parser = argparse.ArgumentParser(description=Description, epilog=Epilog)
    parser.add_argument("-s", "--source"  , type=str,  help="Directory containing files to transfer")
    parser.add_argument("-d", "--destination", type=str, help="Directory to which the files will be transfered")
    parser.add_argument("--p", "--protocol", type=str,default = None, help="command to execute")
    parser.add_argument("--o", "--options", type=str,default = None, help="command parameters")
    parser.add_argument("--e", "--exclusions",default = None, type=str, help="Excluded files in the source folder that will not be transfered")
    return parser.parse_args(args)



def main(args=None):
    args = parser_args(args)

    ## Create output directory if it doesn't exist
    #destination = os.path.dirname(args.destination)
    #make_dir(out_dir)

#protocol rsync 1
    sysrsync.run(source=args.source,
    destination=args.destination,
    options=args.options)
                #exclusions=args.exclusions)

#sysrsync.run(source='/data/bi/services_and_colaborations/CNM/virologia/',
#             destination='/data/bi/sftp/Labvirusres'+ service_number,
#             options=["-rlpv","--update","-L","--inplace"],
#             exclusions=["*_NC","lablog","work","00-reads","*.sh",".nextflow*","*_DEL","*.R","*.py" ])



"""

  "command1":{
    "protocol":"rsync",
    "options":["-rlpv", "--update", "--inplace"],
    "exclusions":["*_NC","lablog","work","00-reads","*.sh",".nextflow*","*_DEL","*.R","*.py","RESULTS" ],

    "destination":"/data/bi/sftp/Labvirusres",
    "source":"/data/bi/services_and_colaborations/CNM/virologia/",
    "service_number":"SRVCNM572_20220209_SARSCOV278_icasas_S"
  },
  command1 = {
    "protocol":"rsync",
    "options":["-rlpv","--update","-L","--inplace"],
    "exclusions":["*_NC","lablog","work","00-reads","*.sh",".nextflow*","*_DEL","*.R","*.py"],

    "destination":"/data/bi/sftp/Labvirusres/SRVCNM572_20220209_SARSCOV278_icasas_S", 
    "source":"/data/bi/services_and_colaborations/CNM/virologia/",
    "service_number":"SRVCNM572_20220209_SARSCOV278_icasas_S"

""" 

# other code. . .



if __name__ == '__main__':
    sys.exit(main())


 
# Opening JSON file
#f = open("deliver_automatization.js")
 
# returns JSON object as a dictionary
#data = json.load(f)

# Closing file
#f.close()
