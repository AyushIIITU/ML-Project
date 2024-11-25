import "./App.css";
import axios from "axios";
import { useState } from "react";
import { Bar } from "react-chartjs-2";

// Import and register Chart.js components
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setResponse(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      const res = await axios.post("http://localhost:8000/upload/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResponse(res.data);
      setLoading(false);
      setError(null);
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.detail || "An error occurred.");
    }
  };

  const chartData = {
    labels: response?.cluster_data ? Object.keys(response.cluster_data) : [],
    datasets: [
      {
        label: "Number of Students per Cluster",
        data: response?.cluster_data ? Object.values(response.cluster_data) : [],
        backgroundColor: "rgba(75, 192, 192, 0.6)",
        borderColor: "rgba(75, 192, 192, 1)",
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: true, position: "top" },
    },
    scales: {
      x: { title: { display: true, text: "Clusters" } },
      y: { title: { display: true, text: "Number of Students" } },
    },
  };

  return (
    <div className="container">
      <div className="flex-container">
        <div className="card">
          <div className="upload-box">
            <div className="upload-text">
              <img
                alt="File Icon"
                className="upload-icon"
                src="https://img.icons8.com/dusk/64/csv.png"
              />
              <span className="first">Drag &amp; drop your files here</span>
              <span className="second">or click to upload</span>
            </div>
            <input
              name="file"
              className="file-input"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
            />
          </div>
          <button className="upload-button" onClick={handleUpload}>
            Upload File
          </button>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}
      {loading && <p className="loading-text">Loading...</p>}
      {response && (<>
         <div className="response-data">
         <h3>Cluster Summary</h3>
         {response.clusters.map((cluster, index) => (
           <div key={index} className="cluster-card">
             <p><strong>Cluster ID:</strong> {cluster.Cluster}</p>
             <p><strong>Total Students:</strong> {cluster.total_students}</p>
             <p><strong>Average Marks:</strong> {cluster.average_marks.toFixed(2)}</p>
             <p><strong>Centers in Cluster:</strong> {cluster.centers_in_cluster}</p>
           </div>
         ))}
         <div className="response-data">
          <h3>Cluster Data Chart</h3>
          <div className="chart-container">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>

         <h3>Detailed Data</h3>
         <table className="">
           <thead>
             <tr>
               <th>Center Name</th>
               <th>Average Marks</th>
               <th>Number of Students</th>
               <th>Cluster</th>
             </tr>
           </thead>
           <tbody>
             {response.detailed_data.map((data, index) => (
               <tr key={index}>
                 <td>{data.center_name}</td>
                 <td>{data.average_marks.toFixed(2)}</td>
                 <td>{data.number_of_students}</td>
                 <td>{data.Cluster}</td>
               </tr>
             ))}
           </tbody>
         </table>
        
        </div>
        </>
      )}
    </div>
  );
}

export default App;
