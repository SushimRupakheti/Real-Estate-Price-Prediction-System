export default function ModelCard() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Model Card</h2>
      <p className="text-gray-500 text-sm">
        This model card documents the intended use, limitations, and ethical considerations
        of the Nepal House Price Prediction model.
      </p>

      {/* Overview */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-blue-700 text-lg mb-3">📋 Model Overview</h3>
        <div className="grid grid-cols-2 gap-4">
          {[
            { label: "Model Name", value: "Nepal House Price Predictor" },
            { label: "Algorithm", value: "Gradient Boosting" },
            { label: "Version", value: "1.0" },
            { label: "Last Updated", value: "June 2026" },
            { label: "R² Score", value: "0.7287" },
            { label: "MAE", value: "₹ 60,75,427" },
            { label: "Training Samples", value: "816 properties" },
            { label: "Test Samples", value: "205 properties" },
          ].map((item) => (
            <div key={item.label} className="flex justify-between border-b pb-2">
              <span className="text-gray-500 text-sm">{item.label}</span>
              <span className="font-medium text-gray-800 text-sm">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Intended Use */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-blue-700 text-lg mb-3">✅ Intended Use</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          {[
            "Provide rough price estimates for residential properties in Nepal",
            "Help buyers and sellers understand key price drivers",
            "Support transparent decision making using explainable AI (SHAP)",
            "Educational tool for understanding Nepal real estate market patterns",
          ].map((item) => (
            <li key={item} className="flex items-start gap-2">
              <span className="text-green-500 mt-0.5">✓</span>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* Out of Scope */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-red-600 text-lg mb-3">❌ Out of Scope</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          {[
            "Not suitable for commercial or investment-grade property valuation",
            "Should not replace professional property appraisals or legal valuations",
            "Not designed for commercial buildings, hostels, or rental complexes",
            "Predictions should not be used as the sole basis for financial decisions",
          ].map((item) => (
            <li key={item} className="flex items-start gap-2">
              <span className="text-red-500 mt-0.5">✗</span>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* Limitations */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-orange-600 text-lg mb-3">⚠️ Limitations</h3>
        <div className="space-y-3 text-sm text-gray-700">
          {[
            {
              title: "Limited Dataset",
              desc: "Trained on ~1,050 cleaned records. Larger datasets would improve accuracy significantly."
            },
            {
              title: "R² of 0.65",
              desc: "The model explains 65% of price variation. The remaining 35% is influenced by factors not captured in the data such as interior condition, negotiation, and market timing."
            },
            {
              title: "Static Model",
              desc: "The model was trained on historical data and does not update automatically. Market conditions change over time and the model may drift."
            },
            {
              title: "Geographic Coverage",
              desc: "Primarily covers Kathmandu Valley and major cities. Predictions for rural or less-represented areas may be less accurate."
            },
            {
              title: "No Temporal Features",
              desc: "The model does not account for market trends over time, interest rates, or inflation — factors highlighted in the Nepal Rastra Bank Housing Price Index."
            },
          ].map((item) => (
            <div key={item.title} className="border-l-4 border-orange-300 pl-3">
              <p className="font-medium text-gray-800">{item.title}</p>
              <p className="text-gray-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Ethical Risks */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-purple-700 text-lg mb-3">🔍 Ethical Risks & Mitigation</h3>
        <div className="space-y-4">
          {[
            {
              risk: "Location as Socio-Economic Proxy",
              level: "High",
              color: "red",
              desc: "Location encoding uses median price per area which may reflect socio-economic disparities. This could reinforce existing inequalities if used for lending or insurance decisions.",
              mitigation: "SHAP values are provided per prediction to make location influence transparent and auditable."
            },
            {
              risk: "Data Entry Errors",
              level: "Medium",
              color: "orange",
              desc: "Original dataset contained properties with 36 bedrooms and 34 bathrooms — likely data entry errors or commercial properties mislabeled as residential.",
              mitigation: "Residential filter applied: properties with more than 10 bedrooms or bathrooms were removed."
            },
            {
              risk: "Overconfident Predictions",
              level: "Medium",
              color: "orange",
              desc: "The model provides point estimates without uncertainty ranges which may give users false confidence.",
              mitigation: "R² score and MAE are displayed prominently to communicate prediction uncertainty."
            },
            {
              risk: "Market Drift",
              level: "Medium",
              color: "orange",
              desc: "Nepal's property market is influenced by remittances, interest rates, and infrastructure changes that the model cannot capture.",
              mitigation: "Model card clearly states the training date and recommends periodic retraining."
            },
          ].map((item) => (
            <div key={item.risk} className="border rounded-xl p-4">
              <div className="flex justify-between items-start mb-2">
                <p className="font-medium text-gray-800">{item.risk}</p>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${item.color === "red"
                    ? "bg-red-100 text-red-700"
                    : "bg-orange-100 text-orange-700"
                  }`}>
                  {item.level} Risk
                </span>
              </div>
              <p className="text-sm text-gray-500 mb-2">{item.desc}</p>
              <p className="text-sm text-green-700">
                <span className="font-medium">Mitigation:</span> {item.mitigation}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Training Data */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-blue-700 text-lg mb-3">📊 Training Data</h3>
        <div className="space-y-2 text-sm text-gray-700">
          {[
            { label: "Source", value: "Nepal real estate listing data" },
            { label: "Total Records", value: "1,082 raw → 1,050 after cleaning" },
            { label: "Features", value: "15 (location, size, amenities, age, access)" },
            { label: "Target Variable", value: "House Price (NPR)" },
            { label: "Price Range", value: "₹ 1 Cr — ₹ 32.5 Cr" },
            { label: "Cities Covered", value: "Kathmandu, Lalitpur, Bhaktapur, Chitwan, Pokhara and more" },
            { label: "Outlier Removal", value: "IQR + residential filter (bedroom ≤ 10, bathroom ≤ 10)" },
            { label: "Train/Test Split", value: "80% train / 20% test (random_state=42)" },
          ].map((item) => (
            <div key={item.label} className="flex justify-between border-b pb-2">
              <span className="text-gray-500">{item.label}</span>
              <span className="font-medium text-gray-800 text-right max-w-xs">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Explainability */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
        <h3 className="font-semibold text-blue-700 text-lg mb-2">🤖 Explainability</h3>
        <p className="text-sm text-gray-700">
          This model uses <strong>SHAP (SHapley Additive exPlanations)</strong> to explain
          every prediction. SHAP values show exactly how much each feature contributed to
          pushing the predicted price up or down from the baseline. This makes the model
          transparent and auditable, addressing ethical concerns around black-box AI in
          high-stakes financial decisions.
        </p>
      </div>

    </div>
  );
}