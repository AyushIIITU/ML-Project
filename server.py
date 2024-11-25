from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import os
import shutil
import uuid
import logging

logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://yourfrontenddomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to save uploaded and processed files
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        response_data = process_file(filepath)
        return JSONResponse(content=response_data)
    except Exception as e:
        logging.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


def process_file(filepath: str) -> dict:
    try:
        # Load the dataset
        df = pd.read_csv(filepath)
        logging.info(f"Loaded CSV with shape: {df.shape}")

        # Check if required columns are present
        required_columns = {'center_name', 'marks', 'sno'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"CSV is missing required columns: {required_columns - set(df.columns)}")
        
        # Group by center_name for clustering
        df_aggregated = df.groupby('center_name').agg(
            average_marks=('marks', 'mean'),
            number_of_students=('sno', 'count')
        ).reset_index()
        logging.info(f"Aggregated data: {df_aggregated.head()}")

        # Normalize the features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(df_aggregated[['average_marks', 'number_of_students']])
        logging.info(f"Scaled features: {scaled_features[:5]}")

        # Perform KMeans clustering
        kmeans = KMeans(n_clusters=6, random_state=42)
        df_aggregated['Cluster'] = kmeans.fit_predict(scaled_features)
        logging.info(f"Clustered data: {df_aggregated.head()}")

        # Create a summary for each cluster
        cluster_summary = (
            df_aggregated.groupby('Cluster')
            .agg(
                total_students=('number_of_students', 'sum'),
                average_marks=('average_marks', 'mean'),
                centers_in_cluster=('center_name', 'count')
            )
            .reset_index()
            .to_dict(orient='records')
        )
        logging.info(f"Cluster summary: {cluster_summary}")

        # Generate and save the graph
        cluster_data = df_aggregated.groupby('Cluster')['number_of_students'].sum().to_dict()
        # graph_filename = generate_graph(cluster_data)

        # Return the detailed response
        response_data = {
            "clusters": cluster_summary,
            "detailed_data": df_aggregated.to_dict(orient='records'),
            "cluster_data": cluster_data,
            # "graph_url": f"/uploads/{graph_filename}"
        }
        return response_data

    except Exception as e:
        logging.error(f"Error in process_file: {e}", exc_info=True)
        raise


def generate_graph(cluster_data: dict) -> str:
    try:
        clusters = list(cluster_data.keys())
        student_counts = list(cluster_data.values())

        plt.figure(figsize=(8, 6))
        plt.bar(clusters, student_counts, color='skyblue')
        plt.xlabel("Cluster")
        plt.ylabel("Number of Students")
        plt.title("Number of Students per Cluster")
        plt.xticks(clusters)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Save the graph
        graph_filename = f"cluster_graph_{uuid.uuid4().hex}.png"
        graph_path = os.path.join(UPLOAD_FOLDER, graph_filename)
        plt.savefig(graph_path)
        plt.close()

        logging.info(f"Graph saved as {graph_path}")
        return graph_filename

    except Exception as e:
        logging.error(f"Error generating graph: {e}", exc_info=True)
        raise


@app.get("/uploads/{graph_filename}")
async def get_graph(graph_filename: str):
    graph_path = os.path.join(UPLOAD_FOLDER, graph_filename)
    if os.path.exists(graph_path):
        return FileResponse(graph_path, media_type="image/png", filename=graph_filename)
    else:
        raise HTTPException(status_code=404, detail="Graph not found.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
