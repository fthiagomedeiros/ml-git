"""
© Copyright 2020 HP Development Company, L.P.
SPDX-License-Identifier: GPL-2.0-only
"""

from mlgit.config import get_key
from mlgit.utils import ensure_path_exists, yaml_save, yaml_load
from mlgit._metadata import MetadataManager
from mlgit import log
import os
import shutil

class Metadata(MetadataManager):
	def __init__(self, spec, metadatapath, config, repotype="dataset"):
		self.__repotype = repotype
		self._spec = spec
		self.__path = metadatapath
		super(Metadata, self).__init__(config, repotype)

	def tag_exists(self, index_path):
		specfile = os.path.join(index_path, "metadata", self._spec, self._spec + ".spec")
		fullmetadatapath, categories_subpath, metadata = self.full_metadata_path(specfile)
		if metadata is None:
			return False

		# generates a tag to associate to the commit
		tag = self.metadata_tag(metadata)

		# check if tag already exists in the ml-git repository
		tags = self._tag_exists(tag)
		if len(tags) > 0:
			log.error("Metadata: tag [%s] already exists in the ml-git repository" % (tag))
			return True
		return False

	def commit_metadata(self, index_path):
		specfile = os.path.join(index_path, "metadata", self._spec, self._spec + ".spec")
		fullmetadatapath, categories_subpath, metadata = self.full_metadata_path(specfile)
		log.debug("Metadata: metadata path [%s]" % (fullmetadatapath))
		ensure_path_exists(fullmetadatapath)

		ret = self.__commit_manifest(fullmetadatapath, index_path)
		if ret == False:
			log.info("Metadata: no files to commit for [%s]" % (self._spec))
			return None, None

		store = self.__commit_metadata(fullmetadatapath, index_path, metadata)

		# generates a tag to associate to the commit
		tag = self.metadata_tag(metadata)

		# check if tag already exists in the ml-git repository
		tags = self._tag_exists(tag)
		if len(tags) > 0:
			log.error("Metadata: tag [%s] already exists in the ml-git repository" % (tag))
			for t in tags: log.error("\t%s" % (t))
			return None, None

		# generates a commit message
		msg = self.metadata_message(metadata)
		log.info("Metadata: commit message [%s]" % (msg))

		sha = self.commit(categories_subpath, msg)
		self.tag_add(tag)
		return str(tag), str(sha)

	def metadata_subpath(self, metadata):
		sep = os.sep
		path = self.__metadata_spec(metadata, sep)
		log.debug("metadata dataset path: %s" % (path))
		return path

	def full_metadata_path(self, specfile):
		log.debug("Metadata: getting subpath from categories in specfile [%s]" % (specfile))
		metadata = yaml_load(specfile)
		if metadata == {}:
			return None, None, None

		categories_path = self.metadata_subpath(metadata)
		fullmetadatapath = os.path.join(self.__path, categories_path)
		return fullmetadatapath, categories_path, metadata

	def __commit_manifest(self, fullmetadatapath, index_path):
		# Append index/files/MANIFEST.yaml to .ml-git/dataset/metadata/ <categories>/MANIFEST.yaml
		idxpath = os.path.join(index_path, "files", self._spec, "MANIFEST.yaml")
		if os.path.exists(idxpath) == False:
			return False

		fullpath = os.path.join(fullmetadatapath, "MANIFEST.yaml")

		# Check duplicates. Don't add to manifest !
		idxfiles = yaml_load(idxpath)
		manifestfiles = yaml_load(fullpath)
		filterout = {}
		for k in idxfiles:
			if k in manifestfiles:
				filterout[k] = True
				log.info("Objects: file [%s] duplicate of [%s]. filtering out." % (idxfiles[k], manifestfiles[k]))

		log.info("Objects: commit manifest [%s] to ml-git metadata" % (self._spec))
		with open(fullpath, "a") as f:
			for k, v in idxfiles.items():
				if k in filterout: continue
				f.write("%s: %s\n" % (k, v))
		os.unlink(idxpath)

		return True

	def spec_split(self, spec):
		sep = "__"
		return spec.split('__')

	def get_metadata_path(self, tag):
		specs = self.spec_split(tag)
		version = specs[-1]
		specname = specs[-2]
		categories_path = os.sep.join(specs[:-1])
		return os.path.join(self.__path, categories_path)

	def __commit_metadata(self, fullmetadatapath, index_path, metadata):
		idxpath = os.path.join(index_path, "metadata", self._spec)

		log.info("Objects: commit spec [%s] to ml-git metadata" % (self._spec))

		specfile = os.path.join(idxpath, self._spec + ".spec")

		#saves README.md if any
		readme = "README.md"
		src_readme = os.path.join(idxpath, readme)
		dst_readme = os.path.join(fullmetadatapath, readme)
		shutil.copy2(src_readme, dst_readme)

		#saves metadata and commit
		metadata[self.__repotype]["manifest"]["files"] = "MANIFEST.yaml"
		store = metadata[self.__repotype]["manifest"]["store"]
		self.__commit_spec(fullmetadatapath, idxpath, metadata)

		return store

	def __commit_spec(self, fullmetadatapath, idxpath, metadata):
		specfile = self._spec + ".spec"
		specidx = os.path.join(idxpath, specfile)

		#saves yaml metadata specification
		dst_specfile = os.path.join(fullmetadatapath, specfile)
		yaml_save(metadata, dst_specfile)

		return True

	def __metadata_spec(self, metadata, sep):
		repotype = self.__repotype
		cats =  metadata[repotype]["categories"]
		if type(cats) is list:
			categories = sep.join(cats)
		else:
			categories = cats

		# Generate Spec from Dataset Name & Categories
		return sep.join([ categories, metadata[repotype]["name"] ])

	def metadata_tag(self, metadata):
		repotype = self.__repotype

		sep = "__"
		tag = self.__metadata_spec(metadata, sep)

		## add Version
		# TODO: add option to auto-increment version
		tag = sep.join( [ tag, str(metadata[repotype]["version"]) ] )

		log.debug("Metadata: new tag created [%s]" % (tag))
		return tag

	def metadata_message(self, metadata):
		repotype = self.__repotype
		message = self.metadata_subpath(metadata)

		return message
