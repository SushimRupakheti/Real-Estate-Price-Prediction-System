import { render, screen } from "@testing-library/react";
import PredictionDashboard from "./PredictionDashboard";

jest.mock("./InfrastructureAnalysis", () => () => <div>Infrastructure</div>);
jest.mock("./macro/MacroConditionsCard", () => () => <div>Macro</div>);

test("labels grouped location SHAP with the selected property location", () => {
  render(<PredictionDashboard
    result={{
      predicted_price: 35000000,
      shap_values: [
        { feature: "LOCATION", shap_value: 9000000 },
        { feature: "BATHROOM", shap_value: 5000000 },
      ],
    }}
    form={{}}
    locationLabel="Kalanki, Kathmandu"
    propertyPoint={{ lat: 27.69, lon: 85.28 }}
  />);

  expect(screen.getByText("Location (Kalanki, Kathmandu)")).toBeInTheDocument();
  expect(screen.queryByText(/Bhaisepati/)).not.toBeInTheDocument();
  expect(screen.getAllByText("Raised estimate")).toHaveLength(2);
});
