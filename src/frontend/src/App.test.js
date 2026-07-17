import { render, screen } from "@testing-library/react";
import App from "./App";

jest.mock("./components/LocationMap", () => () => <div>Map</div>);

test("renders the existing prediction application", () => {
  render(<App />);
  expect(screen.getByText("Nepal House Predictor")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Predict" })).toBeInTheDocument();
});
