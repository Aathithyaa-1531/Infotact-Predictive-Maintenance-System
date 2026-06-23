# Predictive Maintenance System

## About the Project

This project is based on the AI4I 2020 Predictive Maintenance Dataset and focuses on predicting machine failures using Machine Learning. The main goal is to identify whether a machine is likely to fail based on its operating conditions such as temperature, rotational speed, torque, and tool wear. Predictive maintenance helps industries reduce unexpected breakdowns and improve machine reliability.

## Dataset Information

The dataset contains machine operating parameters and failure information. Some of the important features used in this project are:

* Type (L, M, H)
* Air Temperature [K]
* Process Temperature [K]
* Rotational Speed [rpm]
* Torque [Nm]
* Tool Wear [min]

Target Variable:

* Machine Failure (0 = No Failure, 1 = Failure)

## What We Did

* Loaded and explored the dataset
* Cleaned and preprocessed the data
* Removed unnecessary columns such as UDI and Product ID
* Performed feature engineering to create additional useful features
* Split the data into training and testing sets
* Trained Machine Learning models including Decision Tree and Random Forest
* Evaluated model performance using different metrics

## Feature Engineering

To improve model performance, I created some additional features:

* Temperature Difference
* Power Index
* Torque RPM Ratio

## Models Used

* Decision Tree Classifier
* Random Forest Classifier

After comparing both models, Random Forest provided better overall performance and was selected as the final model.

## Results

Random Forest Model Performance:

* Precision: 95%
* Recall: 75.4%
* F1 Score: 82.9%

These results show that the model can effectively identify machine failures while maintaining a good balance between precision and recall.

## Technologies Used

* Python
* Pandas
* NumPy
* Matplotlib
* Seaborn
* Scikit-learn
* Jupyter Notebook

## Future Scope

Some improvements that can be added in the future:

* Deploy the model using Flask
* Create a web dashboard for predictions
* Integrate real-time sensor data
* Explore advanced models such as XGBoost

## Author

AATHITHYAA E

B.Tech Artificial Intelligence and Data Science Student

