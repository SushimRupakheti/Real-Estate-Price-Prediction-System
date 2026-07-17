import { fireEvent, render, screen } from "@testing-library/react";
import axios from "axios";
import InfrastructureHealthIndex from "./InfrastructureHealthIndex";

jest.mock("axios");

const indexResponse = {
  overall_score: 81,
  classification: "Very Good",
  categories: {
    accessibility: {
      key: "accessibility", label: "Accessibility", score: 91, classification: "Excellent",
      description: "Road access", rules_used: [{
        indicator: "nearest_major_road_distance_m", label: "Nearest major road",
        display_value: "415 m", matched_rule: "Major road within 500 m",
        component_score: 90, component_weight: 0.4, weighted_contribution: 36,
      }],
    },
  },
  metadata: { rules_version: "1.0.0" },
};

test("displays the rule-based index and expandable matched rules", async () => {
  axios.post.mockResolvedValue({ data: indexResponse });
  render(<InfrastructureHealthIndex analysis={{ selected_location: { latitude: 27.7, longitude: 85.3 } }} />);
  expect(await screen.findByText("81")).toBeInTheDocument();
  expect(screen.getByText("Very Good")).toBeInTheDocument();
  fireEvent.click(screen.getByText("Accessibility"));
  expect(screen.getByText("Matched: Major road within 500 m")).toBeInTheDocument();
  expect(axios.post).toHaveBeenCalledWith(
    expect.stringContaining("/infrastructure/index"),
    expect.objectContaining({ analysis: expect.any(Object) }),
    { timeout: 15000 },
  );
});
