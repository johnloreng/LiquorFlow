import api from "../api/client";

export async function createDelivery(orderId, riderId) {
  const response = await api.post("/deliveries", {
    order_id: orderId,
    rider_id: riderId,
  });

  return response.data;
}

export async function getRiders() {
  const response = await api.get("/users/riders");

  return response.data;
}
