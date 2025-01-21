from Bio import SeqIO
import os
import argparse

parser = argparse.ArgumentParser(description="Count %Ns")
parser.add_argument("input_dir", type=str, help="Input dir masked files")
parser.add_argument("output_file", type=str, help="Output file for Ns count")
args = parser.parse_args()

out_handle = open(args.output_file, "w")

for f in os.listdir(args.input_dir):
    if f.endswith(".consensus.fa"):
        ffpath = os.path.join(args.input_dir, f)
        for record in SeqIO.parse(ffpath, "fasta"):
            n_count = record.seq.count("N") + record.seq.count("n")
            out_handle.write(
                "%s\t%0.2f\n" % (record.description, n_count * 100.0 / len(record))
            )

out_handle.close()
