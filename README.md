# Ecommerce Order Engine (Hackathon Project)

## Overview

This project is a backend simulation of an e-commerce system built using FastAPI. It mimics real-world platforms like Amazon or Flipkart where multiple users interact with products, carts, and orders at the same time.

The system handles important backend challenges such as stock management, concurrency, payment failures, and order processing.

## Features Implemented

* Product management (add and view products)
* Multi-user cart system
* Real-time stock reservation
* Concurrency handling using locks
* Order placement with payment simulation
* Transaction rollback on failure
* Discount and coupon system
* Order cancellation
* Return and refund system
* Low stock alerts
* Event-driven processing (basic simulation)
* Fraud detection (multiple orders in short time)
* Idempotency handling (prevents duplicate orders)
* Failure injection system
* Audit logging

## Design Approach

* Used Python dictionaries as an in-memory database
* Implemented threading and locks to avoid race conditions
* Designed order placement as an atomic transaction
* Added event queue simulation for backend workflows
* Built REST APIs using FastAPI


## Project Structure

project/
│── app.py
│── requirements.txt
│── README.md


## How to Run

1. Install dependencies:
   pip install -r requirements.txt

2. Run the server:
   uvicorn app:app --reload

3. Open in browser:
   http://127.0.0.1:8000/docs


## Sample Workflow

1. Add product
2. Add item to cart
3. Apply coupon
4. Place order
5. View orders



## Assumptions

* Data is stored in memory (no database used)
* No authentication system (user is entered manually)
* Payment success/failure is randomly simulated
* This project is for learning and demonstration purposes


## Future Improvements

* Add database integration (MongoDB or MySQL)
* Implement user authentication
* Build frontend UI
* Deploy on cloud platforms
