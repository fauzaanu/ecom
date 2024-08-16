from store.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        # get current session key if it exitst
        cart = self.session.get("session_key")

        # if the user is new, no session key, create one
        if "session_key" not in request.session:
            cart = self.session["session_key"] = {}

        # make sure cart is on all pages of sitre
        self.cart = cart

    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = str(quantity)

        if product_id in self.cart:
            pass
        else:
            # self.cart[product_id] = {"price": str(product.price)}
            self.cart[product_id] = int(product_qty)

        self.session.modified = True

    def __len__(self):
        return len(self.cart)

    def cart_total(self):
        # get product IDs
        product_ids = self.cart.keys()

        # lookup those kets in out products database model
        products = Product.objects.filter(id__in=product_ids)

        # get quantities
        quantities = self.cart

        # starting counting at 0
        total = 0

        for key, value in quantities.items():
            # convert key string to int
            key = int(key)
            for product in products:
                if product.id == key:
                    if product.is_sale:
                        total = total + (product.sale_price * value)
                    else:
                        total = total + (product.price * value)
        return total

    def get_prods(self):
        # get ids from cart
        product_ids = self.cart.keys()

        # use ids to lookup products in data base model
        products = Product.objects.filter(id__in=product_ids)

        # return looked up products
        return products

    def get_quants(self):
        quantities = self.cart
        return quantities

    def update(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)

        # get cart
        ourcart = self.cart

        # update cart/dict
        ourcart[product_id] = product_qty

        self.session.modified = True
        thing = self.cart
        return thing

    def delete(self, product):
        product_id = str(product)

        # remove item from cart
        if product_id in self.cart:
            del self.cart[product_id]

        self.session.modified = True
