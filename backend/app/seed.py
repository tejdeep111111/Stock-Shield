from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from .models import Disruption, Inventory, Product, Region, SalesHistory, Shipment, Supplier


PRODUCTS = [
    ("SKU-1001", "Wireless Headphones", "Audio", 120.0, 70.0, "high"),
    ("SKU-1002", "Laptop Stand", "Accessories", 45.0, 21.0, "medium"),
    ("SKU-1003", "USB-C Hub", "Accessories", 60.0, 30.0, "high"),
    ("SKU-1004", "Mechanical Keyboard", "Peripherals", 140.0, 82.0, "high"),
    ("SKU-1005", "Webcam", "Peripherals", 90.0, 50.0, "medium"),
    ("SKU-1006", "Portable Charger", "Power", 50.0, 25.0, "medium"),
    ("SKU-1007", "Monitor", "Displays", 300.0, 210.0, "high"),
    ("SKU-1008", "Smart Speaker", "Audio", 110.0, 65.0, "medium"),
    ("SKU-1009", "Office Chair", "Furniture", 260.0, 170.0, "low"),
    ("SKU-1010", "Gaming Mouse", "Peripherals", 80.0, 42.0, "medium"),
]

REGIONS = ["Northeast", "Southeast", "Midwest", "West"]
SUPPLIERS = [
    ("Supplier A", 0.62, 8, 600, True),
    ("Supplier B", 0.88, 5, 900, True),
    ("Supplier C", 0.81, 6, 850, False),
    ("Supplier D", 0.73, 9, 500, False),
    ("Supplier E", 0.93, 4, 1000, True),
]


def seed_data(db: Session) -> None:
    if db.query(Product).count() > 0:
        return

    products = [Product(sku=s, name=n, category=c, unit_price=p, unit_cost=co, criticality=cr) for s, n, c, p, co, cr in PRODUCTS]
    regions = [Region(name=r) for r in REGIONS]
    suppliers = [
        Supplier(
            name=name,
            reliability_score=rel,
            default_lead_time_days=lead,
            capacity_units=cap,
            expedited_available=exp,
        )
        for name, rel, lead, cap, exp in SUPPLIERS
    ]

    db.add_all(products + regions + suppliers)
    db.flush()

    inv_rows = []
    for p in products:
        for idx, r in enumerate(regions):
            supplier = suppliers[(p.id + idx) % len(suppliers)]
            base = 200 + (p.id * 9) - (idx * 18)
            if p.name == "Wireless Headphones" and r.name == "Northeast":
                base = 120
            if p.name == "USB-C Hub" and r.name == "Northeast":
                base = 80
            if p.name == "Mechanical Keyboard" and r.name == "Midwest":
                base = 90
            inv_rows.append(
                Inventory(
                    product_id=p.id,
                    region_id=r.id,
                    supplier_id=supplier.id,
                    on_hand_units=max(40, base),
                    reserved_units=20 if r.name in {"Northeast", "Midwest"} else 15,
                    in_transit_units=25,
                    warehouse_capacity=650,
                    reorder_point=120,
                    safety_stock=60,
                )
            )
    db.add_all(inv_rows)

    today = date.today()
    sales_rows = []
    for day_offset in range(180, 0, -1):
        d = today - timedelta(days=day_offset)
        weekday = d.weekday()
        weekend_boost = 1.15 if weekday in {4, 5} else 0.95
        for p in products:
            for r in regions:
                region_mult = {"Northeast": 1.2, "Southeast": 1.0, "Midwest": 0.9, "West": 1.05}[r.name]
                base = (18 + (p.id % 5) * 4) * weekend_boost * region_mult
                if p.name == "Wireless Headphones" and r.name == "Northeast":
                    base *= 1.35
                if day_offset in {21, 22, 23} and r.name == "Northeast":
                    base *= 1.4
                units = int(round(base))
                sales_rows.append(
                    SalesHistory(
                        date=d,
                        product_id=p.id,
                        region_id=r.id,
                        units_sold=max(units, 1),
                        price=p.unit_price,
                        promotion_flag=(day_offset % 30 == 0),
                    )
                )
    db.add_all(sales_rows)

    shipment_rows = []
    shipment_id = 1
    for p in products:
        for r in regions:
            supplier = suppliers[(p.id + r.id) % len(suppliers)]
            for lag in (14, 7, 3):
                order_date = today - timedelta(days=lag + supplier.default_lead_time_days)
                expected = order_date + timedelta(days=supplier.default_lead_time_days)
                delayed = (shipment_id % 4 == 0)
                actual = expected + timedelta(days=3 if delayed else 0)
                status = "delivered"
                shipment_rows.append(
                    Shipment(
                        supplier_id=supplier.id,
                        product_id=p.id,
                        region_id=r.id,
                        ordered_units=120,
                        order_date=order_date,
                        expected_arrival_date=expected,
                        actual_arrival_date=actual,
                        status=status,
                    )
                )
                shipment_id += 1
    db.add_all(shipment_rows)

    disruptions = [
        Disruption(
            type="demand_shock",
            name="Back-to-School Northeast Headphones Surge",
            product_id=products[0].id,
            region_id=regions[0].id,
            supplier_id=None,
            severity=0.6,
            start_date=today,
            duration_days=7,
            demand_multiplier=1.5,
            delay_days=0,
            active=True,
        ),
        Disruption(
            type="supplier_delay",
            name="Port Congestion Supplier A",
            product_id=products[0].id,
            region_id=regions[0].id,
            supplier_id=suppliers[0].id,
            severity=0.8,
            start_date=today,
            duration_days=10,
            demand_multiplier=1.0,
            delay_days=8,
            active=True,
        ),
    ]
    db.add_all(disruptions)
    db.commit()
