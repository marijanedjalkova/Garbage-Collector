class GarbageCollector:
	def __init__(self):
		self.heap = []
		self.GENERATION_SIZE = 100
		self.current_moving_index = 0 # this marks where to put the next thing
		self.current_divide_index = 0 # this marks where the heap ended before the current garbage collection
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

	def isTag(self, item):
		return item in ["INT", "STRING", "BOOL", "CONS", "VECTOR", "ARRAY", "EXCEPTION", "IND", "VAR", "FWD"]

	def move_pointer_block(self):
		
		new_block_start = self.current_moving_index
		# print "WILL PASTE HERE: " + str(current_moving_index)
		saved_old_locations = []
		### start of do-while imitation: copying the block 
		# print "copying " + str(heap[current_tracing_index])
		self.heap[self.current_moving_index] = self.heap[self.current_tracing_index]
		saved_old_locations.append(self.current_tracing_index)
		self.current_tracing_index += 1
		self.current_moving_index += 1

		while (not self.isTag(self.heap[self.current_tracing_index])):
			# copy it to the new place

			# print "copying " + str(heap[current_tracing_index])
			self.heap[self.current_moving_index] = self.heap[self.current_tracing_index]
			saved_old_locations.append(self.current_tracing_index)
			self.current_tracing_index += 1
			self.current_moving_index += 1
		### end of do-while imitation
		
		# at this point the block is copied to a new place, need to replace it with pointers
		self.heap[saved_old_locations[0]] = "FWD"
		self.heap[saved_old_locations[1]] = new_block_start
		if len(saved_old_locations)>2:
			for item in saved_old_locations[2:]:
				self.heap[item] = None
		#now the new block is in place and the old place points to it

	def copy_block(self, from_index):
		saved_old_locations = []
		# print "copying " + str(heap[from_index])
		self.heap[self.current_moving_index] = self.heap[from_index]
		saved_old_locations.append(from_index)
		from_index += 1
		self.current_moving_index += 1

		while (not self.isTag(self.heap[from_index])):
			# copy it to the new place
			# print "copying " + str(heap[from_index])
			self.heap[self.current_moving_index] = self.heap[from_index]
			saved_old_locations.append(from_index)
			self.current_moving_index += 1
			from_index += 1
		return saved_old_locations

	def print_status(self, desc):
		print "--------------"
		print desc
		print self.heap
		print "moving " + str(self.current_moving_index)
		print "tracing " + str(self.current_tracing_index)
		print "________"

	def process_pointer2(self, begin_index, end_index):
		if self.heap[begin_index] == "IND":
			begin_index += 1
			return False

		copied_pointer = self.heap[begin_index] # copied pointer is 6
		# now have to copy everything for that pointer
		new_block_start = self.current_moving_index
		saved_old_locations = self.copy_block(copied_pointer) # copied INT 2 into the new place
		# old locs is 6 and 7
		# new block start is where we started putting INT from int 2
		# now have to put fwd new_block_start into old locs
		# also have to put IND new_block_start instead of heap[begin_index]


		# self.print_status("AFTER COPYING ORIGINAL VALUES")
			
		# putting fwd new_block into old locs
		self.heap[saved_old_locations[0]] = "FWD"
		self.heap[saved_old_locations[1]] = new_block_start
		if len(saved_old_locations)>2:
			for item in saved_old_locations[2:]:
				self.heap[item] = None

		# putting reference to new_block_start into heap[begin_index]
		self.heap[begin_index] = new_block_start
		return True

	def process_ind2(self):
		
		# take all the pointers till the next tag
		# begin index marks the beginning of new block in the new space
		begin_index = self.current_moving_index
		self.move_pointer_block()
		end_index = self.current_moving_index
		# self.print_status("AFTER MOVING POINTER BLOCK")
		# now I have to copy all the original values for every pointer I just copied
		while (begin_index < end_index):
			# copy that value to the new place
			result = self.process_pointer(begin_index, end_index)
			if result == True:

				begin_index += 1
				self.current_moving_index += 1
				# self.print_status("AFTER FINISHING WORK WITH A POINTER")
			else:
				begin_index += 1

	def collect_garbage2(self):
		while self.current_tracing_index < self.current_divide_index:
			
			cell = self.heap[self.current_tracing_index]
			
			if cell == "IND":
				self.process_ind()
				self.current_tracing_index -= 1
				self.current_moving_index -= 1
			# self.print_status("AFTER PROCESSING IND")
			self.current_tracing_index += 1
		# have to clean the previous space now
		for i in range(0, self.current_divide_index):
			self.heap[i] = None
		# TODO update divide index?
		# TODO promote to next generation?

	def process_int(self, index):
		# length of the block is 2
		self.heap[self.current_moving_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[self.current_moving_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = self.current_moving_index
		self.current_moving_index += 2		

	def process_string(self, index):
		# TODO this is obviously not right, replace
		self.heap[self.current_moving_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[self.current_moving_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = self.current_moving_index
		self.current_moving_index += 2

	def process_bool(self, index):
		self.heap[self.current_moving_index] = self.heap[index]
		self.heap[index] = "FWD"
		self.heap[self.current_moving_index + 1] = self.heap[index + 1]
		self.heap[index + 1] = self.current_moving_index
		self.current_moving_index += 2

	def process_pointer(self, pointer_index):
		# pointer_index is the value that points onto the original value of the pointer
		# e.g. if we are processing cons 6 3 then by this time the block will have been 
		# copied into new space, and pointer_index is either 6 or 3
		
		tag = self.heap[pointer_index]
		# print "pointer is " + str(pointer_index)
		# print "tag is " + str(tag)
		self.process_tag(tag, pointer_index)

	def process_cons(self, index):
		block_size = 3
		for i in range(0, block_size):
			self.heap[self.current_moving_index + i] = self.heap[index + i]
		self.heap[index] = "FWD"
		self.heap[index + 1] = self.current_moving_index
		self.heap[index + 2] = "-"
		self.current_moving_index += block_size
		
		# now process moving - 2 and moving - 1
		pointers = [self.current_moving_index - 2, self.current_moving_index - 1]
		
		for p in pointers:
			new_index = self.current_moving_index
			self.process_pointer(self.heap[p])
			self.heap[p] = new_index
		

	def process_vector(self, index):
		block_size = self.heap[index + 1] + 2 


	def process_array(self, index):
		pass

	def process_exception(self, index):
		pass

	def process_ind(self, index):
		pass

	def process_var(self, index):
		pass

	def process_tag(self, tag, heap_root_index):
		if tag == self.INT or tag == "INT":
			self.process_int(heap_root_index)
			return
		if tag == self.STRING or tag == "STRING":
			self.process_string(heap_root_index)
			return
		if tag == self.BOOL or tag == "BOOL":
			self.process_bool(heap_root_index)
			return
		if tag == self.CONS or tag == "CONS":
			self.process_cons(heap_root_index)
			return
		if tag == self.VECTOR or tag == "VECTOR":
			self.process_vector(heap_root_index)
			return
		if tag == self.ARRAY or tag == "ARRAY":
			self.process_array(heap_root_index)
			return
		if tag == self.EXCEPTION or tag == "EXCEPTION":
			self.process_exception(heap_root_index)
			return
		if tag == self.IND or tag == "IND":
			self.process_ind(heap_root_index)
			return
		if tag == self.VAR or tag == "VAR":
			self.process_var(heap_root_index)
			return

			print "Error tag"

	def process_root(self, heap_root_index):
		tag = self.heap[heap_root_index]
		self.process_tag(tag, heap_root_index)
		


	def collect_garbage(self):
		for root in self.roots:
			self.process_root(root)
		for i in range(0, self.current_divide_index):
			self.heap[i] = None	


	def initialise_heap(self):
		# add things to the heap, 
		# change the current_moving_index to show the first empty cell in the array
		# change the current_divide_index to the same value
		self.heap = []
		self.heap.append("IND")
		self.heap.append(4)
		self.heap.append("IND")
		self.heap.append(4)
		self.heap.append("BOOL")
		self.heap.append(False)
		self.heap.append("INT")
		self.heap.append(23)
		self.heap.append("CONS")
		self.heap.append(6)
		self.heap.append(4)
		self.current_tracing_index = 0
		self.current_moving_index = len(self.heap)
		self.current_divide_index = len(self.heap)
		for i in range(0, 40):
			self.heap.append(None)
		
		# this index shows where we are in the old section

	def initialise_roots(self):
		self.roots = []
		self.roots.append(8)
		


def main():
	gc = GarbageCollector()
	gc.initialise_heap()
	gc.initialise_roots()
	# at this point we have something that has to be garbage collected in the heap
	# and also the current index shows the first empty cell after all the code
	gc.print_status("INITIAL")
	gc.collect_garbage()
	gc.print_status("FINAL")
	print "finished execution successfully"


if __name__ == '__main__':
	main()