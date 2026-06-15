import numpy as np

# install missing packages using:
# python -m pip install ...

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def linearRegression(points, y):
	numberOfPoints = len(points)

	# Add a column of ones before each data point
	x = np.c_[np.ones((numberOfPoints, 1)), points]

	# Fit linear regression using pseudoinverse
	beta = np.linalg.pinv(x).dot(y)

	return (beta[0], beta[1:])

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def predictSalariesExample(numberOfPoints, newCandidate):
	rng = np.random.default_rng()
	#rng = np.random.default_rng(42)

	# Generate synthetic features
	# =====================================================
	# x1 = years of experience (0–15)
	# x2 = education level (1–5)
	# x3 = skill score (0–100)
	# x4 = leadership score (0–10)
	points = np.column_stack([
		rng.uniform(0, 15, numberOfPoints),
		rng.integers(1, 6, numberOfPoints),
		rng.uniform(0, 100, numberOfPoints),
		rng.uniform(0, 10, numberOfPoints)
	])

	# True underlying salary model (in T€)
	# =====================================================
	# salary = 30
	#        + 5.0 * experience
	#        + 4.0 * education
	#        + 0.3 * skill
	#        + 2.5 * leadership
	#        + noise
	noise = rng.normal(-30, 10, numberOfPoints)
	salaries = (
		30
		+ 5.0 * points[:, 0]
		+ 4.0 * points[:, 1]
		+ 0.3 * points[:, 2]
		+ 2.5 * points[:, 3]
		+ noise
	)

	(intercept, coefficients) = linearRegression(points, salaries)

	# Predictions
	predictedSalaries = points.dot(coefficients) + intercept

	# Output results
	print("=== Linear Regression Model for Salary ===")
	print(f"\tIntercept:  {intercept:.2f} T€")
	print(f"\tExperience: {coefficients[0]:.2f}")
	print(f"\tEducation:  {coefficients[1]:.2f}")
	print(f"\tSkill:      {coefficients[2]:.2f}")
	print(f"\tLeadership: {coefficients[3]:.2f}")
	print("")

	# R² score
	ss_res = np.sum((salaries - predictedSalaries) ** 2)
	ss_tot = np.sum((salaries - np.mean(salaries)) ** 2)
	rSquared = 1 - (ss_res / ss_tot)

	print(f"\tR² Score: {rSquared:.4f}")
	print("")

	print("Actual vs Predicted Salary (T€)")
	print("--------------------------------")

	for actual, pred in zip(salaries, predictedSalaries):
		print(f"{actual:8.2f} -> {pred:8.2f}")
	print("")

	# =====================================================
	# Predict new candidate salary
	# =====================================================

	predictedCandidateSalary = np.array(newCandidate).dot(coefficients) + intercept

	print(f"Predicted salary for {newCandidate[0]} years experience, "
	      f"education level {newCandidate[1]}, "
	      f"skill level {newCandidate[2]}, "
	      f"leadership level {newCandidate[3]}: {predictedCandidateSalary:.2f} T€")

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if __name__ == "__main__":
	predictSalariesExample(
		30, # number of existing employees
		[
			 7, # years of experience
			 4, # education level
			85, # skill
			 7  # leadership
		]
	)

