from fastapi import HTTPException, Depends, APIRouter, Request
from sqlalchemy.orm import Session
from .database import get_db
from .schemas import OrderResponse, OrderItemResponse, PaymentResponse, PaymentRequest, NotificationResponse
from .auth import get_current_user
from .model import User, Product, Cart, Order, OrderItem, Payment, Notification
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
order = APIRouter(prefix="/orders", tags=["orders"])


@order.post("/create-order", response_model=OrderResponse)
def create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_item = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).all()

    if not cart_item:
        raise HTTPException(
            status_code=400,
            detail="Cart is Empty"
        )

    total_amount = 0

    for i in cart_item:

        product = db.query(Product).filter(
            Product.id == i.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        if i.quentity > product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.product_name}"
            )

        total_amount += product.product_price * i.quentity

    new_order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        payment_status="Pending",
        order_status="Pending"
    )

    db.add(new_order)
    db.flush()

    # Create order confirmation notification
    new_notification = Notification(
        user_id=current_user.id,
        type="ORDER_CONFIRMATION",
        message=f"Your order #{new_order.id} has been placed successfully.",
        is_read=False
    )

    db.add(new_notification)

    for i in cart_item:

        product = db.query(Product).filter(
            Product.id == i.product_id
        ).first()

        new_order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=i.quentity,
            price=product.product_price
        )

        db.add(new_order_item)

        product.stock -= i.quentity

    for i in cart_item:
        db.delete(i)

    db.commit()
    db.refresh(new_order)

    return new_order
@order.delete("/delete-order")
def cancel_order(
    order_id: int,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.order_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Order already cancelled"
        )

    order_item = db.query(OrderItem).filter(
        OrderItem.order_id == order.id,
        OrderItem.product_id == product_id
    ).first()

    if not order_item:
        raise HTTPException(
            status_code=404,
            detail="Product is not present in this order"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Restore stock
    product.stock += order_item.quantity

    # Reduce order total
    cancelled_amount = order_item.price * order_item.quantity
    order.total_amount -= cancelled_amount

    # Remove the item from the order
    db.delete(order_item)

    db.commit()
    db.refresh(order)

    return {
        "Message": "Product removed from order successfully",
        "order_id": order.id,
        "product_id": product_id,
        "remaining_total": order.total_amount
    }

@order.get("/view-orders", response_model=list[OrderResponse])
def view_orders(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    order = db.query(Order).filter(
        Order.user_id == current_user.id,
    ).all()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="No orders is found"
        )
    return order
@order.post("/make-payment")
def payment(
    payment_data: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.payment_status.lower() != "pending":
        raise HTTPException(
            status_code=400,
            detail="Payment already completed"
        )

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(order.total_amount * 100),
            currency="inr",
            automatic_payment_methods={"enabled": True}
        )

    except stripe.StripeError as e:
        new_notification = Notification(
            user_id = current_user.id,
            type = "PAYMENT_FAILED",
            message = f"payment failed for order #{order.id}",
            is_read = False
        )
        db.add(new_notification)
        db.commit()
        
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    new_payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_method="Stripe",
        transaction_id=payment_intent.id,
        status="success"
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return {
        "message": "Stripe payment created",
        "payment_id": new_payment.id,
        "order_id": order.id,
        "amount": order.total_amount,
        "transaction_id": payment_intent.id,
        "status": new_payment.status,
        "client_secret": payment_intent.client_secret
    }

@order.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):

    payload = await request.body()

    try:
        event = stripe.Event.construct_from(
            await request.json(),
            stripe.api_key
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe event"
        )

    if event["type"] == "payment_intent.succeeded":

        payment_intent = event["data"]["object"]

        payment = db.query(Payment).filter(
            Payment.transaction_id == payment_intent["id"]
        ).first()

        if payment:
            payment.status = "Success"

            order = db.query(Order).filter(
                Order.id == payment.order_id
            ).first()

            if order:
                order.payment_status = "PAID"

            db.commit()

    elif event["type"] == "payment_intent.payment_failed":

        payment_intent = event["data"]["object"]

        payment = db.query(Payment).filter(
            Payment.transaction_id == payment_intent["id"]
        ).first()

        if payment:
            payment.status = "Failed"
            db.commit()

    return {"message": "Webhook received"}
@order.get("/view-notification",response_model=list[NotificationResponse])
def view_notification(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    if not notifications:
        raise HTTPException(
            status_code=404,
            detail="No notifications found"
        )

    return notifications
@order.put("/mark-read/{notification_id}")
def mark_notification_read(notification_id:int, db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=400,
            detail="Notification not found"
        )
    if notification.is_read:
        raise HTTPException(
            status_code=400,
            detail="Notification is already read"
        )
    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return {
        "Message":"Notification marked as read",
        "Notification_id":notification.id,
        "is_read":notification.is_read
    }

