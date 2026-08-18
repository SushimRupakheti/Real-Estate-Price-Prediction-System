import { fireEvent, render, screen } from "@testing-library/react";
import App from "./App";

jest.mock("./components/LocationMap", () => () => <div>Map</div>);

test("renders the existing prediction application", () => {
  window.history.replaceState({}, "", "/analyze/location");
  render(<App />);
  expect(document.querySelector(".light-theme")).toBeInTheDocument();
  expect(screen.getByText("Nepal Property Insight")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Analyse Property" })).toHaveAttribute("href", "/analyze/location");
  expect(screen.getByRole("link", { name: "Compare Locations" })).toHaveAttribute("href", "/compare");
  expect(screen.getByRole("link", { name: "Saved Estimates" })).toHaveAttribute("href", "/saved_estimates");
});

test("navigation updates the URL and rendered page", () => {
  window.history.replaceState({}, "", "/analyze/location");
  render(<App />);

  fireEvent.click(screen.getByRole("link", { name: "Compare Locations" }));

  expect(window.location.pathname).toBe("/compare");
  expect(screen.getByRole("heading", { name: "Compare Locations" })).toBeInTheDocument();
});
