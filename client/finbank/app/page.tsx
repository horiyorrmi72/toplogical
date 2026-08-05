"use client";

import { Bell } from "lucide-react";

import React, { useState, useEffect } from "react";
import { toast } from "sonner";
// const API_BASE = "http://localhost:8000/api/v1";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

interface Account {
  id: string;
  account_number: string;
  account_type: string;
  balance: string;
  credit_limit: string;
}

interface Transaction {
  id: string;
  reference_number: string;
  category: string;
  amount: string;
  status: string;
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
}

export default function FinBankDashboard() {
  const [email, setEmail] = useState("john@example.com");
  const [password, setPassword] = useState("password123");
  const [fullName, setFullName] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [search, setSearch] = useState("");
  const [authMsg, setAuthMsg] = useState("");
  const [transferType, setTransferType] = useState<"internal" | "external">(
    "internal",
  );
  const [externalAccNum, setExternalAccNum] = useState("");
  const [lookupRecipient, setLookupRecipient] = useState<{
    account_id: string;
    owner_name: string;
    account_type: string;
  } | null>(null);
  const [lookupError, setLookupError] = useState("");
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [isTransferring, setIsTransferring] = useState(false);
  // notifications state
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);

  // profile & settings state
  const [activeTab, setActiveTab] = useState<"dashboard" | "settings">(
    "dashboard",
  );
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [fullNameInput, setFullNameInput] = useState("");
  const [currentPasswordInput, setCurrentPasswordInput] = useState("");
  const [newPasswordInput, setNewPasswordInput] = useState("");
  const [profileMsg, setProfileMsg] = useState("");

  // transfer form
  const [sourceId, setSourceId] = useState("");
  const [destId, setDestId] = useState("");
  const [amount, setAmount] = useState("");
  const [transferMsg, setTransferMsg] = useState("");

  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isRegisteringSubmit, setIsRegisteringSubmit] = useState(false);
  const [downloadingTxnId, setDownloadingTxnId] = useState<string | null>(null);

  const [mounted, setMounted] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    setToken(localStorage.getItem("token"));
  }, []);

  // handle Login
  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoggingIn) return;
    setIsLoggingIn(true);

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok && data.access_token) {
        localStorage.setItem("token", data.access_token);
        setToken(data.access_token);
      } else {
        console.error(data);
        toast.error(data.detail || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      toast.error("Network error while trying to sign in.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  // registeration
  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isRegisteringSubmit) return;
    setIsRegisteringSubmit(true);

    setAuthMsg("");

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        toast.success("Registration successful! Logging you in...");
        await handleLogin(e);
      } else {
        toast.error(`Error: ${data.detail || "Registration failed"}`);
      }
    } catch (err) {
      console.error("Registration error:", err);
      toast.error("Network error during registration.");
    } finally {
      setIsRegisteringSubmit(false);
    }
  };

  //logout
  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  const handleLookup = async () => {
    if (isLookingUp || !externalAccNum) return;
    setLookupError("");
    setLookupRecipient(null);
    if (!externalAccNum) return;

    const res = await fetch(`${API_BASE}/accounts/lookup/${externalAccNum}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (res.ok) {
      setLookupRecipient(data);
      setDestId(data.account_id);
      toast.success(
        `Found recipient: ${data.owner_name} (${data.account_type})`,
      );
    } else {
      setLookupError(data.detail || "Account lookup failed");
      toast.error(data.detail || "Account lookup failed");
    }
  };

  // fetch user  profile
  const fetchProfile = async () => {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    //we send the trigger with necessary params to the server to blacklist the token and invalidate the refresh token and session
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) {
      const data = await res.json();
      setProfile(data);
      setFullNameInput(data.full_name);
    }
  };

  // fetch accounts
  const fetchAccounts = async () => {
    const res = await fetch(`${API_BASE}/accounts/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) setAccounts(await res.json());
  };

  // Fetch Transactions Ledger
  const fetchTransactions = async () => {
    const query = search ? `?search=${encodeURIComponent(search)}` : "";
    const res = await fetch(`${API_BASE}/transactions/${query}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) {
      const data = await res.json();
      setTransactions(data.items);
    }
  };

  // fetch notifications
  const fetchNotifications = async () => {
    const res = await fetch(`${API_BASE}/notifications/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) {
      setNotifications(await res.json());
    }
  };

  // mark notification as read
  const markAsRead = async (notifId: string) => {
    const res = await fetch(`${API_BASE}/notifications/${notifId}/read`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) {
      fetchNotifications();
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchProfile();
    fetchAccounts();
    fetchTransactions();
    fetchNotifications();
  }, [token, search]);

  // transfer
  const handleTransfer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (isTransferring) return;
    setIsTransferring(true);
    setTransferMsg("");

    //we giv it an idempotency key to avoid duplicate transfer
    const idempotencyKey = `idempotency-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    try {
      const res = await fetch(`${API_BASE}/transfers/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({
          source_account_id: sourceId,
          destination_account_id: destId,
          amount: parseFloat(amount),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Transfer successful!");
        setAmount("");
        fetchAccounts();
        fetchTransactions();
        fetchNotifications();
      } else {
        toast.error(`Error: ${data.detail || "Transfer failed"}`);
      }
    } catch (err) {
      console.error("Transfer error:", err);
      toast.error("Error: Network failure or request timeout.");
    } finally {
      // Re-enable the button after process completes
      setIsTransferring(false);
    }
  };

  // update profile name
  const handleProfileUpdate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setProfileMsg("");
    const res = await fetch(`${API_BASE}/profile/me`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ full_name: fullNameInput }),
    });
    const data = await res.json();
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) {
      toast.success("Profile name updated successfully!");
      fetchProfile();
    } else {
      toast.error(`Error: ${data.detail}`);
    }
  };

  // change password
  const handleChangePassword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setProfileMsg("");
    const res = await fetch(`${API_BASE}/profile/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        current_password: currentPasswordInput,
        new_password: newPasswordInput,
      }),
    });
    const data = await res.json();
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) {
      toast.success("Password updated successfully!");
      setCurrentPasswordInput("");
      setNewPasswordInput("");
    } else {
      toast.error(`Error: ${data.detail}`);
    }
  };

  // download PDF receipt
  const downloadReceipt = (txnId: string, refNo: string) => {
    if (downloadingTxnId === txnId) return;
    setDownloadingTxnId(txnId);
    try {
      fetch(`${API_BASE}/transactions/${txnId}/receipt/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => res.blob())
        .then((blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `receipt_${refNo}.pdf`;
          document.body.appendChild(a);
          a.click();
          a.remove();
        });
    } catch (err) {
      console.error("Download error:", err);
    } finally {
      setDownloadingTxnId(null);
    }
  };

  if (!mounted) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-100">
        Loading...
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-100 font-sans">
        <form
          onSubmit={isRegistering ? handleRegister : handleLogin}
          className="p-6 bg-white rounded-lg shadow-md w-80 space-y-4"
        >
          <h2 className="text-xl font-bold text-slate-800">
            {isRegistering ? "Create FinBank Account" : "FinBank Login"}
          </h2>

          {authMsg && (
            <div className="text-xs p-2 rounded bg-blue-50 text-blue-700 font-medium">
              {authMsg}
            </div>
          )}

          {isRegistering && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                Full Name
              </label>
              <input
                className="w-full p-2 border rounded text-sm text-black"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Smith"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Email Address
            </label>
            <input
              className="w-full p-2 border rounded text-sm text-black"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="john@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Password
            </label>
            <input
              className="w-full p-2 border rounded text-sm text-black"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••"
              required
              minLength={8}
            />
          </div>

          <button
            className="w-full bg-blue-600 text-white p-2 rounded font-medium hover:bg-blue-700 text-sm disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all"
            type="submit"
            disabled={isRegistering ? isRegisteringSubmit : isLoggingIn}
          >
            {(isRegistering ? isRegisteringSubmit : isLoggingIn) ? (
              <>
                <svg
                  className="animate-spin h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>
                  {isRegistering ? "Creating Account..." : "Signing In..."}
                </span>
              </>
            ) : (
              <span>{isRegistering ? "Sign Up" : "Sign In"}</span>
            )}
          </button>

          <div className="text-center pt-2">
            <button
              type="button"
              className="text-xs text-blue-600 underline hover:text-blue-800"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setAuthMsg("");
              }}
            >
              {isRegistering
                ? "Already have an account? Sign In"
                : "Need an account? Register"}
            </button>
          </div>
        </form>
      </div>
    );
  }
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="min-h-screen bg-slate-50 p-8 space-y-8 font-sans">
      {/* Header bar */}
      <div className="flex justify-between items-center border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            FinBank Digital Banking
          </h1>
          {profile && (
            <p className="text-sm text-slate-500">
              Welcome, {profile.full_name} ({profile.email})
            </p>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Navigation tabs */}
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`px-3 py-1 rounded text-sm font-medium ${activeTab === "dashboard" ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-700"}`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab("settings")}
              className={`px-3 py-1 rounded text-sm font-medium ${activeTab === "settings" ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-700"}`}
            >
              Profile Settings
            </button>
          </div>

          {/*inapp notification*/}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 bg-slate-200 rounded-full hover:bg-slate-300"
            >
              <Bell />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* notification drawer popover */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-xl z-50 p-4">
                <div className="flex justify-between items-center border-b pb-2 mb-2">
                  <h3 className="font-semibold text-slate-700">
                    Notifications
                  </h3>
                  <button
                    className="text-xs text-slate-400 hover:text-slate-600"
                    onClick={() => setShowNotifications(false)}
                  >
                    Close
                  </button>
                </div>

                {notifications.length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">
                    No notifications available
                  </p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`p-2 rounded border text-xs ${n.is_read ? "bg-slate-50 border-slate-100" : "bg-blue-50 border-blue-200"}`}
                      >
                        <div className="flex justify-between items-start">
                          <span className="font-bold text-slate-800">
                            {n.title}
                          </span>
                          {!n.is_read && (
                            <button
                              onClick={() => markAsRead(n.id)}
                              className="text-[10px] bg-blue-600 text-white px-1.5 py-0.5 rounded hover:bg-blue-700"
                            >
                              Mark Read
                            </button>
                          )}
                        </div>
                        <p className="text-slate-600 mt-1">{n.message}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <button
            className="text-sm bg-red-100 text-red-700 px-3 py-1.5 rounded hover:bg-red-200"
            onClick={() => {
              localStorage.clear();
              setToken("");
            }}
          >
            Sign Out
          </button>
        </div>
      </div>

      {activeTab === "dashboard" ? (
        <>
          {/* accounts section */}
          <section>
            <h2 className="text-lg font-semibold text-slate-700 mb-3">
              Your Accounts
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {accounts.map((acc) => (
                <div
                  key={acc.id}
                  className="p-4 bg-white rounded-lg shadow-sm border border-slate-200"
                >
                  <div className="text-xs font-bold text-blue-600 uppercase tracking-wide">
                    {acc.account_type}
                  </div>
                  <div className="text-sm text-slate-500 mt-1">
                    Account #:{" "}
                    {/*{acc.account_number.length > 4
                      ? `****${acc.account_number.slice(-4)}`
                      : acc.account_number}*/}
                    <span>{acc.account_number}</span>
                  </div>
                  <div className="text-2xl font-bold text-slate-800 mt-2">
                    $
                    {parseFloat(acc.balance).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}
                  </div>
                  {acc.account_type === "CREDIT_CARD" && (
                    <div className="text-xs text-slate-400 mt-1">
                      Credit Limit: $
                      {parseFloat(acc.credit_limit).toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* transfer form */}
          <section className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-slate-700">
                Transfer Money
              </h2>
              <div className="flex space-x-2 text-xs">
                <button
                  type="button"
                  className={`px-3 py-1 rounded font-medium ${transferType === "internal" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}
                  onClick={() => {
                    setTransferType("internal");
                    setLookupRecipient(null);
                    setDestId("");
                  }}
                >
                  My Accounts
                </button>
                <button
                  type="button"
                  className={`px-3 py-1 rounded font-medium ${transferType === "external" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}
                  onClick={() => {
                    setTransferType("external");
                    setDestId("");
                  }}
                >
                  Other Customer
                </button>
              </div>
            </div>

            {transferMsg && (
              <div className="mb-4 text-sm text-blue-600 font-medium">
                {transferMsg}
              </div>
            )}

            {transferType === "external" && (
              <div className="mb-4 p-3 bg-slate-50 border border-slate-200 rounded text-xs space-y-2">
                <label className="block font-medium text-slate-600">
                  Enter Recipient Account Number
                </label>
                <div className="flex space-x-2">
                  <input
                    className="p-2 border rounded text-sm w-64 bg-white"
                    type="text"
                    placeholder="e.g. 9876544829"
                    value={externalAccNum}
                    onChange={(e) => setExternalAccNum(e.target.value)}
                    disabled={isLookingUp}
                  />
                  <button
                    type="button"
                    className="bg-slate-800 text-white px-3 py-1.5 rounded hover:bg-slate-900 disabled:bg-slate-400 disabled:cursor-not-allowed flex items-center space-x-2 text-xs font-medium transition-all"
                    onClick={handleLookup}
                    disabled={isLookingUp || !externalAccNum.trim()}
                  >
                    {isLookingUp ? (
                      <>
                        <svg
                          className="animate-spin h-3.5 w-3.5 text-white"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          ></circle>
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          ></path>
                        </svg>
                        <span>Verifying...</span>
                      </>
                    ) : (
                      <span>Verify Recipient</span>
                    )}
                  </button>
                </div>

                {lookupError && (
                  <p className="text-red-500 font-medium text-xs mt-1">
                    {lookupError}
                  </p>
                )}

                {lookupRecipient && (
                  <p className="text-green-700 font-medium text-xs mt-1">
                    ✓ Verified: {lookupRecipient.owner_name} (
                    {lookupRecipient.account_type})
                  </p>
                )}
              </div>
            )}
            <form
              onSubmit={handleTransfer}
              className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end"
            >
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  From Account
                </label>
                <select
                  className="w-full p-2 border rounded"
                  value={sourceId}
                  onChange={(e) => setSourceId(e.target.value)}
                  required
                >
                  <option value="">Select Account</option>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.account_type} ({a.account_number})
                    </option>
                  ))}
                </select>
              </div>

              {transferType === "internal" && (
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">
                    To Account
                  </label>
                  <select
                    className="w-full p-2 border rounded"
                    value={destId}
                    onChange={(e) => setDestId(e.target.value)}
                    required
                  >
                    <option value="">Select Account</option>
                    {accounts.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.account_type} ({a.account_number})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Amount ($)
                </label>
                <input
                  className="w-full p-2 border rounded"
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  required
                />
              </div>

              <button
                className="bg-blue-600 text-white p-2 rounded font-medium hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all"
                type="submit"
                disabled={
                  isTransferring ||
                  (transferType === "external" && !lookupRecipient)
                }
              >
                {isTransferring ? (
                  <>
                    <svg
                      className="animate-spin h-4 w-4 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    <span>Processing...</span>
                  </>
                ) : (
                  <span>Submit Transfer</span>
                )}
              </button>
            </form>
          </section>

          {/* ledger & receipts */}
          <section className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-slate-700">
                Transaction Ledger
              </h2>
              <input
                className="p-2 border rounded text-sm w-64"
                type="text"
                placeholder="Search reference, description..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b bg-slate-50 text-slate-600">
                    <th className="p-2">Reference</th>
                    <th className="p-2">Category</th>
                    <th className="p-2">Amount</th>
                    <th className="p-2">Status</th>
                    <th className="p-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t) => (
                    <tr key={t.id} className="border-b hover:bg-slate-50">
                      <td className="p-2 font-mono text-xs">
                        {t.reference_number}
                      </td>
                      <td className="p-2">{t.category}</td>
                      <td className="p-2 font-semibold">
                        ${parseFloat(t.amount).toFixed(2)}
                      </td>
                      <td className="p-2">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          {t.status}
                        </span>
                      </td>
                      <td className="p-2">
                        <button
                          className="text-xs text-blue-600 font-medium underline hover:text-blue-800 disabled:text-slate-400 disabled:no-underline flex items-center space-x-1"
                          onClick={() =>
                            downloadReceipt(t.id, t.reference_number)
                          }
                          disabled={downloadingTxnId === t.id}
                        >
                          {downloadingTxnId === t.id ? (
                            <>
                              <svg
                                className="animate-spin h-3 w-3 text-blue-600"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                              >
                                <circle
                                  className="opacity-25"
                                  cx="12"
                                  cy="12"
                                  r="10"
                                  stroke="currentColor"
                                  strokeWidth="4"
                                ></circle>
                                <path
                                  className="opacity-75"
                                  fill="currentColor"
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                ></path>
                              </svg>
                              <span>Downloading...</span>
                            </>
                          ) : (
                            <span>Download PDF</span>
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : (
        /* profile settings */
        <section className="space-y-6 max-w-2xl">
          {profileMsg && (
            <div className="p-3 bg-blue-50 border border-blue-200 text-blue-700 text-sm rounded">
              {profileMsg}
            </div>
          )}

          {/* profile details form */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-700 mb-4">
              Profile Information
            </h2>
            <form onSubmit={handleProfileUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Email Address (Read-only)
                </label>
                <input
                  className="w-full p-2 border rounded bg-slate-100 text-slate-500"
                  type="email"
                  value={profile?.email || ""}
                  disabled
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Full Name
                </label>
                <input
                  className="w-full p-2 border rounded"
                  type="text"
                  value={fullNameInput}
                  onChange={(e) => setFullNameInput(e.target.value)}
                  required
                />
              </div>
              <button
                className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
                type="submit"
              >
                Update Profile
              </button>
            </form>
          </div>

          {/* change password form */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-700 mb-4">
              Change Password
            </h2>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Current Password
                </label>
                <input
                  className="w-full p-2 border rounded"
                  type="password"
                  value={currentPasswordInput}
                  onChange={(e) => setCurrentPasswordInput(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  New Password
                </label>
                <input
                  className="w-full p-2 border rounded"
                  type="password"
                  value={newPasswordInput}
                  onChange={(e) => setNewPasswordInput(e.target.value)}
                  minLength={8}
                  required
                />
              </div>
              <button
                className="bg-slate-800 text-white px-4 py-2 rounded text-sm hover:bg-slate-900"
                type="submit"
              >
                Change Password
              </button>
            </form>
          </div>
        </section>
      )}
    </div>
  );
}
