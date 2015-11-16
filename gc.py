heap = []
GENERATION_SIZE = 100
current_moving_index = 0 # this marks where to put the next thing
current_divide_index = 0 # this marks where the heap ended before the current garbage collection
current_tracing_index = 0 # this shows where we are in the old section

def isTag(item):
	return item in ["INT", "STRING", "BOOL", "CONS", "VECTOR", "ARRAY", "EXCEPTION", "IND", "VAR", "FWD"]

def move_pointer_block():
	global current_moving_index
	global current_tracing_index
	global current_divide_index
	global heap
	
	new_block_start = current_moving_index
	print "WILL PASTE HERE: " + str(current_moving_index)
	saved_old_locations = []
	### start of do-while imitation: copying the block 
	print "copying " + str(heap[current_tracing_index])
	heap[current_moving_index] = heap[current_tracing_index]
	saved_old_locations.append(current_tracing_index)
	current_tracing_index += 1
	current_moving_index += 1

	while (not isTag(heap[current_tracing_index])):
		# copy it to the new place
		print "copying " + str(heap[current_tracing_index])
		heap[current_moving_index] = heap[current_tracing_index]
		saved_old_locations.append(current_tracing_index)
		current_tracing_index += 1
		current_moving_index += 1
	### end of do-while imitation
	
	# at this point the block is copied to a new place, need to replace it with pointers
	heap[saved_old_locations[0]] = "FWD"
	heap[saved_old_locations[1]] = new_block_start
	if len(saved_old_locations)>2:
		for item in saved_old_locations[2:]:
			heap[item] = None
	#now the new block is in place and the old place points to it

def copy_block(from_index):
	global current_moving_index
	global heap
	saved_old_locations = []
	print "copying " + str(heap[from_index])
	heap[current_moving_index] = heap[from_index]
	saved_old_locations.append(from_index)
	from_index += 1
	current_moving_index += 1

	while (not isTag(heap[from_index])):
		# copy it to the new place
		print "copying " + str(heap[from_index])
		heap[current_moving_index] = heap[from_index]
		saved_old_locations.append(from_index)
		current_moving_index += 1
		from_index += 1
	return saved_old_locations

def print_status(desc):
	global current_moving_index
	global current_tracing_index
	global current_divide_index
	global heap
	print "--------------"
	print desc
	print heap
	print "moving " + str(current_moving_index)
	print "tracing " + str(current_tracing_index)
	print "________"

def process_pointer(begin_index, end_index):
	if heap[begin_index] == "IND":
		begin_index += 1
		return False

	copied_pointer = heap[begin_index] # copied pointer is 6
	# now have to copy everything for that pointer
	new_block_start = current_moving_index
	saved_old_locations = copy_block(copied_pointer) # copied INT 2 into the new place
	# old locs is 6 and 7
	# new block start is where we started putting INT from int 2
	# now have to put fwd new_block_start into old locs
	# also have to put IND new_block_start instead of heap[begin_index]
	print_status("AFTER COPYING ORIGINAL VALUES")
		
	# putting fwd new_block into old locs
	heap[saved_old_locations[0]] = "FWD"
	heap[saved_old_locations[1]] = new_block_start
	if len(saved_old_locations)>2:
		for item in saved_old_locations[2:]:
			heap[item] = None

	# putting reference to new_block_start into heap[begin_index]
	heap[begin_index] = new_block_start
	return True


def process_ind():
	global current_moving_index
	global current_tracing_index
	global current_divide_index
	global heap
	
	# take all the pointers till the next tag
	# begin index marks the beginning of new block in the new space
	begin_index = current_moving_index
	move_pointer_block()
	end_index = current_moving_index
	print_status("AFTER MOVING POINTER BLOCK")
	# now I have to copy all the original values for every pointer I just copied
	while (begin_index < end_index):
		# copy that value to the new place
		result = process_pointer(begin_index, end_index)
		if result == True:

			begin_index += 1
			current_moving_index += 1
			print_status("AFTER FINISHING WORK WITH A POINTER")
		else:
			begin_index += 1



def collect_garbage():
	global current_moving_index
	global current_tracing_index
	global current_divide_index
	global heap
	while current_tracing_index < current_divide_index:
		
		cell = heap[current_tracing_index]
		
		if cell == "IND":
			process_ind()
			current_tracing_index -= 1
			current_moving_index -= 1
		print_status("AFTER PROCESSING IND")
		current_tracing_index += 1
	# have to clean the previous space now
	for i in range(0, current_divide_index):
		heap[i] = None


def initialise_heap():
	global current_moving_index
	global current_tracing_index
	global current_divide_index
	global heap
	# add things to the heap, 
	# change the current_moving_index to show the first empty cell in the array
	# change the current_divide_index to the same value
	heap = [None] * 40
	heap[0] = "IND"
	heap[1] = 4
	heap[2] = "IND"
	heap[3] = 6
	heap[4] = "INT"
	heap[5] = 42
	heap[6] = "INT"
	heap[7] = 23
	current_tracing_index = 0
	current_moving_index = 8
	current_divide_index = 8
	# this index shows where we are in the old section
	


def main():
	global heap
	initialise_heap()
	# at this point we have something that has to be garbage collected in the heap
	# and also the current index shows the first empty cell after all the code
	print "heap before collection: "
	print heap
	collect_garbage()
	print_status("FINAL")
	print "finished execution successfully"


if __name__ == '__main__':
	main()