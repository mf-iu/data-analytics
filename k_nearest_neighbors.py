import random
import rtree
import time

# install missing packages using:
# python -m pip install ...

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

from distances import euclideanDistance
from distances import greatCircleDistance
from distances import manhattanDistance

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def createRTree(points):
	"""
		Sets up an R-tree containing indices into the list of points

		points: List of data points, each point is a list of N coordinates
	"""
	if not points:
		raise ValueError("Point list cannot be empty.")

	dimension = len(points[0])
	if any(len(point) != dimension for point in points):
		raise ValueError("All points must have the same dimension.")

	def bulkLoadGenerator(points):
		"""
			Generator function for efficient bulk loading of the R-tree.
		"""
		for pointIndex, point in enumerate(points):
			# Generator has to deliver a tuple: (id, (min_x, min_y, max_x, max_y), object)
			yield (pointIndex, tuple(point) + tuple(point), None)

	rtreeProperties = rtree.index.Property()
	rtreeProperties.dimension = dimension

	tree = rtree.index.Index(bulkLoadGenerator(points), properties = rtreeProperties)

	return tree

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def findKNearestNeighbors(tree, points, queryPoint, distanceFunction, k, candidateMultiplier = 4):
	"""
		Find k nearest neighbors.

		Returns: [ pointIndex, ... ]
	"""
	dimension = len(points[0])
	if len(queryPoint) != dimension:
		raise ValueError(f"Expected {dimension}-D query point, got {len(queryPoint)}-D")

	numberOfCandidates = min(len(points), max(k, k * candidateMultiplier))
	nearestPointIndices = list(
		tree.nearest(coordinates = queryPoint, num_results = numberOfCandidates)
	)

	results = []
	for pointIndex in nearestPointIndices:
		point = points[pointIndex]
		distance = distanceFunction(queryPoint, point)
		results.append((pointIndex, distance))

	results.sort(key = lambda x : x[1])
	pointIndices = map(lambda x : x[0], results[:k])

	# Return a list of point indices pointing to the k nearest points
	return pointIndices

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def example3D():
	queryPoint = [4, 3, 3]
	k = 3

	print(f"{k} nearest neighbors to {queryPoint}:")
	print("")

	startTime = time.time()
	points = [ [ random.uniform(-100, 100),
	             random.uniform(-180, 180),
	             random.uniform(-180, 180) ] for _ in range(100000) ]
	print(f"{len(points)} random 3D points created in {time.time() - startTime:.4f} seconds.")

	startTime = time.time()
	tree = createRTree(points)
	print(f"R-tree index created in {time.time() - startTime:.4f} seconds.")
	print("")

	print("Using Euclidean distance:")

	startTime = time.time()
	neighbors = findKNearestNeighbors(tree, points, queryPoint, euclideanDistance, k)
	print(f"{k} nearest neighbors found in {time.time() - startTime:.4f} seconds.")
	print("")

	for pointIndex in neighbors:
		print(f"id: {pointIndex:<2}, "
		      f"\tpoint: {points[pointIndex]}, "
		      f"\tdistance: {euclideanDistance(queryPoint, points[pointIndex]):.4f}")
	print("")

	print("Using Manhattan distance:")

	startTime = time.time()
	neighbors = findKNearestNeighbors(tree, points, queryPoint, manhattanDistance, k)
	print(f"{k} nearest neighbors found in {time.time() - startTime:.4f} seconds.")
	print("")

	for pointIndex in neighbors:
		print(f"id: {pointIndex:<2}, "
		      f"\tpoint: {points[pointIndex]}, "
		      f"\tdistance: {manhattanDistance(queryPoint, points[pointIndex]):.4f}")
	print("")

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def exampleGeoPoints(k):
	queryPoint = [50.978056, 11.029167] # Erfurt
	print(f"Find {k} locations nearest to Erfurt {queryPoint}")
	print("")

	startTime = time.time()
	points = [ [ random.uniform(-90, 90), random.uniform(-180, 180) ] for _ in range(1000000) ]
	print(f"{len(points)} random geo-locations created in {time.time() - startTime:.4f} seconds.")

	startTime = time.time()
	tree = createRTree(points)
	print(f"R-tree index created in {time.time() - startTime:.4f} seconds.")

	startTime = time.time()
	neighbors = findKNearestNeighbors(tree, points, queryPoint, greatCircleDistance, k)
	print(f"{k} nearest neighbors found in {time.time() - startTime:.4f} seconds.")

	print("")
	for pointIndex in neighbors:
		print(f"id: {pointIndex:<2}, "
		      f"\tpoint: {points[pointIndex]}, "
		      f"\tdistance: {greatCircleDistance(queryPoint, points[pointIndex]):.4f}")
	print("")

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if __name__ == "__main__":
	if True:
		example3D()
		exampleGeoPoints(20)

