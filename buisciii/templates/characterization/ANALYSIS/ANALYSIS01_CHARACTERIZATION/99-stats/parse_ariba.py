#!/usr/bin/env python3

import argparse
import sys
import re
import csv
import pickle
import os

# FUNCTIONS


def check_arg(args=None):
    """
        Description:
        Function collect arguments from command line using argparse
    Input:
        args # command line arguments
    Constant:
        None
    Variables
        parser
    Return
        parser.parse_args() # Parsed arguments
    """

    parser = argparse.ArgumentParser(
        prog="06-ariba.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="06-ariba.py creates a csv file from results.txt file",
    )

    parser.add_argument(
        "--path",
        "-p",
        required=True,
        help="Insert report.tsv from path:Service_folder /home/user/Service_folder/ANALYSIS/06-ariba/sumaryl/out.summarycard.csv ",
    )

    parser.add_argument(
        "--database",
        "-d",
        required=True,
        help="The database used (card, megares or srst2_argannot",
    )

    parser.add_argument(
        "--output_bn", "-b", required=True, help="The output in binary file"
    )

    parser.add_argument(
        "--output_csv", "-c", required=True, help="The output in csv file"
    )

    return parser.parse_args()


def ariba_dictionary_card(file_csv):
    """
    Description:
        Function to extract the relevant part of out.summarycard.csv file
    Input:
        out.summarycard.csv file
    Return:
        dictionary
    """

    parameter = "resistance_genes_card"
    genes_list = {}
    with open(file_csv) as csvfile:
        data = list(csv.reader(csvfile, delimiter=","))

    header = data[0]
    match_indexes = [i for i, h in enumerate(header) if h.endswith(".match")]

    for row in data[1:]:
        genes = []

        for i in match_indexes:
            if row[i] == "yes":
                genes.append(header[i])

        gene_resis = "yes" if genes else "no"

        tmp = os.path.basename(row[0])
        match = re.search(r"(.*?)(?=_card_report.tsv)", tmp)
        if match:
            sample = match.group(1)
        else:
            continue

        genes_list[sample] = {parameter: genes, "resistance_card": gene_resis}

    return genes_list


def ariba_dictionary_vfdb(file_csv):
    """
    Description:
        Function to extract the relevant part of out.summaryvfdb_full.csv file
    Input:
        out.summaryvfdb_full.csv
    Return:
        dictionary
    """

    parameter = "virulence"
    with open(file_csv) as csvfile:
        data = list(csv.reader(csvfile))
        genes_list = {}

        for row in range(len(data)):
            if row == 0:
                header = data[row]
            else:
                genes = []
                for i in range(len(data[row])):
                    if data[row][i] == "yes":
                        genes.append(header[i])

                tmp = os.path.basename(data[row][0])
                sample = re.search(r"(.*?(?=_vfdb_full_report.tsv))", tmp).group(0)

                genes_list[sample] = {}
                genes_list[sample][parameter] = genes
                genes_list[sample].update(virulence_genes_vfdb=len(genes))

    return genes_list


def ariba_dictionary_megares(file_csv):
    """
    Description:
        Function to extract the relevant part of out.summarymegares.csv file
    Input:
        out.summarydatbase.csv file
    Return:
        dictionary
    """

    parameter = "resistance_genes_megares"
    with open(file_csv) as csvfile:
        data = list(csv.reader(csvfile))
        genes_list = {}

        for row in range(len(data)):
            if row == 0:
                header = data[row]
            else:
                genes = []
                for i in range(len(data[row])):
                    if data[row][i] == "yes":
                        gene_resis = "yes"
                        genes.append(header[i])
                    else:
                        gene_resis = "no"

                tmp = os.path.basename(data[row][0])
                sample = re.search(r"(.*?(?=megaresreport.tsv,))", tmp).group(0)

                genes_list[sample] = {}
                genes_list[sample][parameter] = genes
                genes_list[sample].update(resistance_megares=gene_resis)

    return genes_list


def ariba_dictionary_srst2(file_csv):
    """
    Description:
        Function to extract the relevant part of out.summarysrst2_argannot.csv file
    Input:
        out.summarydatbase.csv file
    Return:
        dictionary
    """

    parameter = "resistance_genes_srst2_argannot"
    with open(file_csv) as csvfile:
        data = list(csv.reader(csvfile))
        genes_list = {}

        for row in range(len(data)):
            if row == 0:
                header = data[row]
            else:
                genes = []
                for i in range(len(data[row])):
                    if data[row][i] == "yes":
                        gene_resis = "yes"
                        genes.append(header[i])
                    else:
                        gene_resis = "no"

                tmp = os.path.basename(data[row][0])
                sample = re.search(r"(.*?(?=srst2_argannotreport.tsv))", tmp).group(0)

                genes_list[sample] = {}
                genes_list[sample][parameter] = genes
                genes_list[sample].update(resistance_srst2_argannot=gene_resis)

    return genes_list


