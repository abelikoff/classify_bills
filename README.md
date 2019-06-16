# classify_bills

_[Almost] automatically sort and archive PDF bills
and statements._

I get tons of electronic statements each month: from bank statements
to credit cards statements to updated insurance policy documents. I
store all of them - they don't take much space and you never know when
you need to use one of them (I did have a case quite recently, where a
receipt from a bank issued _18 years ago_ had made all the difference,
but that's a story for some other day).

One problem with so many receipts is storing them in a way that helps
finding things fast (or even finding things _at all_). Renaming each
file by hand sticking to some uniform convention and shuffling those
files around gets mind numbingly boring pretty soon.

This is where `classify_bills` script comes handy. It goes over all
newly downloaded bills and does a couple of things:

* It tries to figure out what account each document belongs to.
* It then figures out what date this document should be associated
  with.
* Finally, it names the document according to the set pattern and
  places it in the right directory.


### What `classify_bills` is not

It is not a jack of all trades. It will not download your statements
for you (which is a much more complex task given different websites
hosting those documents). Neither will it OCR those documents that
don't come with text embedded (some places give you a PDF which has no
text at all).

It is also not really intelligent. At its core, it is driven by a list
of regular expressions.

Still, given the number of bills I get monthly, over the last couple
years, it has saved me probably _hours_ of menial, incredibly boring
work, so I do consider it a win.


## Installation

Install using `pip`:

```shell
pip install classify_bills
```

Once installed, `classify_bills` should be available in your path.

When using the saource code directly or from GitHub, use
`run_classify_bills` shell driver that will invoke the Python code
properly.

Currently, the `classify_bills` has the following external
dependencies:

* Python 3.x
* `pdftotext` program (usually comes as part of `poppler` package.)


## Configuration

`classify_bills` is configured via a set of XML files, where each file
defines a setup for a specific bill type. Those files should be placed
in a configuration directory, which could be specified one of the
following ways:

* Via `-c` command line option.
* Via an environment variable `$CLASSIFY_BILLS_CONFIG_DIRECTORY`
* Using a default location `~/.classify_bills.conf.d`

Each file defines patterns that might be present in the bill's text in
order to be considered for this account. A pattern to match bill date
also must be specified (and must be matched) as well as a pattern to
extract the date (via `strptime()`).

The package directory `classify_bills.config.examples` contains
several examples. In particular, see `0-Example.xml` in that
directory, which describes all aspects of configuration.


## Creating new configuration files

In general, a process of adding support for a new kind of bill works
the following way:

* Use `pdftotext` to examine text output of a couple bills for a given
  account to determine the following:
  * Patterns in the text that could be used to _uniquely identify this
    kind of bill_ (name of a bank or service provider, URLs,
    etc). It's beter to have several specific patterns to allow future
    disambiguation between multiple accounts from the same provider
    (e.g. separate banking and investment bills from the same bank).
  * Pattern that could be used to infer the date this bill should be
    associated with.
  * Format of that date.
* Create a new XML file (use `0-Example.xml` as a boilerplate).

This process is unfortunately not easy to automate so it has to be
done manually and it is a pain. However, it only has to be done once
per each account (that is, until the provider decides to change the
format of the bill thus breaking the patterns, but it also doesn't
happen often).


## Using `classify_bills`

Running `classify_bills` is fairly simple. You can pass either
individual PDF files or directories as command-line arguments. By
default, it runs in dry-run mode, not making any changes. To actually
perform all actions, run it with `-f` flag.

Files that have been successfully detected are moved to the hierarchy
under the output directory (which is specified either with `-o` flag
or via an environment variable `$CLASSIFY_BILLS_OUTPUT_DIRECTORY`. The
script will never overwrite any existing document in the destination
directory (unless it is forced to via `-w` flag).


## Future work

Currently, the most painful aspect of using the tool is manual
configuration of patterns for each bill type. There are several ideas
on how to try to make it easier: from finding and parsing all dates in
the bill to using neural networks to infer those facts from the
bill. This might be an interesting direction for future work.


# Contributing

You are welcome to contribute to this project either by submitting
bill configuration for different institutions or by improving the
code and adding features. :-)
