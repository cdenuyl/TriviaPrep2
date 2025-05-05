# Trivia Prep Hub - Deployment Instructions

This document provides instructions on how to set up and run the Trivia Prep Hub web application locally, and how to deploy it to Render using GitHub.

## Part 1: Local Setup Instructions

### Prerequisites

*   Python 3 (version 3.10 or higher recommended)
*   `pip` (Python package installer)
*   `virtualenv` (optional but recommended for isolating dependencies)

### Setup Steps

1.  **Unzip the Application:**
    *   Extract the contents of the `trivia_prep_app.zip` file to a location of your choice on your computer.

2.  **Navigate to the Directory:**
    *   Open a terminal or command prompt.
    *   Change directory into the extracted `trivia_prep_app` folder:
        ```bash
        cd path/to/trivia_prep_app
        ```

3.  **Create and Activate Virtual Environment (Recommended):**
    *   It's best practice to create a virtual environment to manage the project's dependencies separately.
        ```bash
        # Create the virtual environment (you only need to do this once)
        python3 -m venv venv 
        
        # Activate the virtual environment
        # On macOS/Linux:
        source venv/bin/activate
        # On Windows:
        .\venv\Scripts\activate 
        ```
    *   You should see `(venv)` at the beginning of your terminal prompt, indicating the virtual environment is active.

4.  **Install Dependencies:**
    *   Install the required Python packages using pip and the `requirements.txt` file:
        ```bash
        pip install -r requirements.txt
        ```

### Running Locally

1.  **Ensure Virtual Environment is Active:**
    *   If you closed your terminal, navigate back to the `trivia_prep_app` directory and activate the virtual environment again (Step 3).

2.  **Run the Flask App (Development Server):**
    *   Execute the main Python script:
        ```bash
        python src/main.py
        ```

3.  **Access the Application:**
    *   Open your web browser and go to:
        [http://127.0.0.1:5000](http://127.0.0.1:5000)
    *   You should see the Trivia Prep Hub interface.

### Using the Application

*   **Browse Trivia:** The main page displays current events, top music, top movies, and notable sports news.
*   **Update Data:** Click the "Update Trivia Data" button in the header to manually trigger a refresh of the trivia content. (Note: This currently uses placeholder data; a full implementation would re-scrape the web sources).
*   **Category Search:** Enter a topic (e.g., "World War II", "Astronomy") into the search box and click "Search Trivia" to get dynamically generated (currently simulated) trivia questions and answers.
*   **Geography Quiz:** Click "Start Geography Quiz" to begin an interactive quiz with map/image-based and text-based questions.

### Stopping the Local Application

*   Go back to the terminal where the application is running.
*   Press `Ctrl + C` to stop the Flask development server.

### Deactivating the Virtual Environment (Optional)

*   When you are finished working with the application, you can deactivate the virtual environment:
    ```bash
    deactivate
    ```

---

## Part 2: Deploying to Render via GitHub

### Prerequisites

*   A GitHub account.
*   Git installed on your local machine.
*   The application code extracted from the `trivia_prep_app.zip` file.

### Steps

1.  **Create a GitHub Repository:**
    *   Go to [GitHub](https://github.com/) and log in.
    *   Create a new repository. You can name it something like `trivia-prep-hub`. Choose whether to make it public or private.
    *   **Do not** initialize the repository with a README, .gitignore, or license file yet, as we will push the existing project files.

2.  **Prepare Local Project for Git:**
    *   Navigate to the `trivia_prep_app` directory in your terminal (where you extracted the zip file).
    *   Initialize a Git repository:
        ```bash
        git init -b main
        ```
    *   Create a `.gitignore` file to prevent unnecessary files (like the virtual environment) from being uploaded. Create a file named `.gitignore` in the `trivia_prep_app` directory and add the following lines:
        ```
        venv/
        __pycache__/
        *.pyc
        .DS_Store
        ```

3.  **Add and Commit Files:**
    *   Add all the project files to Git staging:
        ```bash
        git add .
        ```
    *   Commit the files:
        ```bash
        git commit -m "Initial commit of Trivia Prep Hub application"
        ```

4.  **Connect to GitHub Repository:**
    *   Add your GitHub repository as the remote origin. Replace `<YourGitHubUsername>` and `<YourRepoName>` with your actual username and repository name:
        ```bash
        git remote add origin https://github.com/<YourGitHubUsername>/<YourRepoName>.git
        ```

5.  **Push Code to GitHub:**
    *   Push your local `main` branch to GitHub:
        ```bash
        git push -u origin main
        ```
    *   You might be prompted to enter your GitHub credentials.

6.  **Deploy on Render:**
    *   Go to [Render](https://render.com/) and sign up or log in (you can use your GitHub account).
    *   Go to your Dashboard and click "New +" -> "Web Service".
    *   Connect your GitHub account if you haven't already.
    *   Select the GitHub repository you just created (`trivia-prep-hub` or similar).
    *   Configure the service:
        *   **Name:** Give your service a name (e.g., `trivia-prep-hub`).
        *   **Region:** Choose a region close to you.
        *   **Branch:** Ensure it's set to `main`.
        *   **Root Directory:** Leave this blank if your `requirements.txt` and `Procfile` are in the main directory of the repository.
        *   **Runtime:** Select `Python 3`.
        *   **Build Command:** `pip install -r requirements.txt` (Render should detect this).
        *   **Start Command:** `gunicorn src.main:app` (Render should detect this from the `Procfile`).
        *   **Plan:** Choose the `Free` plan for testing.
    *   Click "Create Web Service".

7.  **Monitor Deployment:**
    *   Render will automatically pull the code from GitHub, install dependencies, and start the application using Gunicorn.
    *   You can monitor the deployment progress in the "Events" and "Logs" tabs on Render.
    *   Once the deployment is successful, Render will provide you with a public URL (like `https://your-service-name.onrender.com`).

8.  **Access Deployed Application:**
    *   Visit the public URL provided by Render in your web browser.

Your Trivia Prep Hub should now be live on Render!

