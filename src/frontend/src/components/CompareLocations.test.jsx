import { render, screen } from "@testing-library/react";
import CompareLocations from "./CompareLocations";

const record = (id, location, score) => ({
  id, location, current_price: 40000000, overall_score: score, classification: "Good",
  category_scores: { accessibility: 70, education: 60, healthcare: 55, commerce: 50, public_transport: 65, recreation: 45 },
  indicators: { nearest_major_road_distance_m: 400, schools: 5, hospitals: 2, bus_stops: 3 },
});

test("compares two saved current location analyses", () => {
  localStorage.setItem("propertyAnalyses", JSON.stringify([record("a", "Kalanki", 70), record("b", "Imadol", 62)]));
  render(<CompareLocations />);
  expect(screen.getByText("Compare Locations")).toBeInTheDocument();
  expect(screen.getAllByText("Kalanki").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Imadol").length).toBeGreaterThan(0);
  expect(screen.getByText("Current estimated value")).toBeInTheDocument();
});
