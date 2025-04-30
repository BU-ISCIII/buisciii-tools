# imports
from Bio import SeqIO
import statistics
import argparse
import sys
import copy
import os


def parse_args(args=None):
    Description = "Convert alignment between IRMA consensus and reference fasta to VCF file using IRMA stats"
    Epilog = """Example usage: python create_irma_vcf.py -a <alignment> -i <irma_alleles> -o <out_vcf>"""

    parser = argparse.ArgumentParser(description=Description, epilog=Epilog)
    parser.add_argument(
        "-a",
        "--alignment",
        type=str,
        required=True,
        help="Alignment file",
    )
    parser.add_argument(
        "-i",
        "--irma_alleles",
        type=str,
        required=True,
        help="IRMA allAlleles.txt file",
    )
    parser.add_argument(
        "-o",
        "--out_vcf",
        type=str,
        required=True,
        help="Output vcf file",
    )
    parser.add_argument(
        "-f",
        "--min_freq",
        type=float,
        default=0.25,
        help="Minimum Allele Frequency for a variant to be included in the .vcf file, when that position has a dpeth>= total_depth. Default 0.25. A variant will be included when (Alle Frequency >= min_freq and position depth >= total_depth) OR (allele depth >= alt_depth)",
    )
    parser.add_argument(
        "-t",
        "--total_depth",
        type=int,
        default=10,
        help="Minimum position depth for a variant to be included in the .vcf file when Alle Frequency >= min_freq. Default 10. A variant will be included when (Alle Frequency >= min_freq and position depth >= total_depth) OR (allele depth >= alt_depth)",
    )
    parser.add_argument(
        "-d",
        "--alt_depth",
        type=int,
        default=150,
        help="Minimum depth for a variant to be included in the .vcf file. Default 150X. A variant will be included when (Alle Frequency >= min_freq and position depth >= total_depth) OR (allele depth >= alt_depth)",
    )

    return parser.parse_args(args)


def calc_mean(values, cast=float, precision=2):
    """Calculate lists means

    Parameters
    ----------
    values : list
        List of values to calculate mean.
    cast :
        Type of number (float, int)
    precusion: int
        Number of decimals in the results.

    Returns
    -------
    number
        Number with the mean rounded
    """
    valid = [cast(v) for v in values if v != "NA"]
    if not valid:
        return "NA"
    mean_val = statistics.mean(valid)
    if precision == 0:
        number = str(int(round(mean_val)))
    else:
        number = str(round(mean_val, precision))
    return number


def exit_with_error(msg, sample, details=None):
    print(f"\033[91mERROR: {msg} for \033[1;91m{sample}\033[0m")
    if details:
        print(details)
    print("Please review this sample")
    sys.exit()


def alleles_to_dict(alleles_file):
    """Convert IRMA's allAlleles file to dictionary.

    Parameters
    ----------
    alleles_file : str
        Path to the alleles file.

    Returns
    -------
    alleles_dict
        Dictionary containing alleles information with chrom+positions+allele as key. e.g.
        {
            "rsv_a2_1_A": {
                "Reference_Name": "rsv_a2",
                "Position": "1",
                "Allele": "A",
                "Count": "2",
                "Total": "2",
                "Frequency": "1",
                "Average_Quality": "29.5",
                "ConfidenceNotMacErr": "0.998877981545698",
                "PairedUB": "1",
                "QualityUB": "1",
                "Allele_Type": "Consensus"
            },
            "rsv_a2_2204_A": {
                "Reference_Name": "rsv_a2",
                "Position": "2204",
                "Allele": "A",
                "Count": "6532",
                "Total": "15323",
                "Frequency": "0.426287280558637",
                "Average_Quality": "34.5708818126148",
                "ConfidenceNotMacErr": "0.999181140401206",
                "PairedUB": "0.00396999257813604",
                "QualityUB": "0.0010642711614851",
                "Allele_Type": "Minority"
            },
            "rsv_a2_2204_G": {
                "Reference_Name": "rsv_a2",
                "Position": "2204",
                "Allele": "G",
                "Count": "8768",
                "Total": "15323",
                "Frequency": "0.5722117078901",
                "Average_Quality": "35.0286268248175",
                "ConfidenceNotMacErr": "0.999450989591763",
                "PairedUB": "0.00396999257813604",
                "QualityUB": "0.00100698799816366",
                "Allele_Type": "Consensus"
            },
        }
    """

    alleles_dict = {}
    with open(alleles_file, "r") as file:
        header = file.readline().strip().split("\t")
        for line in file:
            while line.count("\t") < len(header) - 1:
                line += file.readline()
            line_data = line.strip().split("\t")
            position = int(line_data[1])
            entry_dict = {header[i]: line_data[i] for i in range(len(header))}
            variant = str(line_data[0]) + "_" + str(position) + "_" + str(line_data[2])
            alleles_dict[variant] = entry_dict
    return alleles_dict


