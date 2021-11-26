ydiskarc: a command-line tool to backup public resources from Yandex.disk (disk.yandex.ru / yadi.sk) filestorage service
########################################################################################################################

ydiskarc (pronounced *Ai-disk-arc*) is a command line tool used to backup Yandex.Disk public resources.
Public resources are opnly shared files and folders from Yandex.Disk service.
Yandex provides free-to-use API that allow to download the data.


.. contents::

.. section-numbering::



Main features
=============

* Metadata extraction
* Download any public resource file or directory



Installation
============


Any OS
-------------

A universal installation method (that works on Windows, Mac OS X, Linux, …,
and always provides the latest version) is to use pip:


.. code-block:: bash

    # Make sure we have an up-to-date version of pip and setuptools:
    $ pip install --upgrade pip setuptools

    $ pip install --upgrade ydiskarc


(If ``pip`` installation fails for some reason, you can try
``easy_install ydiskarc`` as a fallback.)


Python version
--------------

Python version 3.6 or greater is required.

Usage
=====


Synopsis:

.. code-block:: bash

    $ ydiskarc [command] [flags]


See also ``python -m ydiskarc`` and ``ydiskarc [command] --help`` for help for each command.



Commands
========

Sync command
----------------
Synchronizes files and metadata from public resource of directory type to the local directory.


Extracts all files and metadata from "https://disk.yandex.ru/d/VVNMYpZtWtST9Q" resource to the dir "mos9maystyle"

.. code-block:: bash

    $ ydiskarc sync --url https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle



Full command
----------------
Downloads single file or directory. Single file downloaded with original file format. Directory downloaded as ZIP file
with all files inside.

Downloads file from url "https://disk.yandex.ru/i/t_pNaarK8UJ-bQ" and saves it into folder "files" with metadata saved as "_metadata.json"

.. code-block:: bash

    $ ydiskarc full --url https://disk.yandex.ru/i/t_pNaarK8UJ-bQ -o files -v -m

