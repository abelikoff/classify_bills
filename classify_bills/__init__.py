#!/usr/bin/env python3

"""Tool to classify and sort downloaded bills.
"""


import calendar
import datetime
import glob
import re
import os
import os.path
import logging
import shutil
import subprocess
import sys
import time
from optparse import OptionParser
import xml.etree.ElementTree as ET

if not "CLASSIFY_BILLS_DISABLE_COLOR" in os.environ:
    from classify_bills import colorlogger


class BillConfiguration:      # pylint: disable=too-many-instance-attributes
    """Configuration for a specific bill type."""

    now = datetime.datetime.now()


    def __init__(self):
        self.account_name = None
        self.output_subdirectory = None
        self.output_template = None
        self.match_patterns = []
        self.date_pattern = None
        self.date_format = None
        self.adjust_month_back = False
        self.year_pattern = None


    def match(self, text, filename):
        """Match text contents against bill configuration.

        Returns

            Date - bill date.
            None - not matched.
        """

        for pattern in self.match_patterns:
            if not re.search(pattern, text):
                return None

        logging.debug("%s: match successful for account '%s'",
                      filename, self.account_name)


        # extract date

        match = re.search(self.date_pattern, text, re.IGNORECASE | re.DOTALL)

        if not match:
            logging.debug("%s: date string not found", filename)
            return None

        datestr = match.group(1)
        logging.debug("%s: date matched for account '%s': '%s'",
                      filename, self.account_name, datestr)

        try:
            parsed_date = list(time.strptime(datestr, self.date_format))
        except ValueError:
            # pylint: disable=logging-not-lazy
            logging.error("%s: failed to parse date string '%s' using " +
                          "format '%s'", filename, datestr, self.date_format)
            return None


        # There are 3 cases for the year
        # 1. Dates are listed without year (mm/dd). If we can extract year
        #    separately, we do it, otherwise we default to current year.
        # 2. Dates have short year (mm/dd/yy).
        # 3. Dates have full year.

        if parsed_date[0] < 100:
            parsed_date[0] += 2000

        elif parsed_date[0] == 1900:
            if self.year_pattern:
                match = re.search(self.year_pattern, text)

                if match:
                    parsed_date[0] = int(match.group(1))

                    if parsed_date[0] < 100:
                        parsed_date[0] += 2000

                    logging.debug("%s: year matched: '%d'",
                                  filename, parsed_date[0])
            else:
                parsed_date[0] = BillConfiguration.now.year
                logging.debug("%s: year implied: '%d'",
                              filename, parsed_date[0])

        bill_date = datetime.datetime.fromtimestamp(time.mktime(
            tuple(parsed_date)))

        # adjust bill date 1 month back (if requested)

        if self.adjust_month_back:
            month = bill_date.month - 2
            year = bill_date.year + month // 12
            month = month % 12 + 1
            day = min(bill_date.day, calendar.monthrange(year, month)[1])
            bill_date = datetime.datetime(year, month, day)

        logging.debug("%s: bill date: %s", filename, str(bill_date.date()))
        return bill_date


    def from_json_config(self, acct):
        """Set configuration based on old-style JSON config."""

        self.account_name = acct["name"]

        for pattern in acct["matches-all"]:
            self.match_patterns.append(pattern)

        self.date_pattern = acct["date-extractor"]["regexp"]
        self.date_format = acct["date-extractor"]["format"]

        if "year-extractor-regexp" in acct["date-extractor"]:
            self.year_pattern = acct["date-extractor"]["year-extractor-regexp"]

        if "adjust-month-back" in acct["date-extractor"]:
            self.adjust_month_back = True


    def load(self, filename):
        """Load configuration from XML file."""

        self.__init__()

        tree = ET.parse(filename)
        root = tree.getroot()

        if not "id" in root.attrib:
            raise Exception("no id specified")

        self.account_name = root.attrib["id"]
        naming = root.find("./naming")

        if naming is not None:
            self.output_subdirectory = naming.attrib.get("subdirectory")
            self.output_template = naming.attrib.get("template")

        for pattern in root.findall("./match-all/pattern"):
            regex = pattern.attrib["regex"]

            if regex:
                self.match_patterns.append(regex)

        if not self.match_patterns:
            raise Exception("%s: malformed or missing match patterns" %
                            filename)

        date_extractor = root.find("./date-extraction")

        if date_extractor is None:
            raise Exception("%s: date extraction information is missing" %
                            filename)

        self.date_pattern = date_extractor.attrib.get("regex")
        self.date_format = date_extractor.attrib.get("parsing-format")
        self.year_pattern = date_extractor.attrib.get("year-regex")

        if date_extractor.attrib.get("adjust-month-back"):
            self.adjust_month_back = True


    def write_xml(self, output_file):
        """Write configuration as XML file."""

        with open(output_file, "wt") as fout:
            fout.write("<account id=\"%s\">\n" % self.account_name)

            if self.output_subdirectory or self.output_template:
                fout.write("    <naming ")

                if self.output_subdirectory:
                    fout.write("subdirectory=\"%s\" " %
                               self.output_subdirectory)

                if self.output_template:
                    fout.write("template=\"%s\" " %
                               self.output_template)

                fout.write("/>\n")

            fout.write("    <match-all>\n")

            for pattern in self.match_patterns:
                fout.write("        <pattern regex=\"%s\" />\n" % pattern)

            fout.write("    </match-all>\n")
            fout.write("    <date-extraction regex=\"%s\"\n" %
                       self.date_pattern)
            fout.write("                     parsing-format=\"%s\"" %
                       self.date_format)

            if self.adjust_month_back:
                fout.write(" adjust-month-back=\"true\"")

            if self.year_pattern:
                fout.write(" year-regex=\"%s\"" %
                           self.year_pattern)

            fout.write(" />\n")
            fout.write("</account>\n")