def align2dict(alignment_file):
    """Convert alignment file to dictionary.

    Parameters
    ----------
    alignment_file : str
        Path to the alignment file in fasta format.

    Returns
    -------
    align_dict
        Dictionary containing alignment information with alignment positions as keys.
        E.g.:
        {
            "1": {'CHROM': 'NC_007372.1', 'REF_POS': 1, 'SAMPLE_POS': [0], 'REF': 'A', 'ALT': '-'}, # Deletions
            "46": {'CHROM': 'NC_007372.1', 'REF_POS': 46, 'SAMPLE_POS': [22], 'REF': 'C', 'ALT': 'T'}, #SNP
            "56": {'CHROM': 'NC_007372.1', 'REF_POS': 52, 'SAMPLE_POS': [29], 'REF': '-', 'ALT': 'T'}, #Insertion middle/end
            # Insertion begining
        }
    frag_name
        Fragment name
        E.g.: "PB1"
    """
    sequences_dict = {}
    frag_name = ""
    sample = os.path.basename(alignment_file).split("_ref.fasta")[0]
    with open(alignment_file, "r") as alignment:
        for sequence in SeqIO.parse(alignment, "fasta"):
            sequences_dict[sequence.id] = str(sequence.seq)
    frag_name = list(sequences_dict.keys())[0].split("_")[-1]
    # Check the number of sequences in alignment. Only two sequences should be in the aligment
    if len(sequences_dict) == 0:
        exit_with_error("No sequences in alignment", sample)
    elif len(sequences_dict) == 1:
        exit_with_error(
            "Only one sequence in alignment", sample, list(sequences_dict.keys())[0]
        )
    elif len(sequences_dict) > 2:
        exit_with_error(
            "More than two sequences in alignment", sample, list(sequences_dict.keys())
        )

    _, sample_seq = list(sequences_dict.items())[0]
    ref_id, ref_seq = list(sequences_dict.items())[1]

    # initialize positions, dictionaries and counters
    sample_position = 0
    ref_position = 0
    align_dict = {}
    CHROM = ref_id

    for i, (sample_base, ref_base) in enumerate(zip(sample_seq, ref_seq)):
        align_position = i + 1
        # Ns and gaps aligned together are not considered though are not included in the dict
        if sample_base != "-":
            sample_position += 1
        if ref_base != "-":
            ref_position += 1

        condition = (
            # Insertions in the sample respect to the reference
            (ref_base == "-" and sample_base != "N")
            # Delettions in the sample respect to the reference
            or (sample_base == "-" and ref_base != "N")
            # Low coverage region in the sample
            or (sample_base == "N" and ref_base != "-")
            # Do not consider Ns aligned with gaps.
            or (ref_base not in {"N", "-"} and sample_base not in {"N", "-"})
        )

        if condition:
            align_dict[align_position] = {
                "CHROM": CHROM,
                "REF_POS": ref_position,
                "SAMPLE_POS": [sample_position],
                "REF": ref_base,
                "ALT": sample_base,
            }

    return align_dict, frag_name


def merge_allele_aligment(alignment_dict, alleles_dict):
    """Merges all alleles file and aligment, based in aligment positions

    Parameters
    ----------
    alignment_dict : dict
        Dictionary containing aligment information.
    alleles_dictionary : dict
        Dictionary containing alleles information.

    Returns
    -------
    af_merged_dict
        Updated dictionary with allele frequencies and other metrics.
        E.g:
        {
            "NC_007372.1_1_-": {
                "CHROM": "NC_007372.1",
                "REF_POS": 1,
                "CONSENSUS": true,
                "SAMPLE_POS": [
                    0
                ],
                "REF": "A",
                "ALT": "-",
                "TYPE": "DEL",
                "DP": [
                    "NA"
                ],
                "TOTAL_DP": [
                    "NA"
                ],
                "AF": [
                    "NA"
                ],
                "QUAL": [
                    "NA"
                ]
            },
            "NC_007372.1_53_T": {
                "CHROM": "NC_007372.1",
                "REF_POS": 52,
                "CONSENSUS": true,
                "SAMPLE_POS": [
                    29
                ],
                "REF": "-",
                "ALT": "T",
                "TYPE": "INS",
                "DP": [
                    "11776"
                ],
                "TOTAL_DP": [
                    "17038"
                ],
                "AF": [
                    "0.69116093438197"
                ],
                "QUAL": [
                    "0.69116093438197"
                ]
            },
            "NC_007372.1_53_-": {
                "CHROM": "NC_007372.1",
                "REF_POS": 52,
                "CONSENSUS": false,
                "SAMPLE_POS": [
                    29
                ],
                "REF": "-",
                "ALT": "-",
                "TYPE": "REF",
                "DP": [
                    "5245"
                ],
                "TOTAL_DP": [
                    "17038"
                ],
                "AF": [
                    "0.307841295926752"
                ],
                "QUAL": [
                    "0.307841295926752"
                ]
            },
            "NC_007372.1_2364_-": {
                "CHROM": "NC_007372.1",
                "REF_POS": 2341,
                "CONSENSUS": true,
                "SAMPLE_POS": [
                    2297
                ],
                "REF": "T",
                "ALT": "-",
                "TYPE": "DEL",
                "DP": [
                    "NA"
                ],
                "TOTAL_DP": [
                    "NA"
                ],
                "AF": [
                    "NA"
                ],
                "QUAL": [
                    "NA"
                ]
            }
        }
    """

    af_merged_dict = {}

    # Iterate over the alignment dictionary, where align_pos is the key, pos_values is a dictionary with the values for that key/position
    for align_pos, pos_values in alignment_dict.items():
        # If deletion in sample (only found in alignment)
        if pos_values["REF_POS"] >= 1 and pos_values["ALT"] == "-":
            variant = f"{pos_values['CHROM']}_{align_pos}_{pos_values['ALT']}"
            af_merged_dict[variant] = {
                **pos_values,
                "CONSENSUS": True,
                "TYPE": "DEL",
                "DP": ["NA"],
                "TOTAL_DP": ["NA"],
                "AF": ["NA"],
                "QUAL": ["NA"],
            }
        else:
            # For non deletion positions MUST exist in the AllAlleles file, find all the data available for that sample's position
            sample_positions = set(pos_values["SAMPLE_POS"])
            matching = (
                v
                for v in alleles_dict.values()
                if int(v["Position"]) in sample_positions
            )
            for val in matching:
                # Define the type of allele
                allele_type = (
                    "REF"
                    if val["Allele"] == pos_values["REF"]
                    else (
                        "INS"
                        if pos_values["REF"] == "-"
                        else (
                            "DEL"
                            if val["Allele"] == "-"
                            else "low_cov" if pos_values["ALT"] == "N" else "SNP"
                        )
                    )
                )

                # create the data for those positons
                content_dict = {
                    **pos_values,
                    "CONSENSUS": val["Allele_Type"] == "Consensus",
                    "ALT": val["Allele"],
                    "TYPE": allele_type,
                    "DP": [val["Count"]],
                    "TOTAL_DP": [val["Total"]],
                    "AF": [val["Frequency"]],
                    "QUAL": [val["Frequency"]],
                }
                if allele_type == "low_cov" and content_dict["CONSENSUS"]:
                    content_dict["ALT"] = "N"
                # create a unique key to store the data in the dictionary
                variant = f"{pos_values['CHROM']}_{align_pos}_{val['Allele']}"

                # Add the position to the dictionary
                af_merged_dict[variant] = content_dict

    return af_merged_dict


