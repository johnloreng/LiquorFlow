import api from "../api/client";

export async function getProducts() {
  const response = await api.get("/products", {
    params: {
      is_active: true,
    },
  });

  return response.data;
}

export async function createOrder(orderData) {
  const response = await api.post("/orders", orderData);

  return response.data;
}