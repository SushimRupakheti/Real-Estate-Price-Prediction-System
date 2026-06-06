export default function ResultCard({ result }) {
  return (
    <div className="mt-6 bg-green-50 border border-green-200 rounded-2xl shadow p-6 text-center">
      <p className="text-gray-500 text-sm mb-1">Estimated House Price</p>
      <p className="text-4xl font-bold text-green-600">{result.predicted_price_cr}</p>
      <p className="text-gray-400 text-sm mt-2">
        ₹ {result.predicted_price.toLocaleString("en-IN")}
      </p>
    </div>
  );
}