def handle_initial_insertion(vcf_dictionary, consensus):
    """Generates the dictionary for insertions at the begining of sequence

    Parameters
    ----------
    vcf_dictionary : dict
        Dictionary containing VCF information.
    consensus: boolean
        If the insertion is included in the consensus sequence or not

    Returns
    -------
    initial_dict
        Dictionary with all the insertion data
        {
            "CHROM": "MW626062.1",
            "CONSENSUS": true,
            "AF": [
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332"
            ],
            "ALT": "GGAAAACAAAAGCAACAAAAA",
            "DP": [
                "1761",
                "1764",
                "1768",
                "1770",
                "1761",
                "1764",
                "1768",
                "1770",
                "1761",
                "1764",
                "1768",
                "1770",
                "1761",
                "1764",
                "1768",
                "1770",
                "1761",
                "1764",
                "1768",
                "1770"
            ],
            "QUAL": [
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332",
                "1",
                "1",
                "1",
                "0.998871332"
            ],
            "REF": "A",
            "REF_POS": 1,
            "SAMPLE_POS": [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20
            ],
            "TOTAL_DP": [
                "1761",
                "1764",
                "1768",
                "1772",
                "1761",
                "1764",
                "1768",
                "1772",
                "1761",
                "1764",
                "1768",
                "1772",
                "1761",
                "1764",
                "1768",
                "1772",
                "1761",
                "1764",
                "1768",
                "1772"
            ],
            "TYPE": "INS"
        }
    """
    initial_dict = {}
    # Get all the insertion data at the begining of sequence for the same frequency/consensus
    initial_ins_data = {
        k: v
        for k, v in vcf_dictionary.items()
        if v["REF_POS"] == 0 and v["CONSENSUS"] == consensus and v["TYPE"] == "INS"
    }

    # Get data for the first reference nucleotide
    first_ref_data = next(v for v in vcf_dictionary.values() if v["REF_POS"] == 1)

    for data in initial_ins_data.values():
        # If the first nucleotide, copy dictionary, else, just add new info
        if 1 in data["SAMPLE_POS"]:
            initial_dict = copy.deepcopy(data)
        else:
            initial_dict["SAMPLE_POS"].append(data["SAMPLE_POS"][0])
            initial_dict["DP"].append(data["DP"][0])
            initial_dict["TOTAL_DP"].append(data["TOTAL_DP"][0])
            initial_dict["AF"].append(data["AF"][0])
            initial_dict["QUAL"].append(data["QUAL"][0])
            initial_dict["ALT"] += data["ALT"]

    # Add reference data
    initial_dict["REF_POS"] = 1
    initial_dict["REF"] = first_ref_data["REF"]
    initial_dict["ALT"] += first_ref_data["REF"]
    return initial_dict


