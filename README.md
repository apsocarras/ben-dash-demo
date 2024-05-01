# Local Benefits Cliffs Dashboard Demo

Complete the following commands in your terminal.

0. Navigate to where you want this repo downloaded on your machine: 

```bash 

cd /path/to/your/desired/directory # e.g. a folder called Projects/
```

1. Clone this repo to your local directory: 

```bash
git clone # TO-DO 
```

2. Create & activate a python virtual environment: 

```bash
python3 -m venv venv 
source venv/bin/activate
```

**Be sure to run both of the above steps** to avoid installing any requirements into your base environment.

3. Install the required packages: 

```bash
pip install -r requirements.txt
```

4. Run `download_data.py` to download demo data files from Azure: 

```bash
python download_data.py
```

Note that `creds/` contains credentials to the storage container containing the example data and API keys to use the Skills Matcher. This isn't best practice but there is nothing sensitive here and I want to simplify this procedure for you.

5. Run `app.py` and open the demo dashboard in your browser:  

```bash
python app.py
```

You should see the following in the terminal where you ran this command: 

```bash
Dash is running on http://0.0.0.0:5001/

 * Serving Flask app 'app'
 * Debug mode: on

```

Copy the `http://` link into your browser window to view the app.