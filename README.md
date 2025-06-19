# Odoo Predictive Engine

A machine learning module for Odoo that predicts sales demand and automatically triggers inventory alerts and sales opportunities.

## Features

- Automated data preparation pipeline
- Feature engineering for time-series sales data
- Random Forest regression model for demand prediction
- Automated inventory reorder rules
- Sales opportunity flagging
- Daily prediction generation

## How It Works

### Data Pipeline Architecture

1. **Data Extraction**:
   - Pulls sales orders (`sale.order`) with state='sale'
   - Gathers inventory movements (`stock.move`) and stock levels (`stock.quant`)
   - Uses Odoo's `search_read()` for efficient data retrieval

2. **Data Cleaning**:
   - Filters records from the last 365 days by default
   - Handles missing values in product and quantity fields
   - Converts date fields to proper datetime format

3. **Feature Engineering**:
    - Creates lag features for sales quantities
    - Generates rolling averages for sales trends
    - Encodes categorical variables (e.g., product categories) 
    - Normalizes numerical features (e.g., sales quantities)
4. **Model Training**:
   - Splits data into training and test sets
    - Trains a Random Forest regression model using `scikit-learn`
    - Evaluates model performance using metrics like RMSE and R-squared
5. **Prediction Generation**:
    - Generates daily sales predictions for the next 30 days
    - Flags products with low stock levels and high predicted demand
    - Creates sales opportunities for flagged products
6. **Automated Alerts**:
   - Sends email notifications for low stock products
    - Updates inventory reorder rules based on predictions
## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/gemechisworku/odoo-predictive-engine.git

    cd odoo-predictive-engine
    ```
2. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3. Install the Odoo module:
    - Copy the module folder to your Odoo addons directory.
    - Update the Odoo app list and install the "Predictive Engine" module from the Odoo interface.
4. Configure the module:
    - Set the desired prediction frequency (daily, weekly, etc.)
    - Configure email settings for alerts
    - Adjust model parameters if necessary 
5. Run the data pipeline:
    - Navigate to the module in Odoo and trigger the data pipeline to start generating predictions.
## Usage
- Navigate to the "Predictive Engine" module in Odoo.
- View daily sales predictions and inventory alerts.
- Monitor sales opportunities created from low stock predictions.
## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any bugs or feature requests.
## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details
