import random
import locale
import math
import numpy as np

from ortools.graph.python import min_cost_flow

# install missing packages using:
# python -m pip install ...

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

from distances import euclideanDistance
from distances import greatCircleDistance

from geonames import extractPoints
from geonames import fetchData
from geonames import storeClustering

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def initializeCentroidsAtRandom(points, numberOfClusters, distanceFunction = None):
	"""
		Choose some of the given points at random as the initial cluster centroids.

		points:           List of data points, each point is a list of N coordinates
		numberOfClusters: Number of desired cluster centroids
		distanceFunction: Unused argument needed for compatibility with oder init methods

		Returns: List of centroids in the same format as points.
	"""
	centroids = random.sample(points, numberOfClusters)

	# Sort the centroids for easier comparing with future centroids
	centroids.sort()

	return centroids

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def initializeCentroidsKMeansPlusPlus(points, numberOfClusters, distanceFunction):
	"""
		Choose some of the given points as initial cluster centroids applying the k-means++ method.

		points:           List of data points, each point is a list of N coordinates
		numberOfClusters: Number of desired cluster centroids
		distanceFunction: Distance function to compute the distance between two data points

		Returns: List of centroids in the same format as points.
	"""
	numberOfPoints = len(points)

	# Choose first centroid as one random data point
	centroids = [ random.choice(points) ]

	# Choose remaining k - 1 centroids
	while len(centroids) < numberOfClusters:
		partialSumsDistSq = []
		sumDistSquared = 0

		# For each point, compute squared distance to nearest centroid.
		# Also record the squared sum of distances for all previous points.
		for point in points:
			distances = [ distanceFunction(point, centroid) for centroid in centroids ]
			minDistance = min(distances)

			sumDistSquared = sumDistSquared + minDistance ** 2
			partialSumsDistSq.append(sumDistSquared)

		# Choose a random threshold and choose a point that is not yet a centroid for which the
		# summed square distances is high enough.
		threshold = random.uniform(0, sumDistSquared)
		for point, partialSumDistSq in zip(points, partialSumsDistSq):
			if partialSumDistSq < threshold or point in centroids:
				continue

			centroids.append(point)
			break

	# Sort the centroids for easier comparing with future centroids
	centroids.sort()

	return centroids

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def assignClustersNearest(points, centroids, distanceFunction):
	"""
		Assign a cluster to each point by finding the nearest centroid

		points:           List of data points, each point is a list of N coordinates
		centroids:        List of cluster centroids in the same format as points
		distanceFunction: Distance function to compute the distance between two data points

		Returns: A list of point assignments which's elements are lists of point indices.
		         For all points in a cluster the respective centroid is the nearest centroid.
		         Example:
		             The cluster assignment reflects:
		             [ [0, 3],     # Cluster 1 with centroid[0]: [ points[0], points[3] ]
		               [1, 2, 7],  # Cluster 2 with centroid[1]: [ points[1], points[2], points[7] ]
		               ... ]
	"""
	# Initialize the cluster assignment as [ [], [], ... ]
	clusterAssignment = [ [] for _ in range(len(centroids)) ]

    # For each point in points
	for pointIndex in range(len(points)):
		# Compute the distances for the point to all centroids
		distances = [ distanceFunction(points[pointIndex], centroid) for centroid in centroids ]
		# Determine the index of the nearest centroid
		indexOfClosestCentroid = distances.index(min(distances))
		# Store the point's index in the list of the respective cluster
		clusterAssignment[indexOfClosestCentroid].append(pointIndex)

	return clusterAssignment

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def assignClustersBalanced(points, centroids, distanceFunction):
	"""
		Assign a cluster to each point under the condition that all clusters have an equal
		number of points (+/- 1).

		points:           List of data points, each point is a list of N coordinates
		centroids:        List of cluster centroids in the same format as points
		distanceFunction: Distance function to compute the distance between two data points

		Returns: A list of point assignments which's elements are lists of point indices.
		         For all points in a cluster the respective centroid is the nearest centroid.
		         Example:
		             The cluster assignment reflects:
		             [ [0, 3],     # Cluster 1 with centroid[0]: [ points[0], points[3] ]
		               [1, 2, 7],  # Cluster 2 with centroid[1]: [ points[1], points[2], points[7] ]
		               ... ]
	"""
	numberOfPoints = len(points)
	numberOfClusters = len(centroids)

	numberOfNodes = 2 + numberOfPoints + numberOfClusters

	# Initialize the cluster sizes with floor(numberOfPoints / numberOfClusters).
	clusterSizes = [numberOfPoints // numberOfClusters] * numberOfClusters
	# Increase capacities of the clusters until all points fit
	numberOfPointsInAllClusters = sum(clusterSizes)
	for clusterIndex in range(numberOfClusters):
		if numberOfPointsInAllClusters >= numberOfPoints:
			break
		clusterSizes[clusterIndex] = clusterSizes[clusterIndex] + 1
		numberOfPointsInAllClusters = numberOfPointsInAllClusters + 1

	# Node indexing:
	startNode = 0
	endNode = 1
	pointNodesOffset = 2
	clusterNodesOffset = pointNodesOffset + numberOfPoints

	# Setup the network
	# See https://developers.google.com/optimization/flow/mincostflow
	minCostFlow = min_cost_flow.SimpleMinCostFlow()

	# Start node -> point nodes
	for pointIndex in range(numberOfPoints):
		pointNode = pointNodesOffset + pointIndex
		minCostFlow.add_arc_with_capacity_and_unit_cost(startNode, pointNode, 1, 0)

	# Point nodes -> cluster nodes
	for pointIndex in range(numberOfPoints):
		pointNode = pointNodesOffset + pointIndex
		point = points[pointIndex]

		for clusterIndex in range(numberOfClusters):
			clusterNode = clusterNodesOffset + clusterIndex
			centroid = centroids[clusterIndex]

			# The Min-cost-flow algorithm only supports integer costs.
			# We assume that distances below 0.001 can be considered zero.
			cost = int(1000.0 * distanceFunction(point, centroid))
			minCostFlow.add_arc_with_capacity_and_unit_cost(pointNode, clusterNode, 1, cost)

	# Cluster nodes -> end node
	for clusterIndex in range(numberOfClusters):
		clusterNode = clusterNodesOffset + clusterIndex
		capacity = clusterSizes[clusterIndex]
		minCostFlow.add_arc_with_capacity_and_unit_cost(clusterNode, endNode, capacity, 0)

	# Setup initial supplies
	minCostFlow.set_node_supply(startNode, numberOfPoints)
	minCostFlow.set_node_supply(endNode, -numberOfPoints)
	for pointOrClusterNode in range(pointNodesOffset, numberOfNodes):
		minCostFlow.set_node_supply(pointOrClusterNode, 0)


	# Initialize the cluster assignment as [ [], [], ... ]
	clusterAssignment = [ [] for _ in range(len(centroids)) ]

	# Solve
	status = minCostFlow.solve()
	if status != minCostFlow.OPTIMAL:
		raise RuntimeError("Flow not optimal.")

	# Extract cluster assignment
	for arc in range(minCostFlow.num_arcs()):
		tail = minCostFlow.tail(arc)
		head = minCostFlow.head(arc)

		# For an arc from a point node to a cluster node:
		# If there was a flow computed from the point to the cluster we interpret this
		# as assigning the point to the cluster.
		if (pointNodesOffset <= tail < pointNodesOffset + numberOfPoints and
			clusterNodesOffset <= head < clusterNodesOffset + numberOfClusters and
			minCostFlow.flow(arc) > 0):

			pointIndex = tail - pointNodesOffset
			clusterIndex = head - clusterNodesOffset
			clusterAssignment[clusterIndex].append(pointIndex)

	return clusterAssignment

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def computeCentroids(points, clusterAssignment):
	"""
		Determine the centroid of each cluster by computing the mean of the points.

		points:            List of data points, each point is a list of N coordinates
		clusterAssignment: List of point assignments for each cluster.
		                   Each element is a list of indices into the points list.

		Returns: List of cluster centroids in the same format as points
		         Example: [ [x1, y1, ...], [x2, y2, ...], ... ]
	"""
	newCentroids = []

	def assignRandomPoint():
		newCentroid = []
		while not newCentroid in newCentroids:
			newCentroid = random.choice(points)
		return newCentroid

	for pointIndices in clusterAssignment:
		newCentroid = None

		if pointIndices:
			# Get the list of points assigned to the cluster
			clusterPoints = [ points[pointIndex] for pointIndex in pointIndices ]

			# Compute the centroid of the cluster points as the mean of the point
			newCentroid = [ sum(transposedPoints) / len(clusterPoints)
			                    for transposedPoints in zip(*clusterPoints) ]
		else:
			newCentroid = assignRandomPoint()

		newCentroids.append(newCentroid)

	# If we do not have enough cluster centroids we determine more by chosing randomly from
	# the given data points
	numberOfClusters = len(clusterAssignment)
	while len(newCentroids) < numberOfClusters:
		newCentroid = assignRandomPoint(points)
		newCentroids.append(newCentroid)

	# Sort the centroids for easier comparing with previous or future centroids
	newCentroids.sort()

	return newCentroids

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def kMeansClustering(points, numberOfClusters, distanceFunction,
                     initializeCentroidsFunction = initializeCentroidsAtRandom,
                     assignClustersFunction = assignClustersNearest,
                     maxIterations = 100, tolerance = 0.000001):
	"""
		Determine the centroid of each cluster by computing the mean of the points.

		points:                      List of data points, each point is a list of N coordinates
		numberOfClusters:            number of clusters that should be determined
		distanceFunction:            Distance function to compute the distance between two points
		initializeCentroidsFunction: may be initializeCentroidsAtRandom or
		                                    initializeCentroidsKMeansPlusPlus
		assignClustersFunction:      may be assignClustersNearest or assignClustersBalanced
		maxIterations:               maximum number of iterations in case clustering does not
		                             converge
		tolerance:                   total deviation to determine if centroids have not moved
		                             from one iteration to the next

		Returns: Tuple (centroids, clusterAssignment)
		         with: centroids:         List of cluster centroids in the same format as points
		               clusterAssignment: List of point assignments for each cluster.
		                                  Each element is a list of indices into the points list.
	"""
	centroids = initializeCentroidsFunction(points, numberOfClusters, distanceFunction)

	clusterAssignment = None
	for _ in range(maxIterations):
		clusterAssignment = assignClustersFunction(points, centroids, distanceFunction)
		newCentroids = computeCentroids(points, clusterAssignment)

		# Compute how much the centroids have moved
		shifts = [ distanceFunction(old, new) for old, new in zip(centroids, newCentroids) ]

		centroids = newCentroids

		if max(shifts) < tolerance:
			break

	return (centroids, clusterAssignment)

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def computeStatistics(points, data, centroids, clusterAssignment, distanceFunction):
	"""
		Computes statistical values for each cluster.

		points:                      List of data points, each point is a list of N coordinates
		data:                        List of data points, each point is an object with key-value
		                             pairs as delivered by fetchData
		centroids:                   List of cluster centroids in the same format as points
		clusterAssignment:           List of point assignments for each cluster.
		                             Each element is a list of indices into the points list.
		distanceFunction:            Distance function to compute the distance between two points

		Returns: List of statistical data for each cluster. Each element is an object:
		             { "centroid": {
		                   "point":    [x, y, ...], # Centroid of the cluster as in list centroids
		                   "variance": n,           # Variance of all points in the cluster with
		                                            # respect to the centroid
		                   "radius":   n,           # Maximum radius of all points in the cluster
		                                            # around the centroid
		                   "wcss":     n            # Within-cluster sum of squares of the 
		                                            # distances of all points from the centroid
		               },
		               "geoCenter": {
		                   "point":    [lat, long], # Mean of the geo-positions of all data
		                                            # points in the cluster
		                   "variance": n,           # Variance, radius and wcss as above, but with
		                   "radius":   n,           # respect to the geo-center
		                   "wcss":     n
		               },
		             }
	"""
	statistics = []

	for centroidIndex in range(len(centroids)):
		centroid = centroids[centroidIndex]

		distances = []
		pointIndices = clusterAssignment[centroidIndex]
		numberOfPoints = len(pointIndices)

		geoDistances = []
		geoCenter = [0, 0]

		for pointIndex in pointIndices:
			point = points[pointIndex]
			distance = distanceFunction(point, centroid)
			distances.append(distance)

			entry = data[pointIndex]
			latLong = [entry["latitude"], entry["longitude"]]
			geoCenter = [geoCenter[0] + (latLong[0] / numberOfPoints),
			             geoCenter[1] + (latLong[1] / numberOfPoints)]

		for pointIndex in pointIndices:
			entry = data[pointIndex]
			latLong = [entry["latitude"], entry["longitude"]]

			geoDistance = greatCircleDistance(latLong, geoCenter)
			geoDistances.append(geoDistance)

		statistics.append({
			"centroid": {
				"point": centroid,
				"variance": np.var(distances),
				"radius": np.max(distances) if numberOfPoints > 1 else 0.0,
				"wcss": np.dot(distances, distances) if numberOfPoints > 1 else 0.0
			},
			"geoCenter": {
				"point": geoCenter,
				"variance": np.var(geoDistances),
				"radius": np.max(geoDistances) if numberOfPoints > 1 else 0.0,
				"wcss": np.dot(geoDistances, geoDistances) if numberOfPoints > 1 else 0.0
			}
		})

	return statistics

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def findBestCluster(centroids, point, distanceFunction):
	"""
		Finds the cluster that has its centroid nearest to the given point.

		centroids:        List of cluster centroids in the same format as points
		point:            Point as a list of N coordinates
		distanceFunction: Distance function to compute the distance between two data points

		Returns: Index of the best fitting cluster
	"""
	distances = [ distanceFunction(point, centroid) for centroid in centroids ]
	clusterIndex = distances.index(min(distances))
	return clusterIndex

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def findElbowPoint(x_values, y_values):
	"""
		Analyses an L-curve (elbow curve) given by a list of x-values and a list of y-values and
		returns the point that is the best "elbow point" of the L.

		x_values: List of values on the x-axis
		y_values: List of values corresponding values on the y-axis

		Returns: Tuple (x, y) that is the best elbow point
	"""
	if len(x_values) == 1:
		return (x_values[0], y_values[0])

	# First and last points
	x_first = x_values[0]
	y_first = y_values[0]
	x_last = x_values[-1]
	y_last = y_values[-1]

	dx = x_last - x_first
	dy = y_last - y_first
	n = x_last * y_first - x_first * y_last
	denominator = math.sqrt(dy * dy + dx * dx)

	maxDistance = -1
	elbowIndex = 0

	for idx in range(len(x_values)):
		# Distance from point to line
		distance = abs(x_values[idx] * dy - y_values[idx] * dx + n) / denominator

		if distance > maxDistance:
			maxDistance = distance
			elbowIndex = idx

	return (x_values[elbowIndex], y_values[elbowIndex])

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def runKMeansExample(minNumberOfClusters = 1, maxNumberOfClusters = 10,
                     initializeCentroidsFunction = initializeCentroidsAtRandom,
                     assignClustersFunction = assignClustersNearest,
                     verboseOutput = False,
                     maxIterations = 100, tolerance = 0.00000001):
	print("Example for k-means clustering:")
	print

	database = "../database.sqlite"

	data = fetchData(database, """
		SELECT geoname_id, name, latitude, longitude, population FROM allCountries
		WHERE country_code = 'DE' AND feature_class = 'A' AND feature_code IN ('ADM3');
	""")

	#points = extractPoints(data, ["population"])
	#distanceFunction = euclideanDistance

	points = extractPoints(data, ["latitude", "longitude"])
	distanceFunction = greatCircleDistance

	# Function to run k-means clustering for the given number of clusters
	def doClustering(numberOfClusters):
		(centroids, clusterAssignment) = kMeansClustering(points, numberOfClusters,
		                                                  distanceFunction,
		                                                  initializeCentroidsFunction,
		                                                  assignClustersFunction)

		statistics = computeStatistics(points, data, centroids, clusterAssignment, distanceFunction)

		return (centroids, clusterAssignment, statistics)

	runs = []

	clusterSizes = range(minNumberOfClusters, maxNumberOfClusters + 1)
	for numberOfClusters in clusterSizes:
		(centroids, clusterAssignment, statistics) = doClustering(numberOfClusters)

		runs.append({
			"centroids": centroids,
			"clusterAssignment": clusterAssignment,
			"statistics": statistics,
			"wcss": sum([ stats["centroid"]["wcss"] for stats in statistics ])
		})

	for run in runs:
		centroids = run["centroids"]
		clusterAssignment = run["clusterAssignment"]
		statistics = run["statistics"]

		if verboseOutput:
			for clusterIndex in range(len(clusterAssignment)):
				stats = statistics[clusterIndex]
				centroid = stats["centroid"]
				geoCenter = stats["geoCenter"]
				print(f"Cluster:\t{clusterIndex + 1}\t"
				      f"Number of points:\t{len(clusterAssignment[clusterIndex])}\t"
				      f"Centroid:\t{centroid["point"]}\t"
				      f"Variance:\t{centroid["variance"]}\t"
				      f"Max. radius:\t{centroid["radius"]}\t"
				      f"3-sigma radius:\t{3.0 * math.sqrt(centroid["variance"])}\t"
				      f"WCSS:\t{centroid["wcss"]}"
				      f"Geo-center:\t{geoCenter["point"]}\t"
				      f"Geo-radius:\t{geoCenter["radius"]}\t"
				      f"3-sigma geo-radius:\t{3.0 * math.sqrt(geoCenter["variance"])}\t"
				)
			print("")

	locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

	for run in runs:
		print(f"Number of clusters:\t{len(run["clusterAssignment"])}\t"
		      f"Total WCSS:\t{locale.format_string("%.2f", run["wcss"], grouping = False)}")
	print("")

	(optimalNumberOfClusters, wcssValue) = findElbowPoint(clusterSizes,
	                                                      [ run["wcss"] for run in runs ])

	print(f"Optimal number of clusters:\t{optimalNumberOfClusters}\t"
	      f"Total WCSS:\t{locale.format_string("%.2f", wcssValue, grouping = False)}")

	optimalRun = runs[clusterSizes.index(optimalNumberOfClusters)]
	storeClustering(database, data, optimalRun["centroids"], optimalRun["statistics"],
	                                optimalRun["clusterAssignment"])
	print("")

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Example usage
if __name__ == "__main__":
	print("Available functions:")
	print("\tinitializeCentroidsAtRandom(points, numberOfClusters)")
	print("\tinitializeCentroidsKMeansPlusPlus(points, numberOfClusters, distanceFunction)")
	print("\tassignClustersNearest(points, centroids, distanceFunction)")
	print("\tassignClustersBalanced(points, centroids, distanceFunction)")
	print("\tcomputeCentroids(points, clusterAssignment)")
	print("\tkMeansClustering(points, numberOfClusters, distanceFunction, "
	                         "initializeCentroidsFunction = initializeCentroidsAtRandom, "
	                         "assignClustersFunction = assignClustersNearest, "
	                         "maxIterations = 100, tolerance = 0.00000001)")
	print("\tcomputeStatistics(points, data, centroids, clusterAssignment, distanceFunction)")
	print("\tfindBestCluster(centroids, point, distanceFunction)")
	print("\tfindElbowPoint(x_values, y_values)")
	print("")

	if True:
		verbose = False

		runKMeansExample(1, 10, initializeCentroidsAtRandom, assignClustersNearest, verbose)
		runKMeansExample(1, 10, initializeCentroidsKMeansPlusPlus, assignClustersNearest, verbose)

		runKMeansExample(10, 16, initializeCentroidsAtRandom, assignClustersBalanced, verbose)
		runKMeansExample(10, 16, initializeCentroidsKMeansPlusPlus, assignClustersBalanced, verbose)
