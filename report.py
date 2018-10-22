#!/usr/bin/env python

import re
import os
import sys
import logging
import argparse
import subprocess
import collections

class CoverageReport(object):
    def __init__(self, dr_path, output, path_maps, src_filter, debug_level=0):
        # Tools path.
        self.dr_cov2lcov = os.path.join(dr_path, "tools", "bin64", "drcov2lcov")
        self.dr_genhtml = os.path.join(dr_path, "tools", "bin64", "genhtml")

        self.path_maps = path_maps
        self.src_filter = src_filter
        self.debug_level = debug_level

        # Create the working directory structure.
        self.output_dir = os.path.abspath(output)
        self.traces_dir = os.path.join(self.output_dir, "traces")
        self.report_dir = os.path.join(self.output_dir, "report")
        self.coverage_info_file = os.path.join(self.output_dir, "coverage.info")

        # Check that the output directory has the right layout.
        if not os.path.exists(self.output_dir) or not os.path.exists(self.traces_dir):
            raise Exception("Output directory is not valid.")

        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

        logging.info("Working directory `%s`" % self.output_dir)
        logging.info("Traces directory `%s`" % self.traces_dir)
        logging.info("Report directory `%s`" % self.traces_dir)

    def run(self):
        # Process all the generated traces and generate a single coverage file.
        if not self.process_traces():
            return False

        # Create an html report with the coverage information.
        if not self.generate_report():
            return False

        return True

    def generate_report(self):
        process_command = [
            self.dr_genhtml,
            "-ignore-errors=source",
            "--output-directory", self.report_dir,
            "--quiet",
            "--demangle-cpp",
            "--legend",
            "--highlight",
            "--show-details",
            self.coverage_info_file
        ]

        try:
            output = subprocess.check_output(process_command, stderr=subprocess.STDOUT)
            logging.debug(output)

            # Extract missing source files from the output so the user can map them to the right places.
            missing_dirs = set()
            for line in output.split("\n"):
                match = re.match(r"(genhtml: WARNING: cannot read )(.+)!", line)
                if not match:
                    continue

                # Extract the missing file and its directory.
                missing_file = match.groups()[1]
                missing_dir = os.path.dirname(missing_file)
                missing_dirs.add(missing_dir)

                logging.debug("Missing file `%s`" % missing_file)

            missing_dirs = sorted(missing_dirs, reverse=True)
            count = collections.defaultdict(int)
            for path in missing_dirs:
                elements = path.split(os.path.sep)
                if elements[0] == "":
                    elements = elements[1:]

                for i in range(0, len(elements)):
                    count[os.path.sep.join(elements[0:i+1])] += 1

            if len(missing_dirs):
                logging.info("-" * 80)
                logging.info(" There are missing source directories. This is not a fatal error.")
                logging.info(" Use the command line option `-m` to map from the missing paths displayed")
                logging.info(" bellow to the actual path. You can add as many source code maps as you need.")
                logging.info(" If you fail to do this, some source will be missing from the report.")
                logging.info("")
                logging.info(" Example:")
                logging.info("    -m \"build/glibc-OTsEL5/glibc-2.27\" \"/home/user/glibc-2.27\"")
                logging.info("-" * 80)


            missing_dirs = sorted([k for (k, v) in count.iteritems() if v > 1], reverse=True)
            for path in missing_dirs:
                logging.info(" Missing directory `%s`" % path)

        except subprocess.CalledProcessError as identifier:
            if "no valid records" in identifier.output:
                logging.warning("Could not generate a report since the trace file is empty. Maybe the source filter is wrong?")
                return False

            logging.error("Could not execute reporting command: %s" % identifier)
            return False

        return True

    def process_traces(self):
        process_command = [
            self.dr_cov2lcov,
            "-warning", str(self.debug_level),
            "-verbose", str(self.debug_level),
            "-dir", self.traces_dir,
            "-output", self.coverage_info_file
        ]

        if self.src_filter:
            process_command.append("-src_filter")
            process_command.append(self.src_filter)

        try:
            output = subprocess.check_output(process_command)
            logging.debug(output)

        except subprocess.CalledProcessError as identifier:
            logging.error("Could not execute processing command: %s" % identifier)
            return False

        # We need to map some paths here. Supposedly dr has builtin support but it does not work for me.
        contents = open(self.coverage_info_file, "rb").read()
        for replacee, replacement in self.path_maps:
            logging.info("Replacing path `%s` with `%s`." % (replacee, replacement))
            contents = contents.replace(replacee, replacement)

        with open(self.coverage_info_file, "wb") as file:
            file.write(contents)

        return True

def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser(description='Test case coverage collector.')
    parser.add_argument("-p", action="store", dest="dr_path", required=True, help="DynamoRio installation path.")
    parser.add_argument("-o", action="store", dest="output", required=True, help="Output directory that will contain the trace files.")
    parser.add_argument("-d", type=int, default=0, dest="debug_level", help="Set the debug/warning level of dr's tools to a value.")
    parser.add_argument("-f", action="store", dest="src_filter", help="Only include files that match this patter.")
    parser.add_argument("-m", nargs=2, action="append", default=[], dest="src_map", help="Map a source path to another.")

    args = parser.parse_args()

    if not os.path.isdir(args.dr_path):
        logging.error("Path to DynamoRio is not a directory.")
        return -1

    try:
        # Create a report.
        report = CoverageReport(args.dr_path, args.output, args.src_map, args.src_filter, debug_level=args.debug_level)
        if not report.run():
            return -1

    except Exception as error:
        logging.error("Error: %s" % error)
        return -1

    return 0

if __name__ == "__main__":
    main(sys.argv)
