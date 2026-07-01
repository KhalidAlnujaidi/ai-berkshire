"""Stripe subscription billing service.

Handles checkout sessions, webhooks, and subscription status management.
Fail-soft: if Stripe is not configured (no API key), subscription endpoints
return informative errors rather than crashing.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from models import User

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_MONTHLY = os.getenv("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_YEARLY = os.getenv("STRIPE_PRICE_YEARLY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ── Lazy Stripe initialization ──────────────────────────────────────────────
# Stripe is imported lazily so the app doesn't crash if the package or key
# is missing. In development without Stripe, the endpoints return clear errors.

_stripe_client = None


def get_stripe():
    """Return a configured Stripe client, or None if not configured."""
    global _stripe_client
    if not STRIPE_SECRET_KEY:
        return None
    if _stripe_client is None:
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            _stripe_client = stripe
        except ImportError:
            logger.warning("stripe package not installed")
            return None
    return _stripe_client


def is_configured() -> bool:
    """Check if Stripe is configured and ready to use."""
    return get_stripe() is not None


# ── Price lookup ─────────────────────────────────────────────────────────────

_PRICES = {
    "monthly": STRIPE_PRICE_MONTHLY,
    "yearly": STRIPE_PRICE_YEARLY,
}


def _get_price_id(plan: str) -> str:
    """Return the Stripe Price ID for the given plan."""
    price_id = _PRICES.get(plan)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown plan '{plan}'. Available: monthly, yearly",
        )
    return price_id


# ── Checkout session ────────────────────────────────────────────────────────

def create_checkout_session(user: User, plan: str) -> str:
    """Create a Stripe Checkout session for subscription. Returns the URL."""
    stripe = get_stripe()
    if stripe is None:
        raise HTTPException(
            status_code=503,
            detail="Payment system not configured. Please contact support.",
        )

    price_id = _get_price_id(plan)

    try:
        # Get or create Stripe customer
        customer_id = user.stripe_customer_id
        if customer_id:
            try:
                customer = stripe.Customer.retrieve(customer_id)
            except stripe.error.InvalidRequestError:
                customer_id = None

        if not customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name or None,
                metadata={"mizan_user_id": str(user.id)},
            )
            customer_id = customer.id
            user.stripe_customer_id = customer_id

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{FRONTEND_URL}/research?checkout=success",
            cancel_url=f"{FRONTEND_URL}/research?checkout=cancelled",
            metadata={"mizan_user_id": str(user.id)},
        )
        return session.url

    except stripe.error.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=502, detail="Payment provider error")


# ── Portal session ──────────────────────────────────────────────────────────

def create_portal_session(user: User) -> str:
    """Create a Stripe Customer Portal session for subscription management."""
    stripe = get_stripe()
    if stripe is None:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account found. Subscribe first.",
        )

    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{FRONTEND_URL}/research",
        )
        return session.url
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=502, detail="Payment provider error")


# ── Webhook processing ──────────────────────────────────────────────────────

def process_webhook_event(payload: bytes, signature: str, db: Session) -> bool:
    """Process a Stripe webhook event. Returns True on success."""
    stripe = get_stripe()
    if stripe is None:
        logger.warning("Stripe webhook received but Stripe not configured")
        return False

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        return False
    except Exception as e:
        logger.warning(f"Stripe webhook construction error: {e}")
        return False

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Processing Stripe webhook: {event_type}")

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data, db)
    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(data, db)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(data, db)
    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")

    return True


def _find_user_by_customer(customer_id: str, db: Session) -> Optional[User]:
    """Find a user by their Stripe customer ID."""
    return db.query(User).filter(User.stripe_customer_id == customer_id).first()


def _find_user_by_sub_id(sub_id: str, db: Session) -> Optional[User]:
    """Find a user by their Stripe subscription ID."""
    return db.query(User).filter(User.stripe_subscription_id == sub_id).first()


def _handle_checkout_completed(session_obj: dict, db: Session) -> None:
    """Handle checkout.session.completed — activate subscription."""
    customer_id = session_obj.get("customer")
    sub_id = session_obj.get("subscription")
    if not sub_id:
        return

    # Find user by customer ID or metadata
    user = _find_user_by_customer(customer_id, db) if customer_id else None
    if user is None:
        user_id = session_obj.get("metadata", {}).get("mizan_user_id")
        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        logger.warning(f"Checkout completed but no user found for customer {customer_id}")
        return

    user.stripe_customer_id = customer_id
    user.stripe_subscription_id = sub_id
    user.subscription_status = "active"

    # Get subscription details for period end
    stripe = get_stripe()
    if stripe:
        try:
            sub = stripe.Subscription.retrieve(sub_id)
            user.subscription_period_end = datetime.fromtimestamp(
                sub.current_period_end
            )
            # Determine plan from price
            item = sub["items"]["data"][0] if sub["items"]["data"] else None
            if item:
                price_id = item["price"]["id"]
                if price_id == STRIPE_PRICE_YEARLY:
                    user.subscription_plan = "yearly"
                else:
                    user.subscription_plan = "monthly"
        except Exception as e:
            logger.warning(f"Could not retrieve subscription details: {e}")

    db.commit()
    logger.info(f"Subscription activated for user {user.id}")


def _handle_subscription_updated(sub_obj: dict, db: Session) -> None:
    """Handle customer.subscription.updated — sync status and period."""
    sub_id = sub_obj.get("id")
    user = _find_user_by_sub_id(sub_id, db)
    if user is None:
        return

    status = sub_obj.get("status")
    if status in ("active", "trialing"):
        user.subscription_status = "active"
    elif status in ("past_due", "canceled", "unpaid"):
        user.subscription_status = "canceled"

    period_end = sub_obj.get("current_period_end")
    if period_end:
        user.subscription_period_end = datetime.fromtimestamp(period_end)

    db.commit()
    logger.info(f"Subscription updated for user {user.id}: {status}")


def _handle_subscription_deleted(sub_obj: dict, db: Session) -> None:
    """Handle customer.subscription.deleted — cancel subscription."""
    sub_id = sub_obj.get("id")
    user = _find_user_by_sub_id(sub_id, db)
    if user is None:
        return

    user.subscription_status = "canceled"
    user.subscription_plan = None
    db.commit()
    logger.info(f"Subscription canceled for user {user.id}")


# ── Subscription status helper ──────────────────────────────────────────────

def get_subscription_info(user: User) -> dict:
    """Return a dict with subscription info for the frontend."""
    is_active = user.subscription_status == "active"

    # Check if subscription has expired
    if is_active and user.subscription_period_end:
        if user.subscription_period_end < datetime.utcnow():
            is_active = False

    return {
        "status": "active" if is_active else (user.subscription_status or "free"),
        "plan": user.subscription_plan if is_active else None,
        "current_period_end": user.subscription_period_end,
        "is_subscribed": is_active,
    }
