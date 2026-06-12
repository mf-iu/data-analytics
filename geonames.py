import sqlite3

# install missing packages using:
# python -m pip install ...

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def fetchData(database, sql, parameters = ()):
	"""
		Executes the SQL query and returns the resulting rows as a list of objects,
		each object having properties named after the queried columns.
		Note: Rename columns using "AS" to avoid duplicate column names.

		database:   Filename of the Sqlite database
		sql:        SQL statement
		parameters: Parameters to the SQL statement as a tuple

		Returns: List of rows as objects
		         Example: [ { geoname_id: 1, latitude: 50.0, longitude: 10.0 }, ... ]
	"""
	dbConnection = sqlite3.connect(database)
	cursor = dbConnection.cursor()

	cursor.execute(sql, parameters)

	# Extract the names of the columns returned by the SQL query.
	columnNames = []
	description = cursor.description
	for entry in description:
		columnNames.append(entry[0])

	# Return the resulting rows as a list of objects with properties named after the queried
	# columns and associated values
	data = []
	for row in cursor:
		entry = {}
		for columnIndex in range(len(row)):
			entry[columnNames[columnIndex]] = row[columnIndex]
		data.append(entry)

	dbConnection.close()

	return data

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def extractPoints(data, propertyNames):
	"""
		Extracts the elements with the given property names.

		data:         List of rows as objects
		              Example: [ { geoname_id: 1, latitude: 50.0, longitude: 10.0 }, ... ]
		propertyNames List of property names indicating specific properties of the objects in data
		              Example: [ "latitude", "longitude", ... ]

		Returns: List of points, each point being a list of values
		         Example [ [50.978056, 11.029167], [52.518611, 13.408333], ... ]
	"""
	points = []
	for entry in data:
		point = []
		for propertyName in propertyNames:
			point.append(entry[propertyName])
		points.append(point)

	return points

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def storeClustering(database, data, centroids, statistics, clusterAssignment):
	dbConnection = sqlite3.connect(database)

	dbConnection.execute("""
		DROP TABLE IF EXISTS clusters;
	""")
	dbConnection.execute("""
		CREATE TABLE clusters (
			cluster_id INTEGER PRIMARY KEY NOT NULL,
			latitude DOUBLE NOT NULL,
			longitude DOUBLE NOT NULL,
			variance DOUBLE,
			radius DOUBLE,
			wcss DOUBLE
		);
	""")

	dbConnection.execute("""
		DROP TABLE IF EXISTS cluster_assignments;
	""")
	dbConnection.execute("""
		CREATE TABLE cluster_assignments (
			geoname_id INTEGER PRIMARY KEY NOT NULL,
			cluster_id INTEGER NOT NULL
		);
	""")

	for centroidIndex in range(len(clusterAssignment)):
		# centroid = centroids[centroidIndex]

		stats = statistics[centroidIndex]
		geoCenter = stats["geoCenter"]
		latLong = geoCenter["point"]
		variance = geoCenter["variance"]
		radius = geoCenter["radius"]
		wcss = geoCenter["wcss"]

		dbConnection.execute("""
				INSERT INTO clusters (cluster_id, latitude, longitude, variance, radius, wcss)
				            VALUES (?, ?, ?, ?, ?, ?);
			""",
			(centroidIndex + 1, latLong[0], latLong[1], variance, radius, wcss)
		)

		pointIndices = clusterAssignment[centroidIndex]
		for pointIndex in pointIndices:
			geoname_id = data[pointIndex]["geoname_id"]
			dbConnection.execute("""
					INSERT INTO cluster_assignments (geoname_id, cluster_id) VALUES (?, ?);
				""",
				(geoname_id, centroidIndex + 1)
			)

	dbConnection.commit()
	dbConnection.close()

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if __name__ == "__main__":
	print("Available functions:")
	print("\tfetchData(database, sql, parameters = ())")
	print("\textractPoints(data, propertyNames)")
	print("\tstoreClustering(database, data, centroids, statistics, clusterAssignment)")
	print("")
