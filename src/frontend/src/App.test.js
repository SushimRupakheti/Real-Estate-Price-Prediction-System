import { render, screen } from "@testing-library/react";
import App from "./App";

jest.mock("./components/LocationMap", () => () => <div>Map</div>);

test("renders the existing prediction application", () => {
  render(<App />);
  expect(screen.getByText("Nepal Property Insight")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Analyse Property" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Compare Locations" })).toBeInTheDocument();
});
