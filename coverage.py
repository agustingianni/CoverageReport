#!/usr/bin/env python

import os
import sys
import logging
import argparse
import subprocess

class CoverageCollector(object):
    def __init__(self, dr_path, output, debug_level=0):
        # Tools path.
        self.dr_run = os.path.join(dr_path, "bin64", "drrun")
        self.dr_cov2lcov = os.path.join(dr_path, "tools", "bin64", "drcov2lcov")

        # Create the working directory structure.
        self.output_dir = os.path.abspath(output)
        self.traces_dir = os.path.join(self.output_dir, "traces")

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        if not os.path.exists(self.traces_dir):
            os.makedirs(self.traces_dir)

        self.debug_level = debug_level

        logging.info("Working directory `%s`" % self.output_dir)
        logging.info("Traces directory `%s`" % self.traces_dir)

    def run(self, command, samples):
        # Get the absolute path.
        samples = os.path.abspath(samples)
        if not os.path.isdir(samples):
            logging.error("The supplied path `%s` is not a directory." % samples)
            return False

        logging.info("Running test cases from `%s`." % samples)

        # Create a list with all the regular files inside the directory.
        test_cases = os.listdir(samples)
        test_cases = map(lambda filename: os.path.join(samples, filename), test_cases)
        test_cases = filter(lambda filepath: os.path.isfile(filepath), test_cases)

        # No test cases to try.
        if not len(test_cases):
            logging.error("Test case directory is empty.")
            return False

        # For each of the files, run the code coverage program.
        for test_case in test_cases:
            logging.info("Running coverage analysis for file `%s`" % os.path.basename(test_case))
            if not self.run_test_case(command, test_case):
                logging.error("Could not execute test case `%s`" % os.path.basename(test_case))
                return False

        return True

    def run_test_case(self, command, test_case_path):
        trace_command = [
            self.dr_run,
            "-t", "drcov",
            "-logdir", self.traces_dir,
            "--"
        ]

        # Push all the arguments and replace `%TESTCASE%` with the path to the current test case.
        for element in command:
            if element == "%TESTCASE%":
                element = test_case_path

            trace_command.append(element)

        try:
            output = subprocess.check_output(trace_command)
            logging.debug(output)

        except Exception as identifier:
            logging.error("Could not execute tracing command: %s" % identifier)
            return False

        return True


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser(description='Test case coverage collector.')
    parser.add_argument("-p", action="store", dest="dr_path", required=True, help="DynamoRio installation path.")
    parser.add_argument("-o", action="store", dest="output", required=True, help="Output directory that will contain the trace files.")
    parser.add_argument("-d", type=int, default=0, dest="debug_level", help="Set the debug/warning level of dr's tools to a value.")
    parser.add_argument("-s", action="store", dest="samples", required=True, help="Directory containing file samples.")
    parser.add_argument("command", nargs="+", help="Command to trace. Use %%TESTCASE%% as a placeholder for the current test file.")

    args = parser.parse_args()

    if not os.path.isdir(args.dr_path):
        logging.error("Path to DynamoRio is not a directory.")
        return -1

    try:
        # Collect coverage information.
        coverage = CoverageCollector(args.dr_path, args.output, debug_level=args.debug_level)
        if not coverage.run(args.command, args.samples):
            return -1

    except Exception as error:
        logging.error("Error: %s" % error)
        return -1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
