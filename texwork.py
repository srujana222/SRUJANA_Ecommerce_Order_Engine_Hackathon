
from fastapi import FastAPI
from pydantic import BaseModel
import threading
import time
import random
from datetime import datetime

app = FastAPI(title="E-Commerce Order Engine")


inventory = {}
carts = {}
orders = {}
logs = []
events = []
user_orders_time = {}

inventory_lock = threading.Lock()
order_counter = 1
idempotency_keys = set()
user_coupons = {}

class Product(BaseModel):
    pid: str
    name: str
    price: float
    stock: int

class CartItem(BaseModel):
    user: str
    pid: str
    qty: int

class Coupon(BaseModel):
    user: str
    coupon: str

class OrderRequest(BaseModel):
    user: str
    idempotency_key: str

class CancelRequest(BaseModel):
    order_id: str

class ReturnRequest(BaseModel):
    order_id: str
    pid: str
    qty: int


def log_event(msg):
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

@app.post("/add_product")
def add_product(p: Product):
    if p.pid in inventory:
        return {"error": "Duplicate product"}

    if p.stock < 0:
        return {"error": "Invalid stock"}

    inventory[p.pid] = {
        "name": p.name,
        "price": p.price,
        "stock": p.stock
    }

    log_event(f"Product {p.pid} added")
    return {"msg": "Product added"}

@app.get("/products")
def view_products():
    return inventory


@app.post("/add_to_cart")
def add_to_cart(item: CartItem):
    if item.pid not in inventory:
        return {"error": "Product not found"}

    with inventory_lock:
        if inventory[item.pid]["stock"] >= item.qty:
            inventory[item.pid]["stock"] -= item.qty
            carts.setdefault(item.user, {})
            carts[item.user][item.pid] = carts[item.user].get(item.pid, 0) + item.qty
            log_event(f"{item.user} added {item.pid}")
            return {"msg": "Added to cart"}
        else:
            return {"error": "Not enough stock"}

@app.post("/remove_from_cart")
def remove_from_cart(item: CartItem):
    if item.user in carts and item.pid in carts[item.user]:
        qty = carts[item.user][item.pid]

        with inventory_lock:
            inventory[item.pid]["stock"] += qty

        del carts[item.user][item.pid]
        return {"msg": "Removed"}

@app.get("/cart/{user}")
def view_cart(user: str):
    return carts.get(user, {})

@app.post("/apply_coupon")
def apply_coupon(c: Coupon):
    if c.coupon not in ["SAVE10", "FLAT200"]:
        return {"error": "Invalid coupon"}

    user_coupons[c.user] = c.coupon
    return {"msg": "Coupon applied"}

def apply_discount(total, cart, coupon=None):
    if total > 1000:
        total *= 0.9

    for q in cart.values():
        if q > 3:
            total *= 0.95

    if coupon == "SAVE10":
        total *= 0.9
    elif coupon == "FLAT200":
        total -= 200

    return max(total, 0)


def process_payment():
    time.sleep(0.2)
    return random.random() > 0.3

def process_events():
    while events:
        event = events.pop(0)
        log_event(f"Processed {event}")


@app.post("/place_order")
def place_order(req: OrderRequest):
    global order_counter

    if req.idempotency_key in idempotency_keys:
        return {"error": "Duplicate request"}
    idempotency_keys.add(req.idempotency_key)

    if req.user not in carts or not carts[req.user]:
        return {"error": "Cart empty"}

    cart = carts[req.user]

    total = sum(inventory[p]["price"] * q for p, q in cart.items())
    coupon = user_coupons.get(req.user)
    total = apply_discount(total, cart, coupon)

    oid = f"O{order_counter}"
    order_counter += 1

    orders[oid] = {
        "user": req.user,
        "items": cart.copy(),
        "total": total,
        "status": "PENDING_PAYMENT"
    }

    events.append("ORDER_CREATED")

    
    now = time.time()
    user_orders_time.setdefault(req.user, []).append(now)
    if len([t for t in user_orders_time[req.user] if now - t < 60]) >= 3:
        return {"warning": "Fraud detected"}

    if process_payment():
        orders[oid]["status"] = "PAID"
        carts[req.user] = {}
        events.append("PAYMENT_SUCCESS")
        process_events()
        return {"msg": "Order success", "order_id": oid}
    else:
        for pid, q in cart.items():
            inventory[pid]["stock"] += q

        orders[oid]["status"] = "FAILED"
        return {"error": "Payment failed"}


@app.get("/orders")
def view_orders():
    return orders

@app.post("/cancel_order")
def cancel_order(req: CancelRequest):
    if req.order_id not in orders:
        return {"error": "Not found"}

    if orders[req.order_id]["status"] == "CANCELLED":
        return {"error": "Already cancelled"}

    for pid, q in orders[req.order_id]["items"].items():
        inventory[pid]["stock"] += q

    orders[req.order_id]["status"] = "CANCELLED"
    return {"msg": "Cancelled"}


@app.post("/return")
def return_product(r: ReturnRequest):
    if r.order_id not in orders:
        return {"error": "Order not found"}

    inventory[r.pid]["stock"] += r.qty
    orders[r.order_id]["total"] -= inventory[r.pid]["price"] * r.qty

    return {"msg": "Refund processed"}

@app.get("/low_stock")
def low_stock():
    return {k: v for k, v in inventory.items() if v["stock"] <= 2}


@app.get("/logs")
def view_logs():
    return logs


@app.post("/failure")
def inject_failure():
    if inventory:
        pid = list(inventory.keys())[0]
        inventory[pid]["stock"] = -5
    return {"msg": "Failure injected"}

@app.get("/simulate")
def simulate_users():
    def action(u):
        if inventory:
            pid = list(inventory.keys())[0]
            with inventory_lock:
                if inventory[pid]["stock"] > 0:
                    inventory[pid]["stock"] -= 1

    t1 = threading.Thread(target=action, args=("A",))
    t2 = threading.Thread(target=action, args=("B",))
    t1.start(); t2.start()
    t1.join(); t2.join()

    return {"msg": "Simulation complete"}