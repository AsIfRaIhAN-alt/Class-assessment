# Pharmacy Shelf Intelligence System

A runnable local web application prototype for pharmacy expiry-risk monitoring and decision support.

## Features
- Product and batch-level inventory (each batch has its own expiry date).
- Supplier-specific return cutoff and return eligibility.
- Product-specific discount permission.
- Sales entry with FEFO stock reduction (first-expiry-first-out).
- Weighted moving-average sales estimate using 7/30/90-day sales rates.
- Expected leftover stock, approximate financial exposure, risk level and action recommendation.
- Daily decision dashboard, decision log, CSV import and JSON summary endpoint.
- SQLite database created automatically on first run.

## Requirements
- Python 3.10 or newer
- VS Code (or another editor)
- Internet only for the first installation of Python packages

## Run on Windows (VS Code terminal)
1. Extract the ZIP folder.
2. Open the extracted `pharmacy_shelf_intelligence` folder in VS Code.
3. Open **Terminal > New Terminal**.
4. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

5. Activate it:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run this once in that terminal:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .venv\Scripts\Activate.ps1
   ```

6. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Start the server:

   ```powershell
   python app.py
   ```

8. Open this address in your browser:

   http://127.0.0.1:5000

Keep the terminal running while using the website. Press `Ctrl+C` to stop the server.

## Demo data
The first run automatically creates a local `pharmacy.db` SQLite database with four sample products and synthetic sample sales. These values are for demonstration only. Replace them with verified pharmacy data before relying on recommendations.

To reset the demo database, stop the server, delete `pharmacy.db`, and run `python app.py` again.

## CSV import
Use **Import CSV** in the navigation. Required columns:

`sku,product_name,supplier,batch_code,quantity,expiry_date,purchase_price,selling_price,discount_allowed,return_cutoff_days,accepts_returns`

- Dates must use `YYYY-MM-DD`, e.g. `2027-03-31`.
- Boolean values: `yes` or `no`.
- One row represents one inventory batch.
- If multiple batches share a SKU, use the same SKU and different batch codes/expiry dates.
- Existing products are matched by SKU. Supplier policy is created only when the supplier does not already exist.

A template is included at `sample_inventory.csv`.

## Important assumptions and limitations
- This is a local educational prototype, not a validated commercial pharmacy system.
- Supplier cutoff means the stock must be returned at least that many days before expiry.
- Forecasting is a weighted moving average, not a trained ML model. It is a baseline that requires real historical sales to become useful.
- Sales are recorded against product-level history and stock is reduced by FEFO. The batch-level forecast allocates product-level expected demand proportionally across active batches; this is an approximation.
- If only month/year expiry is known, enter the actual printed expiry convention confirmed by the pharmacy. Do not guess the date.
- Financial exposure is estimated as expected leftover units multiplied by purchase price. It is not a guaranteed loss.
- Recommendations are advisory. The pharmacist/owner must verify supplier terms and all applicable medicine laws. Never sell expired, recalled, damaged, or otherwise unsuitable medicine.
- No login, multi-user access, external notifications, automated supplier returns, or payment processing are included.

## Useful routes
- `/` Dashboard
- `/inventory` Inventory
- `/products/new` Add product and batch
- `/suppliers` Supplier policies
- `/sales` Record sales
- `/decisions` Decision history
- `/import` CSV import
- `/api/summary` JSON summary
