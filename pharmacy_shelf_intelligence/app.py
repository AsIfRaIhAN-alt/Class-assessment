from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import csv, io, os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.path.dirname(__file__), "pharmacy.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    return_cutoff_days = db.Column(db.Integer, default=90)  # must be returned this many days before expiry
    accepts_returns = db.Column(db.Boolean, default=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"), nullable=False)
    purchase_price = db.Column(db.Float, default=0)
    selling_price = db.Column(db.Float, default=0)
    discount_allowed = db.Column(db.Boolean, default=False)
    supplier = db.relationship("Supplier", backref="products")

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    batch_code = db.Column(db.String(80), default="")
    quantity = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.Date, nullable=False)
    product = db.relationship("Product", backref="batches")

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sold_on = db.Column(db.Date, nullable=False, default=date.today)
    product = db.relationship("Product", backref="sales")

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batch.id"), nullable=False)
    action = db.Column(db.String(40), nullable=False)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    batch = db.relationship("Batch", backref="decisions")

def average_daily_sales(product, days):
    start = date.today() - timedelta(days=days-1)
    total = db.session.query(func.coalesce(func.sum(Sale.quantity), 0)).filter(
        Sale.product_id == product.id, Sale.sold_on >= start, Sale.sold_on <= date.today()
    ).scalar() or 0
    return total / float(days)

def forecast(product, days_to_expiry):
    # Weighted moving average: recent sales receive more weight.
    a7, a30, a90 = (average_daily_sales(product, d) for d in (7, 30, 90))
    rate = 0.5*a7 + 0.3*a30 + 0.2*a90
    expected = min(sum(b.quantity for b in product.batches), max(0, rate * max(0, days_to_expiry)))
    confidence = "Low" if len(product.sales) < 5 else ("Medium" if len(product.sales) < 20 else "Higher")
    return rate, round(expected), confidence

def assess(batch):
    today = date.today()
    product, supplier = batch.product, batch.product.supplier
    days = (batch.expiry_date - today).days
    return_days = days - supplier.return_cutoff_days
    rate, expected_total, confidence = forecast(product, days)
    # Allocate expected demand to this batch only; approximate because sales are product-level.
    stock_all = sum(max(0, b.quantity) for b in product.batches if b.expiry_date >= today)
    share = (batch.quantity / stock_all) if stock_all else 0
    expected_batch_sales = min(batch.quantity, round(expected_total * share))
    leftover = max(0, batch.quantity - expected_batch_sales)
    surplus_ratio = (leftover / batch.quantity * 100) if batch.quantity else 0
    exposure = round(leftover * product.purchase_price, 2)

    return_eligible = supplier.accepts_returns and days > 0 and return_days >= 0
    return_closing = return_eligible and return_days <= 14
    risk = "Low"
    if days <= 0 and batch.quantity > 0:
        risk = "Expired"
    elif leftover > 0 and surplus_ratio >= 60:
        risk = "High"
    elif leftover > 0 and surplus_ratio >= 25:
        risk = "Medium"

    if risk == "Expired":
        recommendation = "Quarantine and handle under applicable pharmacy rules"
        priority = 100
    elif leftover == 0:
        recommendation = "Continue normal sales; monitor FEFO stock rotation"
        priority = 0
    elif return_eligible and (return_closing or risk == "High"):
        recommendation = f"Contact {supplier.name} about returning up to {leftover} units"
        priority = 90 if return_closing else 75
    elif return_eligible:
        recommendation = f"Return may be available; review returning up to {leftover} units"
        priority = 55
    elif product.discount_allowed and days > 0:
        recommendation = "Review a permitted discount/clearance strategy"
        priority = 65 if risk == "High" else 45
    else:
        recommendation = "Manual review: no return or discount option is recorded"
        priority = 70 if risk == "High" else 40

    if days <= 30 and batch.quantity > 0:
        priority = max(priority, 95)
    elif days <= 60 and leftover > 0:
        priority = max(priority, 80)

    needs_action = priority >= 40 and batch.quantity > 0
    return {
        "batch": batch, "product": product, "days": days, "return_days": return_days,
        "daily_sales": round(rate, 2), "expected_sales": expected_batch_sales,
        "leftover": leftover, "surplus_ratio": round(surplus_ratio),
        "exposure": exposure, "confidence": confidence, "risk": risk,
        "return_eligible": return_eligible, "return_closing": return_closing,
        "recommendation": recommendation, "priority": priority, "needs_action": needs_action
    }

