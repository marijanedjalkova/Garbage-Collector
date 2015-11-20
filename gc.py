class GarbageCollector:
	def __init__(self):
		self.heap = []
		self.GENERATION_SIZE = 100
		self.current_moving_index = 0 # this marks where to put the next thing
		self.current_tracing_index = 0 # this shows where we are in the old section
		self.INT = 11
		self.STRING = 12
		self.BOOL = 13
		self.CONS = 14
		self.VECTOR = 15
		self.ARRAY = 16
		self.EXCEPTION = 17
		self.IND = 18
		self.VAR = 19
		self.TRUE = 1
		self.FALSE = 0
		self.NIL = -1
		self.moved_roots = [] # this is for preserving roots when doing gc > once

	"""This is legacy, not needed"""
	def isTag(self, item):
		return item in ["INT", "STRING", "BOOL", "CONS", "VECTOR", "ARRAY", "EXCEPTION", "IND", "VAR", "FWD"]

	def print_status(self, desc):
		print "--------------"
		print desc
		print self.heap
		print self.mapping_table
		print "moving " + str(self.current_moving_index)
		print "tracing " + str(self.current_tracing_index)
		print "________"


	def process_int(self, index):
		# length of the block is 2
		self.moved_roots.append(self.current_moving_index)
		self.heap[self.current_moving_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[self.current_moving_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = self.current_moving_index
		self.current_moving_index += 2		

	def process_string(self, index):
		# this is implemented as a var, i.e. the string object lies in the 
		# mapping table together with its code. 
		# when a string is referenced, check it up in the mapping table and copy.
		# in the mapping table, mark as checked.
		# mention in the report that it actually clears the memory
		string_code = self.heap[index + 1]
		if string_code in self.mapping_table:
			# length of the block is 2
			string_tuple = self.mapping_table.pop(string_code) # returns ("myVar", False)
			self.mapping_table[string_code] = (string_tuple[0], True) # mark as checked
			self.moved_roots.append(self.current_moving_index)
			self.heap[self.current_moving_index] = self.heap[index]
			self.heap[index] = "FWD"
			self.heap[self.current_moving_index + 1] = self.heap[index + 1]
			self.heap[index + 1] = self.current_moving_index
			self.current_moving_index += 2

	def process_bool(self, index):
		self.moved_roots.append(self.current_moving_index)
		self.heap[self.current_moving_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[self.current_moving_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = self.current_moving_index
		self.current_moving_index += 2

	def process_pointer(self, pointer_index, from_index):
		# pointer_index is the value that points onto the original value of the pointer
		# e.g. if we are processing cons 6 3 then by this time the block will have been 
		# copied into new space, and pointer_index is either 6 or 3
		# from_pointer gives index of a heap cell where this object was referenced
		# e.g. if after copying there was a reference to cell 6 in cell 35, 
		# from index is 35
		
		
		tag = self.heap[pointer_index]
		
		
		return self.process_tag(tag, pointer_index, from_index)


	def process_block(self, block_size, overhead, index):
		# this is for common blocks such as cons, arrays, vectors
		# since they have a lot in common
		self.moved_roots.append(self.current_moving_index)
		for i in range(0, block_size):
			self.heap[self.current_moving_index + i] = self.heap[index + i]
			if i == 0:
				self.heap[index + i] = "FWD"
				continue
			if i == 1:
				self.heap[index + i] = self.current_moving_index
				continue
			else:
				self.heap[index + i] = "-"
		
		
		pointers = [self.current_moving_index + k for k in 
			range(overhead, block_size)]
		
		self.current_moving_index += block_size
		# pointers are places in heap new space where old pointers are held.
		for p in pointers:
			new_index = self.current_moving_index
			res = self.process_pointer(self.heap[p], p)
			if res:
				self.heap[p] = new_index


	def process_cons(self, index):
		block_size = 3
		overhead = 1 # overhead size is not pointers - tag, num of elements etc
		self.process_block(block_size, overhead, index)
		

	def process_vector(self, index):
		block_size = self.heap[index + 1] + 2
		overhead = 2 # overhead size is not pointers - tag, num of elements etc
		self.process_block(block_size, overhead, index) 


	def process_array(self, index):
		n = self.heap[index + 1]
		m = 1
		for i in range(0, n):
			m *= self.heap[index + 2 + i]
		block_size = 2 + n + m
		overhead = 2 + n
		self.process_block(block_size, overhead, index)
			

	def process_exception(self, index):
		# exception has a model of EXCEPTION e p, where e is name 
		# and p is pointer. e has to be in the mapping table. Treat as var
		block_size = 3
		overhead = 2
		exception_code = self.heap[index + 1]
		
		if exception_code in self.mapping_table:
			# length of the block is 2
			
			exception_tuple = self.mapping_table.pop(exception_code) # returns ("myVar", False)
			
			self.mapping_table[exception_code] = (exception_tuple[0], True) # mark as checked
			self.moved_roots.append(self.current_moving_index)
			self.heap[self.current_moving_index] = self.heap[index]
			self.heap[index] = "FWD"
			
			self.heap[self.current_moving_index + 1] = self.heap[index + 1]

			self.heap[index + 1] = self.current_moving_index # this is correct

			self.heap[self.current_moving_index + 2] = self.heap[index + 2]
			self.heap[index + 2] = "-"

			# this repeats part of the process_block since we cannot reuse it fully

			p = self.current_moving_index + range(overhead, block_size) 
			# 2 is the only element of the range(overhead, block_size) = range(2, 3)
			# so there is only one p in pointers

			self.current_moving_index += block_size

			new_index = self.current_moving_index
			res = self.process_pointer(self.heap[p], p)
			if res:
				self.heap[p] = new_index



	def process_ind(self, index):
		# go to heap[index + 1] 
		self.process_pointer(self.heap[index+1], index + 1)

	def process_var(self, index):
		# look it up in the mapping table
		# if it is not there, don't do anything? or just copy
		# if it is there, copy
		# remove unused things from the mapping table
		# explain in report that only roots are considered
		var_code = self.heap[index + 1]
		if var_code in self.mapping_table:
			# length of the block is 2
			var_tuple = self.mapping_table.pop(var_code) # returns ("myVar", False)
			self.mapping_table[var_code] = (var_tuple[0], True) # mark as checked
			self.moved_roots.append(self.current_moving_index)
			self.heap[self.current_moving_index] = self.heap[index]
			self.heap[index] = "FWD"
			self.heap[self.current_moving_index + 1] = self.heap[index + 1]
			self.heap[index + 1] = self.current_moving_index
			self.current_moving_index += 2


	def process_fwd(self, index, from_index):
		self.heap[from_index] = self.heap[index + 1]
		

	def process_tag(self, tag, heap_root_index, from_index):
		if tag == self.INT or tag == "INT":
			self.process_int(heap_root_index)
			return True
		if tag == self.STRING or tag == "STRING":
			self.process_string(heap_root_index)
			return True
		if tag == self.BOOL or tag == "BOOL":
			self.process_bool(heap_root_index)
			return True
		if tag == self.CONS or tag == "CONS":
			self.process_cons(heap_root_index)
			return True
		if tag == self.VECTOR or tag == "VECTOR":
			self.process_vector(heap_root_index)
			return True
		if tag == self.ARRAY or tag == "ARRAY":
			self.process_array(heap_root_index)
			return True
		if tag == self.EXCEPTION or tag == "EXCEPTION":
			self.process_exception(heap_root_index)
			return True
		if tag == self.IND or tag == "IND":
			self.process_ind(heap_root_index)
			return True
		if tag == self.VAR or tag == "VAR":
			self.process_var(heap_root_index)
			return True
		if tag == "FWD":
			self.process_fwd(heap_root_index, from_index)
			return False
		print "Error tag"


	def collect_garbage(self):
		for root in self.roots:
			self.process_pointer(root, root)
			
		self.print_status("BEFORE CLEANUP")
		for i in range(0, self.TO):
			self.heap[i] = None
		self.swap_spaces()
		self.roots = self.moved_roots
		self.moved_roots = []
		self.clean_mapping_table()
	

	def swap_spaces(self):
		tmp = self.TO
		self.TO = self.FROM
		self.FROM = tmp
		self.current_moving_index = self.TO


	def initialise_heap(self):
		
		self.heap = []
		self.heap.extend(["EXCEPTION", 101, 3])
		self.heap.extend(["INT", 77])
		
		self.heap.extend(["VAR", 0])

		self.heap.extend(["STRING", 201])

		self.heap.extend(["BOOL", False])
		
		self.heap.extend(["INT", 23])

		#self.heap.extend(["VECTOR", 3, 2, 6, 6])

		#self.heap.extend(["ARRAY", 2, 3, 2, 0, 6, 4, 0, 6, 4])
		
		self.heap.extend(["CONS", 3, 7])
		for i in range(0, 50):
			self.heap.append(None)
		
		self.FROM = 0
		self.TO = 25
		self.current_moving_index = self.TO


	def initialise_roots(self):
		self.roots = []

		self.roots.append(3)

		
		
	def initialise_mapping_table(self):
		self.mapping_table = {}
		self.mapping_table[101] = ("myvar", False)
		self.mapping_table[201] = ("this wonderful string", False)

	def clean_mapping_table(self):
		to_remove = []
		for code in self.mapping_table:
			mapping_tuple = self.mapping_table[code]
			if mapping_tuple[1]==False:
				to_remove.append(code)
			else:
				self.mapping_table.pop(code)
				self.mapping_table[code] = (mapping_tuple[0], False)
		for code in to_remove:
			self.mapping_table.pop(code)


def main():
	gc = GarbageCollector()
	gc.initialise_heap()
	gc.initialise_roots()
	gc.initialise_mapping_table()
	# at this point we have something that has to be garbage collected in the heap
	# and also the current index shows the first empty cell after all the code
	gc.print_status("INITIAL")
	gc.collect_garbage()

	gc.print_status("FINAL1")
	gc.collect_garbage()
	
	gc.print_status("FINAL2")
	gc.collect_garbage()
	
	gc.print_status("FINAL3")
	print "finished execution successfully"


if __name__ == '__main__':
	main()