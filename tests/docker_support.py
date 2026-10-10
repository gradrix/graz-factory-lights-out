"""Skip tests that execute real containers when no Docker CLI is reachable (e.g. the local test container)."""
import shutil
import unittest

requires_docker = unittest.skipUnless(shutil.which('docker'), 'needs a Docker CLI (and on the rig, the pinned sandbox image); run make rig-check')
