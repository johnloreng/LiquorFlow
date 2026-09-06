import { useEffect, useState } from "react";
import {
  syncDashboardData,
  updateDeliveryStatus,
} from "../services/syncService";
import CreateOrder from "../components/CreateOrder";
import { getRiders, createDelivery } from "../services/deliveryService";

function Dashboard() {
    const getDeliveryStatus = (delivery) => {
    if (delivery.delivered_at) {
      return "DELIVERED";
    }

    if (delivery.out_for_delivery_at) {
      return "OUT_FOR_DELIVERY";
    }

    if (delivery.picked_up_at) {
      return "PICKED_UP";
    }

    return "ASSIGNED";
  };
  const [orders, setOrders] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [riders, setRiders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [lastSync, setLastSync] = useState(null);
  const [proofOfDelivery, setProofOfDelivery] = useState("");
  const [deliveryNotes, setDeliveryNotes] = useState("");
  const [selectedDeliveryId, setSelectedDeliveryId] = useState(null);
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [selectedRiderId, setSelectedRiderId] = useState("");

  const role = localStorage.getItem("user_role");

  const roleTitles = {
  ADMIN: "Administrator Dashboard",
  ATTENDANT: "Attendant Dashboard",
  DISPATCHER: "Dispatcher Dashboard",
  RIDER: "Rider Dashboard",
};
const handleLogout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_role");

  window.location.href = "/";
};

const dashboardTitle = roleTitles[role] || "LiquorFlow Dashboard";
const handleAssignOrder = async (orderId) => {
  if (!selectedRiderId) {
    setError("Please select a rider.");
    return;
  }

  try {
    setError("");
    setSyncing(true);

    await createDelivery(orderId, Number(selectedRiderId));

    setSelectedOrderId(null);
    setSelectedRiderId("");

    await syncData();
  } catch (err) {
    console.error("Order assignment failed:", err);

    if (err.response?.status === 400) {
      setError(
        err.response?.data?.detail ||
          "Unable to assign this order."
      );
    } else if (err.response?.status === 401) {
      setError("Your session has expired. Please log in again.");
    } else if (err.response?.status === 403) {
      setError("You do not have permission to assign deliveries.");
    } else {
      setError("Unable to assign order to rider.");
    }
  } finally {
    setSyncing(false);
  }
};
const handleDeliveryStatusUpdate = async (deliveryId, status, proof = null, notes = null
  ) => {
    try {
      setError("");
      setSyncing(true);

      await updateDeliveryStatus(deliveryId, status, proof, notes);

      setProofOfDelivery("");
      setDeliveryNotes("");
      setSelectedDeliveryId(null);

      await syncData();
    } catch (err) {
      console.error("Delivery status update failed:", err);

      if (err.response?.status === 400) {
        setError(
          err.response?.data?.detail ||
            "Invalid delivery status transition."
        );
      } else if (err.response?.status === 401) {
        setError("Your session has expired. Please log in again.");
      } else {
        setError("Unable to update delivery status.");
      }
    } finally {
      setSyncing(false);
    }
};
const syncData = async () => {

  try {
    setSyncing(true);
    setError("");

const data = await syncDashboardData(role);

    setOrders(data.orders);
    setDeliveries(data.deliveries);
    if (role === "DISPATCHER") {
const riderData = await getRiders();
  setRiders(riderData);
}
    setLastSync(data.syncedAt);
  } catch (err) {
    console.error("Sync failed:", err);

    if (err.response?.status === 401) {
      setError("Your session has expired. Please log in again.");
    } else {
      setError("Unable to synchronize dashboard data.");
    }
  } finally {
    setLoading(false);
    setSyncing(false);
  }
};

const roleDescriptions = {
  ADMIN: "Monitor orders, deliveries and overall store operations.",
  ATTENDANT: "Create and monitor customer orders.",
  DISPATCHER: "Manage orders and coordinate delivery assignments.",
  RIDER: "View your assigned deliveries and update delivery progress.",
};

const roleDescription =
  roleDescriptions[role] || "Manage liquor store operations.";

  useEffect(() => {
    syncData();

    const interval = setInterval(() => {
      syncData();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const totalOrders = orders.length;

  const pendingOrders = orders.filter(
    (order) => order.status === "PENDING"
  ).length;

  const activeOrders = deliveries.filter((delivery) =>
    ["ASSIGNED", "PICKED_UP", "OUT_FOR_DELIVERY"].includes(getDeliveryStatus(delivery))
  ).length;

  const deliveredOrders = deliveries.filter(
    (delivery) => getDeliveryStatus(delivery) === "DELIVERED"
  ).length;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
  <div>
    <h1>{dashboardTitle}</h1>
    <p>
      Logged in as: {role} — {roleDescription}
    </p>
  </div>

  <div className="dashboard-actions">
    <button onClick={syncData} disabled={syncing}>
      {syncing ? "Syncing..." : "Sync Now"}
    </button>

    <button onClick={handleLogout}>
      Logout
    </button>
      </div>
    </header>

      {error && <div className="error-message">{error}</div>}

<section className="stats-grid">
    {role !== "RIDER" && (
    <>
      <div className="stat-card">
        <h3>Total Orders</h3>
        <strong>{totalOrders}</strong>
      </div>

      <div className="stat-card">
        <h3>Pending Orders</h3>
        <strong>{pendingOrders}</strong>
      </div>
    </>
  )}

  <div className="stat-card">
    <h3>Active Deliveries</h3>
    <strong>{activeOrders}</strong>
  </div>

  <div className="stat-card">
    <h3>Delivered</h3>
    <strong>{deliveredOrders}</strong>
  </div>
</section>
{role === "ATTENDANT" && (
  <CreateOrder onOrderCreated={syncData} />
)}
{role !== "RIDER" && (
      <section className="orders-section">
        <div className="section-header">
          <h2>Recent Orders</h2>

          <span>
            {lastSync
              ? `Last sync: ${lastSync.toLocaleTimeString()}`
              : "Not synchronized"}
          </span>
        </div>

        {loading ? (
          <p>Loading orders...</p>
        ) : orders.length === 0 ? (
          <p>No orders found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Customer</th>
                  <th>Address</th>
                  <th>Total</th>
                  <th>Status</th>
                  {role === "DISPATCHER" && <th>Action</th>}
                </tr>
              </thead>

              <tbody>
  {orders.map((order) => (
    <tr key={order.id}>
      <td>#{order.id}</td>

      <td>Customer #{order.customer_id}</td>

      <td>{order.delivery_address}</td>

      <td>KES {Number(order.total_amount).toFixed(2)}</td>

      <td>
        <span
          className={`status-${order.status
            .toLowerCase()
            .replaceAll("_", "-")}`}
        >
          {order.status.replaceAll("_", " ")}
        </span>
      </td>

      {role === "DISPATCHER" && (
        <td>
          {order.status === "PENDING" ? (
            selectedOrderId === order.id ? (
              <div className="assignment-controls">
                <select
                  value={selectedRiderId}
                  onChange={(event) =>
                    setSelectedRiderId(event.target.value)
                  }
                  disabled={syncing}
                >
                  <option value="">Select rider</option>

                  {riders.map((rider) => (
                    <option key={rider.id} value={rider.id}>
                      {rider.name} — Rider #{rider.id}
                    </option>
                  ))}
                </select>

                <button
                  onClick={() => handleAssignOrder(order.id)}
                  disabled={syncing || !selectedRiderId}
                >
                  {syncing ? "Assigning..." : "Assign"}
                </button>

                <button
                  onClick={() => {
                    setSelectedOrderId(null);
                    setSelectedRiderId("");
                  }}
                  disabled={syncing}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  setSelectedOrderId(order.id);
                  setSelectedRiderId("");
                }}
                disabled={syncing}
              >
                Assign Rider
              </button>
            )
          ) : (
            <span>—</span>
          )}
        </td>
      )}
    </tr>
  ))}
</tbody>
            </table>
          </div>
        )}
      </section>
)}

{(role === "ADMIN" || role === "DISPATCHER" || role === "RIDER") && (
      <section className="orders-section delivery-section">
        <div className="section-header">
          <h2>Delivery Tracking</h2>

          <span>
            {deliveries.length}{" "}
            {deliveries.length === 1 ? "delivery" : "deliveries"}
          </span>
        </div>

        {loading ? (
          <p>Loading deliveries...</p>
        ) : deliveries.length === 0 ? (
          <p>No deliveries found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Delivery ID</th>
                  <th>Order ID</th>
                  <th>Rider ID</th>
                  <th>Assigned At</th>
                  <th>Status</th>
                  {role === "RIDER" && <th>Actions</th>}
                </tr>
              </thead>

              <tbody>
                {deliveries.map((delivery) => {
                  const order = orders.find(
                    (item) => item.id === delivery.order_id
                  );

                  const deliveryStatus = getDeliveryStatus(delivery);

                  return (
                    <tr key={delivery.id}>
                      <td>#{delivery.id}</td>
                      <td>#{delivery.order_id}</td>
                      <td>
                        {delivery.rider_id
                          ? `Rider #${delivery.rider_id}`
                          : "Unassigned"}
                      </td>
                      <td>
                        {delivery.assigned_at
                          ? new Date(
                              delivery.assigned_at
                            ).toLocaleString()
                          : "—"}
                      </td>
                      <td>
                        <span
                          className={`status-${deliveryStatus
                            .toLowerCase()
                            .replaceAll("_", "-")}`}
                        >
                          {deliveryStatus.replaceAll("_", " ")}
                        </span>
                      </td>
                      {role === "RIDER" && (
                        <td>
                          {deliveryStatus === "ASSIGNED" && (
                            <button
                              onClick={() =>
                                handleDeliveryStatusUpdate(
                                  delivery.id,
                                  "PICKED_UP"
                                )
                              }
                              disabled={syncing}
                            >
                              Pick Up
                            </button>
                          )}
                          {deliveryStatus === "PICKED_UP" && (
                            <button
                              onClick={() =>
                                handleDeliveryStatusUpdate(
                                  delivery.id,
                                  "OUT_FOR_DELIVERY"
                                )
                              }
                              disabled={syncing}
                            >
                              Start Delivery
                            </button>
                          )}
                          {deliveryStatus === "OUT_FOR_DELIVERY" && (
  <>
    {selectedDeliveryId !== delivery.id ? (
      <button
        onClick={() => setSelectedDeliveryId(delivery.id)}
        disabled={syncing}
      >
        Mark Delivered
      </button>
    ) : (
      <div className="delivery-confirmation">
        <input
          type="text"
          placeholder="Proof of delivery"
          value={proofOfDelivery}
          onChange={(event) =>
            setProofOfDelivery(event.target.value)
          }
        />

        <input
          type="text"
          placeholder="Optional notes"
          value={deliveryNotes}
          onChange={(event) =>
            setDeliveryNotes(event.target.value)
          }
        />

        <button
          onClick={() =>
            handleDeliveryStatusUpdate(
              delivery.id,
              "DELIVERED",
              proofOfDelivery || null,
              deliveryNotes || null
            )
          }
          disabled={syncing || !proofOfDelivery.trim()}
        >
          Confirm Delivery
        </button>

        <button
          onClick={() => {
            setSelectedDeliveryId(null);
            setProofOfDelivery("");
            setDeliveryNotes("");
          }}
          disabled={syncing}
        >
          Cancel
        </button>
      </div>
    )}
  </>
)}
                          {deliveryStatus === "DELIVERED" && (
                            <span>Completed</span>
                          )}
                        </td>
                      )}
                        </tr>

                      );
                    })}
              </tbody>
            </table>
          </div>
        )}
      </section>
)}
    </div>
  );
}

export default Dashboard;