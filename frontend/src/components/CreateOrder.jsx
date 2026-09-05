import { useEffect, useState } from "react";
import { createOrder } from "../services/orderService";
import { getProducts } from "../services/orderService";

function CreateOrder({ onOrderCreated }) {
  const [products, setProducts] = useState([]);
  const [customerId, setCustomerId] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [selectedProductId, setSelectedProductId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [items, setItems] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const loadProducts = async () => {
      try {
        setLoadingProducts(true);

        const data = await getProducts();

        setProducts(data);
      } catch (err) {
        console.error("Failed to load products:", err);
        setError("Unable to load products.");
      } finally {
        setLoadingProducts(false);
      }
    };

    loadProducts();
  }, []);

  const addItem = () => {
    setError("");
    setSuccess("");

    if (!selectedProductId) {
      setError("Please select a product.");
      return;
    }

    const selectedProduct = products.find(
      (product) => product.id === Number(selectedProductId)
    );

    if (!selectedProduct) {
      setError("Selected product was not found.");
      return;
    }

    if (quantity < 1) {
      setError("Quantity must be at least 1.");
      return;
    }

    if (quantity > selectedProduct.stock_quantity) {
      setError(
        `Only ${selectedProduct.stock_quantity} units of ${selectedProduct.name} are available.`
      );
      return;
    }

    const existingItem = items.find(
      (item) => item.product_id === selectedProduct.id
    );

    if (existingItem) {
      const newQuantity = existingItem.quantity + quantity;

      if (newQuantity > selectedProduct.stock_quantity) {
        setError(
          `Only ${selectedProduct.stock_quantity} units of ${selectedProduct.name} are available.`
        );
        return;
      }

      setItems(
        items.map((item) =>
          item.product_id === selectedProduct.id
            ? {
                ...item,
                quantity: newQuantity,
              }
            : item
        )
      );
    } else {
      setItems([
        ...items,
        {
          product_id: selectedProduct.id,
          name: selectedProduct.name,
          price: Number(selectedProduct.price),
          quantity,
        },
      ]);
    }

    setSelectedProductId("");
    setQuantity(1);
  };

  const removeItem = (productId) => {
    setItems(
      items.filter((item) => item.product_id !== productId)
    );
  };

  const totalAmount = items.reduce(
    (total, item) => total + item.price * item.quantity,
    0
  );

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!customerId) {
      setError("Please enter a customer ID.");
      return;
    }

    if (!deliveryAddress.trim()) {
      setError("Please enter a delivery address.");
      return;
    }

    if (items.length === 0) {
      setError("Please add at least one product.");
      return;
    }

    try {
      setSubmitting(true);

      const orderData = {
        customer_id: Number(customerId),
        delivery_address: deliveryAddress.trim(),
        items: items.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
      };

      const createdOrder = await createOrder(orderData);

      setSuccess(
        `Order #${createdOrder.id} created successfully.`
      );

      setCustomerId("");
      setDeliveryAddress("");
      setSelectedProductId("");
      setQuantity(1);
      setItems([]);

      if (onOrderCreated) {
        onOrderCreated();
      }
    } catch (err) {
      console.error("Order creation failed:", err);

      if (err.response?.status === 404) {
        setError(
          err.response?.data?.detail ||
            "Customer or product not found."
        );
      } else if (err.response?.status === 400) {
        setError(
          err.response?.data?.detail ||
            "Unable to create order."
        );
      } else if (err.response?.status === 401) {
        setError(
          "Your session has expired. Please log in again."
        );
      } else {
        setError("Unable to create order.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="create-order-section">
      <div className="section-header">
        <h2>Create New Order</h2>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="customer-id">
            Customer ID
          </label>

          <input
            id="customer-id"
            type="number"
            min="1"
            value={customerId}
            onChange={(event) =>
              setCustomerId(event.target.value)
            }
            placeholder="Enter customer ID"
          />
        </div>

        <div className="form-group">
          <label htmlFor="delivery-address">
            Delivery Address
          </label>

          <input
            id="delivery-address"
            type="text"
            value={deliveryAddress}
            onChange={(event) =>
              setDeliveryAddress(event.target.value)
            }
            placeholder="Enter delivery address"
          />
        </div>

        <div className="order-item-form">
          <div className="form-group">
            <label htmlFor="product">
              Product
            </label>

            <select
              id="product"
              value={selectedProductId}
              onChange={(event) =>
                setSelectedProductId(event.target.value)
              }
              disabled={loadingProducts}
            >
              <option value="">
                {loadingProducts
                  ? "Loading products..."
                  : "Select a product"}
              </option>

              {products.map((product) => (
                <option
                  key={product.id}
                  value={product.id}
                  disabled={product.stock_quantity === 0}
                >
                  {product.name} — KES{" "}
                  {Number(product.price).toFixed(2)}{" "}
                  ({product.stock_quantity} in stock)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="quantity">
              Quantity
            </label>

            <input
              id="quantity"
              type="number"
              min="1"
              value={quantity}
              onChange={(event) =>
                setQuantity(Number(event.target.value))
              }
            />
          </div>

          <button
            type="button"
            onClick={addItem}
            disabled={loadingProducts}
          >
            Add Item
          </button>
        </div>

        {items.length > 0 && (
          <div className="order-items">
            <h3>Order Items</h3>

            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Qty</th>
                  <th>Price</th>
                  <th>Subtotal</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {items.map((item) => (
                  <tr key={item.product_id}>
                    <td>{item.name}</td>
                    <td>{item.quantity}</td>
                    <td>
                      KES {item.price.toFixed(2)}
                    </td>
                    <td>
                      KES{" "}
                      {(item.price * item.quantity).toFixed(2)}
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() =>
                          removeItem(item.product_id)
                        }
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="order-total">
              <strong>
                Total: KES {totalAmount.toFixed(2)}
              </strong>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || items.length === 0}
        >
          {submitting ? "Creating Order..." : "Create Order"}
        </button>
      </form>
    </section>
  );
}

export default CreateOrder;