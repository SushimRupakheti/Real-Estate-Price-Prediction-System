jest.mock("./LocationMap", () => () => <div>Map</div>);

import { validatePropertyForm } from "./PredictForm";

const validForm = {
  floor: "2.5",
  bedroom: "3",
  bathroom: "2",
  land_area: "1369",
  property_age: "10",
};

test("accepts property details inside the model-supported ranges", () => {
  expect(validatePropertyForm(validForm)).toEqual({});
});

test("rejects zero bedrooms before the prediction request", () => {
  expect(validatePropertyForm({ ...validForm, bedroom: "0" })).toEqual({
    bedroom: "Bedrooms must be between 1 and 36.",
  });
});

test("returns field-level errors for missing and out-of-range values", () => {
  expect(validatePropertyForm({
    ...validForm,
    floor: "8",
    bathroom: "",
    land_area: "6000",
    property_age: "101",
  })).toEqual({
    land_area: "Land area must be between 102.675 and 5,886.7 sq ft.",
    bathroom: "Bathrooms is required.",
    floor: "Floors must be between 1 and 7.",
    property_age: "Property age must be between 0 and 100 years.",
  });
});
