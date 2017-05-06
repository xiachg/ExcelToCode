# -*- coding: utf-8 -*-
import os
from tps import tp0
import util

def type2string(tp):
	if tp == int or tp == tp0.to_int: return "int"
	if tp == long: return "long"
	if tp == float or tp == tp0.to_float: return "float"
	if tp == bool or tp == tp0.to_bool: return "boolean"
	return "String"

BUILTIN_TYPES = set((
	"int", "long", "float", "boolean", "String",
))

INDENTS = [" " * (i * 4) for i in xrange(10)]

class JavaCodeGen(object):

	def __init__(self, module, module_path, output_path):
		super(JavaCodeGen, self).__init__()
		self.content = []

		src_path = os.path.dirname(module_path)
		src_name = os.path.basename(module_path)
		self.class_name = util.to_class_name(src_name)

		self.module = module
		self.output_path = os.path.join(output_path, self.class_name + ".java")

		path = os.path.dirname(self.output_path)
		util.safe_makedirs(path)

	def run(self):
		self.write_line(0, "// 此文件由导表工具自动生成，禁止手动修改。")
		self.write_line()
		
		self.write_line(0, "package com.wolf.shoot.service.excel;")
		self.write_line()

		type_info = getattr(self.module, "JAVA_TYPE_INFO", {})
		removed_fields = getattr(self.module, "HIDDEN_FIELDS", ())
		items = self.collect_members(self.module.CONFIG, type_info, removed_fields)

		self.gen_class(items, 0)

		content = "".join(self.content)

		origin_content = None
		if os.path.exists(self.output_path):
			with open(self.output_path, "r") as f:
				origin_content = f.read()

		if content == origin_content: return

		print self.output_path

		with open(self.output_path, "w") as f:
			f.write(content)

	def write(self, indent, *args):
		assert(type(indent) == int)
		if indent > 0: self.content.append(INDENTS[indent])
		self.content.extend(args)

	def write_line(self, indent = 0, *args):
		assert(type(indent) == int)
		if indent > 0: self.content.append(INDENTS[indent])
		self.content.extend(args)
		self.content.append("\n")

	def collect_members(self, config, type_info, removed_fields):
		items = []
		for info in config:
			text = info[0]
			field = info[1]
			if field in removed_fields: continue

			type = type2string(info[2])
			method = None
			if field in type_info:
				types = type_info[field]
				type = types[0]
				if len(types) > 1: method = types[1]
			items.append([field, text, type, method])

		# 暂不排序。排序的话，与json数组的对应关系就乱了。
		# items.sort(key = lambda item: item[0])
		return items

	def gen_class(self, items, indent):	
		self.write_line(indent, "public class %s {" % self.class_name)
		self.write_line()

		indent += 1
		self.gen_field_list(items, indent)
		#self.gen_contructor(self.class_name, indent)
		#self.gen_init_method(items, indent)
		self.gen_get_set(items, indent)
		indent -= 1

		self.write_line(indent, "};")

	def gen_field_list(self, items, indent):
		for item in items:
			name, comment, type, _ = item

			self.write_line(indent, "private %-10s %-10s // %s" % (type, name + ";", comment))

		self.write_line()

	def gen_get_set(self, items, indent):
		for item in items:
			name, comment, type, _ = item

			java_name = util.to_class_name(name)

			self.write_line(indent, "public %s get%s() {" % (type, java_name))
			self.write_line(indent + 1, "return %s;" % name)
			self.write_line(indent, "}")

			self.write_line(indent, "public void set%s(%s %s) {" % (java_name, type, name))
			self.write_line(indent + 1, "this.%s = %s;" % (name, name))
			self.write_line(indent, "}")

			self.write_line()

		self.write_line()

	def gen_contructor(self, class_name, indent):
		self.write_line(indent, "public %s(JsonObject row) {" % class_name)

		indent += 1
		self.write_line(indent, "init(row);")
		indent -= 1

		self.write_line(indent, "}")
		self.write_line()

	def gen_init_method(self, items, indent):
		self.write_line(indent, "public void init(JsonObject row) {")

		indent += 1
		for i, item in enumerate(items):
			name, comment, type, method = item

			if type in BUILTIN_TYPES:
				self.write_line(indent, "%-10s = (%s)row[%d];" % (name, type, i))
			elif method:
				self.write_line(indent, "%-10s = %s(row[%d]);" % (name, method, i))
			else:
				self.write_line(indent, "%-10s = new %s(row[%d]);" % (name, type, i))

		indent -= 1

		self.write_line(indent, "}")
		self.write_line()