usage_string = """Usage:  %prog [options]
        %prog [options] <file(s)>

%prog processes all PDF documents in a specified directory and
attempts to identify bills and sort them out in to the destination
directory using uniform naming. The rules by which bills are
identified and named are specified in the configuration file.

"""

prog = os.path.basename(sys.argv[0])
program_version = 1.0
version_string = "%%prog  %s" % program_version


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def main():

    """Main function."""

    # parse command-line options

    parser = OptionParser(usage=usage_string, version=version_string)
    parser.add_option("-c", "--config-dir",
                      help="Directory holding configuration files",
                      dest="config_dir", metavar="DIR")
    parser.add_option("-O", "--output-dir", help="Output directory to use",
                      dest="output_dir", metavar="DIR")
    parser.add_option("-f", "--force",
                      help="perform actions (as opposed to dry run)",
                      action="store_true", dest="do_things")
    parser.add_option("-w", "--overwrite",
                      help="overwrite if destination file exists",
                      action="store_true", dest="overwrite")
    parser.add_option("-i", "--ignore-errors", help="ignore errors",
                      action="store_true", dest="ignore_errors")
    parser.add_option("-e", "--only-errors", help="only show errors",
                      action="store_true", dest="only_errors")
    parser.add_option("-v", "--verbose", help="verbose operation",
                      action="store_true", dest="verbose_mode")

    (options, args) = parser.parse_args()
    logging.basicConfig(format="%(levelname)s: %(message)s")

    if options.verbose_mode:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


    # basic checks

    if options.only_errors and (options.do_things or options.ignore_errors):
        logging.fatal("Conflicting options passed")
        sys.exit(1)


    # figure out config directory

    config_dir = options.config_dir

    if not config_dir:
        config_dir = os.environ.get("CLASSIFY_BILLS_CONFIG_DIRECTORY", None)

    if not config_dir:
        config_dir = "~/.classify_bills.conf.d"

    config_dir = os.path.expanduser(config_dir)

    if not os.path.isdir(config_dir):
        logging.fatal("Configuration directory '%s' does not exist.",
                      config_dir)
        sys.exit(1)


    # list of files to process

    file_list = []

    for arg in args:
        if os.path.isfile(arg):
            file_list.append(arg)

        elif os.path.isdir(arg):
            file_list += [os.path.join(arg, x) for x in os.listdir(arg)]

    file_list = [filename for filename in file_list
                 if (filename.endswith(".pdf") or filename.endswith(".PDF"))]

    if not file_list:
        logging.fatal("No files to process")
        sys.exit(1)


    # output directory

    dst_dir = options.output_dir

    if not dst_dir:
        dst_dir = os.environ.get("CLASSIFY_BILLS_OUTPUT_DIRECTORY", None)

    if not dst_dir:
        logging.fatal("Destination directory not specified")
        sys.exit(1)

    dst_dir = os.path.expanduser(options.output_dir)

    if not os.path.isdir(dst_dir):
        logging.fatal("Destination directory '%s' does not exist.", dst_dir)
        sys.exit(1)


    # load bill configs

    bill_config_files = sorted(glob.glob(os.path.join(config_dir, "*.xml")))

    if not bill_config_files:
        logging.error("Directory '%s' contains no config files.", config_dir)
        sys.exit(1)

    all_bill_configs = []

    for filename in bill_config_files:
        bill_config = BillConfiguration()

        try:
            bill_config.load(filename)
            all_bill_configs.append(bill_config)
        except ET.ParseError as ex:
            logging.error("Failed to load file %s: %s", filename, ex)


    # process each bill

    dirs_created = {}
    devnull = open(os.devnull, "wb")

    for fname in file_list:
        short_fname = os.path.basename(fname)
        processed = False

        try:
            process = subprocess.Popen(["pdftotext", fname, "-"],
                                       stdout=subprocess.PIPE,
                                       stderr=devnull)
            (text, _) = process.communicate()
            text = text.decode("utf-8")

        except OSError:
            logging.fatal("Error running pdftotext (not installed?)")
            sys.exit(1)

        if process.returncode != 0:
            if not options.ignore_errors:
                logging.error("Failed to extract text from file '%s'",
                              short_fname)
            continue

        for bill_config in all_bill_configs:
            bill_date = bill_config.match(text, short_fname)

            if not bill_date:
                continue

            out_dir = os.path.join(dst_dir, str(bill_date.year))

            if bill_config.output_subdirectory:
                out_dir = os.path.join(out_dir, bill_config.output_subdirectory)
            else:
                out_dir = os.path.join(out_dir, bill_config.account_name)

            if os.path.exists(out_dir):
                if not os.path.isdir(out_dir):
                    logging.error("Destination %s is not a directory")
                    continue

            else:
                if options.do_things:
                    os.makedirs(out_dir)
                elif out_dir not in dirs_created:
                    logging.info("WILL MKDIR '%s'", out_dir)
                    dirs_created[dst_dir] = True

            if bill_config.output_template:
                tmpl = bill_config.output_template
            else:
                tmpl = bill_config.account_name + " %Y-%m.pdf"

            quarter = ((bill_date.month - 1) / 3) + 1
            tmpl = tmpl.replace("%Q", "Q%d" % quarter, 1)
            out_fname = os.path.join(out_dir, bill_date.strftime(tmpl))
            logging.debug("%s: will be moved to %s", short_fname, out_fname)

            if options.do_things:
                if os.path.isfile(out_fname) and not options.overwrite:
                    # pylint: disable=logging-not-lazy
                    logging.warning("not moving %s -> %s (destination file " +
                                    "exists)", fname, out_fname)
                else:
                    logging.info("moving '%s'  ->  '%s'", fname, out_fname)
                    shutil.move(fname, out_fname)
            else:
                logging.info("WILL MOVE '%s'  ->  '%s'", fname, out_fname)

            processed = True
            break

        if not processed and not options.ignore_errors:
            logging.error("Failed to categorize %s", short_fname)


    sys.exit()


if __name__ == "__main__":
    main()

# Local Variables:
# compile-command: "pylint -r n __init__.py"
# end:
