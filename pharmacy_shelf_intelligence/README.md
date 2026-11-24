# Pharmacy Shelf Intelligence System

An AI-assisted pharmacy inventory management and decision-support system designed to help pharmacy owners monitor medicine expiry dates, forecast product demand, identify potential inventory losses, and make informed stock management decisions.

## 1. Project Overview

Managing hundreds of pharmaceutical products with different expiry dates and supplier return policies can be time-consuming and challenging.

Traditional inventory management approaches mainly rely on manually checking expiry dates and maintaining stock registers. This often results in missed supplier return deadlines, unnecessary alerts, and financial losses caused by expired medicines.

The **Pharmacy Shelf Intelligence System** addresses this problem by combining inventory management, sales forecasting, expiry-risk analysis, and an intelligent recommendation engine.

Instead of presenting a long list of products approaching expiry, the system identifies only the products that require attention and provides actionable recommendations based on their sales performance, remaining shelf life, supplier return policies, and discount permissions.

## 2. Project Objectives

The main objectives of this project are:

- Automate pharmacy inventory and expiry-date monitoring.
- Identify slow-moving products that may remain unsold before expiry.
- Forecast expected product demand using historical sales data.
- Manage supplier-specific stock return policies.
- Maintain product-specific discount permissions.
- Estimate potential financial exposure from unsold inventory.
- Prioritize products according to urgency and financial risk.
- Generate actionable daily recommendations.
- Reduce manual inventory checking and prevent avoidable financial losses.

## 3. Key Features

### 3.1 Inventory Management
- Add and manage pharmaceutical products.
- Maintain product information, purchase prices, and selling prices.
- Track individual inventory batches.
- Store separate expiry dates and quantities for different batches.
- View all recorded inventory through a centralized dashboard.

### 3.2 Supplier Policy Management
- Maintain supplier information.
- Configure supplier-specific return cutoff periods.
- Record whether a supplier accepts product returns.
- Evaluate return eligibility based on supplier policies and expiry dates.

### 3.3 Product Discount Management
- Maintain individual discount permissions for products.
- Prevent the recommendation engine from suggesting unauthorized discounts.
- Identify alternative actions when discounting is not permitted.

### 3.4 Sales Recording and Tracking
- Record product sales and transaction dates.
- Maintain historical sales information.
- Automatically reduce inventory using the FEFO (First Expiry, First Out) approach.
- Use recorded sales data for demand estimation.

### 3.5 Sales Forecasting
The system uses a weighted moving-average approach to estimate future product demand.

It considers sales activity over three periods:

- Last 7 days.
- Last 30 days.
- Last 90 days.

Recent sales receive greater weight when calculating the estimated average daily sales rate.

### 3.6 Expiry-Risk Analysis
The system evaluates inventory batches using:

- Remaining days until expiry.
- Supplier return deadlines.
- Current stock quantities.
- Estimated future sales.
- Expected leftover quantities.
- Product discount permissions.

### 3.7 Financial-Risk Estimation
The system estimates potential financial exposure using the expected leftover quantity and purchase price per unit.

This helps pharmacy owners identify products that could result in significant financial losses.

### 3.8 Intelligent Recommendation Engine
The recommendation engine combines sales estimates, expiry information, and supplier policies to suggest appropriate actions.

Possible recommendations include:

- Contacting suppliers for stock returns.
- Reviewing permitted discount strategies.
- Continuing normal sales for products expected to sell before expiry.
- Requesting manual intervention when no return or discount option is available.
- Quarantining expired products for appropriate handling.

### 3.9 Decision Dashboard
The dashboard provides:

- Total monitored products.
- Number of inventory batches.
- Products requiring attention.
- Estimated financial exposure.
- Prioritized inventory recommendations.
- Individual product and batch analysis.

The system focuses on displaying products requiring decisions rather than overwhelming users with the entire inventory.

### 3.10 Decision Tracking
- Record decisions made by the pharmacy owner.
- Maintain a history of recommended and selected actions.
- Store notes explaining individual decisions.
- Support manual review and human verification.

### 3.11 CSV Inventory Import
The system supports importing multiple inventory batches through a CSV file.

This reduces the need to enter hundreds of products individually.

## 4. Technologies Used

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| Frontend | HTML, CSS |
| Database | SQLite |
| Database Integration | Flask-SQLAlchemy |
| Data Processing | Python |
| Forecasting | Weighted Moving Average |
| Development Environment | Visual Studio Code |

## 5. System Workflow

The system follows these main stages:

1. **Data Collection:** Product information, inventory quantities, expiry dates, supplier policies, and sales records are collected.

2. **Inventory Management:** Products and their individual batches are stored in the database.

3. **Sales Analysis:** Historical sales information is analyzed to estimate average daily demand.

4. **Demand Forecasting:** The system estimates how much of each product may sell before its expiry date.

5. **Expiry-Risk Assessment:** Expected leftover stock and supplier return deadlines are calculated.

6. **Financial-Risk Estimation:** Potential financial exposure is estimated using purchase prices and expected leftover quantities.

7. **Decision Generation:** The recommendation engine identifies appropriate actions based on available supplier return and discount options.

8. **Prioritization:** Products are ranked according to urgency and potential risk.

9. **Decision Tracking:** The pharmacy owner reviews recommendations and records the actions taken.

## 6. Installation and Setup

### Requirements

- Python 3.10 or newer.
- Visual Studio Code.
- Internet connection for installing Python dependencies.

### Step 1: Extract the Project

Download and extract the project ZIP folder.

Open the extracted `pharmacy_shelf_intelligence` folder in Visual Studio Code.

### Step 2: Open the Terminal

In VS Code, navigate to:

**Terminal → New Terminal**

### Step 3: Create a Virtual Environment

Run:

```bash
py -m venv .venv
```

### Step 4: Activate the Virtual Environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### Step 5: Install Dependencies

Run:

```bash
pip install -r requirements.txt
```

### Step 6: Start the Application

Run:

```bash
python app.py
```

The Flask development server will start locally.

### Step 7: Open the Application

Open your browser and navigate to:

```text
http://127.0.0.1:5000
```

The Pharmacy Shelf Intelligence dashboard should now be accessible.

Keep the terminal running while using the application.

To stop the server, press `Ctrl + C` in the terminal.

## 7. Database Management

The application uses SQLite as its database.

The database is automatically created when the application runs for the first time.

The main database entities include:

- Suppliers
- Products
- Inventory Batches
- Sales Transactions
- Decisions

The application uses SQLAlchemy to manage database operations and relationships.

The initial database is populated with sample products and synthetic sales records for demonstration purposes.

## 8. CSV Import Format

The system supports importing inventory information through a CSV file.

The required column names are:

```text
sku,product_name,supplier,batch_code,quantity,expiry_date,purchase_price,selling_price,discount_allowed,return_cutoff_days,accepts_returns
```

Example:

```csv
MED-101,Sample Medicine A,ACI,BATCH-A1,50,2027-03-31,100,120,yes,90,yes
MED-102,Sample Medicine B,Square,BATCH-B1,30,2027-01-31,80,100,no,60,yes
```

Important requirements:

- Expiry dates must use the `YYYY-MM-DD` format.
- Boolean values should use `yes` or `no`.
- Each row represents an individual inventory batch.
- Multiple batches of the same product can share the same SKU while having different batch codes and expiry dates.

A sample CSV file is included in the project folder.

## 9. Project Limitations and Future Improvements

The current implementation is an initial working prototype. Several improvements can be introduced in future versions.

### Current Limitations

- Sales forecasting currently uses a weighted moving average rather than a trained machine-learning model.
- Forecast accuracy depends on the availability and quality of historical sales data.
- Batch-level demand estimation is approximate because sales history is maintained at the product level.
- Supplier policies and product permissions must be entered and updated manually.
- The current application does not include user authentication or multi-user access.
- External email, SMS, and WhatsApp notifications are not implemented.
- Recommendations require verification by the pharmacy owner.

### Future Improvements

- Introduce advanced machine-learning forecasting models.
- Improve demand prediction using seasonal sales patterns.
- Implement automated daily background analysis.
- Add email and mobile notifications.
- Introduce user authentication and role-based access control.
- Improve batch-level sales tracking.
- Add interactive analytics and reporting.
- Implement automated model evaluation and forecasting improvements.
- Support multiple pharmacy branches.

## 10. Expected Outcomes

The proposed system aims to:

- Reduce manual inventory monitoring.
- Identify slow-moving products earlier.
- Prevent missed supplier return opportunities.
- Reduce avoidable losses caused by expired medicines.
- Improve inventory management decisions.
- Minimize unnecessary notifications.
- Help pharmacy owners focus on the products that genuinely require attention.

## 11. Conclusion

The Pharmacy Shelf Intelligence System transforms traditional expiry-date monitoring into an intelligent inventory decision-support process.

By combining sales forecasting, supplier-specific return policies, product discount restrictions, expiry-risk assessment, and financial-risk estimation, the system helps pharmacy owners make more informed decisions about their inventory.

Rather than simply identifying products approaching expiry, the system focuses on understanding which products are likely to remain unsold and what actions can be taken to minimize potential losses.

**The ultimate goal is to help pharmacy owners spend less time checking inventory and more time making the decisions that matter.**