def ariba_dictionary_plasmidfinder(file_csv):
    """
    Description:
        Function to extract the relevant part of out.summaryplasmidfinder_full.csv file
    Input:
        out.summaryplasmidfinder_full.csv
    Return:
        dictionary
    """

    parameter = "plasmids_found"
    with open(file_csv) as csvfile:
        data = list(csv.reader(csvfile))
        plasmids_list = {}

        for row in range(len(data)):
            if row == 0:
                header = data[row]
            else:
                plasmids = []
                for i in range(len(data[row])):
                    if data[row][i] == "yes":
                        plasmids.append(header[i])

                tmp = os.path.basename(data[row][0])
                sample = re.search(r"(.*?(?=_plasmidfinder_report.tsv))", tmp).group(0)

                plasmids_list[sample] = {}
                plasmids_list[sample][parameter] = plasmids

    return plasmids_list


def ariba_dictionary_pubmlst(file_csv):
    """
    Description:
        Function to extract the relevant part of out.summarypubmlst_full.csv file
    Input:
        out.summarypubmlst_full.csv
    Return:
        dictionary
    """

    parameter = "st_found"
    with open(file_csv) as csvfile:
        data = list(csv.reader(csvfile))
        plasmids_list = {}

        for row in range(len(data)):
            if row == 0:
                header = data[row]
            else:
                plasmids = []
                for i in range(len(data[row])):
                    if data[row][i] == "yes":
                        plasmids.append(header[i])

                tmp = os.path.basename(data[row][0])
                sample = re.search(r"(.*?(?=_pubmlst_report.tsv))", tmp).group(0)

                plasmids_list[sample] = {}
                plasmids_list[sample][parameter] = plasmids

    return plasmids_list


def dictionary2csv(dictionary, csv_file):
    """
    Description:
        Function to create a csv from a dictionary
    Input:
        dictionary
    Return:
        csv file
    """

    header = sorted(set(i for b in map(dict.keys, dictionary.values()) for i in b))
    with open(csv_file, "w", newline="") as f:
        write = csv.writer(f)
        write.writerow(["sample", *header])
        for a, b in dictionary.items():
            write.writerow([a] + [b.get(i, "") for i in header])


def dictionary2bn(dictionary, binary_file):
    """
    Description:
        Function to create a binary file from a dictionary
    Input:
        dictionary
    Return:
        binary file
    """

    pickle_out = open(binary_file, "wb")
    pickle.dump(dictionary, pickle_out)
    pickle_out.close()

    return


# MAIN SCRIPT


if __name__ == "__main__":

    # Variables
    version = "06-ariba v 0.1.0."  # Script version
    arguments = check_arg(sys.argv[1:])

    # Create a dictionary

    if arguments.database == "card":
        ariba_dict = ariba_dictionary_card(arguments.path)
        print("ariba_dict_card done")
        # print (ariba_dict)

    if arguments.database == "megares":
        ariba_dict = ariba_dictionary_megares(arguments.path)
        print("ariba_dict_megares done")
        # print (ariba_dict)

    if arguments.database == "srst2_argannot":
        ariba_dict = ariba_dictionary_megares(arguments.path)
        print("ariba_dict_srst2 done")
        # print (ariba_dict)

    if arguments.database == "vfdb_full":
        ariba_dict = ariba_dictionary_vfdb(arguments.path)
        print("ariba_dict_vfdb done")

    if arguments.database == "plasmidfinder":
        ariba_dict = ariba_dictionary_plasmidfinder(arguments.path)
        print("ariba_dict_plasmidfinder done")

    if arguments.database == "pubmlst":
        ariba_dict = ariba_dictionary_pubmlst(arguments.path)
        print("ariba_dict_pubmlst done")

    # Convert the dictionary to csv file

    dictionary2csv(ariba_dict, arguments.output_csv)

    print("ariba_dictionary_csv done")

    # Save the dicctionary to binary file

    dictionary2bn(ariba_dict, arguments.output_bn)

    print("ariba_dictionary_bn done")
