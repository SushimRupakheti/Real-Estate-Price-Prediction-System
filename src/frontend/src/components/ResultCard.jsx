export default function ResultCard({ result }) {
  const price = Math.round(result.predicted_price);

  // NRB 2023/24 macro indicators
  const CPI_INFLATION     = 0.054;  // 5.4% consumer price inflation
  const HOUSING_INFLATION = 0.082;  // 8.2% housing specific inflation
  const LENDING_RATE      = 0.115;  // 11.5% average lending rate

  const forecast = [
    {
      year: "1 Year",
      cpi  : Math.round(price * Math.pow(1 + CPI_INFLATION, 1)),
      housing: Math.round(price * Math.pow(1 + HOUSING_INFLATION, 1)),
    },
    {
      year: "3 Years",
      cpi  : Math.round(price * Math.pow(1 + CPI_INFLATION, 3)),
      housing: Math.round(price * Math.pow(1 + HOUSING_INFLATION, 3)),
    },
    {
      year: "5 Years",
      cpi  : Math.round(price * Math.pow(1 + CPI_INFLATION, 5)),
      housing: Math.round(price * Math.pow(1 + HOUSING_INFLATION, 5)),
    },
  ];

  return (
    <div className="space-y-4 mt-6">

      {/* Current Price */}
      <div className="bg-green-50 border border-green-200 rounded-2xl p-6 flex justify-between items-center">
        <div>
          <p className="text-gray-500 text-sm mb-1">Current Estimated Price</p>
          <p className="text-4xl font-bold text-green-600">
            {result.predicted_price_cr}
          </p>
          <p className="text-gray-400 text-sm mt-1">
            ₹ {price.toLocaleString("en-IN")}
          </p>
        </div>
        <div className="text-6xl">🏡</div>
      </div>

      {/* Price Forecast */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-gray-700 mb-1">
          📈 Price Forecast
        </h3>
        <p className="text-xs text-gray-400 mb-4">
          Based on NRB 2023/24 macro indicators — CPI inflation 5.4% and housing inflation 8.2%
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-blue-700 text-white">
                <th className="px-4 py-2 text-left">Period</th>
                <th className="px-4 py-2 text-right">CPI Based (5.4%)</th>
                <th className="px-4 py-2 text-right">Housing Based (8.2%)</th>
                <th className="px-4 py-2 text-right">Change</th>
              </tr>
            </thead>
            <tbody>
              <tr className="bg-gray-50">
                <td className="px-4 py-2 font-medium">Now</td>
                <td className="px-4 py-2 text-right">
                  ₹ {price.toLocaleString("en-IN")}
                </td>
                <td className="px-4 py-2 text-right">
                  ₹ {price.toLocaleString("en-IN")}
                </td>
                <td className="px-4 py-2 text-right text-gray-400">—</td>
              </tr>
              {forecast.map((f, i) => (
                <tr key={f.year} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                  <td className="px-4 py-2 font-medium">{f.year}</td>
                  <td className="px-4 py-2 text-right text-blue-600">
                    ₹ {f.cpi.toLocaleString("en-IN")}
                  </td>
                  <td className="px-4 py-2 text-right text-green-600 font-medium">
                    ₹ {f.housing.toLocaleString("en-IN")}
                  </td>
                  <td className="px-4 py-2 text-right text-orange-500 font-medium">
                    +{(((f.housing - price) / price) * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* NRB Context */}
        <div className="mt-4 grid grid-cols-3 gap-3">
          {[
            { label: "CPI Inflation", value: "5.4%", icon: "📊" },
            { label: "Housing Inflation", value: "8.2%", icon: "🏠" },
            { label: "Lending Rate", value: "11.5%", icon: "🏦" },
          ].map((item) => (
            <div key={item.label} className="bg-blue-50 rounded-xl p-3 text-center">
              <div className="text-xl mb-1">{item.icon}</div>
              <p className="text-xs text-gray-500">{item.label}</p>
              <p className="font-bold text-blue-700">{item.value}</p>
            </div>
          ))}
        </div>

        <p className="text-xs text-gray-400 mt-3">
          ⚠️ Forecasts are estimates based on NRB FY 2023/24 annual data. 
          Actual prices depend on market conditions, location development, and economic factors.
        </p>
      </div>

    </div>
  );
}