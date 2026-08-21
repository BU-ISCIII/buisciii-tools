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
        default=0.01,
        help=(
            "Minimum alternate allele frequency required for a variant. Default 0.01. "
            "A variant is retained only when ALT_FREQ >= min_freq AND "
            "ALT_DP >= alt_depth."
        ),
    )
    parser.add_argument(
        "-d",
        "--alt_depth",
        type=int,
        default=10,
        help=(
            "Minimum number of reads supporting the alternate allele. Default 10. "
            "A variant is retained only when ALT_DP >= alt_depth AND "
            "ALT_FREQ >= min_freq."
        ),
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


def parse_numeric_metric(value, cast):
    """Safely convert an IRMA metric to a numeric value.

    IRMA can report missing values as ``NA``. Malformed or missing values should
    never make VCF generation crash; they are treated as unavailable instead.
    """
    if value in {None, "", "NA"}:
        return None
    try:
        return cast(value)
    except (TypeError, ValueError):
        return None


def passes_variant_filter(alt_dp, alt_af, min_freq, alt_depth):
    """Return True when a measured alternate allele passes both thresholds.

    Filtering is intentionally based only on support for the alternate allele:
    
    * ALT_DP >= alt_depth
    * ALT_AF >= min_freq

    Total position depth is retained as VCF metadata but is not an independent
    filter. Requiring ALT_DP already guarantees at least that much total depth.
    """
    dp = parse_numeric_metric(alt_dp, int)
    af = parse_numeric_metric(alt_af, float)
    if dp is None or af is None:
        return False
    return dp >= alt_depth and af >= min_freq


def exit_with_error(msg, sample, details=None):
    print(f"\033[91mERROR: {msg} for \033[1;91m{sample}\033[0m")
    if details:
        print(details)
    print("Please review this sample")
    sys.exit()


def alleles_to_dict(alleles_file):
    """Convert IRMA's allAlleles file to a dictionary without variant filtering.

    All valid allele rows are kept at this stage. Reference and low-frequency
    alleles can be required later to anchor and normalize indels correctly.
    Applying ALT_DP/ALT_AF filtering here would remove that context before the
    reference-based VCF representation has been constructed.

    Returns
    -------
    alleles_dict : dict
        Dictionary containing all parsed IRMA allele rows, keyed by
        ``Reference_Name_Position_Allele``. Values retain the original
        ``allAlleles`` fields as strings. No ALT_DP/ALT_AF filtering is applied
        at this stage.

        Example::

            {
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
                    "Allele_Type": "Minority",
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
                    "Allele_Type": "Consensus",
                },
            }
    """
    alleles_dict = {}

    with open(alleles_file, "r") as file:
        header_line = file.readline().strip()
        if not header_line:
            return alleles_dict

        header = header_line.split("\t")
        for line_number, line in enumerate(file, start=2):
            # Some IRMA records can contain embedded newlines. Continue reading
            # until the expected number of tab-separated fields is available.
            while line and line.count("\t") < len(header) - 1:
                continuation = file.readline()
                if not continuation:
                    break
                line += continuation

            line_data = line.strip().split("\t")
            if len(line_data) < len(header):
                print(
                    f"WARNING: skipping malformed allAlleles record near line "
                    f"{line_number}: expected {len(header)} columns, "
                    f"found {len(line_data)}."
                )
                continue

            try:
                position = int(line_data[1])
            except (IndexError, ValueError):
                print(
                    f"WARNING: skipping allAlleles record with invalid position "
                    f"near line {line_number}."
                )
                continue

            entry_dict = {header[i]: line_data[i] for i in range(len(header))}
            reference_name = entry_dict.get("Reference_Name")
            allele = entry_dict.get("Allele")
            if not reference_name or allele is None:
                print(
                    f"WARNING: skipping incomplete allAlleles record near line "
                    f"{line_number}."
                )
                continue

            variant = f"{reference_name}_{position}_{allele}"
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
    # Validate the alignment before indexing sequence records. This avoids an
    # IndexError on empty/corrupt FASTA files and produces an actionable error.
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

    frag_name = list(sequences_dict.keys())[0].split("_")[-1]
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


def handle_initial_insertion(vcf_dictionary, consensus, freq, alt_depth):
    """Generates the dictionary for insertions at the begining of sequence

    Parameters
    ----------
    vcf_dictionary : dict
        Dictionary containing VCF information.
    consensus: boolean
        If the insertion is included in the consensus sequence or not
    freq : float
        Minimum alternate allele frequency.
    alt_depth : int
        Minimum alternate allele depth.

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
        if v["REF_POS"] == 0
        and v["CONSENSUS"] == consensus
        and v["TYPE"] == "INS"
        and passes_variant_filter(
            v["DP"][0], v["AF"][0], min_freq=freq, alt_depth=alt_depth
        )
    }
    if not initial_ins_data:
        return None

    # A VCF insertion must be anchored to a real reference nucleotide. Keeping
    # all alleles until this point makes this anchor much less likely to be lost.
    first_ref_data = next(
        (v for v in vcf_dictionary.values() if v["REF_POS"] == 1), None
    )
    if first_ref_data is None:
        print(
            "WARNING: cannot normalize an insertion at the beginning of the "
            "reference because REF_POS 1 is unavailable. Skipping it."
        )
        return None

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


def ref_based_dict(vcf_dictionary, freq, alt_depth):
    """Converts information in variants to reference based positions. Combines insertion and deletion to be reference based.

    Parameters
    ----------
    vcf_dictionary : dict
        Dictionary containing VCF information.
    freq : float
        Minimum allele frequency to consider a variant
    alt_depth : int
        Minimum allele depth to consider a variant
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

        # Apply the variant threshold only after the reference-based context
        # has been built. Measured variants must satisfy BOTH alternate-depth
        # and alternate-frequency thresholds. TOTAL_DP is metadata only.
        dp = value["DP"][0]
        af = value["AF"][0]
        measured_variant_passes = passes_variant_filter(
            dp, af, min_freq=freq, alt_depth=alt_depth
        )

        # Consensus deletions inferred directly from the consensus/reference
        # alignment have no Count/Frequency entry in IRMA allAlleles. They must
        # remain available for VCF reconstruction; otherwise genuine consensus
        # deletions would be lost solely because IRMA reports their metrics as NA.
        alignment_consensus_deletion = (
            value["TYPE"] == "DEL"
            and value["CONSENSUS"]
            and dp == "NA"
            and af == "NA"
        )

        if measured_variant_passes or alignment_consensus_deletion:
            # Manage insertions
            if value["TYPE"] == "INS":
                # If the insertion is at the begining of the sequence, we use the first reference nucleotide at the end of ALT
                # For example REF='-' and ALT='G' TO REF="A" and ALT='GA'
                if value["REF_POS"] == 0:
                    if value["CONSENSUS"] and "INIT_INS_CONS" not in combined_vcf_dict:
                        initial_dict = handle_initial_insertion(
                            vcf_dictionary, consensus=True, freq=freq, alt_depth=alt_depth
                        )
                        if initial_dict is not None:
                            combined_vcf_dict["INIT_INS_CONS"] = initial_dict
                    elif (
                        not value["CONSENSUS"]
                        and "INIT_INS_MIN" not in combined_vcf_dict
                    ):
                        initial_dict = handle_initial_insertion(
                            vcf_dictionary, consensus=False, freq=freq, alt_depth=alt_depth
                        )
                        if initial_dict is not None:
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
                            # Only compare minority insertion candidates that
                            # themselves pass BOTH ALT_DP and ALT_AF thresholds.
                            # Otherwise a passing candidate could be replaced by
                            # a high-AF but poorly supported insertion.
                            insertion_data = {
                                k: v
                                for k, v in vcf_dictionary.items()
                                if value["SAMPLE_POS"] == v["SAMPLE_POS"]
                                and value["TYPE"] == v["TYPE"]
                                and value["CONSENSUS"] == v["CONSENSUS"]
                                and passes_variant_filter(
                                    v["DP"][0],
                                    v["AF"][0],
                                    min_freq=freq,
                                    alt_depth=alt_depth,
                                )
                            }
                            if not insertion_data:
                                continue

                            max_key = max(
                                insertion_data,
                                key=lambda k: (
                                    parse_numeric_metric(insertion_data[k]["AF"][0], float)
                                    or float("-inf"),
                                    parse_numeric_metric(insertion_data[k]["QUAL"][0], float)
                                    or float("-inf"),
                                ),
                            )
                            # Replace the data with the highest-supported passing
                            # insertion while keeping all depth metadata aligned.
                            value = vcf_dictionary[max_key]
                            content_dict["ALT"] = value["ALT"]
                            content_dict["DP"] = value["DP"].copy()
                            content_dict["TOTAL_DP"] = value["TOTAL_DP"].copy()
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
                        if not ref_pos_data:
                            print(
                                f"WARNING: cannot anchor insertion at REF_POS "
                                f"{value['REF_POS']}: reference context not found. "
                                "Skipping this insertion."
                            )
                            continue
                        prev_pos_allele = next(iter(ref_pos_data.values()))["REF"]
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
                    if not next_pos_data:
                        print(
                            f"WARNING: cannot normalize deletion at REF_POS "
                            f"{value['REF_POS']}: next reference position not found. "
                            "Skipping this deletion instead of aborting VCF generation."
                        )
                        continue

                    next_pos_allele = next(iter(next_pos_data.values()))["REF"]
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
                    if not prev_pos_data:
                        print(
                            f"WARNING: cannot normalize deletion at REF_POS "
                            f"{value['REF_POS']}: previous reference position not found. "
                            "Skipping this deletion instead of aborting VCF generation."
                        )
                        continue

                    prev_pos_allele = next(iter(prev_pos_data.values()))["REF"]
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

    if not os.path.exists(alignment):
        exit_with_error("Alignment file does not exist:", alignment)

    if not os.path.exists(all_alleles):
        exit_with_error("Alleles file does not exist:", all_alleles)

    # Start analysis
    # Convert allAlleles file to dictionary
    alleles_dict = alleles_to_dict(all_alleles)
    if not alleles_dict:
        exit_with_error(
            "No valid alleles found in allAlleles file",
            all_alleles,
        )
    reference_name = next(iter(alleles_dict.values())).get("Reference_Name", "")
    reference_parts = reference_name.split("_")
    if len(reference_parts) < 2:
        exit_with_error(
            "Cannot infer fragment from allAlleles Reference_Name",
            all_alleles,
            f"Reference_Name={reference_name!r}",
        )
    alleles_frag = reference_parts[1]

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

    # Build reference-based variants and only then apply ALT_DP + ALT_AF filtering.
    # Delaying filtering preserves reference alleles needed to normalize indels.
    combined_vcf_dict = ref_based_dict(af_merged_dict, freq, alt_dp)

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
