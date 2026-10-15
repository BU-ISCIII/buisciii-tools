#!/usr/bin/env python3
"""Select annotations associated to Exomiser's results based on passing
its own filters and their mode of inheritance (MOI).

This script should be run from 03-annotation (using the _06_filter_inheritance_ALL.sh script):
    python3 aux_postprocess_exomiser_direct.py wgstrio
    python3 aux_postprocess_exomiser_direct.py exometrio

Requires Python >=3.6. Reads inheritance_types.txt, exomiser's variants TSV
and variants_annot_all.tab, and generates annotated results from Exomiser
separated in different files depending on MOI. In the case of wgstrio, this is done
for general, exome and genes results (within a folder called filter_inheritance);
while for exometrio this is done only for exome (results are directly saved in the cwd).

The annotation table must retain original CHROM, POS, REF, ALT, ID and Allele columns.
"""

import argparse
import csv
import gzip
import re
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path


def require_file(path):
    """Check if input required files are available."""
    path = Path(path)
    if not path.is_file() or not path.stat().st_size:
        raise ValueError("Missing or empty file: {}".format(path))


def columns(header, required, path):
    """Read by name, rejecting missing or duplicated required columns."""
    header = header or []
    for name in required:
        if header.count(name) != 1:
            raise ValueError("{}: expected one '{}' column".format(path, name))
    return {name: header.index(name) for name in required}


def variant_key(chrom, pos, ref, alt):
    """Return a normalized (chrom, pos, ref, alt) tuple for comparing variants.
    Strips the "chr" prefix, maps "M" to "MT", and trims bases shared by
    ref and alt (suffix first, then prefix, shifting pos accordingly)"""
    if chrom.startswith("chr"):
        chrom = chrom[3:]
    if chrom == "M":
        chrom = "MT"
    pos = int(pos)
    while ref and alt and ref[-1] == alt[-1]:
        ref, alt = ref[:-1], alt[:-1]
    while ref and alt and ref[0] == alt[0]:
        ref, alt = ref[1:], alt[1:]
        pos += 1
    return chrom, pos, ref, alt


def read_selection(path, models):
    """Map each distinct PASS allele to its selected inheritance models.
    Only variants from Exomiser with FILTER == PASS and MOI within
    the inheritance models external file are kept.

    Takes the inheritance models and the variants TSV file from Exomiser
    and returns a dictionary of variants each one linked to their corresponding
    mode/s of inheritance.

    Example of return:
    CONTIG = 15 (it is actually the chromosome)
    POSITION = 78776843
    REF = T
    ALT = C
    MOI = AD:
    {('15', 78776843, 'T', 'C'): {'AD'}}"""
    selected = {}
    required = ["MOI", "FILTER", "CONTIG", "START", "REF", "ALT"]
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        columns(reader.fieldnames, required, path)
        for row in reader:
            if any(row.get(name) is None for name in required):
                raise ValueError("{}: incomplete row {}".format(path, reader.line_num))
            if row["FILTER"] != "PASS" or row["MOI"] not in models:
                continue
            if (
                not re.fullmatch(r"[0-9]+", row["START"])
                or not re.fullmatch(r"[ACGTN]+", row["REF"])
                or not re.fullmatch(r"[ACGTN]+", row["ALT"])
            ):
                raise ValueError(
                    "{}: unsupported variant at row {}".format(path, reader.line_num)
                )
            key = variant_key(row["CONTIG"], row["START"], row["REF"], row["ALT"])
            selected.setdefault(key, set()).add(row["MOI"])
    return selected


def candidates(row, selected):
    """Check which alleles of a variant were selected by Exomiser. Each
    line of the annotations file is checked against the exomiser's variants
    file. Its CHROM, POS, REF and ALT columns hold the original VCF record,
    which may have several ALT alleles (e.g. "C,CA"). Each ALT is compared
    against `selected`, not just the one this row annotates.
    This function returns a list of:
        key:        normalized variant key, as stored in `selected`.
        alt:        the ALT exactly as written in the annotations file.
        vep_allele: the same allele as VEP writes it in the Allele column
                    (anchor base removed if VEP trimmed it, "-" if nothing is left).

    This function returns a list of tuples, indicating for each variant identified
    in exomiser's variants file the ALT and Allele written in the annotations file.

    Example:
    CONTIG = 15 (it is actually the chromosome)
    POSITION = 78776843
    REF = T
    ALT = C
    Returns: [(('15', 78776843, 'T', 'C'), 'C', 'C')]
    """
    if not re.fullmatch(r"[0-9]+", row["POS"]) or not re.fullmatch(
        r"[ACGTN]+", row["REF"]
    ):
        raise ValueError("Invalid original coordinates/REF for {}".format(row["ID"]))
    ref, alts = row["REF"], row["ALT"].split(",")
    # VEP 116 without --minimal trims ONE anchor base if the record has an
    # indel and all non-'*' alleles share that base. Empty ALT becomes '-'.
    trim = any(len(alt) != len(ref) for alt in alts) and all(
        alt == "*" or (alt and alt[0] == ref[0]) for alt in alts
    )
    result = []
    for alt in alts:
        if alt != "*" and not re.fullmatch(r"[ACGTN]+", alt):
            continue
        key = variant_key(row["CHROM"], row["POS"], ref, "N" if alt == "*" else alt)
        if key in selected:
            allele = (alt[1:] if trim and alt != "*" else alt) or "-"
            result.append((key, alt, allele))
    return result


