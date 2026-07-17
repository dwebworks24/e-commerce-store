import os
import django
import uuid
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Role, Users, Fabric, Color, Category, SubCategory, Product, ProductImage, Coupon

def seed():
    print("Starting database seed with expanded dummy products...")

    # 1. Roles
    roles_data = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("customer", "Customer")
    ]
    roles = {}
    for name, cat in roles_data:
        role, created = Role.objects.get_or_create(role_name=name, defaults={"role_category": name})
        roles[name] = role
        print(f"Role {name}: {'created' if created else 'already exists'}")

    # 2. Fabrics
    fabrics_data = ["Cotton", "Silk", "Georgette", "Chiffon", "Denim", "Polyester Blend", "Linen", "Leather", "Brass", "Wool"]
    fabrics = {}
    for name in fabrics_data:
        fabric, created = Fabric.objects.get_or_create(name=name)
        fabrics[name] = fabric
        print(f"Fabric {name}: {'created' if created else 'already exists'}")

    # 3. Colors
    colors_data = [
        ("Black", "#1a1a1a"),
        ("White", "#f5f5f5"),
        ("Navy", "#1e3a5f"),
        ("Pink", "#e8a0bf"),
        ("Burgundy", "#722f37"),
        ("Olive", "#808000"),
        ("Cream", "#f5f0e1"),
        ("Red", "#c41e3a"),
        ("Blush", "#fcd5d9"),
        ("Mint", "#d2f8d2"),
        ("Lavender", "#e6e6fa"),
        ("Emerald", "#50c878"),
        ("Sage", "#9c9f84"),
        ("Dusty Rose", "#cca9a8"),
        ("Champagne", "#f7e7ce"),
        ("Wine", "#722f37"),
        ("Rust", "#b7410e"),
        ("Coral", "#ff7f50"),
        ("Teal", "#008080"),
        ("Ivory", "#fffff0"),
        ("Gold", "#ffd700"),
        ("Silver", "#c0c0c0"),
        ("Black Floral", "#241515"),
        ("Navy Floral", "#1c2230"),
        ("Wine Floral", "#3a1924"),
        ("Light Wash", "#add8e6"),
        ("Medium Wash", "#6495ed"),
    ]
    colors = {}
    for name, hex_code in colors_data:
        color, created = Color.objects.get_or_create(name=name, defaults={"hex_code": hex_code})
        colors[name] = color
        print(f"Color {name}: {'created' if created else 'already exists'}")

    # 4. Categories & Subcategories
    categories_data = [
        {
            "name": "Western",
            "slug": "western",
            "description": "Modern western fashion collection",
            "image": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=500",
            "subcategories": ["Dresses", "Tops", "Pants", "Skirts", "Jackets", "Jeans"]
        },
        {
            "name": "Ethnic",
            "slug": "ethnic",
            "description": "Traditional Indian ethnic wear",
            "image": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=500",
            "subcategories": ["Kurtis", "Sarees"]
        },
        {
            "name": "Indo-Western",
            "slug": "indo-western",
            "description": "Fusion of Indian and Western styles",
            "image": "https://images.unsplash.com/photo-1596783074918-c84cb06531ca?w=500",
            "subcategories": ["Palazzo Sets", "Cape Dresses", "Jumpsuits"]
        },
        {
            "name": "Accessories",
            "slug": "accessories",
            "description": "Fashion accessories and jewelry",
            "image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=500",
            "subcategories": ["Bags", "Jewelry"]
        }
    ]
    categories = {}
    subcategories = {}
    for c_data in categories_data:
        cat, created = Category.objects.get_or_create(
            slug=c_data["slug"],
            defaults={
                "name": c_data["name"],
                "description": c_data["description"],
                "image": c_data["image"],
                "status": "active"
            }
        )
        categories[c_data["slug"]] = cat
        print(f"Category {cat.name}: {'created' if created else 'already exists'}")

        for sub_name in c_data["subcategories"]:
            sub_slug = sub_name.lower().replace(" ", "-")
            sub, sub_created = SubCategory.objects.get_or_create(
                category=cat,
                slug=sub_slug,
                defaults={"name": sub_name}
            )
            subcategories[f"{c_data['slug']}-{sub_slug}"] = sub
            print(f"  Subcategory {sub_name}: {'created' if sub_created else 'already exists'}")

    # 5. Coupons
    coupons_data = [
        {
            "code": "WELCOME20",
            "type": "percentage",
            "value": 20.00,
            "min_order": 1000.00,
            "max_uses": 500,
            "description": "20% off for new customers",
            "days": 90
        },
        {
            "code": "FLAT500",
            "type": "fixed",
            "value": 500.00,
            "min_order": 2500.00,
            "max_uses": 200,
            "description": "₹500 off on orders above ₹2500",
            "days": 60
        },
        {
            "code": "SUMMER15",
            "type": "percentage",
            "value": 15.00,
            "min_order": 1500.00,
            "max_uses": 1000,
            "description": "Summer sale 15% discount",
            "days": 45
        },
        {
            "code": "ETHNIC10",
            "type": "percentage",
            "value": 10.00,
            "min_order": 2000.00,
            "max_uses": 300,
            "description": "10% off on ethnic wear",
            "days": -5  # Expired
        }
    ]
    for c_data in coupons_data:
        start = timezone.now() - timedelta(days=10)
        end = timezone.now() + timedelta(days=c_data["days"])
        coupon, created = Coupon.objects.get_or_create(
            code=c_data["code"],
            defaults={
                "type": c_data["type"],
                "value": c_data["value"],
                "min_order": c_data["min_order"],
                "max_uses": c_data["max_uses"],
                "status": "active",
                "start_date": start,
                "end_date": end,
                "description": c_data["description"]
            }
        )
        print(f"Coupon {coupon.code}: {'created' if created else 'already exists'}")

    # 6. Products
    products_data = [
        # --- Western Wear ---
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a1",
            "name": "Floral Print Wrap Dress",
            "slug": "floral-print-wrap-dress",
            "price": 2499.00,
            "original_price": 3999.00,
            "category_slug": "western",
            "subcategory_slug": "dresses",
            "color_names": ["Black Floral", "Navy Floral", "Wine Floral"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "fabric_name": "Georgette",
            "rating": 4.5,
            "review_count": 128,
            "description": "A stunning floral wrap dress perfect for any occasion. Features a flattering V-neckline and flowing silhouette.",
            "is_new": True,
            "is_featured": True,
            "stock": 45,
            "sku": "WD-001",
            "images": [
                "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600",
                "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a2",
            "name": "Silk V-Neck Blouse",
            "slug": "silk-v-neck-blouse",
            "price": 1299.00,
            "original_price": 1899.00,
            "category_slug": "western",
            "subcategory_slug": "tops",
            "color_names": ["Cream", "Blush", "White"],
            "sizes": ["S", "M", "L", "XL"],
            "fabric_name": "Silk",
            "rating": 4.3,
            "review_count": 86,
            "description": "Luxurious silk blouse with elegant V-neckline. Perfect for workwear or evening outings.",
            "is_new": False,
            "is_featured": True,
            "stock": 30,
            "sku": "WT-002",
            "images": [
                "https://images.unsplash.com/photo-1548624149-f7b2e6ce34f6?w=600",
                "https://images.unsplash.com/photo-1607746882042-944635dfe10e?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a4",
            "name": "High Waist Wide Leg Pants",
            "slug": "high-waist-wide-leg-pants",
            "price": 1799.00,
            "original_price": None,
            "category_slug": "western",
            "subcategory_slug": "pants",
            "color_names": ["Navy", "Black", "Olive"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "fabric_name": "Polyester Blend",
            "rating": 4.4,
            "review_count": 92,
            "description": "Flattering high-waist wide leg pants with a modern silhouette. Perfect for work or weekends.",
            "is_new": False,
            "is_featured": True,
            "stock": 60,
            "sku": "WP-004",
            "images": [
                "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a5",
            "name": "Burgundy Wrap Dress",
            "slug": "burgundy-wrap-dress",
            "price": 2999.00,
            "original_price": 4499.00,
            "category_slug": "western",
            "subcategory_slug": "dresses",
            "color_names": ["Burgundy", "Emerald", "Black"],
            "sizes": ["XS", "S", "M", "L"],
            "fabric_name": "Chiffon",
            "rating": 4.6,
            "review_count": 167,
            "description": "Elegant wrap dress in rich burgundy. Features balloon sleeves and a tie waist.",
            "is_new": True,
            "is_featured": False,
            "stock": 18,
            "sku": "WD-005",
            "images": [
                "https://images.unsplash.com/photo-1539008885759-c21d817b1d91?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a6",
            "name": "Olive Button-Down Blouse",
            "slug": "olive-button-down-blouse",
            "price": 999.00,
            "original_price": 1499.00,
            "category_slug": "western",
            "subcategory_slug": "tops",
            "color_names": ["Olive", "Rust", "Cream"],
            "sizes": ["S", "M", "L", "XL"],
            "fabric_name": "Cotton",
            "rating": 4.2,
            "review_count": 54,
            "description": "Casual yet chic button-down blouse in a gorgeous olive shade. Rolled-up sleeves for effortless style.",
            "is_new": False,
            "is_featured": False,
            "stock": 75,
            "sku": "WT-006",
            "images": [
                "https://images.unsplash.com/photo-1607746882042-944635dfe10e?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a7",
            "name": "Pleated Maxi Skirt",
            "slug": "pleated-maxi-skirt",
            "price": 1999.00,
            "original_price": None,
            "category_slug": "western",
            "subcategory_slug": "skirts",
            "color_names": ["Dusty Rose", "Sage", "Champagne"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "fabric_name": "Chiffon",
            "rating": 4.8,
            "review_count": 203,
            "description": "Flowing pleated maxi skirt in a beautiful dusty rose. Elegant movement with every step.",
            "is_new": False,
            "is_featured": True,
            "stock": 40,
            "sku": "WS-007",
            "images": [
                "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a8",
            "name": "Cropped Denim Jacket",
            "slug": "cropped-denim-jacket",
            "price": 2299.00,
            "original_price": 2999.00,
            "category_slug": "western",
            "subcategory_slug": "jackets",
            "color_names": ["Light Wash", "Medium Wash", "White"],
            "sizes": ["XS", "S", "M", "L"],
            "fabric_name": "Denim",
            "rating": 4.5,
            "review_count": 142,
            "description": "Classic cropped denim jacket with a modern fit. A wardrobe essential for layering.",
            "is_new": True,
            "is_featured": False,
            "stock": 10,
            "sku": "WJ-008",
            "images": [
                "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a9",
            "name": "Slim Fit High Rise Jeans",
            "slug": "slim-fit-high-rise-jeans",
            "price": 1899.00,
            "original_price": 2499.00,
            "category_slug": "western",
            "subcategory_slug": "jeans",
            "color_names": ["Light Wash", "Medium Wash", "Black"],
            "sizes": ["26", "28", "30", "32"],
            "fabric_name": "Denim",
            "rating": 4.4,
            "review_count": 78,
            "description": "Ultra-comfortable slim fit jeans with a high-rise waist. Designed to shape and flatter.",
            "is_new": True,
            "is_featured": False,
            "stock": 50,
            "sku": "WJ-009",
            "images": [
                "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df910",
            "name": "Oversized Knit Sweater",
            "slug": "oversized-knit-sweater",
            "price": 2199.00,
            "original_price": 3199.00,
            "category_slug": "western",
            "subcategory_slug": "tops",
            "color_names": ["Cream", "Sage", "Rust"],
            "sizes": ["S", "M", "L"],
            "fabric_name": "Wool",
            "rating": 4.6,
            "review_count": 62,
            "description": "Cozy oversized sweater in a chunky cable knit design. Perfect for chilly days.",
            "is_new": False,
            "is_featured": False,
            "stock": 22,
            "sku": "WT-010",
            "images": [
                "https://images.unsplash.com/photo-1517256064527-09c53b2d0bc6?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df911",
            "name": "Classic Black Slip Dress",
            "slug": "classic-black-slip-dress",
            "price": 1999.00,
            "original_price": 2999.00,
            "category_slug": "western",
            "subcategory_slug": "dresses",
            "color_names": ["Black", "Champagne"],
            "sizes": ["XS", "S", "M", "L"],
            "fabric_name": "Silk",
            "rating": 4.7,
            "review_count": 104,
            "description": "Timeless cowl neck slip dress in premium satin silk. Featuring adjustable crossover straps.",
            "is_new": False,
            "is_featured": True,
            "stock": 25,
            "sku": "WD-011",
            "images": [
                "https://images.unsplash.com/photo-1485462537746-965f33f7f6a7?w=600"
            ]
        },

        # --- Ethnic Wear ---
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df9a3",
            "name": "Embroidered Pink Kurta Set",
            "slug": "embroidered-pink-kurta-set",
            "price": 3499.00,
            "original_price": 4999.00,
            "category_slug": "ethnic",
            "subcategory_slug": "kurtis",
            "color_names": ["Pink", "Mint", "Lavender"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "fabric_name": "Cotton",
            "rating": 4.7,
            "review_count": 215,
            "description": "Beautifully embroidered kurta set with intricate gold thread work. Comes with matching dupatta.",
            "is_new": True,
            "is_featured": True,
            "stock": 25,
            "sku": "EK-003",
            "images": [
                "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df912",
            "name": "Banarasi Silk Saree",
            "slug": "banarasi-silk-saree",
            "price": 5999.00,
            "original_price": 8999.00,
            "category_slug": "ethnic",
            "subcategory_slug": "sarees",
            "color_names": ["Red", "Burgundy", "Gold"],
            "sizes": ["Free Size"],
            "fabric_name": "Silk",
            "rating": 4.9,
            "review_count": 56,
            "description": "Exquisite Banarasi silk saree woven with gold zari work. An iconic masterpiece for weddings.",
            "is_new": True,
            "is_featured": True,
            "stock": 12,
            "sku": "ES-012",
            "images": [
                "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df913",
            "name": "Lucknowi Chikankari Anarkali",
            "slug": "lucknowi-chikankari-anarkali",
            "price": 4299.00,
            "original_price": 5999.00,
            "category_slug": "ethnic",
            "subcategory_slug": "kurtis",
            "color_names": ["White", "Blush", "Mint"],
            "sizes": ["S", "M", "L", "XL"],
            "fabric_name": "Georgette",
            "rating": 4.8,
            "review_count": 89,
            "description": "Authentic Lucknowi Chikankari embroidery on a georgette Anarkali gown with inner slip included.",
            "is_new": False,
            "is_featured": False,
            "stock": 15,
            "sku": "EK-013",
            "images": [
                "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df914",
            "name": "Georgette Floral Print Saree",
            "slug": "georgette-floral-print-saree",
            "price": 1899.00,
            "original_price": 2799.00,
            "category_slug": "ethnic",
            "subcategory_slug": "sarees",
            "color_names": ["Pink", "Lavender", "Cream"],
            "sizes": ["Free Size"],
            "fabric_name": "Georgette",
            "rating": 4.5,
            "review_count": 42,
            "description": "Lightweight georgette saree featuring a modern floral print. Perfect for casual events and summer wear.",
            "is_new": False,
            "is_featured": False,
            "stock": 35,
            "sku": "ES-014",
            "images": [
                "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=600"
            ]
        },

        # --- Indo-Western ---
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df915",
            "name": "Fusion Crop Top & Palazzo Set",
            "slug": "fusion-crop-top-and-palazzo-set",
            "price": 2799.00,
            "original_price": 3999.00,
            "category_slug": "indo-western",
            "subcategory_slug": "palazzo-sets",
            "color_names": ["Teal", "Mustard", "Coral"],
            "sizes": ["S", "M", "L", "XL"],
            "fabric_name": "Georgette",
            "rating": 4.6,
            "review_count": 48,
            "description": "Chic fusion outfit comprising a hand-embroidered crop top and flared palazzo pants with a long shrug.",
            "is_new": True,
            "is_featured": True,
            "stock": 20,
            "sku": "IW-015",
            "images": [
                "https://images.unsplash.com/photo-1596783074918-c84cb06531ca?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df916",
            "name": "Ethnic Print Jacket Dress",
            "slug": "ethnic-print-jacket-dress",
            "price": 3199.00,
            "original_price": None,
            "category_slug": "indo-western",
            "subcategory_slug": "cape-dresses",
            "color_names": ["Navy", "Rust"],
            "sizes": ["S", "M", "L", "XL"],
            "fabric_name": "Cotton",
            "rating": 4.3,
            "review_count": 27,
            "description": "Double-layered fusion dress featuring a solid cotton slip dress underneath an ethnic printed open jacket.",
            "is_new": False,
            "is_featured": False,
            "stock": 18,
            "sku": "IW-016",
            "images": [
                "https://images.unsplash.com/photo-1618244972963-dbee1a7edc95?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df917",
            "name": "Embroidered Cape Jumpsuit",
            "slug": "embroidered-cape-jumpsuit",
            "price": 3899.00,
            "original_price": 5499.00,
            "category_slug": "indo-western",
            "subcategory_slug": "jumpsuits",
            "color_names": ["Emerald", "Wine"],
            "sizes": ["XS", "S", "M", "L"],
            "fabric_name": "Polyester Blend",
            "rating": 4.7,
            "review_count": 33,
            "description": "A striking modern jumpsuit styled with an attached georgette cape, detailed with mirror work at the collar.",
            "is_new": True,
            "is_featured": False,
            "stock": 14,
            "sku": "IW-017",
            "images": [
                "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600"
            ]
        },

        # --- Accessories ---
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df918",
            "name": "Leather Saddle Crossbody Bag",
            "slug": "leather-saddle-crossbody-bag",
            "price": 2599.00,
            "original_price": 3999.00,
            "category_slug": "accessories",
            "subcategory_slug": "bags",
            "color_names": ["Brown", "Black", "Tan"],
            "sizes": ["Free Size"],
            "fabric_name": "Leather",
            "rating": 4.6,
            "review_count": 91,
            "description": "Classic saddle silhouette bag crafted in 100% genuine full-grain leather. Adjustable shoulder strap.",
            "is_new": False,
            "is_featured": True,
            "stock": 40,
            "sku": "AC-018",
            "images": [
                "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df919",
            "name": "Kundan Choker Necklace Set",
            "slug": "kundan-choker-necklace-set",
            "price": 1499.00,
            "original_price": 2499.00,
            "category_slug": "accessories",
            "subcategory_slug": "jewelry",
            "color_names": ["Gold", "Mint", "White"],
            "sizes": ["Free Size"],
            "fabric_name": "Brass",
            "rating": 4.8,
            "review_count": 112,
            "description": "Stunning Kundan choker necklace paired with matching drop earrings and beaded pearl drops.",
            "is_new": True,
            "is_featured": True,
            "stock": 65,
            "sku": "AC-019",
            "images": [
                "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=600"
            ]
        },
        {
            "id": "e305e71b-d102-45e9-86bd-d2c6c06df920",
            "name": "Statement Gold Hoop Earrings",
            "slug": "statement-gold-hoop-earrings",
            "price": 499.00,
            "original_price": 899.00,
            "category_slug": "accessories",
            "subcategory_slug": "jewelry",
            "color_names": ["Gold", "Silver"],
            "sizes": ["Free Size"],
            "fabric_name": "Brass",
            "rating": 4.5,
            "review_count": 145,
            "description": "High-shine 18k gold plated chunky hoops. Lightweight and water-resistant for everyday wear.",
            "is_new": False,
            "is_featured": False,
            "stock": 120,
            "sku": "AC-020",
            "images": [
                "https://images.unsplash.com/photo-1630019852942-f89202989a59?w=600"
            ]
        }
    ]

    for p_data in products_data:
        cat = categories[p_data["category_slug"]]
        sub = subcategories.get(f"{p_data['category_slug']}-{p_data['subcategory_slug']}")
        fab = fabrics.get(p_data["fabric_name"])

        product, created = Product.objects.get_or_create(
            sku=p_data["sku"],
            defaults={
                "id": uuid.UUID(p_data["id"]),
                "name": p_data["name"],
                "slug": p_data["slug"],
                "price": p_data["price"],
                "original_price": p_data["original_price"],
                "category": cat,
                "subcategory": sub,
                "sizes": p_data["sizes"],
                "fabric": fab,
                "rating": p_data["rating"],
                "review_count": p_data["review_count"],
                "description": p_data["description"],
                "is_new": p_data["is_new"],
                "is_featured": p_data["is_featured"],
                "in_stock": p_data["stock"] > 0,
                "stock": p_data["stock"],
                "status": "active"
            }
        )
        # Force update fields in case product already exists to populate expanded fields
        if not created:
            product.name = p_data["name"]
            product.price = p_data["price"]
            product.original_price = p_data["original_price"]
            product.category = cat
            product.subcategory = sub
            product.sizes = p_data["sizes"]
            product.fabric = fab
            product.rating = p_data["rating"]
            product.review_count = p_data["review_count"]
            product.description = p_data["description"]
            product.is_new = p_data["is_new"]
            product.is_featured = p_data["is_featured"]
            product.stock = p_data["stock"]
            product.in_stock = p_data["stock"] > 0
            product.save()

        print(f"Product {product.name}: {'created' if created else 'updated'}")

        # Set Colors
        product.colors.clear()
        for col_name in p_data["color_names"]:
            if col_name in colors:
                product.colors.add(colors[col_name])

        # Set Images
        ProductImage.objects.filter(product=product).delete()
        for idx, img_url in enumerate(p_data["images"]):
            img, img_created = ProductImage.objects.get_or_create(
                product=product,
                image=img_url,
                defaults={"alt_text": f"{product.name} image {idx + 1}", "order": idx}
            )
            print(f"  Image {img_url}: {'created' if img_created else 'already exists'}")

    print("Database seeding completed successfully with 20 premium products!")

if __name__ == "__main__":
    seed()
