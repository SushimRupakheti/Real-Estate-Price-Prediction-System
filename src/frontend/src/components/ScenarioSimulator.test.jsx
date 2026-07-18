import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import ScenarioSimulator from "./ScenarioSimulator";

jest.mock("axios");

const currentIndex = {
  overall_score: 59,
  indicators_used: {
    nearest_road_distance_m: 60, nearest_major_road_distance_m: 850,
    nearest_major_road_type: "secondary", schools: 5, colleges: 1,
    kindergartens: 1, hospitals: 2, clinics: 2, bus_stops: 3,
    marketplaces: 1, supermarkets: 1, banks: 3, parks: 2,
  },
};
const response = {
  current: { overall_index: 59, category_scores: { accessibility: 76, healthcare: 48 } },
  scenario: { overall_index: 66, index_change: 7, category_scores: { accessibility: 88, healthcare: 61 }, category_score_differences: { accessibility: 12, healthcare: 13 } },
  value_shift: {
    classification: "Strong Positive Scenario", minimum_percent: 3, maximum_percent: 7,
    minimum_value: 41200000, maximum_value: 42800000,
    minimum_value_formatted: "NPR 4.12 Crore", maximum_value_formatted: "NPR 4.28 Crore",
  },
  rule_contributions: [{
    change: "Added 1 hospital", change_type: "new_hospital", category: "healthcare",
    current_category_score: 48, scenario_category_score: 61, score_difference: 13,
  }],
  metadata: { disclaimer: "This result is a configurable, rule-based what-if analysis. It is not a statistically trained future-price forecast, investment guarantee, or professional valuation." },
};

const openPlanner = () => fireEvent.click(screen.getByLabelText("Enable future scenario"));

test("uses progressive disclosure and evaluates one selected planned development", async () => {
  axios.post.mockResolvedValue({ data: response });
  render(<ScenarioSimulator baselinePrice={40000000} currentIndex={currentIndex} />);
  expect(screen.getByText("Future Infrastructure Planning")).toBeInTheDocument();
  expect(screen.queryByLabelText("Planned development")).not.toBeInTheDocument();
  openPlanner();
  fireEvent.change(screen.getByLabelText("Planned development"), { target: { value: "new_hospital" } });
  expect(screen.getByText("Planned hospital", { selector: "p" })).toBeInTheDocument();
  expect(axios.post).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Evaluate Future Scenario" }));
  await screen.findByText("Future scenario");
  expect(axios.post).toHaveBeenCalledWith(expect.stringContaining("/scenarios/simulate"), expect.objectContaining({
    baseline_price: 40000000,
    changes: [{ type: "new_hospital", quantity: 1 }],
  }), { timeout: 15000 });
  expect(screen.getByText("48 → 61")).toBeInTheDocument();
  expect(screen.getAllByText(/NPR 4.12 Crore/)[0]).toHaveTextContent("NPR 4.12 Crore – NPR 4.28 Crore");
  expect(screen.getByText("Difference: +12,00,000 to +28,00,000 NPR")).toBeInTheDocument();
  expect(screen.getByText("Healthcare accessibility improved.")).toBeInTheDocument();
  expect(screen.getByText(/not a statistically trained future-price forecast/)).toBeInTheDocument();
});

test("shows only the field needed for a planned road upgrade", () => {
  render(<ScenarioSimulator baselinePrice={40000000} currentIndex={currentIndex} />);
  openPlanner();
  fireEvent.change(screen.getByLabelText("Planned development"), { target: { value: "road_upgrade" } });
  expect(screen.getByLabelText("Future road classification")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Future road classification"), { target: { value: "primary" } });
  expect(screen.getByText("Planned road upgrade: secondary to primary")).toBeInTheDocument();
});

test("shows loading state and API errors", async () => {
  let rejectRequest;
  axios.post.mockReturnValue(new Promise((resolve, reject) => { rejectRequest = reject; }));
  render(<ScenarioSimulator baselinePrice={40000000} currentIndex={currentIndex} />);
  openPlanner();
  fireEvent.change(screen.getByLabelText("Planned development"), { target: { value: "new_bus_stop" } });
  fireEvent.click(screen.getByRole("button", { name: "Evaluate Future Scenario" }));
  expect(screen.getByRole("button", { name: "Evaluating future scenario..." })).toBeDisabled();
  rejectRequest({ response: { data: { detail: "Invalid scenario" } } });
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Invalid scenario"));
});

test("reset clears controls and scenario results", async () => {
  axios.post.mockResolvedValue({ data: response });
  render(<ScenarioSimulator baselinePrice={40000000} currentIndex={currentIndex} />);
  openPlanner();
  fireEvent.change(screen.getByLabelText("Planned development"), { target: { value: "new_hospital" } });
  fireEvent.click(screen.getByRole("button", { name: "Evaluate Future Scenario" }));
  await screen.findByText("Future scenario");
  fireEvent.click(screen.getByRole("button", { name: "Reset scenario" }));
  expect(screen.queryByText("Future scenario")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("Planned development")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Enable future scenario")).not.toBeChecked();
});

test("offers readable proximity bands instead of manual distance entry", () => {
  render(<ScenarioSimulator baselinePrice={40000000} currentIndex={currentIndex} />);
  openPlanner();
  fireEvent.change(screen.getByLabelText("Planned development"), { target: { value: "major_road_distance" } });
  const proximity = screen.getByLabelText("Planned accessibility");
  expect(proximity).toHaveTextContent("Within 250 m");
  expect(proximity).toHaveTextContent("Within 500 m");
  expect(proximity).not.toHaveTextContent("Within 1 km");
});