@app.context_processor
def inject_today():
    return {"today": date.today()}

@app.route("/")
def dashboard():
    assessments = [assess(b) for b in Batch.query.order_by(Batch.expiry_date).all()]
    actions = sorted([a for a in assessments if a["needs_action"]], key=lambda x: x["priority"], reverse=True)
    total_units = sum(max(0, b.quantity) for b in Batch.query.all())
    exposure = sum(a["exposure"] for a in assessments)
    return render_template("dashboard.html", actions=actions[:20], total_products=Product.query.count(),
                           total_batches=Batch.query.count(), total_units=total_units,
                           exposure=exposure, action_count=len(actions), assessments=assessments)

@app.route("/inventory")
def inventory():
    batches = Batch.query.join(Product).order_by(Batch.expiry_date).all()
    return render_template("inventory.html", batches=batches)

@app.route("/products/new", methods=["GET", "POST"])
def new_product():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    if request.method == "POST":
        try:
            supplier_id = int(request.form["supplier_id"])
            product = Product(sku=request.form["sku"].strip(), name=request.form["name"].strip(),
                              supplier_id=supplier_id, purchase_price=float(request.form.get("purchase_price") or 0),
                              selling_price=float(request.form.get("selling_price") or 0),
                              discount_allowed=request.form.get("discount_allowed") == "on")
            db.session.add(product); db.session.flush()
            batch = Batch(product_id=product.id, batch_code=request.form.get("batch_code","").strip(),
                          quantity=int(request.form["quantity"]),
                          expiry_date=date.fromisoformat(request.form["expiry_date"]))
            db.session.add(batch); db.session.commit()
            flash("Product and first batch added.", "success")
            return redirect(url_for("inventory"))
        except Exception as e:
            db.session.rollback(); flash(f"Could not save product: {e}", "error")
    return render_template("new_product.html", suppliers=suppliers)

@app.route("/suppliers", methods=["GET", "POST"])
def suppliers():
    if request.method == "POST":
        try:
            supplier = Supplier(name=request.form["name"].strip(),
                                return_cutoff_days=int(request.form.get("return_cutoff_days") or 90),
                                accepts_returns=request.form.get("accepts_returns") == "on")
            db.session.add(supplier); db.session.commit()
            flash("Supplier added.", "success")
            return redirect(url_for("suppliers"))
        except Exception as e:
            db.session.rollback(); flash(f"Could not add supplier: {e}", "error")
    return render_template("suppliers.html", suppliers=Supplier.query.order_by(Supplier.name).all())

@app.route("/sales", methods=["GET", "POST"])
def sales():
    products = Product.query.order_by(Product.name).all()
    if request.method == "POST":
        try:
            sale = Sale(product_id=int(request.form["product_id"]), quantity=int(request.form["quantity"]),
                        sold_on=date.fromisoformat(request.form["sold_on"]))
            if sale.quantity <= 0: raise ValueError("Quantity must be positive.")
            db.session.add(sale)
            # Reduce earliest-expiring non-expired batches first (FEFO).
            remaining = sale.quantity
            batches = Batch.query.filter_by(product_id=sale.product_id).filter(Batch.expiry_date >= sale.sold_on).order_by(Batch.expiry_date).all()
            for batch in batches:
                used = min(batch.quantity, remaining)
                batch.quantity -= used; remaining -= used
                if remaining <= 0: break
            if remaining > 0:
                db.session.rollback()
                flash("Sale exceeds available non-expired stock. No changes were saved.", "error")
            else:
                db.session.commit(); flash("Sale recorded and stock reduced using FEFO.", "success")
            return redirect(url_for("sales"))
        except Exception as e:
            db.session.rollback(); flash(f"Could not record sale: {e}", "error")
    recent = Sale.query.order_by(Sale.sold_on.desc(), Sale.id.desc()).limit(15).all()
    return render_template("sales.html", products=products, recent=recent)

@app.route("/decisions", methods=["GET", "POST"])
def decisions():
    if request.method == "POST":
        d = Decision(batch_id=int(request.form["batch_id"]), action=request.form["action"],
                     notes=request.form.get("notes","").strip())
        db.session.add(d); db.session.commit()
        flash("Decision recorded. Update stock separately after the real return/adjustment is confirmed.", "success")
        return redirect(url_for("decisions"))
    rows = Decision.query.order_by(Decision.created_at.desc()).limit(50).all()
    return render_template("decisions.html", rows=rows, batches=Batch.query.join(Product).order_by(Product.name).all())

