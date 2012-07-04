Firebat-console
===============
.. image:: https://secure.travis-ci.org/greggyNapalm/firebat_console.png?branch=master
   :alt: Build Status
   :target: https://secure.travis-ci.org/greggyNapalm/firebat_console

Console tool designed to make simple test case for Phantom load tool.

Documentation
-------------

More info and documentation can be found at: `<http://firebat-console.readthedocs.org/>`_

Russian documentation is also available: `<http://firebat-console-ru.readthedocs.org/>`_


Installation
------------

Use pip and `vurtualev/virtualenvwrapper <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_

Stable version:

::

    pip install -e git+git://github.com/greggyNapalm/firebat_console.git@production#egg=firebat-console

Development version:

::

    pip install -e git+git://github.com/greggyNapalm/firebat_console.git#egg=firebat-console



Test example
------------

::

    comming soon

Arguments
---------

``-a AMMO_FILE, --ammo AMMO_FILE``
  Path to ammo file, overlaps ``input_file`` config option

``-o , --only-prepare-stpd``
  Only generate ammo stpd and exit

``--list``
  List details of currently running fires(jobs)

``-h, --help``
  Display args list

``--debug``
  Enable verbose logging

``--version``
  Display current version and exit
