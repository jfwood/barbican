#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import sys
sys.path.insert(0, os.getcwd())

from barbican.model.migration.commands import main


main()