@app.route("/batch/<int:batch_id>")
def batch_detail(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    result = assess(batch)
    return render_template("batch_detail.html", r=result)

@app.route("/import", methods=["GET", "POST"])
def import_csv():
    if request.method == "POST":
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename.lower().endswith(".csv"):
            flash("Please choose a CSV file.", "error"); return redirect(url_for("import_csv"))
        try:
            text = uploaded.stream.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            count = 0
            for row in reader:
                supplier_name = row["supplier"].strip()
                supplier = Supplier.query.filter_by(name=supplier_name).first()
                if not supplier:
                    supplier = Supplier(name=supplier_name,
                        return_cutoff_days=int(row.get("return_cutoff_days") or 90),
                        accepts_returns=str(row.get("accepts_returns","yes")).lower() in ("yes","true","1"))
                    db.session.add(supplier); db.session.flush()
                sku = row["sku"].strip()
                product = Product.query.filter_by(sku=sku).first()
                if not product:
                    product = Product(sku=sku, name=row["product_name"].strip(), supplier_id=supplier.id,
                        purchase_price=float(row.get("purchase_price") or 0),
                        selling_price=float(row.get("selling_price") or 0),
                        discount_allowed=str(row.get("discount_allowed","no")).lower() in ("yes","true","1"))
                    db.session.add(product); db.session.flush()
                expiry = date.fromisoformat(row["expiry_date"].strip())
                batch = Batch(product_id=product.id, batch_code=row.get("batch_code","").strip(),
                              quantity=int(row["quantity"]), expiry_date=expiry)
                db.session.add(batch); count += 1
            db.session.commit(); flash(f"Imported {count} inventory batches.", "success")
        except Exception as e:
            db.session.rollback(); flash(f"Import failed. Check the CSV columns and values: {e}", "error")
        return redirect(url_for("inventory"))
    return render_template("import.html")

@app.route("/api/summary")
def api_summary():
    assessments = [assess(b) for b in Batch.query.all()]
    return jsonify({"products": Product.query.count(), "batches": Batch.query.count(),
                    "decisions_required": sum(1 for a in assessments if a["needs_action"]),
                    "estimated_exposure": round(sum(a["exposure"] for a in assessments), 2)})

def seed():
    if Supplier.query.count() > 0: return
    aci = Supplier(name="ACI", return_cutoff_days=90, accepts_returns=True)
    square = Supplier(name="Square", return_cutoff_days=60, accepts_returns=True)
    beximco = Supplier(name="Beximco", return_cutoff_days=90, accepts_returns=True)
    db.session.add_all([aci, square, beximco]); db.session.flush()
    examples = [
        ("MED-001","Napa Extra",aci,100,120,True,[
            ("NAPA-0327",40,date(2027,3,31))]),
        ("MED-002","Seclo 20mg",square,35,45,False,[
            ("SEC-0127",12,date(2027,1,31))]),
        ("MED-003","Cough syrup 100ml",beximco,55,70,True,[
            ("COU-1226",6,date(2026,12,31))]),
        ("MED-004","Vitamin C",aci,25,35,True,[
            ("VTC-0227",100,date(2027,2,28))]),
    ]
    for sku,name,supplier,cost,price,discount,batches in examples:
        p = Product(sku=sku,name=name,supplier=supplier,purchase_price=cost,
                    selling_price=price,discount_allowed=discount)
        db.session.add(p); db.session.flush()
        for code,qty,exp in batches:
            db.session.add(Batch(product_id=p.id,batch_code=code,quantity=qty,expiry_date=exp))
        # Synthetic demonstration sales: explicitly sample data, replace with real records.
        recent = 42 if sku=="MED-001" else 2 if sku=="MED-002" else 1
        middle = 120 if sku=="MED-001" else 8 if sku=="MED-002" else 5
        older = 330 if sku=="MED-001" else 24 if sku=="MED-002" else 15
        # Separate date buckets make the rolling 7/30/90-day totals cumulative as intended.
        db.session.add(Sale(product_id=p.id, quantity=recent, sold_on=date.today()-timedelta(days=3)))
        db.session.add(Sale(product_id=p.id, quantity=max(0, middle-recent), sold_on=date.today()-timedelta(days=15)))
        db.session.add(Sale(product_id=p.id, quantity=max(0, older-middle), sold_on=date.today()-timedelta(days=60)))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed()

if __name__ == "__main__":
    app.run(debug=True)
