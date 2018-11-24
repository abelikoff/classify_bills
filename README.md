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

The script `classify_bills` is pretty self-contained and can be placed
anywhere. If `colorlogger.py` is located anywhere where Python can
load it from (current directory, symlink destination, `$PYTHONPATH`),
it will be loaded and output would be colorized.

The script is driven by the configuration file, which is searched in
the following order:

* `./.classify_bills.conf`
* `./classify_bills.conf`
* `~/.classify_bills.conf`
* `/etc/classify_bills.conf`

Currently, the script has the following external dependencies:

* Python 3.x
* `pdftotext` program (usually comes as part of `poppler` package.)



## Configuration

Use `classify_bills.conf.example` to build your own configuration. In
general, a process of adding support for a new kind of bill works the
following way:

* Create a new entry in the `accounts` array.
* Configure the destination directory and naming convention for bills.
* Use `pdftotext` to examine text output of a couple bills to find out
  the following facts:
  * Patterns in the text that could be used to _uniquely identify this
    kind of bill_ (name of a bank or service provider, URLs,
    etc). It's beter to have several specific patterns to allow future
    disambiguation between multiple accounts from the same provider
    (e.g. separate banking and investment bills from the same bank).
  * Pattern that could be used to infer the date this bill should be
    associated with.
  * Format of that date.

This process is unfortunately not easy to automate so it has to be
done manually and it is a pain. However, it only has to be done once
per each account (that is, until the provider decides to change the
format of the bill thus breaking the patterns, but it also doesn't
happen often).


## Using `classify_bills`

Running `classify_bills` is fairly simple. It can be run either on the
entire directory of input documents (configured via `source-directory`
in the config file), or documents can be explicitly specified in the
command line. By default, the script runs in dry-run mode, not making
any changes. To actually perform all actions, run it with `-f` flag.

The script will never overwrite any existing document in the
destination directory (unless it is forced to via `-w` flag).


## Future work

From the overall design point, it is clear that the decision to use
JSON as configuration language was not an optimal one. In retrospect,
I should've let the configuration be split into individual files, most
probably using XML. If I change it in the future, I'll supply a
conversion tool. That would also allow individually contributed
configurations to be shared.

Furthermore, the most painful aspect of using the tool is manual
configuration of patterns for each bill type. There are several ideas
on how to try to make it easier: from finding and parsing all dates in
the bill to using neural networks to infer those facts from the
bill. This might be an interesting direction for future work.
