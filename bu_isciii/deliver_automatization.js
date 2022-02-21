
  schema = {
    "properties":{
    "destination_path":{
      "example":"/data/bi/sftp/Labvirusres" ,
      "description":"Folder at which the command will be executed",
      "type":"string"
    },
    "protocol":{
      "example":"rsync",
      "description":"Command to execute",
      "type":"string"
    },
    "protocol_params":{
      "example":"-rlpv",
      "description":"Parameters for the command",
      "type":"string"
    },
    "exclude":{
      "example":"",
      "description":"Files to exclude from command",
      "type":"string"
    },
    "origin_path":{
      "example":"/data/bi/services_and_colaborations/CNM/virologia/",
      "description":"Folder from which the files are comming from",
      "type":"string"
    },
    "service_number":{
      "example":"SRVCNM572_20220209_SARSCOV278_icasas_S",
      "description":"Service identifying name and number",
      "type":"string"
    },
  
  
  }
  }
  
