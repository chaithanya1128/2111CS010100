from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import uuid

app = Flask(__name__)
CORS(app)


# Caching mechanism (in-memory for simplicity, consider Redis for production)
cache = {}

# Test E-Commerce Server base URL
BASE_URL = "http://20.244.56.144/test"

# Supported companies
COMPANIES = ["AMZ", "FLP", "SNP", "MYN", "AZO"]

@app.route('/categories/<string:categoryname>/products', methods=['GET'])
def get_products(categoryname):
    n = int(request.args.get('n', 10))
    min_price = request.args.get('minPrice', 0)
    max_price = request.args.get('maxPrice', 1000000)
    sort_by = request.args.get('sort', 'price')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))

    all_products = []
    
    # Fetch products from each company
    for company in COMPANIES:
        cache_key = f"{company}-{categoryname}-{min_price}-{max_price}"
        if cache_key in cache:
            products = cache[cache_key]
        else:
            try:  # Handle potential network errors
                response = requests.get(f"{BASE_URL}/companies/{company}/categories/{categoryname}/products",
                                         params={'top': n, 'minPrice': min_price, 'maxPrice': max_price})
                products = response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching products from {company}: {e}")
                products = []  # Set an empty list to avoid further processing for this company

            # Check for errors in the response
            if isinstance(products, dict) and "message" in products:
                print(f"Error from {company}: {products['message']}")
                continue  # Skip to the next company
            elif not isinstance(products, list):
                print(f"Unexpected response format from {company}: {products}")
                continue  # Skip to the next company

            # Cache the result
            cache[cache_key] = products

        # Ensure each product is a dictionary
        for product in products:
            if isinstance(product, dict):
                product['id'] = str(uuid.uuid4())
                product['company'] = company
                all_products.append(product)
            else:
                print(f"Warning: Skipping a non-dict product: {product}")
    
    # Ensure each product is a dictionary
    for product in products:
        if isinstance(product, dict):
            product['id'] = str(uuid.uuid4())
            product['company'] = company
            all_products.append(product)
        else:
            print(f"Warning: Skipping a non-dict product: {product}")


    # Sorting
    all_products.sort(key=lambda x: x[sort_by], reverse=(order == 'desc'))
    
    # Pagination
    start = (page - 1) * n
    end = start + n
    paginated_products = all_products[start:end]
    
    return jsonify(paginated_products)

@app.route('/products/<string:product_id>', methods=['GET'])
def get_product_details(product_id):
    # Search for the product in the cache (simple approach for this example)
    for products in cache.values():
        for product in products:
            if product.get('id') == product_id:
                return jsonify(product)
    
    return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
