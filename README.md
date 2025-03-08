# sxscatalog

[![PyPI - Version](https://img.shields.io/pypi/v/sxscatalog.svg)](https://pypi.org/project/sxscatalog)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sxscatalog.svg)](https://pypi.org/project/sxscatalog)

-----

## NOTES

Temporary list of things to do:

* Split sxs.utilities.sxs_directories to keep `read_config`, `write_config`, and `sxs_directory`
  in this package, but keep `sxs_path_to_system_path` and `cached_path` in `sxs`.
* Remove `path_to_invenio` and `invenio_to_path` from `sxs`; import them from `.utilities`.
* Remove all other files present in this package from `sxs`, and re-import them correctly:
  - `metadata/*`
  - `simulations/simulations.py`, `simulations/local.py`
  - `utilities/downloads.py`, `utilities/string_converters.py`, `utilities/sxs_directories.py`, `utilities/sxs_identifiers.py`


## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

```console
python -m pip install sxscatalog
```

## License

`sxscatalog` is distributed under the terms of the
[MIT](https://spdx.org/licenses/MIT.html) license.
