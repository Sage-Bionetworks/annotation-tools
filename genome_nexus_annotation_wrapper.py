"""
Adapted from cBioprotal's https://github.com/cBioPortal/datahub-study-curation-tools/blob/master/GN-annotation-wrapper/GN_annotation_wrapper.py
"""
import os
import sys
import subprocess
import argparse

ANNOTATED_MAF_FILE_EXT = ".annotated"
UNANNOTATED_MAF_FILE_EXT = ".unannotated"
HGVSP_SHORT_COLUMN = "HGVSp_Short"


def get_header(data_file):
    """
    Returns file header.
    """
    header = ""
    with open(data_file, "r") as f:
        for line in f.readlines():
            if not line.startswith("#"):
                header = line
                break
    return header


def get_comments(data_file):
    """
    Returns file comments.
    """
    comments = []
    with open(data_file, "r") as f:
        for line in f.readlines():
            if line.startswith("#"):
                comments.append(line)
            else:
                break
    return comments


def write_records_to_maf(filename, comments, header, records):
    """
    Writes MAF records to given file.
    """
    data_file = open(filename, "w")
    if comments:
        for comment in comments:
            data_file.write(comment)
    data_file.write(header)
    for record in records:
        data_file.write(record)
    data_file.close()


def split_maf_file_records(filename, ordered_header_columns):
    """
    Splits records from file into list of annotated and unannotated records.
    """
    annotated_records = []
    unannotated_records = []
    comment_lines = get_comments(filename)
    header = get_header(filename)
    columns = list(map(str.strip, header.split("\t")))
    if not ordered_header_columns:
        ordered_header_columns = columns[:]
    if not HGVSP_SHORT_COLUMN in columns:
        print(f"Could not find {HGVSP_SHORT_COLUMN} column in file header - exiting...")
        sys.exit(1)

    with open(filename, "r") as f:
        header_processed = False
        for line in f.readlines():
            if line.startswith("#"):
                continue
            if not header_processed:
                header_processed = True
                continue
            # now split the records by annotated or unannotated
            data = dict(zip(columns, map(str.strip, line.split("\t"))))
            ordered_data = map(lambda x: data.get(x, ""), ordered_header_columns)
            if data[HGVSP_SHORT_COLUMN] != "":
                annotated_records.append("\t".join(ordered_data) + "\n")
            else:
                unannotated_records.append("\t".join(ordered_data) + "\n")
    return annotated_records, unannotated_records


def run_genome_nexus_annotator(
    annotator_jar: str,
    input_maf: str,
    output_maf: str,
    error_report: str,
    isoform: str,
    attempt_num: int,
    ordered_header_columns: list,
    truststore_file: str,
    post_size: int,
):
    """
    Calls the Genome Nexus annotator and returns a list of annotated and unannotated records.
    - annotated records:
        - records which were succesfully annotated by Genone Nexus.
    - unannotated records:
        - records which were not successfully annotated by Genome Nexus OR
        - records which were successfully annotated by Genome Nexus but are non-coding so HGVSp_Short column is empty.
    """ 
    print(f"Annotation attempt: {attempt_num}")

    cmd = [
        "java",
        "-Xmx48g",
        f"-Djavax.net.ssl.trustStore={truststore_file}",
        "-jar",
        annotator_jar,
        "--filename",
        input_maf,
        "--output-filename",
        output_maf,
        "--isoform-override",
        isoform,
        "-e",
        error_report,
        "-p",
        str(post_size),
        "-r",
    ]

    subprocess.check_call(cmd)

    annotated_records, unannotated_records = split_maf_file_records(
        output_maf, ordered_header_columns
    )
    # split_maf_file_records() orders the data according to the ordered_header_columns if provided -
    # therefore the header in the output MAF from GN may not match the column order of the data values
    # in the returned annotated_records,unannotated_records. This is resolved by overwriting the output_maf
    # with the values of annotated_records
    if ordered_header_columns:
        ordered_header = "\t".join(ordered_header_columns) + "\n"
        write_records_to_maf(
            output_maf, get_comments(output_maf), ordered_header, annotated_records
        )

    return annotated_records, unannotated_records


def delete_intermediate_mafs(intermediate_mafs):
    """
    Deletes intermedite MAFs.
    """
    print("Deleting %s intermediate MAFs:" % (str(len(intermediate_mafs))))
    for maf in intermediate_mafs:
        if os.path.exists(maf):
            print('\tDeleting intermediate MAF "%s" ...' % (maf))
            os.remove(maf)
        else:
            print(
                '\tIntermediate MAF "%s" does not exist, nothing to delete. Continuing...'
                % (maf)
            )


def split_final_output(output_maf):
    unann_data = ""
    ann_data = ""

    filters = ["Silent", "Intron", "3'UTR", "5'UTR", "3'Flank", "5'Flank", "IGR"]
    filters = [element.lower() for element in filters]

    with open(output_maf, "r") as file:
        for line in file:
            if line.startswith("#"):
                comment_lines = line
            elif line.upper().startswith("HUGO_SYMBOL"):
                header = line
                cols = line.split("\t")
                try:
                    hgvsp_index = cols.index("HGVSp_Short")
                    varclas_index = cols.index("Variant_Classification")
                except ValueError:
                    print(
                        "HGVSp_Short/Variant_Classification column is not found in the MAF file. File can't be split. Exiting.."
                    )
                    sys.exit(1)
            else:
                data = line.split("\t")
                if (
                    data[hgvsp_index] == ""
                    and data[varclas_index].lower() not in filters
                ):
                    unann_data += line
                else:
                    ann_data += line
    os.remove(output_maf)
    return ann_data, unann_data


