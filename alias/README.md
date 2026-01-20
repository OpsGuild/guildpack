# Guildpack

**This is an alias package for [oguild](https://pypi.org/project/oguild/).**

## Installation

```bash
pip install guildpack
```

This will automatically install `oguild` as a dependency.

## Usage

You can import directly from `guildpack`:

```python
from guildpack import Logger, Ok, Error

# Or use oguild directly (recommended)
from oguild import Logger, Ok, Error
```

## Documentation

For full documentation, see the [oguild repository](https://github.com/OpsGuild/guildpack).

## Why Two Package Names?

- **oguild** - The primary package name
- **guildpack** - An alternative name for easier discovery

Both packages provide the same functionality. Installing either one will give you access to all OGuild utilities.
