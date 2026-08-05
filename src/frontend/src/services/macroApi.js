import axios from "axios";
const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
export const getCurrentMacro = () => axios.get(`${API}/api/macro/current`).then((r) => r.data);
export const adjustPrice = (predictedPrice) => axios.post(`${API}/api/macro/adjust`, { predicted_price: predictedPrice }).then((r) => r.data);
export const simulateMacroScenario = (payload) => axios.post(`${API}/api/macro/scenario`, payload).then((r) => r.data);
