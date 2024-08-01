# imports
from Bio import SeqIO
import statistics
import argparse
import sys


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
    return parser.parse_args(args)


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
        header = file.readline().strip().split('\t')
        for line in file:
            while line.count('\t') < len(header) - 1:
                line += file.readline()
            line_data = line.strip().split('\t')
            position = int(line_data[1])
            variant_af = float(line_data[5])
            if variant_af > 0.25:
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
    vcf_dict
        Dictionary containing alignment information with alignment positions as keys.
        E.g.:
        {
            "10": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 1,
                "SAMPLE_POS": [
                    8,
                    9
                ],
                "REF": "A",
                "ALT": "AAA",
                "TYPE": "INS"
            },
            "11": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 2,
                "SAMPLE_POS": [
                    11
                ],
                "REF": "A",
                "ALT": "A",
                "TYPE": "REF"
            },
            "7542": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 7531,
                "SAMPLE_POS": [
                    7542
                ],
                "REF": "T",
                "ALT": "TT",
                "TYPE": "INS"
            },
            "7543": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 7531,
                "SAMPLE_POS": [
                    7543
                ],
                "REF": "T",
                "ALT": "TC",
                "TYPE": "INS"
            },
            "7544": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 7531,
                "SAMPLE_POS": [
                    7544
                ],
                "REF": "C",
                "ALT": "CA",
                "TYPE": "INS"
            },
            "10081": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10068,
                "SAMPLE_POS": [
                    10079
                ],
                "REF": "AA",
                "ALT": "A",
                "TYPE": "DEL"
            },
            "10082": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10069,
                "SAMPLE_POS": [
                    10079
                ],
                "REF": "-C",
                "ALT": "-",
                "TYPE": "DEL"
            },
            "10083": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10070,
                "SAMPLE_POS": [
                    10079
                ],
                "REF": "-T",
                "ALT": "-",
                "TYPE": "DEL"
            }
        }
    """
    sequences_dict = {}
    with open(alignment_file, "r") as alignment:
        for sequence in SeqIO.parse(alignment, "fasta"):
            sequences_dict[sequence.id] = str(sequence.seq)
    sample_id, sample_seq = list(sequences_dict.items())[0]
    ref_id, ref_seq = list(sequences_dict.items())[1]
    sample_position = 0
    ref_position = 0
    vcf_dict = {}
    CHROM = ref_id
    ALT = ""
    SAMPLE_POS = []
    for i, (sample_base, ref_base) in enumerate(zip(sample_seq, ref_seq)):
        align_position = i + 1
        if sample_base != "-":
            sample_position += 1
        if ref_base != "-":
            ref_position += 1
        if ref_base == "-" and sample_base != "N":
            if ref_position == 0:
                ALT += sample_base
                SAMPLE_POS.append(sample_position)
            else:
                content_dict = {
                    "CHROM": CHROM,
                    "REF_POS": ref_position,
                    "SAMPLE_POS": [sample_position],
                    "REF": sample_seq[i-1],
                    "ALT": sample_seq[i-1] + sample_base,
                    "TYPE": "INS"
                }
                vcf_dict[align_position] = content_dict
        elif ref_position == 1 and len(SAMPLE_POS) > 1:
            content_dict = {
                "CHROM": CHROM,
                "REF_POS": ref_position,
                "SAMPLE_POS": SAMPLE_POS,
                "REF": ref_base,
                "ALT": ALT + sample_base,
                "TYPE": "INS"
            }
            vcf_dict[align_position] = content_dict
        elif sample_base == "-" and ref_base != "N":
            content_dict = {
                "CHROM": CHROM,
                "REF_POS": ref_position-1,
                "SAMPLE_POS": [sample_position],
                "REF": sample_seq[i-1] + ref_base,
                "ALT": sample_seq[i-1],
                "TYPE": "DEL"
            }
            vcf_dict[align_position] = content_dict
        elif ref_base != sample_base and ref_base != "N" and ref_base != "-" and sample_base != "N" and sample_base != "-":
            content_dict = {
                "CHROM": CHROM,
                "REF_POS": ref_position,
                "SAMPLE_POS": [sample_position],
                "REF": ref_base,
                "ALT": sample_base,
                "TYPE": "SNP"
            }
            vcf_dict[align_position] = content_dict
        elif ref_base != "N" and ref_base != "-" and sample_base != "N" and sample_base != "-":
            content_dict = {
                "CHROM": CHROM,
                "REF_POS": ref_position,
                "SAMPLE_POS": [sample_position],
                "REF": ref_base,
                "ALT": sample_base,
                "TYPE": "REF"
            }
            vcf_dict[align_position] = content_dict
    return vcf_dict


def stats_vcf(vcf_dictionary, alleles_dictionary):
    """Add stats to VCF dictionary.

    Parameters
    ----------
    vcf_dictionary : dict
        Dictionary containing VCF information.
    alleles_dictionary : dict
        Dictionary containing alleles information.

    Returns
    -------
    af_vcf_dict
        Updated dictionary with allele frequencies and other metrics.
        E.g:
        {
            "EPI_ISL_18668201_1_AAA": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 1,
                "SAMPLE_POS": [
                    8,
                    9
                ],
                "REF": "A",
                "ALT": "AAA",
                "TYPE": "INS",
                "DP": [
                    "9",
                    "10"
                ],
                "AF": [
                    "1",
                    "1"
                ],
                "QUAL": [
                    "33.7777777777778",
                    "34"
                ]
            },
            "19": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10,
                "SAMPLE_POS": [
                    19
                ],
                "REF": "T",
                "ALT": "A",
                "TYPE": "SNP",
                "DP": [
                    "60"
                ],
                "AF": [
                    "0.833333333333333"
                ],
                "QUAL": [
                    "34.0166666666667"
                ]
            },
            "7542": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 7531,
                "SAMPLE_POS": [
                    7542
                ],
                "REF": "T",
                "ALT": "TT",
                "TYPE": "INS",
                "DP": [
                    "74"
                ],
                "AF": [
                    "0.986666666666667"
                ],
                "QUAL": [
                    "34.8648648648649"
                ]
            },
            "7543": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 7531,
                "SAMPLE_POS": [
                    7543
                ],
                "REF": "T",
                "ALT": "TC",
                "TYPE": "INS",
                "DP": [
                    "75"
                ],
                "AF": [
                    "1"
                ],
                "QUAL": [
                    "35.04"
                ]
            },
            "7544": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 7531,
                "SAMPLE_POS": [
                    7544
                ],
                "REF": "C",
                "ALT": "CA",
                "TYPE": "INS",
                "DP": [
                    "75"
                ],
                "AF": [
                    "1"
                ],
                "QUAL": [
                    "33.8533333333333"
                ]
            },
            "10081": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10068,
                "SAMPLE_POS": [
                    10079
                ],
                "REF": "AA",
                "ALT": "A",
                "TYPE": "DEL",
                "DP": [
                    "10"
                ],
                "AF": [
                    "1"
                ],
                "QUAL": [
                    "34.3"
                ]
            },
            "10082": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10069,
                "SAMPLE_POS": [
                    10079
                ],
                "REF": "-C",
                "ALT": "-",
                "TYPE": "DEL",
                "DP": [
                    "10"
                ],
                "AF": [
                    "1"
                ],
                "QUAL": [
                    "34.3"
                ]
            },
            "10083": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10070,
                "SAMPLE_POS": [
                    10079
                ],
                "REF": "-T",
                "ALT": "-",
                "TYPE": "DEL",
                "DP": [
                    "10"
                ],
                "AF": [
                    "1"
                ],
                "QUAL": [
                    "34.3"
                ]
            }
        }
    """
    af_vcf_dict = {}
    for _, value in alleles_dictionary.items():
        pos = value["Position"]
        for _, subdict in vcf_dictionary.items():
            if value["Allele_Type"] == "Consensus" and subdict["TYPE"] == "REF":
                continue
            if 'SAMPLE_POS' in subdict and int(pos) in subdict['SAMPLE_POS']:
                DP = []
                AF = []
                QUAL = []
                content_dict = {
                    "CHROM": subdict["CHROM"],
                    "REF_POS": subdict["REF_POS"],
                    "SAMPLE_POS": subdict["SAMPLE_POS"],
                    "REF": subdict["REF"],
                    "ALT": subdict["ALT"],
                    "TYPE": subdict["TYPE"]
                }
                if value["Allele"] == content_dict["ALT"] or value["Allele_Type"] == "Minority" or content_dict["TYPE"] in ["INS", "DEL", "REF"]:
                    DP.append(value["Count"])
                    AF.append(value["Frequency"])
                    QUAL.append(value["Average_Quality"])
                else:
                    print("SNP not the same in .fasta file and alleles file")
                    print(value)
                    print(content_dict)

                content_dict.update({"DP": DP, "AF": AF, "QUAL": QUAL})
                variant = content_dict["CHROM"] + "_" + str(content_dict["REF_POS"]) + "_" + content_dict["ALT"]

                if variant in af_vcf_dict:
                    af_vcf_dict[variant]["DP"] += DP
                    af_vcf_dict[variant]["AF"] += AF
                    af_vcf_dict[variant]["QUAL"] += QUAL
                else:
                    af_vcf_dict[variant] = content_dict
                break

    return af_vcf_dict


def combine_indels(vcf_dictionary):
    """Combine insertion and deletion pñositons in the VCF dictionary.

    Parameters
    ----------
    vcf_dictionary : dict
        Dictionary containing VCF information.

    Returns
    -------
    combined_vcf_dict
        Updated dictionary with combined insertion and deletion variants.
        {
            "1": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 1,
                "SAMPLE_POS": [
                    8,
                    9
                ],
                "REF": "A",
                "ALT": "AAA",
                "DP": [
                    "9"
                ],
                "AF": [
                    "1"
                ],
                "QUAL": [
                    "33.7777777777778"
                ],
                "TYPE": "INS"
            },
            "10": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10,
                "SAMPLE_POS": [
                    19
                ],
                "REF": "T",
                "ALT": "A",
                "DP": [
                    "60"
                ],
                "AF": [
                    "0.833333333333333"
                ],
                "QUAL": [
                    "34.0166666666667"
                ],
                "TYPE": "SNP"
            },
            "7531": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 7531,
                "SAMPLE_POS": [
                    7542,
                    7543,
                    7544
                ],
                "REF": "T",
                "ALT": "TTCA",
                "DP": [
                    "74",
                    "75",
                    "75"
                ],
                "AF": [
                    "0.986666666666667",
                    "1",
                    "1"
                ],
                "QUAL": [
                    "34.8648648648649",
                    "35.04",
                    "33.8533333333333"
                ],
                "TYPE": "INS"
            },
            "10068": {
                "CHROM": "EPI_ISL_18668201",
                "REF_POS": 10068,
                "SAMPLE_POS": [
                    10079
                ],
                "REF": "AACT",
                "ALT": "A",
                "DP": [
                    "10"
                ],
                "AF": [
                    "1"
                ],
                "QUAL": [
                    "34.3"
                ],
                "TYPE": "DEL"
            }
        }

    """
    combined_vcf_dict = {}
    for key, value in vcf_dictionary.items():
        content_dict = {
            "CHROM": value["CHROM"],
            "REF_POS": value["REF_POS"],
            "SAMPLE_POS": value["SAMPLE_POS"],
            "REF": value["REF"],
            "ALT": value["ALT"],
            "DP": value["DP"],
            "AF": value["AF"],
            "QUAL": value["QUAL"],
            "TYPE": value["TYPE"]
        }
        if value["TYPE"] == "INS":
            if value["REF_POS"] in combined_vcf_dict:
                if value["TYPE"] == combined_vcf_dict[value["REF_POS"]]["TYPE"]:
                    NEW_ALT = value["ALT"].replace(value["REF"], "")
                    combined_vcf_dict[value["REF_POS"]]["ALT"] += NEW_ALT
                    combined_vcf_dict[value["REF_POS"]]["SAMPLE_POS"].append(value["SAMPLE_POS"][0])
                    combined_vcf_dict[value["REF_POS"]]["DP"].append(value["DP"][0])
                    combined_vcf_dict[value["REF_POS"]]["AF"].append(value["AF"][0])
                    combined_vcf_dict[value["REF_POS"]]["QUAL"].append(value["QUAL"][0])
                else:
                    print("Same position annotated with multiple variant types")
                    print("value")
                    print(value)
                    print("combined_vcf_dict")
                    print(combined_vcf_dict[value["REF_POS"]])
            else:
                combined_vcf_dict[value["REF_POS"]] = content_dict
        elif value["TYPE"] == "DEL":
            sample_found = False
            for pos, data in combined_vcf_dict.items():
                var_type = data["TYPE"]
                if var_type == "DEL":
                    if value["SAMPLE_POS"] == data["SAMPLE_POS"]:
                        if value["TYPE"] == var_type:
                            sample_found = data["REF_POS"]
                            break
                        else:
                            print("Same position annotated with multiple variant types")
                            print("value")
                            print(value)
                            print("combined_vcf_dict")
                            print(combined_vcf_dict[value["REF_POS"]])
            if sample_found:
                NEW_REF = value["REF"].replace(value["ALT"], "")
                combined_vcf_dict[sample_found]["REF"] += NEW_REF
            else:
                combined_vcf_dict[value["REF_POS"]] = content_dict
        elif value["TYPE"] == "SNP":
            if value["REF_POS"] in combined_vcf_dict:
                if value["TYPE"] == combined_vcf_dict[value["REF_POS"]]["TYPE"]:
                    print("Repeated SNP!!!")
                else:
                    print("Same position annotated with multiple variant types")
                    print("value")
                    print(value)
                    print("combined_vcf_dict")
                    print(combined_vcf_dict[value["REF_POS"]])
            else:
                combined_vcf_dict[value["REF_POS"]] = content_dict
        else:
            print("Different annotation type found")
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
    # Define VCF header
    header_source = ["##fileformat=VCFv4.2", "##source=custom"]
    header_contig = []
    if chromosome:
        header_contig += [
            "##contig=<ID=" + chromosome + ">"
        ]
        header_source += header_contig

    header_info = [
        '##INFO=<ID=TYPE,Number=1,Type=String,Description="Either SNP (Single Nucleotide Polymorphism), DEL (deletion) or INS (Insertion)">',
    ]
    header_format = [
        '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth of alternate base">',
        '##FORMAT=<ID=AF,Number=1,Type=Float,Description="Frequency of alternate base">',
    ]
    columns = [
        '#CHROM\tPOS\tREF\tALT\tQUAL\tINFO\tFORMAT\t' + sample_name
    ]
    header = header_source + header_info + header_format + columns
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
    sample = alignment.replace(".align.fasta", "")
    vcf_header = "\n".join(get_vcf_header(chrom, sample))
    FORMAT = "DP:AF"
    with open(out_vcf, "w") as file_out:
        file_out.write(vcf_header + "\n")
        for key, value in variants_dict.items():
            CHROM = value["CHROM"]
            POS = value["REF_POS"]
            REF = value["REF"]
            ALT = value["ALT"]
            QUAL_list = [float(number) for number in value["QUAL"]]
            QUAL = str(round(statistics.mean(QUAL_list), 2))
            INFO = "TYPE=" + value["TYPE"]
            DP_list = [int(number) for number in value["DP"]]
            AF_list = [float(number) for number in value["AF"]]
            SAMPLE = str(round(statistics.mean(DP_list))) + ':' + str(round(statistics.mean(AF_list), 4))
            oline = CHROM + '\t' + str(POS) + '\t' + REF + '\t' + ALT + '\t' + str("".join(QUAL)) + '\t' + INFO + '\t' + FORMAT + '\t' + SAMPLE
            file_out.write(oline + "\n")


def main(args=None):
    # Process args
    args = parse_args(args)

    # Initialize vars
    alignment = args.alignment
    all_alleles = args.irma_alleles
    output_vcf = args.out_vcf

    # Start analysis
    alleles_dict = alleles_to_dict(all_alleles)
    alignment_dict = align2dict(alignment)
    af_vcf_dict = stats_vcf(alignment_dict, alleles_dict)
    combined_vcf_dict = combine_indels(af_vcf_dict)
    create_vcf(combined_vcf_dict, output_vcf, alignment)


if __name__ == "__main__":
    sys.exit(main())