def genome_nexus_annotator_wrapper(
    annotator_jar,
    input_maf,
    output_maf,
    isoform,
    error_report,
    truststore_file,
    post_size,
    max_attempts,
):
    """
    Runs Genome Nexus annotator on input MAF and saves results to designated output MAF.
    If all records are not successfully annotated on first attempt, then script will continue
    running annotator on remaining unannotated records until one of the following conditions is met:

    1. The annotator did not successfully annotate
    """
    attempt_num = 1
    annotated_records, unannotated_records = run_genome_nexus_annotator(
        annotator_jar,
        input_maf,
        output_maf,
        error_report,
        isoform,
        attempt_num,
        [],
        truststore_file,
        post_size,
    )

    if len(unannotated_records) == 0:
        return

    annotated_file_comments = get_comments(output_maf)
    annotated_file_header = get_header(output_maf)
    ordered_header_columns = list(map(str.strip, annotated_file_header.split("\t")))

    intermediate_mafs = []
    while len(unannotated_records) > 0 and attempt_num <= max_attempts:
        attempt_num += 1
        isoform_extension = f"_{isoform}_attempt_{attempt_num}"
        input_unannotated_maf = input_maf + UNANNOTATED_MAF_FILE_EXT + isoform_extension
        output_reannotated_maf = input_maf + ANNOTATED_MAF_FILE_EXT + isoform_extension
        intermediate_mafs += [input_unannotated_maf, output_reannotated_maf]

        write_records_to_maf(
            input_unannotated_maf,
            annotated_file_comments,
            annotated_file_header,
            unannotated_records,
        )

        input_unannotated_maf_header = get_header(input_unannotated_maf)
        if input_unannotated_maf_header != annotated_file_header:
            print(
                "ERROR: header for %s does not match the output header in %s!"
                % (input_unannotated_maf, output_maf)
            )
            sys.exit(2)
        new_annotated, unannotated_records = run_genome_nexus_annotator(
            annotator_jar,
            input_unannotated_maf,
            output_reannotated_maf,
            error_report,
            isoform,
            attempt_num,
            ordered_header_columns,
            truststore_file,
            post_size,
        )

        #if len(new_annotated) == 0:
        #    # if there aren't any new annotated records then no improvement was made - exit while loop
        #    print(
        #        "Annotation attempt %s did not produce any newly annotated records - saving data to output file: %s"
        #        % (str(attempt_num), output_maf)
        #    )
        #    break

        annotated_records.extend(new_annotated)

    compiled = annotated_records + unannotated_records
    write_records_to_maf(
        output_maf, annotated_file_comments, annotated_file_header, compiled
    )

    if intermediate_mafs:
        delete_intermediate_mafs(intermediate_mafs)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-f", "--input_maf", required=True, help="Input MAF file path", type=str
    )
    parser.add_argument(
        "-an",
        "--annotated_maf",
        required=True,
        help="Output annotated MAF file path",
        type=str,
    )
    parser.add_argument(
        "-unan",
        "--unannotated_maf",
        required=True,
        help="Output unannotated MAF file path",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--annotator_jar_path",
        required=True,
        help="Path to Genome Nexus annotator JAR",
        type=str,
    )
    parser.add_argument(
        "-i",
        "--isoform",
        required=True,
        help="Isoform override (uniprot or mskcc)",
        type=str,
    )
    parser.add_argument(
        "-e",
        "--error_report_path",
        required=True,
        help="Path for failed annotations error report",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--truststore_file",
        required=True,
        help="Path to Java truststore file",
        type=str,
    )
    parser.add_argument(
        "-p",
        "--post_size",
        required=True,
        default=1000,
        help="Genome Nexus POST size",
        type=int,
    )
    parser.add_argument(
        "-m",
        "--max_annotation_attempts",
        required=False,
        default=10,
        type=int,
        help="Maximum re-annotation retries (default=10)",
    )

    args = parser.parse_args()
    output_maf = args.input_maf + "_annotated"
    genome_nexus_annotator_wrapper(
        annotator_jar=args.annotator_jar_path,
        input_maf=args.input_maf,
        output_maf=output_maf,
        isoform=args.isoform,
        error_report=args.error_report_path,
        truststore_file=args.truststore_file,
        post_size=args.post_size,
        max_attempts=args.max_annotation_attempts,
    )

    """
    Split the final output to two files 1) Annotated 2) Unannotated records
    Records that fall into one of the two criteria are considered annotated: 
      - Non-empty HGVSp_Short
      - HGVSp_Short is empty but the variant_Classification is Silent, Intron, 3'UTR, 5'UTR, 3'Flank, IGR
    If the HGVSp_Short is empty and the variant classification is not one of the above then the records are considered unannotated.
    """

    comments = "".join(get_comments(output_maf))
    header = get_header(output_maf)
    annotated, unannotated = split_final_output(output_maf)

    if len(annotated) != 0 and len(unannotated) == 0:
        ann_data = comments + header + annotated
        open(args.annotated_maf, "w").write(ann_data)
        print(
            "All the records are annotated and the output is saved to file: %s"
            % (args.annotated_maf)
        )
    elif len(annotated) != 0 and len(unannotated) != 0:
        ann_data = comments + header + annotated
        unan_data = comments + header + unannotated
        open(args.annotated_maf, "w").write(ann_data)
        open(args.unannotated_maf, "w").write(unan_data)
        print(
            "Annotated records are save to: %s and unannotated records are saved to: %s"
            % (args.annotated_maf, args.unannotated_maf)
        )
    elif len(annotated) == 0 and len(unannotated) != 0:
        unan_data = comments + header + unannotated
        open(args.unannotated_maf, "w").write(unan_data)
        print(
            "No records were annotated, the output is saved to file: %s"
            % (args.unannotated_maf)
        )


if __name__ == "__main__":
    main()
