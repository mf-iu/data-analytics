import math

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def manhattanDistance(p1, p2):
	"""
		p1: Point 1 as an array of N coordinates
		p2: Point 2 as an array of N coordinates

		Returns: Manhattan distance (distance when walking only along the axes) between p1 and p2
	"""
	return sum(abs(a - b) for a, b in zip(p1, p2))

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def euclideanDistanceSquared(p1, p2):
	"""
		p1: Point 1 as an array of N coordinates
		p2: Point 2 as an array of N coordinates

		Returns: Squared euclidean distance between p1 and p2
	"""
	return sum((a - b) ** 2 for a, b in zip(p1, p2))

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def euclideanDistance(p1, p2):
	"""
		p1: Point 1 as an array of N coordinates
		p2: Point 2 as an array of N coordinates

		Returns: Euclidean distance between p1 and p2
	"""
	return math.sqrt(euclideanDistanceSquared(p1, p2))

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def greatCircleDistance(p1, p2):
	"""
		See https://en.wikipedia.org/wiki/Great-circle_distance

		p1: Point 1 as an array of N coordinates,
		    p1[0] is the latitude in degrees, p1[1] the longitude in degrees
		p2: Point 2 as an array of N coordinates
		    p2[0] is the latitude in degrees, p2[1] the longitude in degrees

		Returns: Distance in kilometers assuming p1 and p2 are on a great circle around the earth
		         at sea level (assuming the circumference of the earth having 40.000 km)
	"""
	lat1_deg = p1[0]
	long1_deg = p1[1]
	lat2_deg = p2[0]
	long2_deg = p2[1]

	oneMeter_deg = 0.00899928005759539236861051115911 # = 0.001 km / 60' / 1.852 km at the equator

	if math.fabs(lat1_deg - lat2_deg) < oneMeter_deg and \
	   math.fabs(long1_deg - long2_deg) < oneMeter_deg:
		return 0

	lat1 = math.radians(lat1_deg)
	long1 = math.radians(long1_deg)
	lat2 = math.radians(lat2_deg)
	long2 = math.radians(long2_deg)

	distance_rad = math.acos(math.sin(lat1) * math.sin(lat2) +
	                         math.cos(lat1) * math.cos(lat2) * math.cos(long1 - long2))
	distance_km = math.degrees(distance_rad) * 60.0 * 1.852
	return distance_km

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def runExample():
	print("Example:")
	print("")

	a_m = [1, 1]
	b_m = [2, 2]
	d_m = manhattanDistance(a_m, b_m)
	print("Manhattan distance between "
	      "[" + "; ".join(map(str, a_m)) + "] and "
	      "[" + "; ".join(map(str, b_m)) + "] is " + str(d_m) + ".")

	a_es = [1, 1, 1]
	b_es = [2, 2, 2]
	d_es = euclideanDistanceSquared(a_es, b_es)
	print("Squared Euclidean distance between "
	      "[" + "; ".join(map(str, a_es)) + "] and "
	      "[" + "; ".join(map(str, b_es)) + "] is " + str(d_es) + ".")

	a_e = [0, 1, 2, 3, 4]
	b_e = [5, 6, 7, 8, 9]
	d_e = euclideanDistance(a_e, b_e)
	print("Euclidean distance between "
	      "[" + "; ".join(map(str, a_e)) + "] and "
	      "[" + "; ".join(map(str, b_e)) + "] is " + str(d_e) + ".")

	a_gc = [50.978056, 11.029167] # Erfurt
	b_gc = [52.518611, 13.408333] # Berlin
	d_gc = greatCircleDistance(a_gc, b_gc)
	print("Great-circle distance between "
	      "[" + "; ".join(map(str, a_gc)) + "] and "
	      "[" + "; ".join(map(str, b_gc)) + "] is " + str(d_gc) + " km.")

	print("")

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if __name__ == "__main__":
	print("Available functions:")
	print("\tmanhattanDistance(p1, p2)")
	print("\teuclideanDistanceSquared(p1, p2)")
	print("\tdistanceSquared(p1, p2)")
	print("\tgreatCircleDistance(p1, p2)")
	print("")

	if True:
		runExample()
