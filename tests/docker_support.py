"""Skip tests that execute real containers when no Docker CLI is reachable (e.g. the local test container)."""
import shutil
import unittest

requires_docker = unittest.skipUnless(shutil.which('docker'), 'needs Docker and the pinned sandbox image; run on the rig')
