import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import LocationMap from "./LocationMap";
import axios from "axios";

jest.mock("axios");

let mockMapHandlers = {};
jest.mock("react-leaflet", () => ({
  MapContainer: ({ children }) => <div data-testid="map" onClick={() => mockMapHandlers.click?.({ latlng: { lat: 27.701234, lng: 85.301234 } })}>{children}</div>,
  TileLayer: () => <div>OpenStreetMap contributors</div>,
  CircleMarker: () => <div data-testid="marker" />,
  Marker: () => <div data-testid="marker" />,
  Popup: ({ children }) => <div>{children}</div>,
  useMap: () => ({ setView: jest.fn(), getZoom: () => 14 }),
  useMapEvents: (handlers) => { mockMapHandlers = handlers; },
}));

test("renders, moves marker, displays coordinates, and confirms point", async () => {
  axios.post.mockResolvedValue({ data: { latitude: 27.659, longitude: 85.352 } });
  const confirm = jest.fn();
  const change = jest.fn();
  render(<LocationMap locationLabel="Imadol, Lalitpur" onCoordinateChange={change} onCoordinateConfirm={confirm} />);
  await waitFor(() => expect(axios.post).toHaveBeenCalled());
  expect(screen.getByTestId("marker")).toBeInTheDocument();
  fireEvent.click(screen.getByTestId("map"));
  expect(screen.getByTestId("selected-coordinates")).toHaveTextContent("27.701234");
  expect(change).toHaveBeenCalledWith({ lat: 27.701234, lon: 85.301234 });
  fireEvent.click(screen.getByRole("button", { name: "Confirm property point" }));
  expect(confirm).toHaveBeenCalledWith({ lat: 27.701234, lon: 85.301234 });
});
