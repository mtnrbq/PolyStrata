"""Shop-wide settings."""

# Tax by region, applied to the goods subtotal after discounts. Shipping is never taxed.
# An order from a region not listed here is rejected with ValueError.
TAX_RATES = {"AU": 0.10, "NZ": 0.15, "JP": 0.10, "US-CA": 0.0725, "US-OR": 0.0}

# The most units of one SKU a single order line may hold (and the least is 1).
MAX_LINE_QTY = 24

# Shipping in AUD cents by parcel weight in grams: (up to and including this weight, price).
# A parcel heavier than the last band cannot be shipped, and neither can one of 0 grams or less.
SHIPPING_TABLE = [(500, 895), (2000, 1295), (10000, 2450), (22000, 4900)]

# Regions we take orders from but do not ship to: their orders are collected in store, and asking for a shipping
# price for them is an error.
NO_SHIP_REGIONS = {"US-OR"}
