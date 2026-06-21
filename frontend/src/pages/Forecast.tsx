import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { generateForecast, ForecastPointResponse } from "../api/forecast";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export const Forecast: React.FC = () => {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentPathPoints, setCurrentPathPoints] = useState<ForecastPointResponse[]>([]);
  const [recommendedPathPoints, setRecommendedPathPoints] = useState<ForecastPointResponse[]>([]);
  const [customPathPoints, setCustomPathPoints] = useState<ForecastPointResponse[]>([]);

  useEffect(() => {
    const fetchForecasts = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Generate all 3 forecasts simultaneously
        const [current, recommended, custom] = await Promise.all([
          generateForecast({ forecast_type: "current_path" }),
          generateForecast({ forecast_type: "recommended_path" }),
          generateForecast({
            forecast_type: "custom_path",
            custom_rates: { transport: 0.1, energy: 0.1, food: 0.1, waste: 0.1 }
          })
        ]);

        // Ensure points are sorted by month_offset
        const sortByOffset = (a: ForecastPointResponse, b: ForecastPointResponse) => a.month_offset - b.month_offset;

        setCurrentPathPoints([...current.forecast_points].sort(sortByOffset));
        setRecommendedPathPoints([...recommended.forecast_points].sort(sortByOffset));
        setCustomPathPoints([...custom.forecast_points].sort(sortByOffset));

      } catch (_err: unknown) {
        const err = _err instanceof Error ? _err : new Error(String(_err));
        if ((err as any).response?.status === 422) {
          setError("No carbon assessment found. Please complete an assessment first.");
        } else {
          setError(err.message || "Failed to generate forecasts.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchForecasts();
  }, []);

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center p-4">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-earth-green"></div>
          <p className="mt-4 text-muted dark:text-muted">Generating forecast models...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center p-4">
        <div className="max-w-md rounded-2xl bg-red-50 p-6 text-center text-red-600 dark:bg-red-900/20 dark:text-red-400">
          <p className="font-medium">{error}</p>
          <button
            onClick={() => navigate("/assessment")}
            className="mt-4 rounded-xl bg-red-100 px-4 py-2 font-medium text-red-700 hover:bg-red-200 dark:bg-red-900/40 dark:text-red-300 dark:hover:bg-red-900/60"
          >
            Take Assessment
          </button>
        </div>
      </div>
    );
  }

  // Chart configuration
  const labels = ["3 Months", "6 Months", "12 Months"];

  const data = {
    labels,
    datasets: [
      {
        label: "Current Path",
        data: currentPathPoints.map((p) => p.predicted_emission),
        borderColor: "rgb(239, 68, 68)", // Red
        backgroundColor: "rgba(239, 68, 68, 0.5)",
        tension: 0.3,
      },
      {
        label: "Recommended Path",
        data: recommendedPathPoints.map((p) => p.predicted_emission),
        borderColor: "rgb(16, 185, 129)", // Green
        backgroundColor: "rgba(16, 185, 129, 0.5)",
        tension: 0.3,
      },
      {
        label: "Custom Path",
        data: customPathPoints.map((p) => p.predicted_emission),
        borderColor: "rgb(59, 130, 246)", // Blue
        backgroundColor: "rgba(59, 130, 246, 0.5)",
        tension: 0.3,
        borderDash: [5, 5], // Make it dashed to distinguish
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
        labels: {
          color: "rgb(156, 163, 175)", // gray-400
        }
      },
      title: {
        display: true,
        text: "Emission Forecast (kg CO₂e)",
        color: "rgb(156, 163, 175)", // gray-400
        font: { size: 16 }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: "rgba(156, 163, 175, 0.1)" },
        ticks: { color: "rgb(156, 163, 175)" }
      },
      x: {
        grid: { display: false },
        ticks: { color: "rgb(156, 163, 175)" }
      }
    }
  };

  return (
    <div className="p-4 md:p-8 animate-fade-in max-w-7xl mx-auto">
      <div className="mb-8 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-primary text-primary">
            Future Projection
          </h1>
          <p className="mt-2 text-muted dark:text-muted">
            See how your carbon footprint could evolve over the next year.
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Chart Section */}
        <div className="col-span-1 lg:col-span-3 rounded-2xl bg-bg-secondary p-6 shadow-sm ring-1 ring-slate-200 dark:bg-bg-secondary dark:ring-slate-800">
          <div className="h-80 w-full">
            <Line options={options} data={data} />
          </div>
        </div>

        {/* Callout Cards for Recommended Path */}
        <div className="col-span-1 lg:col-span-3">
          <h2 className="text-xl font-bold mb-4 text-primary text-primary">Recommended Path Trajectory</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {recommendedPathPoints.map((point) => (
              <div key={point.id} className="rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 p-6 ring-1 ring-emerald-100 dark:from-emerald-950/40 dark:to-teal-900/40 dark:ring-emerald-900/50 flex flex-col justify-between items-start">
                <div>
                  <div className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
                    At {point.month_offset} Months
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-bold tracking-tight text-emerald-950 dark:text-emerald-100">
                      {point.predicted_emission.toFixed(1)}
                    </span>
                    <span className="text-sm font-medium text-emerald-700 dark:text-earth-green">
                      kg CO₂e
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-8 flex justify-center">
             <button
                onClick={() => navigate("/coach")}
                className="group relative overflow-hidden rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-8 py-3 font-semibold text-primary shadow-lg transition-all hover:scale-[1.02] hover:shadow-emerald-500/25 active:scale-95"
              >
                <div className="absolute inset-0 bg-bg-secondary/20 opacity-0 transition-opacity group-hover:opacity-100"></div>
                <span className="relative flex items-center gap-2">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  How to achieve this with AI Coach
                </span>
             </button>
          </div>
        </div>
      </div>
    </div>
  );
};