def process(tsv, annotations, directory, suffix, models):
    """Extract the VEP annotation rows associated to the variants that passed Exomiser's filters.

    This function reads Exomiser's variants TSV (PASS rows with a MOI within `models`) and scans
    the annotation table once, line by line. For each allele that passed filters it
    keeps only the annotation rows whose Allele column matches, and writes
    them to one file per inheritance model.

    Args:
        tsv:         Exomiser's variants TSV.
        annotations: variants_annot_all.tab (or .tab.gz), which includes all annotations.
        directory:   Temporary directory to create (must not already exist).
        suffix:      Appended to output names ("", "_exome", "_genes"), based on the service.
        models:      Inheritance models to keep, e.g. ["AD", "AR"], which will be written on the final output tables.

    Returns:
          vep_annot_<MOI><suffix>_final.txt   annotation rows, one file per MOI.
          selected_alleles.tsv                MOI, FILTER, VCF_ID, VEP_ALLELE.
          exomiser_spanning_deletions.tsv     selected '*' alleles, listed by MOI (see Notes below).

    Notes:
        An '*' in the ALT column of the annotations table marks a spanning deletion:
        the position is covered by a deletion described in another record. It has no sequence,
        so VEP gives it no annotation, and Exomiser writes it as 'N' in its variants TSV file.

        Example: the record chr1:6790377 T>*,A. Exomiser selects the '*'
        allele (as T>N, MOI=AR) as indicated in its TSV file, but VEP only
        annotates 'A' (ALT=*,A but Allele=A). There is nothing
        to extract for '*', so it is not written to the vep_annot files, since in this case
        the AR MOI is linked to "*", not to "A". This record is therefore listed in a separate
        file called exomiser_spanning_deletions.tsv instead, so it is not
        silently lost. This file contains the following columns: MOI, VCF_ID, REF, ALT ('*'), REASON,
        where REASON is always SPANNING_DELETION_PLACEHOLDER.
        The 'A' allele was not selected by Exomiser, so it is not written to the AR file either:
        that would assign it a MOI Exomiser never gave to it.

    Example:
        Exomiser variants TSV file has the following variant:
        MOI=AD  FILTER=PASS  15:78776843 T>C.
        Meanwhile, the annotation table has three rows (one per transcript) with:
        ID=rs761832715, REF=T, ALT=C, Allele=C. Then, we'd get:
            vep_annot_AD_final.txt    -> those three rows (plus the header)
            selected_alleles.tsv      -> AD  PASS  rs761832715  C
    """
    selected = read_selection(tsv, models)
    originals, selected_alleles, matched = {}, set(), set()
    counts = dict.fromkeys(models, 0)
    directory.mkdir()
    opener = gzip.open if annotations.suffix == ".gz" else open
    with ExitStack() as stack:
        outputs = {
            m: stack.enter_context(
                (directory / ("vep_annot_{}{}_final.txt".format(m, suffix))).open(
                    "w", encoding="utf-8"
                )
            )
            for m in models
        }
        handle = stack.enter_context(
            opener(annotations, "rt", newline="", encoding="utf-8")
        )
        header = next(handle, "").rstrip("\r\n")
        indexes = columns(
            header.split("\t"),
            ["ID", "CHROM", "POS", "REF", "ALT", "Allele"],
            annotations,
        )
        last = max(indexes.values())
        for output in outputs.values():
            output.write(header + "\n")

        previous_record, hits = None, []
        for number, line in enumerate(handle, 2):
            line = line.rstrip("\r\n")
            if not line:
                continue
            fields = line.split("\t", last + 1)
            if len(fields) <= last:
                raise ValueError("Incomplete annotation row {}".format(number))
            row = {name: fields[index] for name, index in indexes.items()}
            record = tuple(row[name] for name in ("ID", "CHROM", "POS", "REF", "ALT"))
            if record != previous_record:
                hits = candidates(row, selected)
                previous_record = record

            row_models = set()
            for key, alt, allele in hits:
                source = (record, alt, allele)
                if key in originals and originals[key] != source:
                    raise ValueError("Ambiguous original variant for {}".format(key))
                originals[key] = source
                if alt == "*":
                    continue
                if row["ID"] in ("", ".") or ";" in row["ID"]:
                    raise ValueError("Empty or ambiguous ID: {}".format(row["ID"]))
                for model in selected[key]:
                    match = (row["ID"], allele, model)
                    selected_alleles.add(match)
                    if row["Allele"] == allele:
                        matched.add(match)
                        row_models.add(model)
            for model in row_models:
                outputs[model].write(line + "\n")
                counts[model] += 1

    # Missing originals and wrong/missing Allele annotations both stop publication.
    missing = set(selected) - set(originals)
    if missing:
        raise ValueError(
            "{} selected variants absent from annotations; examples: {}".format(
                len(missing), sorted(missing)[:5]
            )
        )
    missing = selected_alleles - matched
    if missing:
        raise ValueError(
            "{} ID/Allele/MOI matches lack annotations; examples: {}".format(
                len(missing), sorted(missing)[:5]
            )
        )

    with (directory / "selected_alleles.tsv").open("w", encoding="utf-8") as handle:
        handle.write("MOI\tFILTER\tID\tVEP_ALLELE\n")
        for id_, allele, model in sorted(selected_alleles):
            handle.write("{}\tPASS\t{}\t{}\n".format(model, id_, allele))
    stars = 0
    with (directory / "exomiser_spanning_deletions.tsv").open(
        "w", encoding="utf-8"
    ) as handle:
        handle.write("MOI\tID\tREF\tALT\tREASON\n")
        for key in sorted(originals):
            record, alt, allele = originals[key]
            if alt == "*":
                for model in sorted(selected[key]):
                    handle.write(
                        "{}\t{}\t{}\t*\tSPANNING_DELETION_PLACEHOLDER\n".format(
                            model, record[0], record[3]
                        )
                    )
                    stars += 1
    print("{}: {} '*' allele/model markers recorded".format(tsv, stars), flush=True)
    for model in models:
        print(
            "{}: {} PASS alleles; {} annotated rows".format(
                model, sum(m[2] == model for m in selected_alleles), counts[model]
            ),
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["wgstrio", "exometrio"])
    args = parser.parse_args()
    require_file("inheritance_types.txt")
    # We define the available MOI listed in inheritance_types.txt.
    # These will be used to map Exomiser variants to their corresponding MOI.
    models = []
    for line in Path("inheritance_types.txt").read_text().splitlines():
        model = line.strip()
        if not model or model.startswith("#"):
            continue
        if not re.fullmatch(r"[A-Z_]+", model):
            raise ValueError("Invalid inheritance model: {}".format(model))
        if model not in models:
            models.append(model)
    if not models:
        raise ValueError(
            "No inheritance models supplied. Please make sure these are being provided"
        )
    annotations = Path("variants_annot_all.tab")
    if not annotations.is_file() or not annotations.stat().st_size:
        annotations = Path("variants_annot_all.tab.gz")
    require_file(annotations)

    # Input TSV, staging subdirectory, output suffix, destination directory.
    analyses = (
        [
            (
                "exomiser/exomiser/exomiser.variants.tsv",
                "genome",
                "",
                "filter_inheritance/filter_inheritance",
            ),
            (
                "exomiser/exomiser_exome/exomiser_exome.variants.tsv",
                "exome",
                "_exome",
                "filter_inheritance/filter_inheritance_exome",
            ),
            (
                "exomiser/exomiser_genes/exomiser_genes.variants.tsv",
                "genes",
                "_genes",
                "filter_inheritance/filter_inheritance_genes",
            ),
        ]
        if args.mode == "wgstrio"
        else [("exomiser/exomiser.variants.tsv", "exome", "", ".")]
    )
    for tsv, name, suffix, destination in analyses:
        require_file(tsv)

    # Temporary directory to work on.
    stage = Path(tempfile.mkdtemp(prefix=".exomiser_annotation.", dir="."))
    print("Temporary directory: {} (retained on failure)".format(stage), flush=True)
    for tsv, name, suffix, destination in analyses:
        process(Path(tsv), annotations, stage / name, suffix, models)

    # Publish final results only after all analyses pass.
    for tsv, name, suffix, destination in analyses:
        dest = Path(destination)
        dest.mkdir(parents=True, exist_ok=True)
        for path in sorted((stage / name).iterdir()):
            path.replace(dest / path.name)
        (stage / name).rmdir()
    stage.rmdir()
    print(
        "Annotation of exomiser's results completed! Please run _08_merge_vep_annot.sh next."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR: {}".format(error), file=sys.stderr)
        sys.exit(2)
