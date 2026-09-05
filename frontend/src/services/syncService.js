import api from "../api/client";

export async function syncDashboardData(role) {
  if (role === "RIDER") {
    const deliveriesResponse = await api.get("/deliveries/mine");

    return {
      orders: [],
      deliveries: deliveriesResponse.data,
      syncedAt: new Date(),
    };
  }

  if (role === "ATTENDANT") {
    const ordersResponse = await api.get("/orders");

    return {
      orders: ordersResponse.data,
      deliveries: [],
      syncedAt: new Date(),
    };
  }

  const [ordersResponse, deliveriesResponse] = await Promise.all([
    api.get("/orders"),
    api.get("/deliveries"),
  ]);

  return {
    orders: ordersResponse.data,
    deliveries: deliveriesResponse.data,
    syncedAt: new Date(),
  };
}

export async function updateDeliveryStatus(
  deliveryId,
  status,
  proofOfDelivery = null,
  notes = null
) {
  const response = await api.patch(
    `/deliveries/${deliveryId}/status`,
    {
      status,
      proof_of_delivery: proofOfDelivery,
      notes,
    }
  );

  return response.data;
}