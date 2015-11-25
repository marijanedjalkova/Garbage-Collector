class GarbageCollector:
	def __init__(self):
		self.heap = []
		self.SPACE_SIZE = 30
		self.GENERATION_SIZE = self.SPACE_SIZE * 2
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
		self.moved_roots = [] 
		# this is for preserving roots when doing gc > once
		# moved_roots works in a similar way to the whole two-space collection as a whole
		self.promotion_list = [[], [], [], [], []] 
		# this is for tracking amount of gcs an element survived
		
	"""Helper function that prints the current state of the class"""
	def print_status(self, desc):
		print "--------------"
		print desc.upper()
		print "Space 1: "
		print self.heap[:self.SPACE_SIZE]
		print "Space 2: "
		print self.heap[self.SPACE_SIZE:self.GENERATION_SIZE]
		print "Old generation: "
		print self.heap[self.GENERATION_SIZE:]
		print self.promotion_list
		print "______________"

	""" Moves simple 2-cell structures such as integers and booleans """
	def simple_copy_2_elements(self, index, to_index):
		self.heap[to_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[to_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = to_index
		to_index += 2
		return to_index

	""" Collects an integer """
	def process_int(self, index, to_index, isPromotion):
		# length of the block is 2
		if not isPromotion:
			self.moved_roots.append(to_index)
		return self.simple_copy_2_elements(index, to_index)

	""" Collects a string by checking its existence in the mapping table
	and excavating it if it exists in the mapping table """
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
				return self.simple_copy_2_elements(index, to_index)
			else:
				return to_index
		return self.simple_copy_2_elements(index, to_index)


	""" Excavates a boolean object """
	def process_bool(self, index, to_index, isPromotion):
		if not isPromotion:
			self.moved_roots.append(to_index)
		return self.simple_copy_2_elements(index, to_index)

	""" Processes a pointer by following its direction and processing
	the corresponding element"""
	def process_pointer(self, pointer_index, from_index, to_index, isPromotion):
		# pointer_index is the value that points onto the original value of the pointer
		# e.g. if we are processing cons 6 3 then by this time the block will have been 
		# copied into new space, and pointer_index is either 6 or 3
		# from_pointer gives index of a heap cell where this object was referenced
		# e.g. if after copying there was a reference to cell 6 in cell 35, 
		# from index is 35
		tag = self.heap[pointer_index]
		return self.process_tag(tag, pointer_index, from_index, to_index, isPromotion)


	""" Excavates a given block of heap """
	def move_block(self, index, to_index, block_size, overhead, isPromotion):
		# by block we mean complex structures such as arrays, lists and vectors
		# every such block consists of a tag, pointers and values between the tag
		# and the pointers. For example, it can be the length of the vector or amount
		# of dimensions and length of each dimension for an array
		# Those values, plus the tag, make the overhead. Overhead and the pointers 
		# make the whole object. To excavate such a block, can copy the overhead 
		# and then process each pointer by following the algorithm of excavation
		# If we are promoting, then the pointers do not have to be processed, but simply copied
		for i in range(0, block_size):
				self.heap[to_index + i] = self.heap[index + i]
				if i == 0:
					self.heap[index + i] = "FWD"
					continue
				if i == 1:
					self.heap[index + i] = to_index
					continue
				else:
					self.heap[index + i] = "-"

		if not isPromotion:
			pointers = [to_index + k for k in range(overhead, block_size)]
			# pointers are places in heap new space where old pointers are held.
			to_index += block_size
			for p in pointers:
				new_index = to_index
				result = self.process_pointer(self.heap[p], p, to_index, isPromotion)
				res = result[1]
				to_index = result[0]
				if res:
					self.heap[p] = new_index
			new_index = to_index
		else:
			to_index += block_size
			new_index = to_index
		return new_index


	""" Moves a block described above """
	def process_block(self, block_size, overhead, index, to_index, isPromotion):
		if not isPromotion:
			self.moved_roots.append(to_index)
		return self.move_block(index, to_index, block_size, overhead, isPromotion)
		

	""" Processes a CONS p1 p2"""
	def process_cons(self, index, to_index, isPromotion):
		block_size = 3
		overhead = 1
		return self.process_block(block_size, overhead, index, to_index, isPromotion)
		
	""" Processes a VECTOR n p1..pn"""
	def process_vector(self, index, to_index, isPromotion):
		block_size = self.heap[index + 1] + 2
		overhead = 2
		return self.process_block(block_size, overhead, index, to_index, isPromotion) 
		

	""" Processes an ARRAY n d1..dn p1..pm"""
	def process_array(self, index, to_index, isPromotion):
		n = self.heap[index + 1]
		m = 1
		for i in range(0, n):
			m *= self.heap[index + 2 + i]
		block_size = 2 + n + m
		overhead = 2 + n
		result = self.process_block(block_size, overhead, index, to_index, isPromotion)
		return result
			
	""" Moves a block for EXCEPTION e p"""
	def move_exception(self, index, to_index, isPromotion):
		self.heap[to_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[to_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = to_index 
		self.heap[to_index + 2] = self.heap[index + 2]
		self.heap[index + 2] = "-"

		if not isPromotion:
			# this repeats part of the process_block since we cannot reuse it fully
			p = to_index + 2 
				# 2 is the only element of the range(overhead, block_size) = range(2, 3)
				# so there is only one p in pointers
			to_index += 3
			new_index = to_index		
			result = self.process_pointer(self.heap[p], p, new_index, isPromotion)
			res = result[1]
			to_index = result[0]
			new_index = to_index
			if res:
					self.heap[p] = new_index
		else:
			new_index = to_index + 3	
		return new_index

	""" Processes an EXCEPTION e p"""
	def process_exception(self, index, to_index, isPromotion):
		# exception has a model of EXCEPTION e p, where e is name 
		# and p is pointer. e has to be in the mapping table. Treat as var
		block_size = 3
		overhead = 2
		if not isPromotion:
			exception_code = self.heap[index + 1]
			if exception_code in self.mapping_table:
				# take the old value from the mapping table
				exception_tuple = self.mapping_table.pop(exception_code) 
				# put back the value marked with True
				self.mapping_table[exception_code] = (exception_tuple[0], True) 
				self.moved_roots.append(to_index)
				new_index = self.move_exception(index, to_index, isPromotion)
			else:
				return to_index
		else:
			new_index = self.move_exception(index, to_index, isPromotion)
		return new_index

	""" Processes an indirection by processing the location that it points at. """
	def process_ind(self, index, to_index, isPromotion):
		# go to heap[index + 1]. Thus, INDs collapse
		return self.process_pointer(self.heap[index+1], index + 1, to_index, isPromotion)

	""" Processes a VAR e """
	def process_var(self, index, to_index, isPromotion):
		# looks it up in the mapping table
		# if it is not there, don't do anything
		# if it is there, copy it 
		if not isPromotion:
			var_code = self.heap[index + 1]
			if var_code in self.mapping_table:
				# length of the block is 2
				var_tuple = self.mapping_table.pop(var_code) # returns ("myVar", False)
				self.mapping_table[var_code] = (var_tuple[0], True) # mark as checked
				self.moved_roots.append(to_index)
				return self.simple_copy_2_elements(index, to_index)
			else:
				return to_index	
		return self.simple_copy_2_elements(index, to_index)

	""" Processes the FWD note which is left for later reference"""
	def process_fwd(self, index, from_index, to_index, isPromotion):
		if index != from_index:
			self.heap[from_index] = self.heap[index + 1]

	""" Updates the promotion list for one element"""
	def update_collection_times(self, heap_root_index, to_index):
		# Finds it in the current list, and replaces it into the next subsection
		# If the element has never been seen before, places it into the first section
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

	""" Recognizes the tag and calles the corresponding function for a tag """		
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
		print "Error tag : " + str(tag) + " at index " + str(heap_root_index)

	""" Removes the old reference notes from the specific area """
	def clearFWDs(self, start_index, end_index):
		position = start_index
		while position < end_index:
			if self.heap[position] == "FWD":
				self.heap[position] = None
				self.heap[position + 1] = None
				if self.heap[position + 2] == "-":
					i = 0
					while self.heap[position + 2 + i] == "-":
						self.heap[position + 2 + i] = None
						i += 1
			else:
				position += 1

	""" For a certain element, update its index in the promotion list
	This is necessary to keep track of elements that are being moved, but not collected.
	Such situation can happen, for example, during compression """
	def update_promotion_index(self, tracking_index, writing_index):
		for part in self.promotion_list:
			if tracking_index in part:
				number_index = part.index(tracking_index)
				list_number = self.promotion_list.index(part)
				self.promotion_list[list_number][number_index] = writing_index
				return

	""" In the specified area, moves all the elements to the left border
	Also updates all the references from all over the heap"""
	def compress(self, start_index, end_index):
		writing_index = start_index
		tracking_index = start_index
		while self.heap[writing_index] is not None and tracking_index < end_index:
			writing_index += 1
			tracking_index += 1
		# at this point we know where to write things to
		# and where to write things from
		while tracking_index < end_index:
			while self.heap[tracking_index] is None and tracking_index < end_index:
				tracking_index += 1
			if tracking_index == end_index:
				break
			if self.heap[tracking_index] != "FWD":
				self.update_promotion_index(tracking_index, writing_index)
				writing_index = self.process_pointer(tracking_index, tracking_index, writing_index, True)[0]
			else:
				tracking_index += 2
				while self.heap[tracking_index] == "-":
					tracking_index += 1
		self.cross_reference(0, len(self.heap))
		self.clearFWDs(0, len(self.heap))


	""" Takes all the elements from the last section of the 
	promotion list and excavates them to the new generation"""
	def promote(self):
		to_promote = self.promotion_list[len(self.promotion_list)-1]
		where_to = self.GENERATION_SIZE
		# find where to place - first empty space in the old gen
		while self.heap[where_to] is not None:
			where_to +=1
		for element in to_promote:
			where_to = self.process_pointer(element, element, where_to, True)[0]
		self.cross_reference(0, self.GENERATION_SIZE)
		self.clearFWDs(0, len(self.heap))
		self.compress(0, self.SPACE_SIZE)
		self.compress(self.SPACE_SIZE, self.GENERATION_SIZE)
		self.promotion_list[len(self.promotion_list)-1] = []

	""" Used for cross-referencing and updating values when something has been moved """
	def checkPointer(self, pos):
		numberi = self.heap[pos]
		original_tag = self.heap[numberi]
		if original_tag == "FWD":
			data = self.heap[numberi + 1]
			if self.heap[data] == "FWD":
				return checkPointer(numberi + 1)
			else:
				return data
		return -1

	""" Excavates a pointer reference during promotion"""
	def move_pointer_reference(self, pos):
		res = self.checkPointer(pos)
		if res != -1:
			self.heap[pos] = res;

	""" For complex structures during promotion, updates the references to other
	objects in case they were promoted, too.
	Although this partly repeats the existing methods, this is necessary since 
	the order of excavation cannot be guaranteed and some simple objects can be 
	promoted without any reference the more complex object that points at them """
	def cross_reference(self, start_index, end_index):
		position = start_index
		while position < self.GENERATION_SIZE or self.heap[position] is not None:
			if self.heap[position] == self.CONS or self.heap[position] == "CONS":
				self.move_pointer_reference(position + 1)
				self.move_pointer_reference(position + 2)
				position += 3
				continue
			if self.heap[position] == self.VECTOR or self.heap[position] == "VECTOR":
				for i in range(1, self.heap[position+1]):
					self.move_pointer_reference(position + i)
				position += self.heap[position+1] + 2
				continue
			if self.heap[position] == self.ARRAY or self.heap[position] == "ARRAY":
				n = self.heap[position + 1]
				m = 1
				for i in range(0, n):
					m *= self.heap[position + 2 + i]
				block_size = 2 + n + m
				overhead = 2 + n
				for i in range(overhead, block_size):
					self.move_pointer_reference(position + i)
				position += block_size
				continue
			if self.heap[position] == self.EXCEPTION or self.heap[position] == "EXCEPTION":
				self.move_pointer_reference(position + 2)
				position += 3
				continue
			else:
				position += 1
				continue

	""" After a collection, cleans out any values that were not changed.
	This is easy to track by their values. If, for example, latest collection was
	from space 1 to space 2, then any elements with indices lying within
	the range of space 1 can be removed since they have clearly not been 
	updated """
	def clean_promotion_list(self):
		start_index = self.FROM
		to_index = start_index + self.SPACE_SIZE
		for part in self.promotion_list:
			for index in part:
				if index >= start_index and index < to_index:
					list_index = self.promotion_list.index(part)
					index_index = part.index(index)
					print self.promotion_list
					del self.promotion_list[list_index][index_index]
					print self.promotion_list
					

	""" Methid resposible for one garbage collection """
	def collect_garbage(self):
		where_to = self.TO
		for root in self.roots:
			where_to = self.process_pointer(root, root, where_to, False)[0]
		# this cleans the fwds and uncollected elements
		
		cleaning_start = self.FROM	
		cleaning_end = cleaning_start + self.SPACE_SIZE

		for i in range(cleaning_start, cleaning_end):
			self.heap[i] = None
		
		self.clean_promotion_list()
		self.promote()
		self.swap_spaces()
		self.roots = self.moved_roots
		self.moved_roots = []
		self.clean_mapping_table()
	
	""" Swaps space 1 and space 2 """
	def swap_spaces(self):
		tmp = self.TO
		self.TO = self.FROM
		self.FROM = tmp
		
	""" Initialises heap. This is manual. """
	def initialise_heap(self):
		
		self.heap = []
		self.heap.extend(["BOOL", False])
		self.heap.extend(["EXCEPTION", 101, 0])
		self.heap.extend(["INT", 77])

		self.heap.extend(["ARRAY", 1, 4, 2, 0, 5, 14])
		self.heap.extend(["INT", 45])#14
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

	""" Initialises roots to collect. This is manual. """
	def initialise_roots(self):
		self.roots = []
		self.roots.append(7)
		self.roots.append(16)
		
	""" Initialises the mapping table. This is manual. """	
	def initialise_mapping_table(self):
		self.mapping_table = {}
		self.mapping_table[101] = ("myvar", False)
		self.mapping_table[201] = ("this wonderful string", False)

	""" Cleans the mapping table by removing unchecked values
	and unchecking the checked ones """
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
	#gc.print_status("FINAL1")
	gc.collect_garbage()
	#gc.print_status("FINAL2")
	gc.heap[18] = "STRING"
	gc.heap[19] = 201
	gc.mapping_table[201] = ("this wonderful string", False)
	gc.roots.append(18)
	#gc.print_status("We added String to the heap and put it into the roots")
	gc.collect_garbage()
	#gc.print_status("FINAL3")

	gc.collect_garbage()
	#gc.print_status("FINAL4")
	gc.heap[2] = 5 
	gc.heap[3] = 8
	gc.heap[4] = 13
	gc.heap[5] = 11
	gc.heap[6] = 15
	gc.heap[9] = 13
	gc.heap.insert(7, 21)
	gc.heap.insert(21, "INT") 
	gc.heap.insert(22, 33) 
	gc.roots = [0, 19]
	
	gc.promotion_list[3] = [0, 8, 11, 13, 15, 17]
	gc.promotion_list[1] = [19]
	#gc.print_status("Added INT 33, and added it to the array. The root is now 0 and 19")
	
	gc.collect_garbage()
	#gc.print_status("FINAL5")
	gc.print_status("final")
	print "finished execution successfully"


if __name__ == '__main__':
	main()