def ref_based_dict(vcf_dictionary, freq, alt_depth, total_depth):
    """Converts information in variants to reference based positions. Combines insertion and deletion to be reference based.

    Parameters
    ----------
    vcf_dictionary : dict
        Dictionary containing VCF information.
    freq : float
        Minimum allele frequency to consider a variant
    alt_depth : int
        Minimum allele depth to consider a variant
    total_depth : int
        Minimum total depth to consider a variant

    Returns
    -------
    combined_vcf_dict
        Updated dictionary with combined insertion and deletion variants.
        {
            "INIT_INS_CONS": {
                "CHROM": "MW626062.1",
                "REF_POS": 1,
                "CONSENSUS": true,
                "SAMPLE_POS": [
                    1,
                    2,
                    3,
                    4
                ],
                "REF": "A",
                "ALT": "GGAAA",
                "TYPE": "INS",
                "DP": [
                    "1761",
                    "1764",
                    "1768",
                    "1770"
                ],
                "TOTAL_DP": [
                    "1761",
                    "1764",
                    "1768",
                    "1772"
                ],
                "AF": [
                    "1",
                    "1",
                    "1",
                    "0.998871332"
                ],
                "QUAL": [
                    "1",
                    "1",
                    "1",
                    "0.998871332"
                ]
            },
            "INIT_INS_MIN": {
                "CHROM": "MW626062.1",
                "REF_POS": 1,
                "CONSENSUS": false,
                "SAMPLE_POS": [
                    1,
                    2,
                    3,
                    4
                ],
                "REF": "A",
                "ALT": "AAGGA",
                "TYPE": "INS",
                "DP": [
                    "1761",
                    "1764",
                    "1768",
                    "1770"
                ],
                "TOTAL_DP": [
                    "1761",
                    "1764",
                    "1768",
                    "1772"
                ],
                "AF": [
                    "0.0001",
                    "0.0001",
                    "0.0001",
                    "0.0001"
                ],
                "QUAL": [
                    "0.0001",
                    "0.0001",
                    "0.0001",
                    "0.0001"
                ]
            },
            "4_G": {
                "CHROM": "MW626062.1",
                "REF_POS": 4,
                "CONSENSUS": false,
                "SAMPLE_POS": [
                    24
                ],
                "REF": "A",
                "ALT": "G",
                "TYPE": "SNP",
                "DP": [
                    "1"
                ],
                "TOTAL_DP": [
                    "1772"
                ],
                "AF": [
                    "0.000564334"
                ],
                "QUAL": [
                    "0.000564334"
                ]
            },
            "4_T": {
                "CHROM": "MW626062.1",
                "REF_POS": 4,
                "CONSENSUS": false,
                "SAMPLE_POS": [
                    24
                ],
                "REF": "A",
                "ALT": "T",
                "TYPE": "SNP",
                "DP": [
                    "1"
                ],
                "TOTAL_DP": [
                    "1772"
                ],
                "AF": [
                    "0.000564334"
                ],
                "QUAL": [
                    "0.000564334"
                ]
            },
            "44_T": {
                "CHROM": "MW626062.1",
                "REF_POS": 44,
                "CONSENSUS": true,
                "SAMPLE_POS": [
                    64
                ],
                "REF": "C",
                "ALT": "T",
                "TYPE": "SNP",
                "DP": [
                    "3356"
                ],
                "TOTAL_DP": [
                    "3357"
                ],
                "AF": [
                    "0.999702115"
                ],
                "QUAL": [
                    "0.999702115"
                ]
            },
            "1701_DEL": {
                "CHROM": "MW626062.1",
                "REF_POS": 1701,
                "CONSENSUS": true,
                "SAMPLE_POS": [
                    1720
                ],
                "REF": "ACATTAGGATTTCAGAATCATGAGAAAAACAC",
                "ALT": "A",
                "TYPE": "DEL",
                "DP": [
                    "NA"
                ],
                "TOTAL_DP": [
                    "NA"
                ],
                "AF": [
                    "NA"
                ],
                "QUAL": [
                    "NA"
                ]
            }
        }
    """

    combined_vcf_dict = {}
    for key, value in vcf_dictionary.items():
        content_dict = copy.deepcopy(value)

        # Only process variants passing filters
        dp = value["DP"][0]
        af = value["AF"][0]
        tot_dp = value["TOTAL_DP"][0]

        if (
            dp != "NA"
            and af != "NA"
            and tot_dp != "NA"
            and (
                (int(tot_dp) >= total_depth and float(af) >= freq)
                or int(dp) >= alt_depth
            )
        ) or (dp == "NA" and af == "NA"):
            # Manage insertions
            if value["TYPE"] == "INS":
                # If the insertion is at the begining of the sequence, we use the first reference nucleotide at the end of ALT
                # For example REF='-' and ALT='G' TO REF="A" and ALT='GA'
                if value["REF_POS"] == 0:
                    if value["CONSENSUS"] and "INIT_INS_CONS" not in combined_vcf_dict:
                        initial_dict = handle_initial_insertion(
                            vcf_dictionary, consensus=True
                        )
                        combined_vcf_dict["INIT_INS_CONS"] = initial_dict
                    elif (
                        not value["CONSENSUS"]
                        and "INIT_INS_MIN" not in combined_vcf_dict
                    ):
                        initial_dict = handle_initial_insertion(
                            vcf_dictionary, consensus=False
                        )
                        combined_vcf_dict["INIT_INS_MIN"] = initial_dict
                else:
                    # Check if it is a minority insertion. In that case,
                    minority_ins = not value["CONSENSUS"]
                    # we will keep the consenus and the minority insertion with the highest allele frequency and quality.
                    if minority_ins:
                        # Check if top minority insertion for that sample position was already introduced in the combined dictionary
                        ins_found = False
                        position_data = {
                            k: v
                            for k, v in combined_vcf_dict.items()
                            if content_dict["SAMPLE_POS"][0] in v["SAMPLE_POS"]
                        }
                        for key, data in position_data.items():
                            if (
                                value["TYPE"] == data["TYPE"]
                                and value["CONSENSUS"] == data["CONSENSUS"]
                            ):
                                ins_found = key
                                break

                        # If insertion is not found, look for the insetion with highest AF and QUAL for that position in the sample
                        if not ins_found:
                            insertion_data = {
                                k: v
                                for k, v in vcf_dictionary.items()
                                if value["SAMPLE_POS"] == v["SAMPLE_POS"]
                                and value["TYPE"] == v["TYPE"]
                                and value["CONSENSUS"] == v["CONSENSUS"]
                            }
                            max_key = max(
                                insertion_data,
                                key=lambda k: (
                                    float(insertion_data[k]["AF"][0]),
                                    float(insertion_data[k]["QUAL"][0]),
                                ),
                            )
                            # Replace the data with the top insertion
                            value = vcf_dictionary[max_key]
                            content_dict["ALT"] = value["ALT"]
                            content_dict["DP"] = value["DP"].copy()
                            content_dict["AF"] = value["AF"].copy()
                            content_dict["QUAL"] = value["QUAL"].copy()

                        # If insertion is found, continue, as highest one was already introduced
                        else:
                            continue

                    # Transform REF and ALT values to make sense with INS format
                    # If the insertion is in the middle or at the end
                    # We use the last reference nucleotide as the begining of ALT
                    # For example REF='-' and ALT='G' TO REF="A" and ALT='AG'
                    else:
                        ref_pos_data = {
                            k: v
                            for k, v in vcf_dictionary.items()
                            if v["REF_POS"] == value["REF_POS"]
                        }
                        prev_pos_allele = list(ref_pos_data.values())[0]["REF"]
                        content_dict["ALT"] = prev_pos_allele + value["ALT"]
                        content_dict["REF"] = prev_pos_allele

                    variant_found = False

                    # Once data is ready, check if another previous nucleotide part of that insertion was already in the dictionary.
                    # Thay share the sample reference position as they are insertions not present in the reference.
                    position_data = {
                        k: v
                        for k, v in combined_vcf_dict.items()
                        if content_dict["REF_POS"] == v["REF_POS"]
                    }
                    for key, data in position_data.items():
                        if (
                            content_dict["TYPE"] == data["TYPE"]
                            and content_dict["CONSENSUS"] == data["CONSENSUS"]
                        ):
                            variant_found = key
                            break

                    # If variant is found, merge data.
                    if variant_found:
                        NEW_ALT = content_dict["ALT"][len(content_dict["REF"]) :]
                        combined_vcf_dict[variant_found]["ALT"] += NEW_ALT
                        combined_vcf_dict[variant_found]["SAMPLE_POS"].append(
                            content_dict["SAMPLE_POS"][0]
                        )
                        combined_vcf_dict[variant_found]["DP"].append(
                            content_dict["DP"][0]
                        )
                        combined_vcf_dict[variant_found]["TOTAL_DP"].append(
                            content_dict["TOTAL_DP"][0]
                        )
                        combined_vcf_dict[variant_found]["AF"].append(
                            content_dict["AF"][0]
                        )
                        combined_vcf_dict[variant_found]["QUAL"].append(
                            content_dict["QUAL"][0]
                        )
                    else:
                        # If variant is not found, it is the first nucleitode of the insertion, so it is added to the dictionary
                        variant = (
                            str(content_dict["REF_POS"])
                            + "_"
                            + content_dict["ALT"]
                            + "_"
                            + "INS"
                        )
                        combined_vcf_dict[variant] = content_dict

            elif value["TYPE"] == "DEL":
                # Transform REF and ALT values to make sense with DEL format
                # If the deletion is at the begining of the sequence, the needed allele is the next one
                # For example REF='A' and ALT='-' to REF="AG" and ALT='G'
                if 0 in value["SAMPLE_POS"]:
                    next_pos_data = {
                        k: v
                        for k, v in vcf_dictionary.items()
                        if v["REF_POS"] == value["REF_POS"] + 1
                    }
                    next_pos_allele = list(next_pos_data.values())[0]["REF"]
                    content_dict["ALT"] = next_pos_allele
                    content_dict["REF"] = value["REF"] + next_pos_allele
                # If the deletion is in the middle or at the end, we use the previous nucleotide
                # For example REF='A' and ALT='-' to REF="GA" and ALT='G'
                else:
                    prev_pos_data = {
                        k: v
                        for k, v in vcf_dictionary.items()
                        if v["REF_POS"] == value["REF_POS"] - 1
                    }
                    prev_pos_allele = list(prev_pos_data.values())[0]["REF"]
                    content_dict["REF_POS"] = value["REF_POS"] - 1
                    content_dict["ALT"] = prev_pos_allele
                    content_dict["REF"] = prev_pos_allele + value["REF"]

                # Handle minority variants whose SAMPLE_POS might differ as it is represented in the alignment
                minority_del = not value["CONSENSUS"]
                position_data = {}
                if minority_del:
                    # Check wether that deletion is already included in the combined dictionary.
                    # We look for the previous sample position as the consensus is still moving forward, they have to bee same type (DEL) and same frequency (Minority) in order to be merged
                    position_data = {
                        k: v
                        for k, v in combined_vcf_dict.items()
                        if content_dict["SAMPLE_POS"][0] - 1 in v["SAMPLE_POS"]
                        and content_dict["TYPE"] == v["TYPE"]
                        and content_dict["CONSENSUS"] == v["CONSENSUS"]
                    }
                else:
                    # Check wether that deletion is already included in the combined dictionary.
                    # We look for the sample position which is the same for all the deletions, they have to bee same type (DEL) and same frequency (Consensus) in order to be merged
                    # We only remove one position to sample_pos when handling consensus deletions, to be consistent with AllAlleles which does not contain Consensus deletions
                    if 0 not in content_dict["SAMPLE_POS"]:  # else it will be negative
                        content_dict["SAMPLE_POS"] = [value["SAMPLE_POS"][0] - 1]
                    position_data = {
                        k: v
                        for k, v in combined_vcf_dict.items()
                        if content_dict["SAMPLE_POS"][0] in v["SAMPLE_POS"]
                        and content_dict["TYPE"] == v["TYPE"]
                        and content_dict["CONSENSUS"] == v["CONSENSUS"]
                    }

                if position_data:
                    if len(position_data) > 1:
                        print("Más de un hit igual")
                        print("Is this even possible?")
                        break
                    variant_found = list(position_data.keys())[0]
                    # Check before merging that the reference position makes sense with the length of the deletion, else add deletion, don't merge
                    if 0 in content_dict["SAMPLE_POS"]:
                        combined_vcf_dict[variant_found]["REF"] += content_dict["ALT"]
                        combined_vcf_dict[variant_found]["ALT"] = content_dict["ALT"]
                    else:
                        ref = list(position_data.values())[0]["REF"]
                        ref_pos = list(position_data.values())[0]["REF_POS"]
                        if content_dict["REF_POS"] == ref_pos + len(ref) - 1:
                            new_ref = content_dict["REF"][len(content_dict["ALT"]) :]
                            combined_vcf_dict[variant_found]["REF"] += new_ref
                            if minority_del:
                                combined_vcf_dict[variant_found][
                                    "SAMPLE_POS"
                                ] += content_dict["SAMPLE_POS"]
                                combined_vcf_dict[variant_found]["DP"] += content_dict[
                                    "DP"
                                ]
                                combined_vcf_dict[variant_found][
                                    "TOTAL_DP"
                                ] += content_dict["TOTAL_DP"]
                                combined_vcf_dict[variant_found]["AF"] += content_dict[
                                    "AF"
                                ]
                        else:
                            variant = str(content_dict["REF_POS"]) + "_DEL"
                            combined_vcf_dict[variant] = content_dict
                else:
                    variant = str(content_dict["REF_POS"]) + "_DEL"
                    combined_vcf_dict[variant] = content_dict

            elif value["TYPE"] == "SNP":
                variant = str(content_dict["REF_POS"]) + "_" + content_dict["ALT"]
                combined_vcf_dict[variant] = content_dict
            elif value["TYPE"] == "REF":
                continue
            else:
                print("Different annotation type found for:")
                print(value)

    return combined_vcf_dict


