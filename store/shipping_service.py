import requests
from decimal import Decimal
from .models import ShippingConfig, PincodeRate

METRO_PINCODES = {"110", "400", "560", "600", "700", "500", "380", "411"}  # Delhi, Mumbai, Blr, Chn, Kol, Hyd, Ahem, Pune prefixes

def get_shipping_config():
    config_obj, _ = ShippingConfig.objects.get_or_create(
        id=1,
        defaults={
            "free_shipping_threshold": Decimal("1999.00"),
            "standard_flat_rate": Decimal("99.00"),
            "express_flat_rate": Decimal("199.00"),
            "shiprocket_enabled": False,
        }
    )
    return config_obj

def calculate_shipping(pincode: str, cart_amount: float, state: str = "", delivery_type: str = "standard"):
    pincode = str(pincode).strip()
    config = get_shipping_config()
    cart_decimal = Decimal(str(cart_amount))

    # Free shipping threshold check
    is_free_eligible = cart_decimal >= config.free_shipping_threshold

    # Shiprocket Live API check if enabled
    if config.shiprocket_enabled and config.shiprocket_email and config.shiprocket_password and len(pincode) == 6:
        try:
            # Login token call
            token_res = requests.post(
                "https://apiv2.shiprocket.in/v1/external/auth/login",
                json={"email": config.shiprocket_email, "password": config.shiprocket_password},
                timeout=5
            )
            if token_res.status_code == 200:
                token = token_res.json().get("token")
                # Serviceability query
                srv_res = requests.get(
                    f"https://apiv2.shiprocket.in/v1/external/courier/serviceability/?delivery_postcode={pincode}&weight=0.5&cod=1",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                if srv_res.status_code == 200:
                    data = srv_res.json()
                    couriers = data.get("data", {}).get("available_courier_companies", [])
                    if couriers:
                        first = couriers[0]
                        courier_name = first.get("courier_name", "Shiprocket Partner")
                        est_days = f"{first.get('etd', '3-5')} Days"
                        std_rate = Decimal(str(first.get("rate", config.standard_flat_rate)))
                        exp_rate = std_rate + Decimal("100.00")

                        rate = Decimal("0.00") if is_free_eligible and delivery_type == "standard" else (exp_rate if delivery_type == "express" else std_rate)

                        return {
                            "serviceable": True,
                            "pincode": pincode,
                            "state": state,
                            "standard_rate": float(std_rate),
                            "express_rate": float(exp_rate),
                            "final_shipping_fee": float(rate),
                            "is_free_shipping": is_free_eligible and delivery_type == "standard",
                            "free_shipping_threshold": float(config.free_shipping_threshold),
                            "estimated_days": est_days,
                            "courier_name": courier_name,
                            "cod_available": True,
                        }
        except Exception as e:
            print(f"Shiprocket API error: {e}, falling back to local pincode rates.")

    # Courier Name determination based on Primary Courier choice
    courier_brand = "one.delhivery Express" if config.primary_courier == "one_delhivery" else ("DTDC Express Courier" if config.primary_courier == "dtdc" else "Standard Courier Partner")

    # Local Pincode / Zone Rate lookup
    p_obj = PincodeRate.objects.filter(pincode=pincode).first()
    if p_obj:
        std_rate = p_obj.standard_rate
        exp_rate = p_obj.express_rate
        est_days = p_obj.estimated_days
        courier_name = f"{courier_brand} ({p_obj.city or 'Tier 1'})" if p_obj.zone == "metro" else courier_brand
        serviceable = p_obj.is_serviceable
        cod_avail = p_obj.cod_available
    else:
        # Heuristic zone matching
        prefix = pincode[:3] if len(pincode) >= 3 else ""
        if prefix in METRO_PINCODES:
            std_rate = config.standard_flat_rate
            exp_rate = config.express_flat_rate
            est_days = "2-3 Business Days"
            courier_name = f"{courier_brand} (Metro Air)" if delivery_type == "express" else f"{courier_brand} (Metro Express)"
        else:
            std_rate = config.standard_flat_rate
            exp_rate = config.express_flat_rate
            est_days = "3-5 Business Days"
            courier_name = f"{courier_brand} (Priority Air)" if delivery_type == "express" else f"{courier_brand} (Surface Standard)"
        serviceable = len(pincode) == 6
        cod_avail = True

    final_rate = Decimal("0.00") if (is_free_eligible and delivery_type == "standard") else (exp_rate if delivery_type == "express" else std_rate)

    return {
        "serviceable": serviceable,
        "pincode": pincode,
        "state": state,
        "standard_rate": float(std_rate),
        "express_rate": float(exp_rate),
        "final_shipping_fee": float(final_rate),
        "is_free_shipping": is_free_eligible and delivery_type == "standard",
        "free_shipping_threshold": float(config.free_shipping_threshold),
        "estimated_days": est_days,
        "courier_name": courier_name,
        "cod_available": cod_avail,
    }
