class GarbageCollector:
	def __init__(self):
		self.heap = []
		self.SPACE_SIZE = 30
		self.GENERATION_SIZE = self.SPACE_SIZE * 2
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
		self.promotion_list = [[], [], [], [], []] 
		
	def print_status(self, desc):
		print "--------------"
		print desc
		print self.heap
		print self.promotion_list
		print "________"

	"""finds first empty cell in specified generation"""
	def find_empty(self, gen):
		start = self.GENERATION_SIZE*(gen - 1)
		while self.heap[start] is not None:
			start += 1
		return start

	def simple_copy_2_elements(self, index, to_index):
		self.heap[to_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[to_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = to_index
		to_index += 2
		return to_index

	def process_int(self, index, to_index, isPromotion):
		# length of the block is 2
		if not isPromotion:
			self.moved_roots.append(to_index)
			new_index = self.simple_copy_2_elements(index, to_index)
		else:
			new_gen_index = self.find_empty(2);
			new_index = self.simple_copy_2_elements(index, new_gen_index)
		return new_index


	def process_string(self, index, to_index, isPromotion):
		# this is implemented as a var, i.e. the string object lies in the 
		# mapping table together with its code. 
		# when a string is referenced, check it up in the mapping table and copy.
		# in the mapping table, mark as checked.
		# mention in the report that it actually clears the memory
		if not isPromotion:
			string_code = self.heap[index + 1]
			if string_code in self.mapping_table:
				# length of the block is 2
				string_tuple = self.mapping_table.pop(string_code) # returns ("myVar", False)
				self.mapping_table[string_code] = (string_tuple[0], True) # mark as checked
				self.moved_roots.append(to_index)
				new_index = self.simple_copy_2_elements(index, to_index)
			else:
				return to_index
		else:
			new_gen_index = self.find_empty(2);
			new_index = self.simple_copy_2_elements(index, new_gen_index)
		return new_index

	def process_bool(self, index, to_index, isPromotion):
		if not isPromotion:
			
			self.moved_roots.append(to_index)
			new_index = self.simple_copy_2_elements(index, to_index)
		else:
			new_gen_index = self.find_empty(2);
			new_index = self.simple_copy_2_elements(index, new_gen_index)
		return new_index

	def process_pointer(self, pointer_index, from_index, to_index, isPromotion):
		# pointer_index is the value that points onto the original value of the pointer
		# e.g. if we are processing cons 6 3 then by this time the block will have been 
		# copied into new space, and pointer_index is either 6 or 3
		# from_pointer gives index of a heap cell where this object was referenced
		# e.g. if after copying there was a reference to cell 6 in cell 35, 
		# from index is 35
		#print "pointer index is " + str(pointer_index)
		tag = self.heap[pointer_index]
		if isPromotion:
			print "tag " + str(tag)
		return self.process_tag(tag, pointer_index, from_index, to_index, isPromotion)

	def move_block(self, index, to_index, block_size, overhead, isPromotion):
		# print "moving block of sieze" + str(block_size) + " from index " + str(index) + " to " + str(to_index)
		for i in range(0, block_size):
			# print "will be writing this: " + str(self.heap[index + i]) + "  here: " + str(to_index + i)
			self.heap[to_index + i] = self.heap[index + i]
			if i == 0:
				self.heap[index + i] = "FWD"
				continue
			if i == 1:
				self.heap[index + i] = to_index
				continue
			else:
				self.heap[index + i] = "-"
			
		# self.print_status("just copied")	
		pointers = [to_index + k for k in range(overhead, block_size)]
		
		to_index += block_size
		# pointers are places in heap new space where old pointers are held.
		for p in pointers:
			# print "pointer p: " + str(p)
			new_index = to_index
			
			#print "new index is " + str(new_index) +  " give to pp " + str(self.heap[p]) + " and " + str(p)
			result = self.process_pointer(self.heap[p], p, to_index, isPromotion)
			# print "returned " + str(result)
			res = result[1]
			to_index = result[0]
			
			# self.print_status("after pp")
			if res:
				#print "refer to new position " + str(new_index) + " into " + str(p)
				self.heap[p] = new_index
			# self.print_status("after moving blockling " + str(p))
		# print "returning index " + str(new_index)
		return new_index

	def process_block(self, block_size, overhead, index, to_index, isPromotion):
		# this is for common blocks such as cons, arrays, vectors
		# since they have a lot in common
		if not isPromotion:
			self.moved_roots.append(to_index)
			
			new_index = self.move_block(index, to_index, block_size, overhead, isPromotion)
		else:
			new_gen_index = self.find_empty(2)
			new_index = self.move_block(index, new_gen_index, block_size, overhead, isPromotion)
		return new_index

	def process_cons(self, index, to_index, isPromotion):
		block_size = 3
		overhead = 1 # overhead size is not pointers - tag, num of elements etc
		return self.process_block(block_size, overhead, index, isPromotion)
		

	def process_vector(self, index, to_index, isPromotion):
		# print "processing vector from index " + str(index) + " to index " + str(to_index)
		block_size = self.heap[index + 1] + 2
		overhead = 2 # overhead size is not pointers - tag, num of elements etc
		return self.process_block(block_size, overhead, index, to_index, isPromotion) 
		


	def process_array(self, index, to_index, isPromotion):
		n = self.heap[index + 1]
		m = 1
		for i in range(0, n):
			m *= self.heap[index + 2 + i]
		block_size = 2 + n + m
		overhead = 2 + n
		
		return self.process_block(block_size, overhead, index, to_index, isPromotion)
			
	def move_exception(self, index, to_index, isPromotion):
		self.heap[to_index] = self.heap[index]
		self.heap[index] = "FWD"
		
		self.heap[to_index + 1] = self.heap[index + 1]

		self.heap[index + 1] = to_index # this is correct

		self.heap[to_index + 2] = self.heap[index + 2]
		self.heap[index + 2] = "-"

			# this repeats part of the process_block since we cannot reuse it fully

		p = to_index + 2 
			# 2 is the only element of the range(overhead, block_size) = range(2, 3)
			# so there is only one p in pointers

		to_index += 3

		new_index = to_index
		
		result = self.process_pointer(self.heap[p], p, new_index, isPromotion)
		res = result[1]
		to_index = result[0]
		self.current_moving_index = to_index

		if res:
				self.heap[p] = new_index
		return new_index


	def process_exception(self, index, to_index, isPromotion):
		# exception has a model of EXCEPTION e p, where e is name 
		# and p is pointer. e has to be in the mapping table. Treat as var
		block_size = 3
		overhead = 2
		if not isPromotion:
			
			exception_code = self.heap[index + 1]
			
			if exception_code in self.mapping_table:
				# length of the block is 2
				
				exception_tuple = self.mapping_table.pop(exception_code) # returns ("myVar", False)
				
				self.mapping_table[exception_code] = (exception_tuple[0], True) # mark as checked
				self.moved_roots.append(to_index)
				new_index = self.move_exception(index, to_index, isPromotion)
			else:
				return to_index

		else:
			new_gen_index = self.find_empty(2)
			new_index = self.move_exception(index, new_gen_index, isPromotion)
		return new_index


	def process_ind(self, index, to_index, isPromotion):
		# go to heap[index + 1] 
		return self.process_pointer(self.heap[index+1], index + 1, to_index, isPromotion)

	def process_var(self, index, to_index, isPromotion):
		# look it up in the mapping table
		# if it is not there, don't do anything? or just copy
		# if it is there, copy
		# remove unused things from the mapping table
		# explain in report that only roots are considered
		
		if not isPromotion:
			var_code = self.heap[index + 1]
			
			if var_code in self.mapping_table:
				# length of the block is 2
				var_tuple = self.mapping_table.pop(var_code) # returns ("myVar", False)
				self.mapping_table[var_code] = (var_tuple[0], True) # mark as checked
				self.moved_roots.append(to_index)
				new_index = self.simple_copy_2_elements(index, to_index)
			else:
				return to_index
				
		else:
			new_gen_index = self.find_empty(2);
			new_index = self.simple_copy_2_elements(index, to_index, new_gen_index)
		return new_index
			

	def process_fwd(self, index, from_index, to_index, isPromotion):
		if index != from_index:
			self.heap[from_index] = self.heap[index + 1]


	def update_collection_times(self, heap_root_index, to_index):
		old_pos = -1
		for part in self.promotion_list:
			# for every sub-list
			if heap_root_index in part:
				number_index = part.index(heap_root_index)
				list_number = self.promotion_list.index(part)
				del self.promotion_list[list_number][number_index]
				old_pos = list_number
				break
		if to_index not in self.promotion_list[old_pos + 1]:
			self.promotion_list[old_pos + 1].append(to_index)

			

	def process_tag(self, tag, heap_root_index, from_index, to_index, isPromotion):
		if tag != "FWD" and not isPromotion:
			self.update_collection_times(heap_root_index, to_index)

		if tag == self.INT or tag == "INT":
			new_index = self.process_int(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.STRING or tag == "STRING":
			new_index = self.process_string(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.BOOL or tag == "BOOL":
			new_index = self.process_bool(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.CONS or tag == "CONS":
			new_index = self.process_cons(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.VECTOR or tag == "VECTOR":
			new_index = self.process_vector(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.ARRAY or tag == "ARRAY":
			new_index = self.process_array(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.EXCEPTION or tag == "EXCEPTION":
			new_index = self.process_exception(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.IND or tag == "IND":
			new_index = self.process_ind(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == self.VAR or tag == "VAR":
			new_index = self.process_var(heap_root_index, to_index, isPromotion)
			return (new_index, True)
		if tag == "FWD":
			self.process_fwd(heap_root_index, from_index, to_index, isPromotion)
			return (to_index, False)
		print "Error tag : " + str(tag)

	def promote(self):
		# check what is in the fifth element of the promotion list
		# promote
		# delete from list

		to_promote = self.promotion_list[len(self.promotion_list)-1]
		print " TO PROMOTE"
		print to_promote
		for element in to_promote:
			self.process_pointer(element, element, self.GENERATION_SIZE, True)
		self.promotion_list[len(self.promotion_list)-1] = []
		


	def collect_garbage(self):
		# self.print_status("INITIAL")
		# print self.promotion_list
		for root in self.roots:
			self.process_pointer(root, root, self.current_moving_index, False)
			
		# self.print_status("BEFORE CLEANUP")
		# print self.promotion_list
		cleaning_start = self.FROM	
		cleaning_end = cleaning_start + self.SPACE_SIZE

		for i in range(cleaning_start, cleaning_end):
			self.heap[i] = None

		self.promote()
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
		self.heap.extend(["ARRAY", 2, 3, 2, 0, 5, 3, 0, 5, 3])
		self.heap.extend(["VAR", 101])

		self.heap.extend(["STRING", 201])

		self.heap.extend(["BOOL", False])
		
		self.heap.extend(["INT", 23])

		#self.heap.extend(["VECTOR", 3, 9, 11, 3])

		
		
		self.heap.extend(["CONS", 3, 7])
		for i in range(0, 80):
			self.heap.append(None)
		
		self.FROM = 0
		self.TO = self.FROM + self.SPACE_SIZE
		self.current_moving_index = self.TO
		self.elements = [] # this is for counting how mahy times things survived gc


	def initialise_roots(self):
		self.roots = []
		self.roots.append(5)

		
		
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
	# print "================================================================================="
	gc = GarbageCollector()
	gc.initialise_heap()
	gc.initialise_roots()
	gc.initialise_mapping_table()
	# at this point we have something that has to be garbage collected in the heap
	# and also the current index shows the first empty cell after all the code
	
	gc.collect_garbage()
	gc.print_status("FINAL1")

	gc.collect_garbage()
	gc.print_status("FINAL2")

	gc.collect_garbage()
	gc.print_status("FINAL3")

	gc.collect_garbage()
	gc.print_status("FINAL4")

	gc.collect_garbage()
	gc.print_status("FINAL5")

	print "finished execution successfully"


if __name__ == '__main__':
	main()