def get_vcf_header(chromosome, sample_name):
    """Create the VCF header for VCFv4.2

    Parameters
    ----------
    chromosome : str
        Chromosome name.
    sample_name : str
        Sample name.

    Returns
    -------
    header
        String containing all the VCF header lines separated by newline.
    """

    header_source = ["##fileformat=VCFv4.2", "##source=custom"]
    header_contig = []
    if chromosome:
        header_contig += ["##contig=<ID=" + chromosome + ">"]
        header_source += header_contig

    header_info = [
        '##INFO=<ID=TYPE,Number=1,Type=String,Description="Either SNP (Single Nucleotide Polymorphism), DEL (deletion) or INS (Insertion)">',
        '##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">',
        '##INFO=<ID=consensus,Number=1,Type=String,Description="present if variant is included in consensus fasta">',
    ]
    header_filter = [
        '##FILTER=<ID=PASS,Description="All filters passed">',
    ]
    header_format = [
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        '##FORMAT=<ID=ALT_DP,Number=1,Type=Integer,Description="Depth of alternate base">',
        '##FORMAT=<ID=ALT_QUAL,Number=1,Type=Integer,Description="Mean quality of alternate base">',
        '##FORMAT=<ID=ALT_FREQ,Number=1,Type=Float,Description="Frequency of alternate base">',
    ]
    columns = ["#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + sample_name]
    header = header_source + header_info + header_filter + header_format + columns
    return header


def create_vcf(variants_dict, out_vcf, alignment):
    """Create VCF file from variants dictionary.

    Parameters
    ----------
    variants_dict : dict
        Dictionary containing variants information.
    out_vcf : str
        Path to the output VCF file.
    alignment : str
        Path to the alignment file.
    Returns
    -------
    None
    """
    chrom = next(iter(variants_dict.values()))["CHROM"]
    sample = os.path.basename(alignment).split("_ref.fasta")[0]
    vcf_header = "\n".join(get_vcf_header(chrom, sample))
    FORMAT = "GT:ALT_DP:ALT_QUAL:ALT_FREQ"
    ID = "."
    QUAL = "."
    FILTER = "PASS"
    GT = "1"
    with open(out_vcf, "w") as file_out:
        file_out.write(vcf_header + "\n")
        for _, value in variants_dict.items():
            CHROM = value["CHROM"]
            POS = value["REF_POS"]
            REF = value["REF"]
            ALT = value["ALT"]

            TOTAL_DP = calc_mean(value["TOTAL_DP"], int, 0)
            ALT_QUAL = calc_mean(value["QUAL"], float, 2)
            ALT_DP = calc_mean(value["DP"], int, 0)
            AF = calc_mean(value["AF"], float, 4)

            INFO = (
                "TYPE="
                + value["TYPE"]
                + ";"
                + "DP="
                + TOTAL_DP
                + ";"
                + ("consensus" if value["CONSENSUS"] else "")
            )

            SAMPLE = GT + ":" + ALT_DP + ":" + ALT_QUAL + ":" + AF
            oline = (
                CHROM
                + "\t"
                + str(POS)
                + "\t"
                + ID
                + "\t"
                + REF
                + "\t"
                + ALT
                + "\t"
                + QUAL
                + "\t"
                + FILTER
                + "\t"
                + INFO
                + "\t"
                + FORMAT
                + "\t"
                + SAMPLE
            )
            file_out.write(oline + "\n")


def main(args=None):
    # Process args
    args = parse_args(args)

    # Initialize vars
    alignment = args.alignment
    all_alleles = args.irma_alleles
    output_vcf = args.out_vcf
    freq = args.min_freq
    alt_dp = args.alt_depth
    total_dp = args.total_depth

    if not os.path.exists(alignment):
        exit_with_error("Alignment file does not exist:", alignment)

    if not os.path.exists(all_alleles):
        exit_with_error("Alleles file does not exist:", all_alleles)

    # Start analysis
    # Convert allAlleles file to dictionary
    alleles_dict = alleles_to_dict(all_alleles)
    alleles_frag = next(iter(alleles_dict.values()))["Reference_Name"].split("_")[1]

    # Convert alignment to dictionary
    alignment_dict, align_frag = align2dict(alignment)

    if alleles_frag != align_frag:
        print(
            "\033[93mWARNING: Fragment in allAlleles file is not the same as the one in alignment file.\033[0m"
        )
        print("You are comparing these files:")
        print(f"Alignment: {alignment}")
        print(f"All alleles: {all_alleles}")
        response = input("Are you sure you want to continue? [Y/n]: ").strip().lower()

        if response not in ("y", "yes", ""):
            print("Exiting.")
            exit()
    # Merge info from allAlleles and alignment
    af_merged_dict = merge_allele_aligment(alignment_dict, alleles_dict)

    # Convert merged info into reference based position format prior to vcf, merge INDELS and filter based on thresholds
    combined_vcf_dict = ref_based_dict(af_merged_dict, freq, alt_dp, total_dp)

    if not combined_vcf_dict:
        print("\033[91mERROR: No variants found, so no vcf is generated.\033[0m")
        sys.exit()

    # Sort by reference position
    # If reference position is the same, we will sort by TYPE (DEL, INS, SNP).
    # We took this decission in order to manage the case that a consensus SNP ys followed by a consensus DEL
    # In DEL, the previous alleles information is taken, usually REF information, so SNP and DEL will share same position
    # If the SNP goes prior to DEL in the vcf, a downstream tool like bctools, won't work, as SNP will be overwritten while including deletion.

    sorted_dict = dict(
        sorted(
            combined_vcf_dict.items(),
            key=lambda item: (item[1]["REF_POS"], item[1]["TYPE"]),
        )
    )

    # Create VCF
    create_vcf(sorted_dict, output_vcf, alignment)


if __name__ == "__main__":
    sys.exit(main())
