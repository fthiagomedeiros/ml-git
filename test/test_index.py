"""
© Copyright 2020 HP Development Company, L.P.
SPDX-License-Identifier: GPL-2.0-only
"""

from mlgit.index import MultihashIndex
from mlgit.utils import yaml_load, yaml_save
import unittest
import tempfile
import os

singlefile = {
	"manifest" : {"zdj7WgHSKJkoJST5GWGgS53ARqV7oqMGYVvWzEWku3MBfnQ9u": {"think-hires.jpg"}},
	"datastore" : "zdj7WgHSKJkoJST5GWGgS53ARqV7oqMGYVvWzEWku3MBfnQ9u"
}
secondfile = {
	"manifest" : {"zdj7WemKEtQMVL81UU6PSuYaoxvBQ6CiUMq1fMvoXBhPUsCK2": {"image.jpg"},
					"zdj7WgHSKJkoJST5GWGgS53ARqV7oqMGYVvWzEWku3MBfnQ9u": {"think-hires.jpg"}},
	"datastore" : "zdj7WemKEtQMVL81UU6PSuYaoxvBQ6CiUMq1fMvoXBhPUsCK2"
}
class IndexTestCases(unittest.TestCase):
	def test_add(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			idx = MultihashIndex("dataset-spec", tmpdir)
			idx.add("data", "")

			mf = os.path.join(tmpdir, "metadata", "dataset-spec", "MANIFEST.yaml")
			self.assertEqual(yaml_load(mf), singlefile["manifest"])
			with open(os.path.join(tmpdir, "hashfs", "log", "store.log")) as f:
				self.assertEqual(f.readline().strip(), singlefile["datastore"])

	def test_add_idmpotent(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			idx = MultihashIndex("dataset-spec", tmpdir)
			idx.add("data", "")
			idx.add("data", "")

			mf = os.path.join(tmpdir, "metadata", "dataset-spec", "MANIFEST.yaml")
			self.assertEqual(yaml_load(mf), singlefile["manifest"])

	def test_add2(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			idx = MultihashIndex("dataset-spec", tmpdir)
			idx.add("data", "")

			mf = os.path.join(tmpdir, "metadata", "dataset-spec", "MANIFEST.yaml")
			self.assertEqual(yaml_load(mf), singlefile["manifest"])
			with open(os.path.join(tmpdir, "hashfs", "log", "store.log")) as f:
				self.assertEqual(f.readline().strip(), singlefile["datastore"])

			idx.add("data2", "")
			self.assertEqual(yaml_load(mf), secondfile["manifest"])
			with open(os.path.join(tmpdir, "hashfs", "log", "store.log")) as f:
				for i in range(22): f.readline()
				self.assertEqual(f.readline().strip(), secondfile["datastore"])

	def test_add_manifest(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			manifestfile = os.path.join(tmpdir, "MANIFEST.yaml")
			yaml_save(singlefile["manifest"], manifestfile)

			idx = MultihashIndex("dataset-spec", tmpdir)
			idx.add("data", manifestfile)

			self.assertFalse(os.path.exists(os.path.join(tmpdir, "files", "dataset-spec", "MANIFEST.yaml")))

	# def test_get(self):
	# 	with tempfile.TemporaryDirectory() as tmpdir:
	# 		idx = MultihashIndex("dataset-spec", tmpdir)
	# 		idx.add("data", "")
	#
	# 		tmpfile = os.path.join("")
	# 		idx.get()


if __name__ == "__main__":
	unittest.main()