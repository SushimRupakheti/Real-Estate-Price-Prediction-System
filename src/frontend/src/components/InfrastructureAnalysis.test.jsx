import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import InfrastructureAnalysis from "./InfrastructureAnalysis";

jest.mock("axios");
jest.mock("./LocationMap", () => ({ onCoordinateConfirm, facilities = [], selectedFacility, onFacilitySelect }) => <div><button onClick={() => onCoordinateConfirm({ lat: 27.7, lon: 85.3 })}>Choose point</button>{facilities[0] && <button onClick={() => onFacilitySelect(facilities[0])}>Select map facility</button>}<span data-testid="highlighted-facility">{selectedFacility?.name || "none"}</span></div>);

const empty = { raw_count: 0, deduplicated_count: 0, radius_m: 1000, places: [] };
const school = { name: "School A", osm_id: 10, osm_type: "node", latitude: 27.701, longitude: 85.301, distance_m: 120, tags: { amenity: "school" } };
const road = { name: "Ring Road", distance_m: 25, road_type: "primary", highway_classification: "primary", osm_id: 20, osm_type: "way", latitude: 27.7, longitude: 85.3, tags: { highway: "primary" } };
const response = { selected_location: { latitude: 27.7, longitude: 85.3 }, roads: { nearest_road: road, nearest_major_road: road }, categories: { schools: { raw_count: 1, deduplicated_count: 1, radius_m: 1000, places: [school] }, colleges: empty, kindergartens: empty, hospitals: empty, clinics: empty, bus_stops: empty, marketplaces: empty, supermarkets: empty, banks: empty, parks: empty }, metadata: {} };

test("requests and displays raw infrastructure indicators with loading state", async () => {
  let resolveRequest; axios.post.mockReturnValue(new Promise((resolve) => { resolveRequest = resolve; }));
  render(<InfrastructureAnalysis locationLabel="Balkhu, Kathmandu" />);
  fireEvent.click(screen.getByText("Choose point"));
  fireEvent.click(screen.getByRole("button", { name: "Analyze Infrastructure" }));
  expect(screen.getByText("Analyzing current infrastructure...")).toBeInTheDocument();
  resolveRequest({ data: response });
  expect(await screen.findByText("Current nearby infrastructure")).toBeInTheDocument();
  expect(screen.getAllByText(/Ring Road/).length).toBeGreaterThan(0);
  expect(screen.getByText("Schools (1)")).toBeInTheDocument();
  fireEvent.click(screen.getByText("School A"));
  expect(screen.getByTestId("highlighted-facility")).toHaveTextContent("School A");
  expect(axios.post).toHaveBeenCalledWith(expect.stringContaining("/infrastructure/analyze"), expect.objectContaining({ latitude: 27.7, longitude: 85.3 }));
});

test("exports the transparent response as JSON", async () => {
  URL.createObjectURL = jest.fn(() => "blob:test"); URL.revokeObjectURL = jest.fn();
  jest.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  axios.post.mockResolvedValue({ data: response }); render(<InfrastructureAnalysis locationLabel="Balkhu" />);
  fireEvent.click(screen.getByText("Choose point")); fireEvent.click(screen.getByRole("button", { name: "Analyze Infrastructure" }));
  await screen.findByText("Current nearby infrastructure"); fireEvent.click(screen.getByRole("button", { name: "Export JSON" }));
  expect(URL.createObjectURL).toHaveBeenCalled(); expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();
});

test("shows infrastructure API errors", async () => {
  axios.post.mockRejectedValue({ response: { data: { detail: "OSM unavailable" } } });
  render(<InfrastructureAnalysis locationLabel="Balkhu, Kathmandu" />);
  fireEvent.click(screen.getByText("Choose point"));
  fireEvent.click(screen.getByRole("button", { name: "Analyze Infrastructure" }));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("OSM unavailable"));
});
